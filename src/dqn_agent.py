
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""dqn_agent.py: Defines the DQN agent's neural network and replay memory.

This file contains the PyTorch class for the Deep Q-Network and a class
for the experience replay memory buffer.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import random
from collections import namedtuple, deque

# Define the structure of a single transition (experience)
Transition = namedtuple('Transition', ('state', 'action', 'next_state', 'reward'))

class ReplayMemory:
    """A cyclic buffer of bounded size that holds the transitions observed recently."""
    def __init__(self, capacity):
        """Initializes the memory.

        Args:
            capacity (int): The maximum number of transitions to store.
        """
        self.memory = deque([], maxlen=capacity)

    def push(self, *args):
        """Saves a transition to the memory."""
        self.memory.append(Transition(*args))

    def sample(self, batch_size):
        """Selects a random batch of transitions for training."""
        return random.sample(self.memory, batch_size)

    def __len__(self):
        """Returns the current size of the memory."""
        return len(self.memory)


class DQN(nn.Module):
    """The Deep Q-Network model. This is the agent's 'brain'."""
    def __init__(self, n_observations, n_actions):
        """Initializes the neural network layers.

        Args:
            n_observations (int): The size of the state space (input layer).
            n_actions (int): The size of the action space (output layer).
        """
        super(DQN, self).__init__()
        # A simple Multi-Layer Perceptron (MLP)
        self.layer1 = nn.Linear(n_observations, 128)
        self.layer2 = nn.Linear(128, 128)
        self.layer3 = nn.Linear(128, n_actions)

    def forward(self, x):
        """Defines the forward pass of the network.
        
        Takes a state and returns the Q-values for each possible action.
        """
        # Apply ReLU activation function after the first two layers
        x = F.relu(self.layer1(x))
        x = F.relu(self.layer2(x))
        # The final layer provides the raw Q-values for each action
        return self.layer3(x)
