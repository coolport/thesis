# DQN Training Stabilization Session: 2025-10-09

## **Objective:** Diagnose and resolve the unstable training behavior of the DQN agent.

---

### **1. Initial Problem**

Following the successful debugging of the environment and data pipeline, we observed that training the DQN agent for more episodes resulted in significantly worse performance.

**Evaluation Results (`results.csv`):**
```
timestamp,agent_type,avg_wait_time,avg_queue_length,total_throughput
2025-10-09T09:41:19.972626,dqn,38.23,17.31,580
2025-10-09T09:43:49.141687,dqn,213.18,24.93,578
```
The first row represents a model trained for a few episodes, while the second represents a model trained for 150 episodes. The longer-trained model has a much higher wait time.

---

### **2. Investigation & Findings**

To diagnose this, we took the following steps:

#### **Step 1: Add Reward Logging**

-   **Action:** I modified `src/trainer.py` to log the `total_reward` at the end of each training episode.
-   **Purpose:** To observe the agent's learning trend.

#### **Step 2: Analyze Training Runs**

-   **Action:** You executed a 50-episode training run.
-   **Output (Sample):**
    ```
    Agent: dqn, Episode 0 finished after 100 steps with total reward: -11422.00
    Agent: dqn, Episode 1 finished after 100 steps with total reward: -10484.00
    Agent: dqn, Episode 2 finished after 100 steps with total reward: -5467.00
    Agent: dqn, Episode 3 finished after 100 steps with total reward: -6411.00
    Agent: dqn, Episode 4 finished after 100 steps with total reward: -4383.00
    Agent: dqn, Episode 5 finished after 100 steps with total reward: -6356.00
    Agent: dqn, Episode 6 finished after 100 steps with total reward: -3720.00
    ```
-   **Finding:** The rewards are fluctuating wildly and not consistently improving (i.e., getting closer to 0). This is a classic sign of **unstable training**. The agent is not learning a stable policy.

#### **Step 3: Analyze Hyperparameters**

-   **Action:** I inspected the hyperparameters in `src/config.py`.
-   **Finding:** The learning rate, `LR = 1e-4`, is the most likely cause of the instability. It is likely too high, causing the agent to make large, erratic updates to its policy and overshoot optimal solutions.

---

### **3. Proposed Next Steps**

To address the training instability, the immediate next step is to adjust the learning rate.

1.  **Modify `src/config.py`:** Change the learning rate from `1e-4` to `1e-5`.
    ```python
    # In src/config.py
    LR = 1e-5 # Previous value was 1e-4
    ```
2.  **Re-run Training:** Execute another 50-episode training run.
3.  **Analyze Results:** Observe the `total_reward` output for each episode. We expect to see a much more stable trend, with the reward value showing a clearer and more consistent path toward improvement (a smaller negative number).
