import tkinter as tk
from strategies import (
    HomeTriageStrategy,
    IntakeStrategy,
    ConsultStrategy,
    PharmacyStrategy,
    MonitoringStrategy
)

# --- The Context (The Application) ---
class HealthCompanionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ArcVault: Full-Lifecycle Health Companion")
        
        # Set FULL SCREEN
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", self.exit_fullscreen)

        self.root.configure(bg="#0B1120")

        # Sidebar / Navigation
        self.nav_frame = tk.Frame(self.root, bg="#131B33", width=150)
        self.nav_frame.pack(side="left", fill="y")
        
        self.content_frame = tk.Frame(self.root, bg="#0B1120")
        self.content_frame.pack(side="right", expand=True, fill="both", padx=20, pady=20)

        # Strategies mapping
        self.strategies = {
            "Triage": HomeTriageStrategy(),
            "Intake": IntakeStrategy(),
            "Consult": ConsultStrategy(),
            "Pharmacy": PharmacyStrategy(),
            "Monitoring": MonitoringStrategy()
        }

        self.setup_nav()
        self.set_stage("Triage") # Default starting point

    def setup_nav(self):
        for stage_name in self.strategies.keys():
            btn = tk.Button(self.nav_frame, text=stage_name, 
                            command=lambda s=stage_name: self.set_stage(s),
                            bg="#131B33", fg="white", relief="flat", pady=10)
            btn.pack(fill="x")

    def set_stage(self, stage_name):
        # Clear current content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Apply Strategy
        strategy = self.strategies[stage_name]
        strategy.build_interface(self.content_frame)

    def exit_fullscreen(self, event=None):
        self.root.attributes('-fullscreen', False)
        # Optional: Uncomment the next line to close the app on Escape instead
        # self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = HealthCompanionApp(root)
    root.mainloop()
