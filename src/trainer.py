#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""trainer.py: The main training script for the RL agents.

This universal trainer can train Q-Learning, DQN, and D3QN agents.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import math
import random
import argparse
import os

# Import agent classes
from dqn_agent import DQN, ReplayMemory, Transition
from d3qn_agent import D3QN
from q_learning_agent import QLearningAgent

from sumo_environment import SumoEnvironment
import config

# --- Universal Helper Functions ---

steps_done = 0

def select_action_pytorch(state, policy_net, n_actions):
    """Selects an action for a PyTorch-based agent (DQN, D3QN)."""
    global steps_done
    sample = random.random()
    eps_threshold = config.EPS_END + (config.EPS_START - config.EPS_END) * \
        math.exp(-1. * steps_done / config.EPS_DECAY)
    steps_done += 1
    
    if sample > eps_threshold:
        with torch.no_grad():
            state_tensor = torch.tensor([state], device=config.DEVICE, dtype=torch.float32)
            return policy_net(state_tensor).max(1)[1].view(1, 1)
    else:
        return torch.tensor([[random.randrange(n_actions)]], device=config.DEVICE, dtype=torch.long)

def optimize_model_pytorch(agent_type, policy_net, target_net, memory, optimizer):
    """Performs one step of optimization for DQN or D3QN."""
    if len(memory) < config.BATCH_SIZE:
        return

    transitions = memory.sample(config.BATCH_SIZE)
    batch = Transition(*zip(*transitions))

    state_batch = torch.cat([torch.tensor([s], device=config.DEVICE, dtype=torch.float32) for s in batch.state])
    action_batch = torch.cat(batch.action)
    reward_batch = torch.cat([torch.tensor([r], device=config.DEVICE, dtype=torch.float32) for r in batch.reward])
    
    non_final_mask = torch.tensor(tuple(map(lambda s: s is not None, batch.next_state)), device=config.DEVICE, dtype=torch.bool)
    non_final_next_states = torch.cat([torch.tensor([s], device=config.DEVICE, dtype=torch.float32) for s in batch.next_state if s is not None])

    state_action_values = policy_net(state_batch).gather(1, action_batch)

    next_state_values = torch.zeros(config.BATCH_SIZE, device=config.DEVICE)
    with torch.no_grad():
        if agent_type == 'd3qn': # Double DQN update for D3QN
            best_actions = policy_net(non_final_next_states).max(1)[1].unsqueeze(1)
            next_state_values[non_final_mask] = target_net(non_final_next_states).gather(1, best_actions).squeeze()
        else: # Standard DQN update
            next_state_values[non_final_mask] = target_net(non_final_next_states).max(1)[0]
    
    expected_state_action_values = (next_state_values * config.GAMMA) + reward_batch.squeeze()

    criterion = nn.SmoothL1Loss()
    loss = criterion(state_action_values, expected_state_action_values.unsqueeze(1))

    optimizer.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_value_(policy_net.parameters(), 100)
    optimizer.step()

import sys
import subprocess

def _generate_all_forecasts(project_root):
    """Generates all four directional forecasts by calling the forecasting script."""
    print("--- Generating Directional Forecasts ---")
    # Use absolute path for the forecasting script
    forecasting_script_path = os.path.join(project_root, 'src', 'forecasting.py')
    
    for direction in config.FORECAST_INPUT_PATHS.keys():
        input_path = os.path.join(project_root, config.FORECAST_INPUT_PATHS[direction])
        output_path = os.path.join(project_root, config.FORECAST_OUTPUT_PATHS[direction])
        
        command = [
            sys.executable, # Use the current python interpreter
            forecasting_script_path,
            '--input',
            input_path,
            '--output',
            output_path
        ]
        
        print(f"Running command: {' '.join(command)}")
        try:
            # Using subprocess.run to execute the command
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print(result.stdout) # Print the output from the forecasting script
        except subprocess.CalledProcessError as e:
            print(f"Error generating forecast for {direction}:")
            print(e.stderr)
            # Exit on error to prevent training with missing/stale forecasts
            raise e

def main(args):
    # --- Path Setup for Cross-Platform Compatibility ---
    # Get the absolute path to the project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # --- Generate Forecasts before starting anything else ---
    _generate_all_forecasts(project_root)

    # --- Environment and Agent Initialization ---
    cfg_name = 'real_traffic'
    sumo_config_path = os.path.join(project_root, config.SUMO_CONFIG_DIR, f'{cfg_name}.sumocfg')

    # Construct absolute paths for demand curve files from config
    demand_curve_files_absolute = {
        direction: os.path.join(project_root, path)
        for direction, path in config.FORECAST_OUTPUT_PATHS.items()
    }

    env = SumoEnvironment(
        sumo_config_file=sumo_config_path,
        demand_curve_files=demand_curve_files_absolute,
        use_gui=args.gui
    )

    # --- Agent Specific Setup ---
    agent_name = args.agent.lower()
    if agent_name in ['dqn', 'd3qn']:
        AgentClass = DQN if agent_name == 'dqn' else D3QN
        policy_net = AgentClass(config.N_OBSERVATIONS, config.N_ACTIONS).to(config.DEVICE)
        target_net = AgentClass(config.N_OBSERVATIONS, config.N_ACTIONS).to(config.DEVICE)
        target_net.load_state_dict(policy_net.state_dict())
        target_net.eval()
        optimizer = optim.AdamW(policy_net.parameters(), lr=config.LR, amsgrad=True)
        memory = ReplayMemory(10000)
    elif agent_name == 'q-learning':
        agent = QLearningAgent(n_actions=config.N_ACTIONS)
    else:
        raise ValueError("Invalid agent type specified.")

    # --- Training Loop ---
    env.start()
    for i_episode in range(args.episodes):
        state = env.reset()
        total_reward = 0
        
        for t in range(500): # Limit episode length
            if agent_name in ['dqn', 'd3qn']:
                action_tensor = select_action_pytorch(state, policy_net, config.N_ACTIONS)
                action = action_tensor.item()
            else: # Q-Learning
                action = agent.act(state)

            next_state, reward, done, _ = env.step(action)
            total_reward += reward

            if agent_name in ['dqn', 'd3qn']:
                memory.push(state, action_tensor, next_state, reward)
                optimize_model_pytorch(agent_name, policy_net, target_net, memory, optimizer)
                # Soft update target network
                target_net_state_dict = target_net.state_dict()
                policy_net_state_dict = policy_net.state_dict()
                for key in policy_net_state_dict:
                    target_net_state_dict[key] = policy_net_state_dict[key]*config.TAU + target_net_state_dict[key]*(1-config.TAU)
                target_net.load_state_dict(target_net_state_dict)
            else: # Q-Learning
                agent.learn(state, action, reward, next_state)

            state = next_state
            if done:
                break
        
        print(f"Agent: {agent_name}, Episode {i_episode} finished after {t+1} steps with total reward: {total_reward:.2f}")

    print(f'Training complete for {agent_name}.')

    # --- Save Model ---
    model_dir = 'models'
    os.makedirs(model_dir, exist_ok=True)

    # Determine the model path
    if args.output_path:
        model_path = args.output_path
        # Ensure the directory for the custom path exists
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
    else:
        if agent_name in ['dqn', 'd3qn']:
            model_path = os.path.join(model_dir, f'{agent_name}_agent.pth')
        else: # Q-Learning
            model_path = os.path.join(model_dir, f'{agent_name}_agent.pkl')

    # Save the model
    if agent_name in ['dqn', 'd3qn']:
        torch.save(policy_net.state_dict(), model_path)
    else: # Q-Learning
        import pickle
        with open(model_path, 'wb') as f:
            pickle.dump(dict(agent.q_table), f)
    
    print(f"Trained model saved to {model_path}")

    env.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train a reinforcement learning agent for traffic control.')
    parser.add_argument('--agent', type=str, required=True, choices=['q-learning', 'dqn', 'd3qn'], help='The type of agent to train.')
    parser.add_argument('--episodes', type=int, default=150, help='Number of episodes to train for.')
    parser.add_argument('--gui', action='store_true', help='Enable SUMO GUI for visualization.')
    parser.add_argument('--output-path', type=str, help='Custom path to save the trained model.')
    args = parser.parse_args()
    main(args)