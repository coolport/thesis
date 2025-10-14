
# Configuration file for constants and hyperparameters

import torch

# --- Training Hyperparameters ---
BATCH_SIZE = 128       # Number of transitions sampled from the replay buffer
GAMMA = 0.99           # Discount factor for future rewards
EPS_START = 0.9        # Starting value of epsilon for epsilon-greedy action selection
EPS_END = 0.05         # Final value of epsilon
EPS_DECAY = 1000       # Controls the rate of exponential decay of epsilon
TAU = 0.005            # Update rate of the target network
LR = 1e-5              # Learning rate of the AdamW optimizer

# --- Environment Configuration ---
# Define the directory for SUMO configurations
SUMO_CONFIG_DIR = 'sumo'

# --- Agent Configuration ---
# Define the size of the state and action space
N_OBSERVATIONS = 17 # 12 lanes queue length + 4 forecast placeholders + 1 phase indicator
N_ACTIONS = 2       # STAY or SWITCH

# --- Hardware Configuration ---
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --- File Paths ---
DATA_DIR = 'data'
PROFILES_DIR = f'{DATA_DIR}/profiles'

# Point to the newly generated realistic, per-direction data files
FORECAST_INPUT_PATHS = {
    'N': f'{DATA_DIR}/prophet_input_N.csv',
    'S': f'{DATA_DIR}/prophet_input_S.csv',
    'E': f'{DATA_DIR}/prophet_input_E.csv',
    'W': f'{DATA_DIR}/prophet_input_W.csv',
}

# The output files for the generated demand curves
FORECAST_OUTPUT_PATHS = {
    'N': f'{PROFILES_DIR}/demand_curve_N.json',
    'S': f'{PROFILES_DIR}/demand_curve_S.json',
    'E': f'{PROFILES_DIR}/demand_curve_E.json',
    'W': f'{PROFILES_DIR}/demand_curve_W.json',
}
