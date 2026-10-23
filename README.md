# Bank Automata Workbench

Twenty bank-coursework questions, inspectable automata, streaming CSV processing, and a private-output-aware notebook. Educational software; see the verification limits below.

## Run

Activate an existing Python/Conda environment with the requirements already available. Nothing is installed automatically.

```powershell
conda activate base
python -m streamlit run app.py --server.address 127.0.0.1
```

Dependencies are recorded in `requirements.txt`; review them before any optional installation. Heavy workloads and private datasets are not needed to explore the demos. `run.bat` uses the active environment.

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

See [method and usage](docs/METHOD.md) for capabilities, original comparisons, privacy rules and material limitations. Tests use synthetic data; native MATLAB, full-size datasets and optional external models are not implied to be verified. No license has been selected.

Current lightweight check (Windows, existing Conda base / Python 3.13.5): **17 passed**. No dependency installs, model downloads, live publishing, or heavy datasets were used. Full 32-million-row execution remains unverified.
