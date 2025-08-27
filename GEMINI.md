# Gemini Agent Instructions

This file provides project-specific context and instructions for the Gemini agent to ensure it works effectively and respects project conventions.

### 1. Project Overview

This project is an undergraduate thesis focused on mitigating urban traffic congestion. The goal is to develop a **Zero-Shot Traffic Signal Control** system. This system uses **Prophet** for time-series forecasting of traffic flow, and a **Deep Q-Network (DQN)**, a reinforcement learning model, to make intelligent, proactive decisions for traffic signal control. The entire environment and agent training are conducted within the **SUMO (Simulation of Urban Mobility)** simulator. The key innovation is the "zero-shot" capability, which allows the model to be trained on a limited set of intersections and then deployed to new, unseen intersections without requiring retraining, making it a generalizable and scalable solution.

### 2. Tech Stack

- **Language:** Python
- **Frameworks:** SUMO (Simulation of Urban Mobility)
- **Key Libraries:**
    - `traci` and `sumolib` (for interacting with SUMO)
    - `prophet` (for traffic forecasting)
    - A deep learning library for the DQN, PyTorch most likely to be used (currently not here).

### 3. Development Workflow

The core logic is likely executed via `runner.py` (for now, the implementation is minimal and is used to just test and explore the environment). The development process follows a simulation-based pipeline:

- **To install dependencies:** `pip install -r requirements.txt`. Note that libraries like `prophet` or a deep learning framework may need to be installed separately. NOTE: currently not installed. the user does this. as installing requirements (most times).
- **To run the app:** `python3 runner.py` (again, the current setup is just for exploratory purposes).
- **To run tests:** The thesis specifies evaluation using forecasting accuracy metrics (MAE, RMSE) and simulation-based performance metrics based on ISO/IEC 25010. There is no dedicated test command at the moment.
- **To run the linter:** No linter is specified.

### 4. Coding Conventions & Style

- The project follows a pipeline architecture:
    1.  **Forecasting:** A module that uses Prophet to predict traffic.
    2.  **Simulation:** A SUMO environment that models the road network and traffic.
    3.  **Control:** A DQN agent that observes the simulation and controls the traffic signals.
- The primary goal is to create a generalizable model, so code should favor modularity and abstraction over hard-coded, intersection-specific logic.

### 5. General Instructions & Constraints

These are based on the "Scope and Delimitations" section of the thesis.

- **Simulation Only:** The project does not involve live deployment or control of real-world traffic signals. All work is confined to the SUMO simulation environment.
- **Historical Data:** The model is trained and evaluated using historical traffic datasets. No real-time data collection will be implemented.
- **Limited Scope:** The study focuses exclusively on vehicle traffic volume and signal timing optimization. It does not address:
    - Pedestrian flow
    - Public transport scheduling
    - Adaptive tolling systems
    - External factors like accidents or weather (unless present in the dataset).
- **Zero-Shot Limitations:** The model is expected to generalize only to intersections that share similar attributes (e.g., vehicle flow, complexity) to those in the training set.
- When told to save / archive conversations, create it in this format: MM*DD*(randomnoun).priv.md. The extension is crucial as .priv.md is what's included in the .gitignore. Properly format it (minimally): put code examples etc into actual code blocks. Do not overdo it, like applying random bold / emphasis on words.
- Absolutely DO NOT write to the home ~ directory, or any other unspecified directory, your work will be confined to this directory (~/thesis) and its subdirectories.
