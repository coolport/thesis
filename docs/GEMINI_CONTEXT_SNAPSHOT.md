
# Gemini Agent State Snapshot

This document is a snapshot of the project state at the end of our session. It is intended to be used by a Gemini agent in a future session to rapidly get up to speed on the project's goals, methodology, and current status.

---

## Overall Goal

The primary objective is to build and validate a **Zero-Shot Traffic Signal Control** system. This system uses **Prophet** for traffic forecasting and a **Deep Q-Network (DQN)** as the primary reinforcement learning agent. The entire process is simulated in **SUMO**.

The immediate priority for this session was to **generate preliminary results for the user's Thesis Chapter 3 on a tight deadline.**

## Key Knowledge & Methodology

This section contains the most important context about the project's architecture and the experimental methodology we developed.

-   **Core Pipeline:** The system is a forecast-driven RL pipeline. The agent's state is a vector combining **reactive data** (live queue lengths from SUMO) and **proactive data** (a future demand curve from a Prophet forecast).

-   **Agent Definition:** The agent has a discrete action space (`STAY` or `SWITCH` phase) and is trained using a reward function equal to the negative of the total vehicle waiting time.

-   **Chapter 3 Goal:** The objective was to generate data for two key subchapters: "Tradeoff Analysis" and "Sensitivity Analysis."

-   **Experimental Scenario:** To meet the deadline, we created a standardized `medium_traffic` scenario in SUMO. This scenario has a higher volume of traffic and includes conflicting turns, making it a suitable challenge for a preliminary experiment.

-   **Analysis Methodology:** We established a robust, 4-controller comparison:
    1.  **Fixed-Time Controller:** A non-AI baseline using a static timer.
    2.  **Tabular Q-Learning:** A simple RL baseline to justify the need for a neural network.
    3.  **DQN (Proposed):** The main algorithm for the thesis.
    4.  **D3QN (Advanced):** A more complex RL algorithm for comparison.

-   **Metrics & Ranking:** The controllers are evaluated on three metrics: **Average Wait Time**, **Average Queue Length**, and **Total Throughput**. A 0-10 ranking system is used, where the best performer gets a 10 and others are ranked based on their percentage difference. This is used for the **Tradeoff Analysis**.

-   **Sensitivity Analysis:** A 3-trial sensitivity analysis is performed on the results, applying different weights to the metric ranks to determine the best overall controller under different strategic priorities.

## File System State (End of Session)

-   **`src/` directory:** All scripts are created, debugged, and functional.
    -   `config.py`: Contains the project hyperparameters.
    -   `sumo_environment.py`: The stable bridge between Python and the SUMO simulation.
    -   `dqn_agent.py`, `q_learning_agent.py`, `d3qn_agent.py`: All three agent architectures are implemented.
    -   `trainer.py`: A universal script capable of training any of the three agents via the `--agent` flag.
    -   `runner.py`: A universal script for evaluating any of the four controller types. It correctly measures all metrics (including throughput via detectors) and logs results to a CSV file.
    -   `generate_analysis.py`: A standalone script that reads `results.csv` and generates a complete HTML analysis report.

-   **`sumo/` directory:** All necessary simulation files are in place.
    -   `medium_traffic.sumocfg` & `medium_traffic_fixed.sumocfg`: The two main configuration files for AI-controlled and Fixed-Time simulations, respectively.
    -   `detectors.add.xml` & `fixed_time.add.xml`: The additional files that define the throughput detectors and the static traffic light program.

-   **`models/` directory:** Contains the three fully trained models generated during this session:
    -   `q-learning_agent.pkl`
    -   `dqn_agent.pth`
    -   `d3qn_agent.pth`

-   **Root Directory:** Contains the final outputs of our work.
    -   `results.csv`: The raw, timestamped performance data from the four evaluation runs.
    -   `analysis_report.html`: The final, complete HTML report containing all analysis tables.
    -   `Chapter3_Full_Layout.md` and other documentation files.

## Recent Actions Summary

During this session, we successfully:
1.  Designed and implemented a full, end-to-end pipeline for training, evaluation, and analysis.
2.  Implemented three distinct RL agents and a Fixed-Time baseline.
3.  Overcame numerous bugs related to Python syntax, SUMO configuration, and model saving/loading.
4.  Successfully trained all three agents on the `medium_traffic` scenario.
5.  Ran a full suite of evaluation experiments and logged the results to `results.csv`.
6.  Generated a complete analysis report (`analysis_report.html`) and a full written draft of the chapter (`Chapter3_Full_Layout.md`).

## Next Steps (Phase 2)

1.  **Archive Chapter 3 Artifacts**: Create a new directory, `experiments/chapter3_preliminary/`, and move the contents of the `models/` directory, `results.csv`, and all generated reports (`.html`, `.md`) into it to preserve a clean snapshot of this experiment.

2.  **Implement Zero-Shot Evaluation**: This is the primary goal for the next phase.
    -   Create new, unseen intersection scenarios in the `sumo/` directory (e.g., a five-way intersection, an asymmetric intersection with different lane counts).
    -   Use the existing `runner.py` script to evaluate the best-trained model (`dqn_agent.pth`) on these new maps **without any retraining**.

3.  **Analyze Zero-Shot Results**: Use the `generate_analysis.py` script (or a modified version) to analyze the new results from the zero-shot runs.

4.  **Write Chapter 4**: The results from the zero-shot evaluation will form the basis of the next chapter, focusing on the generalization capabilities of the agent.
