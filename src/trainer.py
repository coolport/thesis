#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""trainer.py: The main training script for the DQN agent.

This script orchestrates the training loop for Phase 1. It will:
- Initialize the agent and the SUMO environment.
- Run for a specified number of episodes.
- In each episode, gather experience (state, action, reward, next_state).
- Store experience and train the agent.
- Save the trained agent's weights.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import math
import random

from dqn_agent import DQN, ReplayMemory, Transition
from sumo_environment import SumoEnvironment
import config

# --- Initialization ---
# Define the paths to the demand curve files
demand_curve_files = {
    'N': 'data/profiles/demand_curve_dummy.json',
    'S': 'data/profiles/demand_curve_dummy.json',
    'E': 'data/profiles/demand_curve_dummy.json',
    'W': 'data/profiles/demand_curve_dummy.json',
}
env = SumoEnvironment(
    sumo_config_file=config.SUMO_CONFIGS['test'], 
    demand_curve_files=demand_curve_files, 
    use_gui=True
)

# Create the policy and target networks
policy_net = DQN(config.N_OBSERVATIONS, config.N_ACTIONS).to(config.DEVICE)
target_net = DQN(config.N_OBSERVATIONS, config.N_ACTIONS).to(config.DEVICE)
target_net.load_state_dict(policy_net.state_dict())
target_net.eval() # Set target network to evaluation mode

optimizer = optim.AdamW(policy_net.parameters(), lr=config.LR, amsgrad=True)
memory = ReplayMemory(10000)

steps_done = 0

def select_action(state):
    """Selects an action using an epsilon-greedy policy."""
    global steps_done
    sample = random.random()
    # Calculate epsilon based on the current step
    eps_threshold = config.EPS_END + (config.EPS_START - config.EPS_END) * \
        math.exp(-1. * steps_done / config.EPS_DECAY)
    steps_done += 1
    
    if sample > eps_threshold:
        # Exploit: choose the best action from the policy network
        with torch.no_grad():
            # state is a list, convert it to a tensor
            state_tensor = torch.tensor([state], device=config.DEVICE, dtype=torch.float32)
            return policy_net(state_tensor).max(1)[1].view(1, 1)
    else:
        # Explore: choose a random action
        return torch.tensor([[random.randrange(config.N_ACTIONS)]], device=config.DEVICE, dtype=torch.long)

def optimize_model():
    """Performs one step of optimization on the policy network."""
    if len(memory) < config.BATCH_SIZE:
        return # Don't train until we have enough samples

    transitions = memory.sample(config.BATCH_SIZE)
    batch = Transition(*zip(*transitions))

    # Create tensors for states, actions, and rewards
    state_batch = torch.cat([torch.tensor([s], device=config.DEVICE, dtype=torch.float32) for s in batch.state])
    action_batch = torch.cat(batch.action)
    reward_batch = torch.cat([torch.tensor([r], device=config.DEVICE, dtype=torch.float32) for r in batch.reward])
    
    # For next_states, we need to handle the case where a state is final (None)
    non_final_mask = torch.tensor(tuple(map(lambda s: s is not None, batch.next_state)), device=config.DEVICE, dtype=torch.bool)
    non_final_next_states = torch.cat([torch.tensor([s], device=config.DEVICE, dtype=torch.float32) for s in batch.next_state if s is not None])

    # Q(s_t, a)
    state_action_values = policy_net(state_batch).gather(1, action_batch)

    # V(s_{t+1}) for all next states.
    next_state_values = torch.zeros(config.BATCH_SIZE, device=config.DEVICE)
    with torch.no_grad():
        next_state_values[non_final_mask] = target_net(non_final_next_states).max(1)[0]
    
    # Expected Q values
    expected_state_action_values = (next_state_values * config.GAMMA) + reward_batch.squeeze()

    # Compute Huber loss
    criterion = nn.SmoothL1Loss()
    loss = criterion(state_action_values, expected_state_action_values.unsqueeze(1))

    # Optimize the model
    optimizer.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_value_(policy_net.parameters(), 100)
    optimizer.step()

# --- Main Training Loop ---
def main():
    num_episodes = 50 # For demonstration
    env.start()

    for i_episode in range(num_episodes):
        state = env.reset()
        
        for t in range(500): # Limit episode length
            action = select_action(state)
            next_state, reward, done, _ = env.step(action.item())

            # Store the transition in memory
            memory.push(state, action, next_state, reward)

            state = next_state

            # Perform one step of the optimization (on the policy network)
            optimize_model()

            # Soft update of the target network's weights
            target_net_state_dict = target_net.state_dict()
            policy_net_state_dict = policy_net.state_dict()
            for key in policy_net_state_dict:
                target_net_state_dict[key] = policy_net_state_dict[key]*config.TAU + target_net_state_dict[key]*(1-config.TAU)
            target_net.load_state_dict(target_net_state_dict)

            if done:
                break
        
        print(f"Episode {i_episode} finished.")

    print('Training complete')

    # Save the final trained model
    model_path = 'models/dqn_agent.pth'
    torch.save(policy_net.state_dict(), model_path)
    print(f"Trained model saved to {model_path}")

    env.close()

if __name__ == '__main__':
    main()