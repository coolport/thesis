
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""runner.py: The script for deploying and evaluating trained agents.

This script loads a pre-trained agent, runs it in the SUMO environment for a 
full episode, and logs the performance metrics to a CSV file.
"""

import torch
import csv
import os
import argparse
import pickle
from collections import defaultdict
from datetime import datetime

# Import agent classes
from dqn_agent import DQN
from d3qn_agent import D3QN
from q_learning_agent import QLearningAgent

from sumo_environment import SumoEnvironment
import config

def run_evaluation(agent_type, model_path, gui, episodes, output_file):
    """Runs a full evaluation for a given agent."""
    # --- Environment and Agent Initialization ---
    if agent_type == 'fixed-time':
        cfg_name = 'medium_traffic_fixed'
    else:
        cfg_name = 'medium_traffic'
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sumo_cfg = os.path.join(project_root, 'sumo', f'{cfg_name}.sumocfg')
    demand_curve_files_relative = {
        'N': 'data/profiles/demand_curve_dummy.json',
        'S': 'data/profiles/demand_curve_dummy.json',
        'E': 'data/profiles/demand_curve_dummy.json',
        'W': 'data/profiles/demand_curve_dummy.json',
    }
    demand_curve_files = {
        direction: os.path.join(project_root, path)
        for direction, path in demand_curve_files_relative.items()
    }

    # Evaluation runs for a longer, fixed duration
    env = SumoEnvironment(
        sumo_config_file=sumo_cfg, 
        demand_curve_files=demand_curve_files, 
        use_gui=gui,
        steps_per_episode=3600 # Run for 1 hour of simulation time
    )

    # --- Load Agent ---
    if agent_type in ['dqn', 'd3qn']:
        AgentClass = DQN if agent_type == 'dqn' else D3QN
        agent = AgentClass(config.N_OBSERVATIONS, config.N_ACTIONS).to(config.DEVICE)
        if model_path:
            agent.load_state_dict(torch.load(model_path))
        agent.eval() # Set agent to evaluation mode (no exploration)
    elif agent_type == 'q-learning':
        agent = QLearningAgent(n_actions=config.N_ACTIONS, epsilon=0.0) # Epsilon = 0 for pure exploitation
        if model_path:
            with open(model_path, 'rb') as f:
                saved_q_table = pickle.load(f)
                agent.q_table = defaultdict(lambda: [0.0] * agent.n_actions, saved_q_table)
    elif agent_type != 'fixed-time':
        raise ValueError("Invalid agent type specified.")

    # --- Evaluation Loop ---
    env.start()
    for i_episode in range(episodes):
        print(f"Running evaluation episode {i_episode + 1}/{episodes} for agent '{agent_type}'...")
        state = env.reset()
        done = False

        total_wait_time = 0
        total_queue_length = 0
        throughput = 0
        steps = 0

        detector_ids = ['det_N', 'det_S', 'det_E', 'det_W']

        while not done:
            if agent_type == 'fixed-time':
                action = 0 
            elif agent_type == 'q-learning':
                action = agent.act(state)
            else: # DQN / D3QN
                with torch.no_grad():
                    state_tensor = torch.tensor([state], device=config.DEVICE, dtype=torch.float32)
                    action = agent(state_tensor).max(1)[1].item()

            next_state, reward, done, info = env.step(action)
            state = next_state
            
            # Log metrics at each step
            total_wait_time -= reward # Reward is negative wait time
            current_queue = sum(s for s in state[:12]) # Sum of queue lengths
            total_queue_length += current_queue
            for det_id in detector_ids:
                throughput += env.traci_conn.inductionloop.getLastStepVehicleNumber(det_id)
            steps += 1

        # --- Calculate Final Metrics ---
        avg_wait_time = total_wait_time / steps if steps > 0 else 0
        avg_queue_length = total_queue_length / steps if steps > 0 else 0

        print("--- Evaluation Results ---")
        print(f"Agent: {agent_type}")
        print(f"Average Vehicle Wait Time: {avg_wait_time:.2f} s")
        print(f"Average Queue Length: {avg_queue_length:.2f} vehicles")
        print(f"Total Throughput: {throughput} vehicles")
        print("--------------------------")

        # --- Save to CSV ---
        file_exists = os.path.isfile(output_file)
        with open(output_file, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['timestamp', 'agent_type', 'avg_wait_time', 'avg_queue_length', 'total_throughput'])
            writer.writerow([datetime.now().isoformat(), agent_type, f'{avg_wait_time:.2f}', f'{avg_queue_length:.2f}', throughput])
        print(f"Results appended to {output_file}")

    env.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate a trained agent.')
    parser.add_argument('--agent', type=str, required=True, choices=['q-learning', 'dqn', 'd3qn', 'fixed-time'], help='The type of agent to evaluate.')
    parser.add_argument('--model-path', type=str, help='Path to the saved model file (.pth or .pkl).')
    parser.add_argument('--episodes', type=int, default=1, help='Number of evaluation episodes to run.')
    parser.add_argument('--output-file', type=str, default='results.csv', help='Path to the output CSV file for results.')
    parser.add_argument('--gui', action='store_true', help='Enable SUMO GUI for visualization.')
    
    args = parser.parse_args()
    if args.agent != 'fixed-time' and not args.model_path:
        parser.error("--model-path is required for AI agents.")

    run_evaluation(args.agent, args.model_path, args.gui, args.episodes, args.output_file)
