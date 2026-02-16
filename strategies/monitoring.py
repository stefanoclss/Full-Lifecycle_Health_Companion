import tkinter as tk
from .base import CareStageStrategy

class MonitoringStrategy(CareStageStrategy):
    def build_interface(self, parent):
        tk.Label(parent, text="📉 Continuous Monitoring", font=('Arial', 16, 'bold'), fg="#EF5350", bg="#0B1120").pack(pady=10)
        
        canvas = tk.Canvas(parent, width=300, height=100, bg="#131B33", highlightthickness=0)
        canvas.pack(pady=10)
        # Mock Recovery Trajectory
        canvas.create_line(0, 80, 50, 70, 100, 40, 200, 30, 300, 10, fill="#64FFDA", width=3)
        
        tk.Label(parent, text="Recovery Trajectory: On Track", fg="#64FFDA", bg="#0B1120").pack()

    def process_action(self, data):
        pass
