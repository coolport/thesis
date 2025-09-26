Of course. Here is a complete, detailed, start-to-finish guide to the entire pipeline, designed to be understood by everyone on your team.

---

## **The Complete Zero-Shot Traffic Control Pipeline**

### **Project Goal**

Our goal is to build an intelligent traffic signal control system that, after being trained once, can be deployed to new, unseen intersections to improve traffic flow without needing to be retrained. This "zero-shot" capability makes the system scalable and data-efficient.

We achieve this using two key technologies:
1.  **Prophet:** A forecasting tool we use to create a smooth "Expected Demand Curve," allowing our agent to anticipate future traffic.
2.  **Deep Q-Network (DQN):** A reinforcement learning algorithm that learns a decision-making "brain" (an agent) for controlling traffic lights.

The entire process is broken down into three distinct phases.

---

### **Phase 0: Calibration - Building the "Standard Model"**

**(A one-time setup phase)**

**Goal:** To analyze our single, high-quality dataset (the MMDA data for EDSA-Aurora) to create a set of reusable, general-purpose models of "typical" traffic behavior. These models are used later when we don't have good data for a new intersection.

*   **Input:** Your rich, detailed MMDA data CSV file.
*   **Process:** We write a script to analyze this data and extract key "contextual" information.
    1.  **Peak Hour Identification:** We confirm the start and end times of the AM and PM rush hours. This allows us to justify our `is_rush_hour` flag later on.
    2.  **Create an Hourly Distribution Profile:** We calculate the percentage of total daily traffic that occurs in each hour. This is saved as `standard_24h_profile.json`. (e.g., `{"08:00": 0.08, "17:00": 0.10, ...}`).
    3.  **Create a Turning Ratio Profile:** We calculate the average percentage of traffic from an approach that turns left, goes straight, or turns right. This is saved as `standard_turning_profile.json`. (e.g., `{"straight": 0.7, "left": 0.1, "right": 0.2}`).
*   **Output:** A set of `.json` files that represent our "Standard Model" of traffic. This model is our educated, data-backed guess for how traffic behaves at a typical intersection in the region.

---

### **Phase 1: Training - Creating the Agent's "Brain"**

**Goal:** To train one single, highly capable DQN agent using our best and most realistic data.

*   **Input:** The same rich MMDA data CSV.
*   **Step 1: Prepare the High-Fidelity Training Environment.**
    *   **For the SUMO Simulator:** We use the granular `Origin_to_Destination` counts from the CSV to generate a `training_routes.rou.xml` file. This file tells SUMO exactly how many cars to create and where they should go, creating a simulation that perfectly mirrors our real-world data.
    *   **For the Prophet Forecaster:** We process the same CSV data to create the inputs for Prophet. For each of the four directions (North, South, East, West), we sum up the total hourly traffic. This results in four separate input files: `prophet_input_north.csv`, `prophet_input_south.csv`, etc. Each file contains 24 hourly data points for its specific direction.
*   **Step 2: Generate the "Expected Demand Curves".**
    *   We run our `prophet_forecaster.py` script four times, once on each of the `prophet_input_*.csv` files.
    *   **Concept:** Prophet is a "fitter," not a "trainer." For each direction, it takes the 24 hourly data points and generates a smooth, continuous curve that represents the expected traffic flow for every minute of the day.
    *   **Output:** Four `demand_curve_*.json` files (e.g., `demand_curve_north.json`). These are lookup tables that the agent will use to see into the near future.
*   **Step 3: Train the DQN Agent (The Learning Loop).**
    *   We run our main `trainer.py` script, which orchestrates the training.
    *   **The Agent's "State":** At every moment it needs to make a decision, the agent is given a "state" vector—a list of numbers describing the intersection:
        1.  **Real-time Data (from SUMO):** The number of waiting cars in each lane.
        2.  **Light Status (from SUMO):** Which light is currently green and for how long.
        3.  **Future Demand (from our `.json` curves):** The expected traffic volume for each of the four directions in the near future, read directly from the `demand_curve_*.json` files.
    *   **The Learning Process:** The agent takes this state and chooses an action (`STAY` or `SWITCH` the light). It gets a reward based on whether its action helped reduce wait times. Over thousands of simulated days, its neural network learns which actions lead to the best rewards for any given state.
    *   **Enhancement: Domain Randomization:** To prevent the agent from just "memorizing" the single training day, we apply this technique. In each training episode, the script adds small, random variations to the traffic volumes and turning ratios. This forces the agent to learn flexible, robust strategies that work under a *range* of conditions, which is critical for generalization.
*   **Output:** The fully trained "brain," a single file named **`dqn_agent.pth`** containing the optimized weights of the neural network.

---

### **Phase 2: Deployment - Using the "Brain" on a New Intersection**

**Goal:** To use our single, pre-trained `dqn_agent.pth` to control a new intersection it has never seen before.

*   **Scenario A: The new intersection also has rich, detailed data.**
    *   **Process:** This is the easy case. We simply repeat `Phase 1, Steps 1 and 2` using the new intersection's data to create a new set of route files and demand curves.
    *   **Execution:** We run our `runner.py` script, which loads our one `dqn_agent.pth`, and points it at this new, high-fidelity environment. No retraining is needed.

*   **Scenario B: The new intersection has only a single AADT value (the hard case).**
    *   **Process:** This is the core "zero-shot" challenge where we use our "Standard Model" from Phase 0.
        1.  **Generate Data:** A `data_generator.py` script takes the AADT as input. It uses the `standard_24h_profile.json` and `standard_turning_profile.json` to generate a full, estimated 24-hour traffic plan for every turning movement.
        2.  **Create Environment:** From these *estimated* movements, we generate the `deployment_routes.rou.xml` for SUMO and the four `prophet_input_*.csv` files.
        3.  **Generate Forecast:** We run our same `prophet_forecaster.py` script on these new input files to produce four new `demand_curve_*.json` files.
    *   **Execution:** The `runner.py` script loads the `dqn_agent.pth` and points it at this new, *approximated* environment. The agent uses its intelligence learned from the real world (in Phase 1) to control this estimated traffic flow.

This pipeline allows us to leverage a single, high-quality dataset to build a powerful, intelligent agent that is flexible enough to be deployed in data-scarce environments, fulfilling the core promise of the thesis.
