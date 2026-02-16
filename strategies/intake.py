import tkinter as tk
from tkinter import ttk, messagebox
from .base import CareStageStrategy

class IntakeStrategy(CareStageStrategy):
    def build_interface(self, parent):
        tk.Label(parent, text="📋 Pre-Consult Intake", font=('Arial', 16, 'bold'), fg="#66BB6A", bg="#0B1120").pack(pady=10)
        
        cols = ('Field', 'Value')
        tree = ttk.Treeview(parent, columns=cols, show='headings', height=5)
        tree.heading('Field', text='Intake Question')
        tree.heading('Value', text='Patient Response')
        tree.insert('', 'end', values=("Occupation", "Construction - High Activity"))
        tree.insert('', 'end', values=("Smoker", "No"))
        tree.pack(pady=10)
        
        tk.Button(parent, text="Generate SOAP Note", command=lambda: self.process_action("SOAP")).pack()

    def process_action(self, data):
        messagebox.showinfo("MedGemma-27b", "SOAP Note Generated: [Subjective: Patient reports back pain...]")
