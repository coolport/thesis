
# Configuration file for constants and hyperparameters

import torch

# --- Training Hyperparameters ---
BATCH_SIZE = 128       # Number of transitions sampled from the replay buffer
GAMMA = 0.99           # Discount factor for future rewards
EPS_START = 0.9        # Starting value of epsilon for epsilon-greedy action selection
EPS_END = 0.05         # Final value of epsilon
EPS_DECAY = 1000       # Controls the rate of exponential decay of epsilon
TAU = 0.005            # Update rate of the target network
LR = 1e-4              # Learning rate of the AdamW optimizer

# --- Environment Configuration ---
# Use a dictionary to easily manage different scenarios
SUMO_CONFIGS = {
    'test': '/home/aidan/thesis/sumo/test.sumocfg'
}

# --- Agent Configuration ---
# Define the size of the state and action space
N_OBSERVATIONS = 17 # 12 lanes queue length + 4 forecast placeholders + 1 phase indicator
N_ACTIONS = 2       # STAY or SWITCH

# --- Hardware Configuration ---
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
