# Q&A Summary: Agent Selection & Traffic Light Definitions (2025-10-09)

This file captures key questions and answers regarding the project's implementation details.

---

### **Question 1: How do `runner.py` and `trainer.py` select which agent model to use?**

**Answer:**

Both scripts use the same simple and effective mechanism:

1.  **Direct Imports:** At the top of each script, the different agent classes are imported directly from their source files in `src/`.
    ```python
    from dqn_agent import DQN
    from d3qn_agent import D3QN
    from q_learning_agent import QLearningAgent
    ```

2.  **Argument Parsing:** The scripts take a command-line argument, `--agent` (e.g., `--agent dqn`).

3.  **Conditional Selection:** An `if/else` block checks the string value passed to the `--agent` argument and assigns the corresponding imported class to a variable named `AgentClass`.
    ```python
    # This line is in both trainer.py and runner.py
    AgentClass = DQN if agent_name == 'dqn' else D3QN
    ```

4.  **Instantiation:** The script then creates an instance of the selected agent using that `AgentClass` variable.

In short, the scripts decide which Python class to use based on a simple `if/else` statement that checks the string you provide in the command line.

---

### **Question 2: What are the traffic light definitions, where are they, and what is the basis for their values?**

**Answer:**

The core definition for the AI-controlled traffic light is located in `sumo/test.net.xml`. The definitions are the same for both training and evaluation to ensure consistency.

The definition block looks like this:
```xml
<tlLogic id="center" type="static" programID="0" offset="0">
    <phase duration="41" state="GGGGggrrrrrrGGGGggrrrrrr"/>
    <phase duration="4"  state="yyyyyyrrrrrryyyyyyrrrrrr"/>
    <phase duration="41" state="rrrrrrGGGGggrrrrrrGGGGgg"/>
    <phase duration="4"  state="rrrrrryyyyyyrrrrrryyyyyy"/>
</tlLogic>
```

#### **Basis for Phase Durations (41s and 4s):**

*   **4 seconds (Yellow Light):** This is based on real-world traffic engineering standards, which typically recommend 3-6 seconds for a yellow light to ensure driver safety.
*   **41 seconds (Green Light):** This is a reasonable but arbitrary value chosen for the simulation. It creates a total cycle time of 90 seconds (41+4+41+4), which is a common baseline for a moderately busy intersection. It is not a specific standard but a sensible choice for the simulation's benchmark.

#### **Syntax of the `state` Attribute (`GGGGggr...`):**

This string is a character-by-character map of the state of every individual signal for every possible movement at the intersection.

*   **Each Character is a Light:** Every character corresponds to one signal for one movement (e.g., North-to-South straight).
*   **The Order is Fixed:** SUMO internally indexes every movement. The position of a character in the string corresponds to one of those indexed movements.
*   **The Character Meanings:**
    *   `G`: **Green**
    *   `g`: **Protected Green** (usually for turns)
    *   `y`: **Yellow**
    *   `r`: **Red**

So, `state="GGGGggrrrrrrGGGGggrrrrrr"` defines a state where North-South traffic is allowed to go (`G` and `g` lights) while East-West traffic is stopped (`r` lights).

#### **How the AI Controls It:**

The agent's actions (`0` for STAY, `1` for SWITCH) control the transitions between these pre-defined phases. It learns the optimal *timing* for switching, rather than inventing new signal patterns.
