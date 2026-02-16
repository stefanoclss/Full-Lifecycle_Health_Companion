import tkinter as tk
from .base import CareStageStrategy

class ConsultStrategy(CareStageStrategy):
    def build_interface(self, parent):
        tk.Label(parent, text="🩺 Clinical Consultation", font=('Arial', 16, 'bold'), fg="#FFA726", bg="#0B1120").pack(pady=10)
        
        btn_frame = tk.Frame(parent, bg="#0B1120")
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Analyze CXR (X-Ray)", width=20).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(btn_frame, text="Live Transcription", width=20).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(btn_frame, text="Pathology View", width=20).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(btn_frame, text="Differential DX", width=20).grid(row=1, column=1, padx=5, pady=5)

    def process_action(self, data):
        pass
