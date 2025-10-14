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

        self.log_text = ctk.CTkTextbox(
            log_frame, state="disabled", corner_radius=6, wrap="word"
        )
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

        button = ctk.CTkButton(
            parent,
            text="Browse...",
            width=100,
            corner_radius=6,
            command=lambda: self.select_file(string_var),
        )
        button.grid(row=row, column=2, sticky="e", padx=(0, 20), pady=(10, 5))
        parent.grid_columnconfigure(1, weight=1)

    def create_sumo_setup_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)

        info_label = ctk.CTkLabel(
            tab,
            text="Define the core simulation files for the environment.",
            wraplength=500,
        )
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
        self.create_file_input(
            tab, "High-Fidelity Training Data (.csv):", self.training_data_path, 0
        )

        # Agent Selection
        agent_frame = ctk.CTkFrame(tab, fg_color="transparent")
        agent_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=20, pady=5)
        ctk.CTkLabel(agent_frame, text="Agent to Train:").grid(
            row=0, column=0, sticky="w"
        )
        self.agent_to_train = ctk.StringVar(value="dqn")
        agent_menu = ctk.CTkOptionMenu(
            agent_frame,
            variable=self.agent_to_train,
            values=["dqn", "d3qn", "q-learning"],
            corner_radius=6,
        )
        agent_menu.grid(row=0, column=1, sticky="w", padx=10)

        # Episodes
        episodes_frame = ctk.CTkFrame(tab, fg_color="transparent")
        episodes_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=20, pady=5)
        ctk.CTkLabel(episodes_frame, text="Training Episodes:").grid(
            row=0, column=0, sticky="w"
        )
        self.training_episodes = ctk.StringVar(value="150")
        episodes_entry = ctk.CTkEntry(
            episodes_frame,
            textvariable=self.training_episodes,
            corner_radius=6,
            width=120,
        )
        episodes_entry.grid(row=0, column=1, sticky="w", padx=10)

        self.train_button = ctk.CTkButton(
            tab, text="Start Training", corner_radius=6, command=self.run_training
        )
        self.train_button.grid(
            row=3, column=0, columnspan=3, sticky="e", padx=20, pady=20
        )

    def create_evaluation_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)

        self.model_path = ctk.StringVar()
        self.create_file_input(
            tab, "Trained Model File (.pth/.pkl):", self.model_path, 0
        )

        # Agent Selection
        agent_frame_eval = ctk.CTkFrame(tab, fg_color="transparent")
        agent_frame_eval.grid(
            row=1, column=0, columnspan=3, sticky="ew", padx=20, pady=5
        )
        ctk.CTkLabel(agent_frame_eval, text="Agent to Evaluate:").grid(
            row=0, column=0, sticky="w"
        )
        self.agent_to_evaluate = ctk.StringVar(value="dqn")
        agent_menu_eval = ctk.CTkOptionMenu(
            agent_frame_eval,
            variable=self.agent_to_evaluate,
            values=["dqn", "d3qn", "q-learning"],
            corner_radius=6,
        )
        agent_menu_eval.grid(row=0, column=1, sticky="w", padx=10)

        self.eval_scenario = ctk.StringVar(value="A")
        radio_frame = ctk.CTkFrame(tab, fg_color="transparent")
        radio_frame.grid(row=2, column=0, columnspan=3, padx=20, pady=10, sticky="w")
        ctk.CTkRadioButton(
            radio_frame,
            text="Scenario A (Rich Data)",
            variable=self.eval_scenario,
            value="A",
        ).pack(side="left")
        ctk.CTkRadioButton(
            radio_frame,
            text="Scenario B (AADT)",
            variable=self.eval_scenario,
            value="B",
        ).pack(side="left", padx=20)

        self.eval_data_path = ctk.StringVar()
        self.create_file_input(tab, "Evaluation Data (.csv):", self.eval_data_path, 3)

        aadt_frame = ctk.CTkFrame(tab, fg_color="transparent")
        aadt_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=20, pady=5)
        ctk.CTkLabel(aadt_frame, text="AADT Value:").grid(row=0, column=0, sticky="w")
        self.aadt_value = ctk.StringVar(value="1000")
        aadt_entry = ctk.CTkEntry(
            aadt_frame, textvariable=self.aadt_value, corner_radius=6, width=120
        )
        aadt_entry.grid(row=0, column=1, sticky="w", padx=10)

        # Options & Control
        control_frame = ctk.CTkFrame(tab, fg_color="transparent")
        control_frame.grid(row=5, column=0, columnspan=3, sticky="ew", padx=20, pady=20)
        self.use_gui = ctk.StringVar(value="on")
        gui_check = ctk.CTkCheckBox(
            control_frame,
            text="Show SUMO GUI",
            variable=self.use_gui,
            onvalue="on",
            offvalue="off",
        )
        gui_check.pack(side="left")
        self.eval_button = ctk.CTkButton(
            control_frame,
            text="Run Evaluation",
            corner_radius=6,
            command=self.run_evaluation,
        )
        self.eval_button.pack(side="right")

    def select_file(self, string_var):
        # Make file paths relative to the application's root if possible
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = filedialog.askopenfilename(initialdir=base_path)
        if file_path:
            try:
                # Convert to relative path
                relative_path = os.path.relpath(file_path, base_path)
                string_var.set(relative_path)
            except ValueError:
                # If the file is on a different drive, use the absolute path
                string_var.set(file_path)

    def log(self, message):
        self.master.after(0, self._log, message)

    def _log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def run_command_in_thread(self, command):
        def target():
            self.log(f"Executing: {' '.join(command)}\n\n")
            # Ensure paths are correctly formatted for the shell
            # command_str = ' '.join(f'"{c}"' if ' ' in c else c for c in command)
            try:
                # We use Popen to get real-time output
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    # Use CREATE_NO_WINDOW to prevent a console from flashing on Windows
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                    cwd=os.path.dirname(
                        os.path.dirname(os.path.abspath(__file__))
                    ),  # Run from project root
                )

                # Read output line by line
                for line in iter(process.stdout.readline, ""):
                    self.log(line)

                process.stdout.close()
                return_code = process.wait()

                if return_code == 0:
                    self.log("\n--- Process finished successfully ---\n")
                else:
                    self.log(
                        f"\n--- Process finished with error (code: {return_code}) ---\n"
                    )

            except FileNotFoundError:
                self.log(f"Error: The command '{command[0]}' was not found.\n")
                self.log(
                    "Please ensure you have a '.venv' folder with Python executable.\n"
                )
            except Exception as e:
                self.log(f"\n--- An unexpected error occurred: {e} ---\n")

        # Run the command in a separate thread to keep the GUI responsive
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()

    def run_training(self):
        self.log("--- Starting Training Pipeline ---\n")
        agent = self.agent_to_train.get()
        episodes = self.training_episodes.get()
        training_data = self.training_data_path.get()

        if not episodes.isdigit() or int(episodes) <= 0:
            messagebox.showerror("Error", "Please enter a valid number of episodes.")
            self.log("Error: Invalid number of episodes provided.\n")
            return

        if not training_data:
            messagebox.showerror("Error", "Please select the training data file.")
            self.log("Error: Training data file not selected.\n")
            return

        output_path = filedialog.asksaveasfilename(
            title="Save Trained Model As...",
            initialdir=os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models"
            ),
            defaultextension=".pth",
            filetypes=[
                ("PyTorch Model", "*.pth"),
                ("Pickle file", "*.pkl"),
                ("All files", "*.*"),
            ],
        )
        if not output_path:
            self.log("Training cancelled by user (no output file selected).\n")
            return

        python_executable = os.path.join(".venv", "Scripts", "python.exe")
        trainer_script = os.path.join("src", "trainer.py")

        command = [
            python_executable,
            trainer_script,
            "--agent",
            agent,
            "--episodes",
            episodes,
            "--output-path",
            output_path,
            "--data-path",
            training_data,
        ]

        # I am assuming trainer.py also needs sumo files.
        net_file = self.net_file.get()
        route_file = self.route_file.get()

        if not net_file or not route_file:
            messagebox.showerror(
                "Error",
                "Please specify Network and Routes files in the 'SUMO Setup' tab.",
            )
            return

        command.extend(["--net-file", net_file])
        command.extend(["--route-file", route_file])

        add_file = self.add_file.get()
        if add_file:
            command.extend(["--add-file", add_file])

        self.run_command_in_thread(command)

    def run_evaluation(self):
        self.log("--- Starting Evaluation Pipeline ---\n")
        model_path = self.model_path.get()
        agent = self.agent_to_evaluate.get()

        if not model_path:
            messagebox.showerror("Error", "Please select a trained model file.")
            self.log("Error: Model file not selected.\n")
            return

        python_executable = os.path.join(".venv", "Scripts", "python.exe")
        runner_script = os.path.join("src", "runner.py")

        command = [
            python_executable,
            runner_script,
            "--agent",
            agent,
            "--model-path",
            model_path,
        ]

        if self.use_gui.get() == "on":
            command.append("--gui")

        net_file = self.net_file.get()
        route_file = self.route_file.get()

        if not net_file or not route_file:
            messagebox.showerror(
                "Error",
                "Please specify Network and Routes files in the 'SUMO Setup' tab.",
            )
            return

        command.extend(["--net-file", net_file])
        command.extend(["--route-file", route_file])

        add_file = self.add_file.get()
        if add_file:
            command.extend(["--add-file", add_file])

        # Handle different evaluation scenarios
        scenario = self.eval_scenario.get()
        if scenario == "A":  # Rich Data
            eval_data = self.eval_data_path.get()
            if not eval_data:
                messagebox.showerror(
                    "Error", "For Scenario A, please provide the evaluation data file."
                )
                self.log("Error: Evaluation data file not provided for Scenario A.\n")
                return
            command.extend(["--data-path", eval_data])
        elif scenario == "B":  # AADT
            aadt = self.aadt_value.get()
            if not aadt.isdigit() or int(aadt) <= 0:
                messagebox.showerror(
                    "Error", "For Scenario B, please provide a valid AADT value."
                )
                self.log("Error: Invalid AADT value for Scenario B.\n")
                return
            command.extend(["--aadt", aadt])

        self.run_command_in_thread(command)


if __name__ == "__main__":
    root = ctk.CTk()
    app = ModernGUI(root)
    root.mainloop()
