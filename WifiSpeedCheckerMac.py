import customtkinter as ctk
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import speedtest
import threading
import time
from collections import deque
from plyer import notification

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")  # You can try "dark-blue" too

SAMPLE_INTERVAL = 1  # seconds
GRAPH_SECONDS = 120

class SpeedCheckerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WiFi Speed Checker — Real-time Dark macOS UI")
        self.geometry("650x540")
        self.resizable(False, False)
        self.configure(fg_color="#232323")

        self.last_notification = 0
        self.last_speed_state = None

        self.speed_history = deque([0] * GRAPH_SECONDS, maxlen=GRAPH_SECONDS)
        self.time_history = deque(range(-GRAPH_SECONDS + 1, 1), maxlen=GRAPH_SECONDS)

        # ========== UI Layout ==========
        self.main_frame = ctk.CTkFrame(self, corner_radius=18, fg_color="#232323")
        self.main_frame.pack(fill="both", expand=True, padx=22, pady=22)

        self.speed_label = ctk.CTkLabel(self.main_frame, text="Download: -- Mbps", font=("San Francisco", 28, "bold"), text_color="#fff")
        self.speed_label.pack(pady=(18, 6))
        self.upload_label = ctk.CTkLabel(self.main_frame, text="Upload: -- Mbps", font=("San Francisco", 20), text_color="#dedede")
        self.upload_label.pack()
        self.ping_label = ctk.CTkLabel(self.main_frame, text="Ping: -- ms", font=("San Francisco", 20), text_color="#dedede")
        self.ping_label.pack(pady=5)

        self.status_alert = ctk.CTkLabel(self.main_frame, text="", font=("San Francisco", 18), text_color="#ff453a")
        self.status_alert.pack(pady=5)

        self.check_button = ctk.CTkButton(self.main_frame, text="Speed Test Now", corner_radius=16, font=("San Francisco", 18), width=190, height=36, command=self.check_speed_once)
        self.check_button.pack(pady=14)

        # ========== Matplotlib Graph ==========
        self.fig = Figure(figsize=(6, 2.3), dpi=100, facecolor="#232323")
        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.07, right=0.98, bottom=0.2, top=0.85)
        self.ax.set_facecolor("#232323")
        self.ax.tick_params(colors="#aaa", labelsize=10)
        self.ax.spines['bottom'].set_color('#bbb')
        self.ax.spines['left'].set_color('#bbb')
        self.plot_line, = self.ax.plot(list(self.time_history), list(self.speed_history), color="#28befa", linewidth=2.5)

        self.ax.set_xlabel("Seconds Ago", color="#bbb", fontsize=12)
        self.ax.set_ylabel("Mbps", color="#bbb", fontsize=13)
        self.ax.set_xlim(-GRAPH_SECONDS, 0)
        self.ax.set_ylim(0, 120)
        self.ax.grid(True, color="#3c3c3c", alpha=0.7)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(padx=6, pady=8)

        # ========== Real-Time Monitoring ==========
        self.running = True
        threading.Thread(target=self.real_time_speed, daemon=True).start()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def notify(self, title, message):
        try:
            notification.notify(title=title, message=message, app_name="WiFi Speed Checker", timeout=5)
        except Exception:
            pass  # Notification is best-effort

    def update_plot(self):
        self.plot_line.set_ydata(list(self.speed_history))
        self.canvas.draw()

    def check_speed_once(self):
        threading.Thread(target=self._check_speed, daemon=True).start()

    def _check_speed(self):
        self.status_alert.configure(text="Testing...")
        try:
            st = speedtest.Speedtest()
            download = st.download() / 1_000_000
            upload = st.upload() / 1_000_000
            ping = st.results.ping

            self.speed_label.configure(text=f"Download: {download:.2f} Mbps")
            self.upload_label.configure(text=f"Upload: {upload:.2f} Mbps")
            self.ping_label.configure(text=f"Ping: {ping:.2f} ms")
            self.status_alert.configure(text="")
        except Exception as e:
            self.status_alert.configure(text="Error: " + str(e))

    def real_time_speed(self):
        st = speedtest.Speedtest()
        low_speed_pending = False
        pending_timer = 0

        while self.running:
            try:
                download = st.download() / 1_000_000
                upload = st.upload() / 1_000_000
                ping = st.results.ping

                # Store to deque
                self.speed_history.append(download)
                self.time_history.append(self.time_history[-1]+1)
                self.ax.set_ylim(0, max(100, max(self.speed_history) + 5))

                self.after(0, self.update_realtime_labels, download, upload, ping)
                self.after(0, self.update_plot)

                # Live alert 5 seconds before drop
                if download < 15:  # threshold for "drop"
                    if not low_speed_pending:
                        low_speed_pending = True
                        pending_timer = time.time()
                    elif time.time() - pending_timer >= 5:
                        self.after(0, self.status_alert.configure, {"text": "⚠️ Speed Drop Warning!", "text_color": "#ff453a"})
                        if time.time() - self.last_notification > 15:
                            self.notify("WiFi Speed Alert", "Your speed is dropping!")
                            self.last_notification = time.time()
                else:
                    low_speed_pending = False
                    self.after(0, self.status_alert.configure, {"text": "", "text_color": "#ff453a"})
                time.sleep(SAMPLE_INTERVAL)
            except Exception as e:
                self.after(0, self.status_alert.configure, {"text": f"Error: {e}", "text_color": "#ff453a"})
                time.sleep(3)

    def update_realtime_labels(self, download, upload, ping):
        self.speed_label.configure(text=f"Download: {download:.2f} Mbps")
        self.upload_label.configure(text=f"Upload: {upload:.2f} Mbps")
        self.ping_label.configure(text=f"Ping: {ping:.2f} ms")
        
    def on_close(self):
        self.running = False
        self.destroy()

if __name__ == "__main__":
    app = SpeedCheckerApp()
    app.mainloop()
