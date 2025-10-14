#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""sumo_environment.py: A wrapper for the SUMO simulation environment.

This class will handle all interactions with the SUMO simulation via the TraCI API.
This includes starting/stopping the simulation, getting state information (queue lengths, etc.),
and executing agent actions (changing traffic light phases).
"""

import traci
import sumolib
import subprocess
import sys
import os
import time
import json

# Add SUMO_HOME/tools to the system path
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

class SumoEnvironment:
    """A wrapper for the SUMO simulation to be used by the RL agent."""

    def __init__(self, sumo_config_file, demand_curve_files, use_gui=False, steps_per_episode=500):
        """Initializes the environment."""
        self.sumo_config = sumo_config_file
        self.use_gui = use_gui
        self.steps_per_episode = steps_per_episode
        self.current_step = 0
        self.sumo_proc = None
        self.traci_conn = None

        # Load demand curves
        self.demand_curves = self._load_demand_curves(demand_curve_files)

        # Hardcoded for our test.net.xml scenario
        self.ts_id = 'center'
        self.incoming_lanes = [
            'N_to_center_0', 'N_to_center_1', 'N_to_center_2',
            'S_to_center_0', 'S_to_center_1', 'S_to_center_2',
            'E_to_center_0', 'E_to_center_1', 'E_to_center_2',
            'W_to_center_0', 'W_to_center_1', 'W_to_center_2',
        ]
        # Directions corresponding to the forecast
        self.directions = ['N', 'S', 'E', 'W']

        # Normalization constants
        self.MAX_QUEUE_LENGTH = 50.0  # Estimated max vehicles in a lane
        self.MAX_FORECAST_DEMAND = 4000.0 # Estimated max forecast value from data
        self.NUM_PHASES = 4.0 # Total number of phases in the traffic light cycle

    def _load_demand_curves(self, demand_curve_files):
        """Loads demand curve JSON files into a lookup dictionary."""
        curves = {}
        for direction, file_path in demand_curve_files.items():
            with open(file_path, 'r') as f:
                # Convert list of dicts to a dictionary mapping time (in seconds) to demand
                data = json.load(f)
                lookup = {}
                for item in data:
                    h, m, s = map(int, item['time'].split(':'))
                    time_in_seconds = h * 3600 + m * 60 + s
                    lookup[time_in_seconds] = item['expected_demand']
                curves[direction] = lookup
        print("Successfully loaded demand curves.")
        return curves

    def start(self):
        """Starts a SUMO simulation and connects with TraCI."""
        sumo_binary = sumolib.checkBinary('sumo-gui' if self.use_gui else 'sumo')
        sumo_cmd = [sumo_binary, "-c", self.sumo_config, "--remote-port", "8813", "--start"]
        self.sumo_proc = subprocess.Popen(sumo_cmd)
        
        # Retry loop for connecting to TraCI
        for _ in range(10):
            try:
                traci.init(port=8813)
                self.traci_conn = traci
                print("Successfully connected to SUMO.")
                return
            except traci.TraCIException:
                time.sleep(1.0)
        raise RuntimeError("Failed to connect to SUMO after multiple attempts.")

    def close(self):
        """Closes the TraCI connection and terminates the SUMO process."""
        if self.traci_conn:
            self.traci_conn.close()
            self.traci_conn = None
            print("TraCI connection closed.")
        if self.sumo_proc:
            self.sumo_proc.terminate()
            self.sumo_proc.wait()
            self.sumo_proc = None
            print("SUMO process terminated.")

    def reset(self):
        """Resets the environment for a new episode."""
        # Reloads the simulation with the same configuration
        self.traci_conn.load(["-c", self.sumo_config, "--start"])
        self.current_step = 0
        return self._get_state()

    def step(self, action):
        """
        Executes one time step in the environment.
        """
        # 1. Apply the action
        if action == 1: # SWITCH
            current_phase = self.traci_conn.trafficlight.getPhase(self.ts_id)
            next_phase = (current_phase + 1) % 4 # Assuming 4 phases
            self.traci_conn.trafficlight.setPhase(self.ts_id, next_phase)
        
        # 2. Run the simulation for a fixed number of steps (e.g., 5 seconds)
        for _ in range(5):
            self.traci_conn.simulationStep()
        self.current_step += 5

        # 3. Get the next state, reward, and done flag
        next_state = self._get_state()
        reward = self._calculate_reward()
        done = self.current_step >= self.steps_per_episode

        # 4. Pass raw metrics for logging
        info = {
            'raw_queue_length': sum(self.traci_conn.lane.getLastStepHaltingNumber(lane_id) for lane_id in self.incoming_lanes)
        }

        return next_state, reward, done, info

    def _get_state(self):
        """
        Retrieves and NORMALIZES the current state of the environment from SUMO.
        """
        state = []
        # Get queue length for each incoming lane and normalize it
        for lane_id in self.incoming_lanes:
            queue_length = self.traci_conn.lane.getLastStepHaltingNumber(lane_id)
            state.append(queue_length / self.MAX_QUEUE_LENGTH)
        
        # Get forecast data and normalize it
        sim_time = self.traci_conn.simulation.getTime()
        # Round to the nearest minute (60 seconds) for lookup
        lookup_time = (int(sim_time / 60) * 60) % (24 * 3600)

        for direction in self.directions:
            # Get demand, default to 0 if not found
            demand = self.demand_curves[direction].get(lookup_time, 0)
            state.append(demand / self.MAX_FORECAST_DEMAND)
        
        # Get traffic light phase and normalize it
        current_phase = self.traci_conn.trafficlight.getPhase(self.ts_id)
        state.append(current_phase / self.NUM_PHASES)

        return state

    def _calculate_reward(self):
        """
        Calculates the reward as the negative of the total waiting time.
        """
        total_wait_time = 0
        for lane_id in self.incoming_lanes:
            total_wait_time += self.traci_conn.lane.getWaitingTime(lane_id)
        return -total_wait_time