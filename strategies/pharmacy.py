import tkinter as tk
from tkinter import messagebox
from .base import CareStageStrategy

class PharmacyStrategy(CareStageStrategy):
    def build_interface(self, parent):
        tk.Label(parent, text="💊 Precision Pharmacy", font=('Arial', 16, 'bold'), fg="#AB47BC", bg="#0B1120").pack(pady=10)
        
        tk.Label(parent, text="Prescription: Lisinopril 10mg", fg="white", bg="#0B1120").pack()
        tk.Label(parent, text="Scanning for interactions...", fg="#64FFDA", bg="#0B1120").pack(pady=10)
        
        tk.Button(parent, text="Verify TxGemma Safety", command=lambda: self.process_action("Safety")).pack()

    def process_action(self, data):
        messagebox.showwarning("Interaction Alert", "Potential Lifestyle-Drug Interaction detected with high sodium intake.")
