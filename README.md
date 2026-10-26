# Bank Automata Lab

**[Explore the interactive project presentation](docs/overview.html)** — open locally in your browser; works offline.

A small lab for following finite-state machines and answering 20 questions about bank records. Start with the built-in data, trace each decision, then try a CSV of your own. This is university coursework, not banking software.

## Try it first

Open **Dataset & pipeline**, select **Synthetic demo**, and click **Run all 20 questions**. Review individual answers in **Questions 1–20**; use **Automata lab** to trace a machine. Real bank data is not needed.

<details>
<summary>Using the existing managed Windows workspace</summary>

Assigned environment: **base** — Python **3.13.5**, using the existing Conda environment `base`. Open `Workspaces/bank-automata-lab.code-workspace` from the workspace folder to select its interpreter.

From this repository folder in PowerShell:

```powershell
& '..\Launchers\bank-automata-lab.cmd' --check --deep
& '..\Launchers\bank-automata-lab.cmd'
```

The launcher activates the assigned environment and checks dependencies. It does not install packages or download models. These launchers belong to the managed parent workspace; for a standalone clone, follow the setup instructions below in your own compatible environment. Keep optional model/provider prerequisites separate from the offline examples.

</details>

## Run

Activate an existing Python/Conda environment with the requirements already available. Nothing is installed automatically.

```powershell
conda activate base
python -m streamlit run app.py --server.address 127.0.0.1
```

Dependencies are recorded in `requirements.txt`; review them before any optional installation. Heavy workloads and private datasets are not needed to explore the demos. `run.bat` uses the active environment.

On Windows, `run.bat --check` checks the active environment without opening the app. Run `run.bat` to start, or `run.bat --server.port 8502` if another app is using the default port. The launcher works from any working directory and installs nothing.

## Layout

- `app.py`: small Streamlit entry point.
- `bank_workbench/`: application logic and interface.
- `tests/`: focused regressions.
- `docs/`: detailed method, formats, comparisons and earlier verification.
- `notebooks/`: executed synthetic coursework notebook; Q20 output stays empty.

## Verify

```powershell
python -m unittest discover -s tests -v
```

See [method and usage](docs/METHOD.md) for capabilities, original comparisons, privacy rules and material limitations. Tests use synthetic data; full-size private bank datasets are not implied to be verified.

Checked on Windows with Python 3.13.5 (Conda base): **22 tests passed**. Full 32-million-row execution remains unverified.

Input checks now reject duplicate CSV headers (including whitespace collisions) and invalid fractional/non-finite processing settings before producing partial answers. Batch credit decisions use the same evidence as the inspectable NFA without building a teaching trace for every row. Fractional birth years are treated as unknown rather than truncated. The interface retains its current tabs and styling; changed source-file metadata invalidates stale results.
