import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import os

class SimulationGUI:
    def __init__(self, master):
        self.master = master
        master.title("Zero-Shot Traffic Control Pipeline")
        master.geometry("700x600")

        main_frame = tk.Frame(master)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)

        self.training_tab = tk.Frame(self.notebook)
        self.evaluation_tab = tk.Frame(self.notebook)

        self.notebook.add(self.training_tab, text="Training")
        self.notebook.add(self.evaluation_tab, text="Evaluation")

        log_frame = tk.LabelFrame(main_frame, text="Logs")
        log_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.log_text = tk.Text(log_frame, height=15, state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        scrollbar = tk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        self.create_training_tab()
        self.create_evaluation_tab()

    def create_training_tab(self):
        tab = self.training_tab
        config_frame = tk.LabelFrame(tab, text="Phase 1: Train Agent")
        config_frame.pack(padx=10, pady=10, fill="x")

        self.training_data_path = tk.StringVar()
        self.create_file_input(config_frame, "High-Fidelity Training Data (.csv):", self.training_data_path, 0)

        tk.Label(config_frame, text="Agent to Train:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.agent_to_train = tk.StringVar(value="dqn")
        agent_menu = ttk.Combobox(config_frame, textvariable=self.agent_to_train, values=["dqn", "d3qn", "q-learning"], state="readonly")
        agent_menu.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        tk.Label(config_frame, text="Training Episodes:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.training_episodes = tk.StringVar(value="150")
        episodes_entry = tk.Entry(config_frame, textvariable=self.training_episodes)
        episodes_entry.grid(row=2, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        control_frame = tk.Frame(tab)
        control_frame.pack(padx=10, pady=10, fill="x")
        self.train_button = tk.Button(control_frame, text="Start Training", command=self.run_training)
        self.train_button.pack(side="right")

    def create_evaluation_tab(self):
        tab = self.evaluation_tab
        model_frame = tk.LabelFrame(tab, text="Phase 2: Select Model for Evaluation")
        model_frame.pack(padx=10, pady=10, fill="x")
        self.model_path = tk.StringVar()
        self.create_file_input(model_frame, "Trained Model File (.pth/.pkl):", self.model_path, 0)

        self.eval_scenario = tk.StringVar(value="A")
        scenario_a_frame = tk.LabelFrame(tab, text="Scenario A: Evaluate with Rich Data")
        scenario_a_frame.pack(padx=10, pady=5, fill="x")
        scenario_b_frame = tk.LabelFrame(tab, text="Scenario B: Evaluate with AADT (Zero-Shot)")
        scenario_b_frame.pack(padx=10, pady=5, fill="x")

        tk.Radiobutton(scenario_a_frame, text="Use this scenario", variable=self.eval_scenario, value="A", command=self.toggle_scenario_frames).grid(row=0, column=0, columnspan=3, sticky="w")
        self.eval_data_path = tk.StringVar()
        self.create_file_input(scenario_a_frame, "Evaluation Data (.csv):", self.eval_data_path, 1)

        tk.Radiobutton(scenario_b_frame, text="Use this scenario", variable=self.eval_scenario, value="B", command=self.toggle_scenario_frames).grid(row=0, column=0, columnspan=2, sticky="w")
        tk.Label(scenario_b_frame, text="AADT Value:").grid(row=1, column=0, sticky="w", padx=(25,5), pady=5)
        self.aadt_value = tk.StringVar(value="1000")
        aadt_entry = tk.Entry(scenario_b_frame, textvariable=self.aadt_value)
        aadt_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        self.scenario_frames = {"A": scenario_a_frame, "B": scenario_b_frame}
        self.toggle_scenario_frames()

        control_frame = tk.Frame(tab)
        control_frame.pack(padx=10, pady=10, fill="x")
        self.use_gui = tk.BooleanVar()
        gui_check = tk.Checkbutton(control_frame, text="Show SUMO GUI", variable=self.use_gui)
        gui_check.pack(side="left")
        self.eval_button = tk.Button(control_frame, text="Run Evaluation", command=self.run_evaluation)
        self.eval_button.pack(side="right")

    def toggle_scenario_frames(self):
        selected = self.eval_scenario.get()
        for key, frame in self.scenario_frames.items():
            for child in frame.winfo_children():
                if str(child) not in [str(frame), str(self.master)]:
                    is_radio = isinstance(child, tk.Radiobutton)
                    if not is_radio:
                        if key == selected:
                            if hasattr(child, 'configure'): child.configure(state="normal")
                        else:
                            if hasattr(child, 'configure'): child.configure(state="disabled")

    def create_file_input(self, parent, label_text, string_var, row):
        label = tk.Label(parent, text=label_text)
        label.grid(row=row, column=0, sticky="w", padx=5, pady=2)
        entry = tk.Entry(parent, textvariable=string_var, width=60)
        entry.grid(row=row, column=1, padx=5, pady=2)
        button = tk.Button(parent, text="Browse...", command=lambda: self.select_file(string_var))
        button.grid(row=row, column=2, padx=5, pady=2)

    def select_file(self, string_var):
        file_path = filedialog.askopenfilename()
        if file_path:
            string_var.set(file_path)

    def log(self, message):
        self.master.after(0, self._log, message)

    def _log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def run_training(self):
        self.log("--- Starting Training Pipeline ---")
        self.log("\n")
        if not self.training_data_path.get():
            messagebox.showerror("Error", "Please select a training data file.")
            return
        self.log("Step 1: Pre-processing data (Not Implemented)...")
        self.log("\n")
        self.log("Step 2: Generating forecasts (Not Implemented)...")
        self.log("\n")
        trainer_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'trainer.py'))
        command = ["python", trainer_path, "--agent", self.agent_to_train.get(), "--episodes", self.training_episodes.get()]
        command_str = ' '.join(command)
        self.log("Step 3: Running trainer...")
        self.log("\n")
        self.log(f"Command: {command_str}")
        self.log("\n\n")
        self.execute_command(command, self.train_button)

    def run_evaluation(self):
        self.log("--- Starting Evaluation Pipeline ---")
        self.log("\n")
        if not self.model_path.get():
            messagebox.showerror("Error", "Please select a trained model file.")
            return
        scenario = self.eval_scenario.get()
        if scenario == "A" and not self.eval_data_path.get():
            messagebox.showerror("Error", "Please select evaluation data for Scenario A.")
            return
        if scenario == "B" and not self.aadt_value.get():
            messagebox.showerror("Error", "Please enter an AADT value for Scenario B.")
            return
        if scenario == "A":
            self.log("Scenario A: Pre-processing rich data (Not Implemented)...")
            self.log("\n")
        else:
            self.log("Scenario B: Generating data from AADT (Not Implemented)...")
            self.log("\n")
        runner_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'runner.py'))
        command = ["python", runner_path, "--model-path", self.model_path.get()]
        if self.use_gui.get():
            command.append("--gui")
        command_str = ' '.join(command)
        self.log("Running evaluation...")
        self.log("\n")
        self.log(f"Command: {command_str}")
        self.log("\n\n")
        self.execute_command(command, self.eval_button)

    def execute_command(self, command, button):
        button.config(state="disabled")
        thread = threading.Thread(target=self._execute_command_thread, args=(command, button))
        thread.start()

    def _execute_command_thread(self, command, button):
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            for line in iter(process.stdout.readline, ''):
                self.log(line)
            process.wait()
        except Exception as e:
            self.log(f"ERROR: {e}")
            self.log("\n")
        finally:
            self.master.after(0, self.on_command_finish, button)

    def on_command_finish(self, button):
        self.log("\n--- Process Finished ---\n")
        button.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = SimulationGUI(root)
    root.mainloop()
