import customtkinter as ctk
from tkinter import filedialog, messagebox
import subprocess
import threading
import os

class ModernGUI:
    def __init__(self, master):
        self.master = master
        master.title("Zero-Shot Traffic Control Pipeline")
        master.geometry("800x700")

        ctk.set_appearance_mode("Light")

        # --- Main Layout ---
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(master, corner_radius=0)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # --- Notebook for Tabs ---
        self.tab_view = ctk.CTkTabview(main_frame, corner_radius=8)
        self.tab_view.grid(row=0, column=0, sticky="nsew")
        self.tab_view.add("SUMO Setup")
        self.tab_view.add("Training")
        self.tab_view.add("Evaluation")

        # --- Log Frame ---
        log_frame = ctk.CTkFrame(main_frame, corner_radius=8)
        log_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)

        self.log_text = ctk.CTkTextbox(log_frame, state="disabled", corner_radius=6, wrap="word")
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # --- Populate Tabs ---
        self.create_sumo_setup_tab(self.tab_view.tab("SUMO Setup"))
        self.create_training_tab(self.tab_view.tab("Training"))
        self.create_evaluation_tab(self.tab_view.tab("Evaluation"))

    def create_file_input(self, parent, label_text, string_var, row):
        label = ctk.CTkLabel(parent, text=label_text)
        label.grid(row=row, column=0, sticky="w", padx=20, pady=(10, 5))

        entry = ctk.CTkEntry(parent, textvariable=string_var, corner_radius=6)
        entry.grid(row=row, column=1, sticky="ew", padx=10, pady=(10, 5))

        button = ctk.CTkButton(parent, text="Browse...", width=100, corner_radius=6, command=lambda: self.select_file(string_var))
        button.grid(row=row, column=2, sticky="e", padx=(0, 20), pady=(10, 5))
        parent.grid_columnconfigure(1, weight=1)

    def create_sumo_setup_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        
        info_label = ctk.CTkLabel(tab, text="Define the core simulation files for the environment.", wraplength=500)
        info_label.grid(row=0, column=0, columnspan=3, padx=20, pady=10)

        self.net_file = ctk.StringVar()
        self.route_file = ctk.StringVar()
        self.add_file = ctk.StringVar()

        self.create_file_input(tab, "Network File (.net.xml):", self.net_file, 1)
        self.create_file_input(tab, "Routes File (.rou.xml):", self.route_file, 2)
        self.create_file_input(tab, "Additional Files (.add.xml):", self.add_file, 3)

    def create_training_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)

        self.training_data_path = ctk.StringVar()
        self.create_file_input(tab, "High-Fidelity Training Data (.csv):", self.training_data_path, 0)

        # Agent Selection
        agent_frame = ctk.CTkFrame(tab, fg_color="transparent")
        agent_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=20, pady=5)
        ctk.CTkLabel(agent_frame, text="Agent to Train:").grid(row=0, column=0, sticky="w")
        self.agent_to_train = ctk.StringVar(value="dqn")
        agent_menu = ctk.CTkOptionMenu(agent_frame, variable=self.agent_to_train, values=["dqn", "d3qn", "q-learning"], corner_radius=6)
        agent_menu.grid(row=0, column=1, sticky="w", padx=10)

        # Episodes
        episodes_frame = ctk.CTkFrame(tab, fg_color="transparent")
        episodes_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=20, pady=5)
        ctk.CTkLabel(episodes_frame, text="Training Episodes:").grid(row=0, column=0, sticky="w")
        self.training_episodes = ctk.StringVar(value="150")
        episodes_entry = ctk.CTkEntry(episodes_frame, textvariable=self.training_episodes, corner_radius=6, width=120)
        episodes_entry.grid(row=0, column=1, sticky="w", padx=10)

        self.train_button = ctk.CTkButton(tab, text="Start Training", corner_radius=6, command=self.run_training)
        self.train_button.grid(row=3, column=0, columnspan=3, sticky="e", padx=20, pady=20)

    def create_evaluation_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)

        self.model_path = ctk.StringVar()
        self.create_file_input(tab, "Trained Model File (.pth/.pkl):", self.model_path, 0)

        self.eval_scenario = ctk.StringVar(value="A")
        radio_frame = ctk.CTkFrame(tab, fg_color="transparent")
        radio_frame.grid(row=1, column=0, columnspan=3, padx=20, pady=10, sticky="w")
        ctk.CTkRadioButton(radio_frame, text="Scenario A (Rich Data)", variable=self.eval_scenario, value="A").pack(side="left")
        ctk.CTkRadioButton(radio_frame, text="Scenario B (AADT)", variable=self.eval_scenario, value="B").pack(side="left", padx=20)

        self.eval_data_path = ctk.StringVar()
        self.create_file_input(tab, "Evaluation Data (.csv):", self.eval_data_path, 2)

        aadt_frame = ctk.CTkFrame(tab, fg_color="transparent")
        aadt_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=20, pady=5)
        ctk.CTkLabel(aadt_frame, text="AADT Value:").grid(row=0, column=0, sticky="w")
        self.aadt_value = ctk.StringVar(value="1000")
        aadt_entry = ctk.CTkEntry(aadt_frame, textvariable=self.aadt_value, corner_radius=6, width=120)
        aadt_entry.grid(row=0, column=1, sticky="w", padx=10)

        # Options & Control
        control_frame = ctk.CTkFrame(tab, fg_color="transparent")
        control_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=20, pady=20)
        self.use_gui = ctk.StringVar(value="on")
        gui_check = ctk.CTkCheckBox(control_frame, text="Show SUMO GUI", variable=self.use_gui, onvalue="on", offvalue="off")
        gui_check.pack(side="left")
        self.eval_button = ctk.CTkButton(control_frame, text="Run Evaluation", corner_radius=6, command=self.run_evaluation)
        self.eval_button.pack(side="right")

    def select_file(self, string_var):
        file_path = filedialog.askopenfilename()
        if file_path:
            string_var.set(file_path)

    def log(self, message):
        self.master.after(0, self._log, message)

    def _log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def run_training(self):
        self.log("--- Starting Training Pipeline ---")
        self.log("\n")
        # Placeholder for actual logic
        self.log("Training logic not implemented in this UI yet.")
        self.log("\n")

    def run_evaluation(self):
        self.log("--- Starting Evaluation Pipeline ---")
        self.log("\n")
        # Placeholder for actual logic
        self.log("Evaluation logic not implemented in this UI yet.")
        self.log("\n")

if __name__ == "__main__":
    root = ctk.CTk()
    app = ModernGUI(root)
    root.mainloop()
