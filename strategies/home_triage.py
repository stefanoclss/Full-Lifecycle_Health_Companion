import tkinter as tk
from tkinter import messagebox
from .base import CareStageStrategy

class HomeTriageStrategy(CareStageStrategy):
    def build_interface(self, parent):
        tk.Label(parent, text="🏠 Home Self-Triage", font=('Arial', 16, 'bold'), fg="#4FC3F7", bg="#0B1120").pack(pady=10)
        tk.Label(parent, text="MedASR Voice / Derm Photo Triage", fg="#8892B0", bg="#0B1120").pack()
        
        self.input = tk.Entry(parent, width=40)
        self.input.insert(0, "Describe symptoms or upload photo path...")
        self.input.pack(pady=20)
        
        tk.Button(parent, text="Run Edge AI Analysis", command=lambda: self.process_action(self.input.get())).pack()

    def process_action(self, data):
        messagebox.showinfo("MedGemma-4b", f"Analyzing: {data}\nResult: Priority Level 2 - Suggested Clinic Visit.")
