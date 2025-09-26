## Dependencies

*   **Python:** >=3.11
*   **SUMO:** >=1.24.0
## Setup

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh #Linux/macOS
```

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex" #Windows
```

### Clone
```bash
git clone https://github.com/coolport/thesis
cd thesis
```

### Run
```bash
uv sync
uv run python src/trainer.py --agent dqn --episodes 10
```

