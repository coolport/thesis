
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""d3qn_agent.py: Defines the Dueling DQN agent architecture.

This is a more advanced agent that separates the value and advantage streams.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

# Note: The ReplayMemory and Transition are the same as in dqn_agent.py
# and will be imported directly in the trainer.

class D3QN(nn.Module):
    """The Dueling Deep Q-Network model."""
    def __init__(self, n_observations, n_actions):
        super(D3QN, self).__init__()
        
        # Shared layers
        self.layer1 = nn.Linear(n_observations, 128)
        self.layer2 = nn.Linear(128, 128)

        # Dueling streams
        # 1. Value stream
        self.value_stream = nn.Sequential(
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, 1) # Outputs a single value for the state
        )

        # 2. Advantage stream
        self.advantage_stream = nn.Sequential(
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, n_actions) # Outputs a value for each action
        )

    def forward(self, x):
        """Defines the forward pass with the dueling architecture."""
        # Pass through shared layers
        x = F.relu(self.layer1(x))
        x = F.relu(self.layer2(x))

        # Calculate value and advantage
        value = self.value_stream(x)
        advantage = self.advantage_stream(x)

        # Combine value and advantage to get Q-values
        # Q(s,a) = V(s) + (A(s,a) - mean(A(s,a)))
        q_values = value + (advantage - advantage.mean(dim=1, keepdim=True))
        return q_values
