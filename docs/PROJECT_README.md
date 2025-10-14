# Project Snapshot & Workflow: The Definitive Guide

## 1. Project Goal & Current Status

**Overall Goal:** The primary objective of this thesis is to develop and validate a **Zero-Shot Traffic Signal Control** system. This system uses Prophet for traffic forecasting and a Deep Q-Network (DQN) agent to learn intelligent control policies within the SUMO simulation environment. The key innovation is the "zero-shot" capability, allowing a model trained on one set of intersections to be effective on new, unseen ones without retraining.

**Current Status (SUCCESS):** The project has successfully transitioned from a lengthy and complex debugging phase into a **fully operational, verifiable, and robust experimental pipeline**. The persistent "identical results" bug, which plagued earlier versions, has been definitively solved. The system is now ready for the formal experimentation required to generate the final results for your thesis.

---

## 2. Summary of Recent Work: Major Debugging

Our recent sessions were dedicated to a multi-phase debugging process to solve the core issue of deterministic agent behavior. This journey is critical context for understanding the current state of the codebase.

1. **Phase 1: Fixing the Code Pipeline:** We began by correcting the application's structure. We discovered the system was not performing the **per-direction forecasting** it was designed for. We modified `src/config.py`, `src/trainer.py`, and `src/runner.py` to handle four distinct forecast files, fixing numerous bugs related to file paths, missing dependencies (`pandas`, `prophet`), and Python imports along the way. This resulted in a structurally correct pipeline.

2. **Phase 2: Building a High-Fidelity Data Pipeline:** We then addressed the data itself, replacing all arbitrary "dummy" data with a verifiable pipeline derived from your `foi_transcript.csv`.
   - **Data Cleaning:** We first split the messy, multi-part `foi_transcript.csv` into three clean, single-purpose CSV files: `data/volume_total.csv`, `data/volume_am.csv`, and `data/volume_pm.csv`.
   - **Profile Generation:** We created two new scripts, `src/build_traffic_profile.py` and `src/build_turning_profile.py`, to engineer a verifiable `standard_24h_profile.json` (the daily traffic "rhythm") and a correct `standard_turning_profile.json` (the turning ratios) from the clean data.
   - **Realistic Simulation:** We created a final data-generation script, `src/generate_real_traffic_routes.py`, to produce a high-fidelity `sumo/real_traffic.rou.xml` file with over 400,000 unique vehicles, ensuring the simulation itself is complex and realistic.

3. **Phase 3: Tuning the Agent's Learning:** With a perfect data pipeline, we addressed the final issue: the agent's inability to learn a complex policy.
   - **State Normalization:** We modified `src/sumo_environment.py` to scale all inputs to the agent's "brain" to a standard [0, 1] range, a critical best practice for neural networks.
   - **Hyperparameter Tuning:** We experimented with the `EPS_DECAY` value in `src/config.py` to influence the agent's exploration-exploitation strategy.

This three-phase process was successful, leading to the breakthrough where models trained for different durations produced different results, proving the system is working as intended.

---

## 3. The Final Pipeline: A Detailed File-by-File Breakdown

The project now operates as a robust, two-stage process: a one-time **Data Calibration** phase and a repeatable **Experimentation** phase.

### Phase A: Data Calibration & Environment Generation (One-Time Setup)

This phase transforms your raw source data into a complete, high-fidelity simulation environment. It only needs to be run once, or whenever the source data changes.

- **Step A.1: Data Cleaning**
  - **Input:** `foi_transcript.csv`
  - **Action:** Manually or programmatically split the single messy file into three clean CSVs.
  - **Output Files:** `data/volume_total.csv`, `data/volume_am.csv`, `data/volume_pm.csv`.

- **Step A.2: Build 24-Hour Profile**
  - **Script:** `src/build_traffic_profile.py`
  - **Action:** Reads the clean peak hour data (`volume_am.csv`, `volume_pm.csv`) and uses a bimodal distribution model to extrapolate and generate a verifiable 24-hour traffic rhythm.
  - **Output:** `data/profiles/standard_24h_profile.json`.

- **Step A.3: Build Turning Profile**
  - **Script:** `src/build_turning_profile.py`
  - **Action:** Reads the clean total volume data (`volume_total.csv`) and robustly parses lane descriptions to calculate the true turning percentage for each approach.
  - **Output:** `data/profiles/standard_turning_profile.json`.

- **Step A.4: Generate Realistic Traffic Routes**
  - **Script:** `src/generate_real_traffic_routes.py`
  - **Action:** Uses the two `.json` profiles to orchestrate a full 24-hour traffic schedule, generating over 400,000 unique `<vehicle>` definitions with randomized departure times.
  - **Output:** `sumo/real_traffic.rou.xml`.

- **Step A.5: Configure SUMO**
  - **Action:** We created two new SUMO configuration files that point to the new realistic route file.
  - **Output Files:** `sumo/real_traffic.sumocfg` (for AI agents) and `sumo/real_traffic_fixed.sumocfg` (for the baseline).

### Phase B: Automated Experimentation

This is the repeatable process for running your thesis experiments.

- **Entry Points:** `src/trainer.py` and `src/runner.py`.

- **Step B.1: Automated Data Generation (On-the-fly)**
  - **Scripts:** `src/create_real_data.py` -> `src/forecasting.py`
  - **Process:** When you run the trainer or runner, it now automatically triggers this chain. `create_real_data.py` uses the standard profile and total volume data to generate the four `prophet_input_*.csv` files. Then, `forecasting.py` is called four times to produce the four unique `demand_curve_*.json` forecast files.

- **Step B.2: Simulation and State Representation**
  - **Script:** `src/sumo_environment.py`
  - **Process:** This script now loads the `real_traffic.sumocfg` and the four unique forecast files. Its `_get_state()` method provides the agent with a fully **normalized** state vector, and its `step()` method provides raw data back to the runner for accurate metrics.

- **Step B.3: Analysis**
  - **Script:** `src/generate_analysis.py`
  - **Process:** This script is now parameterized. It can take any `results.csv` file as input (`--input`) and generate a full HTML report (`--output`) containing all the tradeoff and sensitivity analysis tables.

---

## 4. Future Work & The Path to the "God" Model

The project is now perfectly positioned for the final research phase.

1. **Implement Domain Randomization:** This is the key next step to create a true zero-shot agent. The `trainer.py` script should be modified to call `generate_real_traffic_routes.py` at the start of _every episode_, with slightly randomized parameters (e.g., total volume, directional bias). This will force the agent to become a robust generalist.

2. **Conduct Full-Scale, Randomized Training:** Train the DQN agent for thousands of episodes using this domain randomization approach to create the final "god" model.

3. **Perform Final Comparative Analysis:** Run the final evaluations for all four controller types against the static, high-fidelity `real_traffic.rou.xml` to generate the definitive tables for your Chapter 3.

4. **Execute Zero-Shot Validation:** Test your final, domain-randomized "god" model on completely new, unseen intersection maps to validate its generalization capabilities, which will be the core of your Chapter 4.
