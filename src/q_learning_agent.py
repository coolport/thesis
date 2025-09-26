
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""q_learning_agent.py: Defines a basic Tabular Q-Learning agent.

This agent uses a dictionary as a Q-table and requires state discretization.
"""

import random
from collections import defaultdict

class QLearningAgent:
    """A simple agent that learns via a Q-table."""
    def __init__(self, n_actions, learning_rate=0.1, discount_factor=0.9, epsilon=0.1):
        self.n_actions = n_actions
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        
        # Use a defaultdict to handle unseen states gracefully
        self.q_table = defaultdict(lambda: [0.0] * n_actions)

    def discretize_state(self, state):
        """
        Converts a continuous state vector into a discrete, hashable tuple.
        Example: [17, 5, 2, ...] -> ('high', 'low', 'low', ...)
        """
        # We only discretize the first 12 elements (queue lengths)
        queue_lengths = state[:12]
        discretized = []
        for queue in queue_lengths:
            if queue < 5:
                discretized.append('low')
            elif queue < 15:
                discretized.append('medium')
            else:
                discretized.append('high')
        # The rest of the state (forecast, phase) can be ignored for this simple agent
        return tuple(discretized)

    def act(self, state):
        """Choose an action using an epsilon-greedy policy."""
        discrete_state = self.discretize_state(state)
        if random.random() > self.epsilon:
            # Exploit: choose the best known action
            return self.q_table[discrete_state].index(max(self.q_table[discrete_state]))
        else:
            # Explore: choose a random action
            return random.randrange(self.n_actions)

    def learn(self, state, action, reward, next_state):
        """
        Update the Q-table using the Bellman equation.
        """
        discrete_state = self.discretize_state(state)
        discrete_next_state = self.discretize_state(next_state)
        
        old_value = self.q_table[discrete_state][action]
        next_max = max(self.q_table[discrete_next_state])
        
        # Q-learning formula
        new_value = (1 - self.lr) * old_value + self.lr * (reward + self.gamma * next_max)
        self.q_table[discrete_state][action] = new_value
