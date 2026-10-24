# Bank Automata Lab

A local, educational Python application for the twenty-question **Theory of Languages and Machines** fictional bank project. It combines a five-tab interface, bounded CSV processing, inspectable DFA/NFA/tape-machine simulations, and a runnable Jupyter submission notebook.

No real banking operations are performed. The included demo is generated synthetic data; original customer data and private relative results are not distributed.

## Run

Tested on Windows with Python **3.13.5**. From the repository root:

```powershell
conda activate base
# Optional, only if dependencies are missing and installation is authorized:
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

From an activated terminal, Windows users can run `run.bat`. On other platforms, use Python from an existing compatible environment; those platforms have not been tested. Dependencies are pinned to the tested Streamlit, pandas, and NumPy versions. Keep the server bound to localhost: this is a personal coursework tool, not a multi-user service.

1. Open **Dataset & pipeline**, keep **Synthetic demo**, and click **Run all 20 questions**.
2. Inspect individual results in **Questions 1–20**, including the age-cohort chart.
3. Use **Automata lab** to inspect diagrams and transition traces.
4. Download the executed notebook in **Notebook & exports**. Private Q20 CSV export requires an explicit new destination outside the repository.

Uploaded CSVs are limited to 25 MB. For large datasets choose **Local CSV path**; the application reads two passes in configurable chunks and retains only bounded previews. Keep the file unchanged until processing/export completes. Streamlit's Stop control interrupts work; the previous successful report survives failed processing. Changed inputs visibly mark old results stale and disable exports.

## Dataset format

UTF-8 CSV, optionally with a BOM, with these canonical columns:

```text
national_id,first_name,last_name,father_name,birth_date,birth_city,birth_province,residence_city,residence_province
```

The original schema is also accepted: `national_code`, `FULL_NAME`, `FATHER_NAME`, `BIRTH_DATE`, `BIRTH_CITY`, `BIRTH_PROVINCE`, `CITY_NAME`, `PROVINCE_NAME`. `FULL_NAME` splits at its first whitespace: compound given names are ambiguous, so use separate canonical name columns when needed. Canonical columns take precedence over aliases. Unrelated columns are ignored.

All values are read as strings to retain leading zeros. Arabic/Persian ye and kaf, Persian/Arabic digits, half-spaces, and repeated whitespace are normalized. National IDs must contain 1–10 digits; invalid values are preserved and counted, never truncated. This checks format, not the Iranian national-ID checksum. Dates use `YYYY/MM/DD`; cohort ages are reference year minus birth year, not precise birthday-adjusted ages. Input date validation checks format and basic ranges, not full Jalali leap-year validity.

## Coursework coverage

| Questions | Implemented behavior |
|---|---|
| 1–3 | Seeded reservoir sample of 10, source schema/Unicode inspection, missing-province rule, ID padding and invalid-ID counts |
| 4–8 | Exact surname/province filters, dormitory address, unique 16-digit cards, compound surname lookup, Vania count |
| 9–12 | Two birth cohorts and average-age chart, configurable birthday twins, Persian father-name letters, Khalkhal count |
| 13 | Real suffix DFA; count rejected surnames |
| 14 | Parallel credit evidence paths: accept, reject, or review |
| 15 | DFA requiring a vowel before an allowed final character |
| 16 | Two-of-three risk NFA, with subset-construction explanation |
| 17 | Global richest account and exact integer redistribution to dormitory recipients |
| 18–19 | Balance tape/register simulation, separate numeric balance and blocked status, active VIP filter |
| 20 | Exact relative surname; exact city also required without a known suffix; explicit private CSV export |

Q2 deliberately fills the **province** field with the birth province's capital **city**, because that is what the assignment requests. Unknown provinces remain blank. Q14 priority surnames match exactly after removing word separators; unmatched records remain undecided. NFAs consume Boolean evidence tokens derived from record fields. Q18 is an educational tape/register simulation with explicit read/compare/write/halt steps, not a minimal single-tape transition table.

Balances are seeded integers from 100,000 through 200,000,000,000 IRR by default. In Q17, ties choose the first source row. The donor is zeroed before distributing shares, including when the donor is a recipient. Integer remainders go to the first recipients in source order; no recipients means no transfer. The pipeline verifies conservation and replay counts. Cards and balances are independent of chunk size for unchanged row order and configuration.

Q18 exposes `tm_balance` (number or `مسدود`) while preserving `account_balance` and `account_status`. Q19 excludes blocked accounts. Q20 exports only cleaned identity/location fields, never banking fields; it refuses to overwrite existing files or the source. Export is committed with an exclusive hard link, so the destination filesystem must support hard links (tested on NTFS).

## Notebook

`notebooks/bank_coursework.ipynb` contains **20 ordered code cells**, explanatory Markdown, executed synthetic outputs, and an age chart. Q20 output is empty. Open it with Jupyter or a notebook-capable editor using this environment; Jupyter itself is optional and not installed by the app requirements.

Run the notebook from this repository so it can import `bank_workbench/bank_core.py`, `bank_workbench/automata.py`, and `bank_workbench/demo.py`. The notebook relies on these readable modules rather than embedding duplicate implementations. Q1 computes the complete pipeline; each later cell displays its question. Set `SOURCE_PATH` and the `Config` values in Q1 to rerun on your dataset. The default always reruns synthetic data. Personal-source notebook downloads omit row previews and relative-search criteria; their saved aggregate results describe the completed run, and rerunning the default demo will change them. Q10's configured birthday remains in the notebook configuration: treat personal exports as private.

## Compared with the original project

| Original behavior inspected | Result here |
|---|---|
| CSV chunks repeatedly concatenated into one full DataFrame | Two bounded passes; no full-dataset accumulation |
| Suffix regex accepted a ye anywhere in the surname | Explicit DFA, checked exhaustively against the intended suffix language |
| Floating-point transfers could erase the donor's own recipient share | Integer conservation, deterministic remainder allocation, donor-as-recipient regression |
| Default generated balances never reached the blocking threshold | Synthetic runs exercise blocked and active accounts; threshold boundaries tested |
| Individual questions depended on earlier mutable GUI actions | A single reproducible run resolves dependencies in order |
| Dense text outputs and separate machine displays | Five task-oriented tabs, tables, age chart, input-specific machine controls and inspectable traces |
| Private relative rows could appear in question output | Q20 previews and notebook outputs suppressed; explicit guarded local export |

The original Tkinter files and original notebook remain untouched outside this repository. The new app preserves the twenty required workflows and the interactive machine inspection purpose. It does not carry forward every decorative log/statistic, full-dataset in-memory table, or standalone Tkinter window.

## Verification and limits

```powershell
python -m unittest discover -s tests -v
python -m bank_workbench.benchmark --rows 100000 --chunksize 5000
```

All 16 tests passed in a newly created isolated environment; dependency and Ruff checks passed. Chromium browser review passed at desktop, tablet, and mobile sizes, including all five machines and the TM step slider.

Tests cover exhaustive small DFA languages, all risk truth combinations, credit/TM boundaries, expected demo counts, chunk independence, legacy schema compatibility, money conservation, private export protection, input mutation, notebook replay/privacy, and real Streamlit AppTest workflows.

Measured locally on Windows/Python 3.13.5 with 5,000-row chunks:

| Synthetic rows | Two-pass time | Peak process working set |
|---:|---:|---:|
| 100,000 | 9.129 s | 96.85 MiB |
| 300,000 | 27.734 s | 96.63 MiB |

Both runs conserved total balances. Memory is the Windows peak working set including Python/pandas, measured in separate processes; these are observations, not a guarantee for other machines or unusually wide records. The original **32-million-row dataset was unavailable and has not been tested**. Local source-change checks use file metadata, not a full content hash. Uploads occupy memory as bytes. Only aggregate counts and bounded example rows are retained, so arbitrary browsing of every match is not offered. No production banking, creditworthiness, fraud, or identity-validation claim is made.

## Files

`app.py` and `.streamlit/config.toml` provide the interface; `bank_workbench/bank_core.py` owns streaming rules; `bank_workbench/automata.py` owns machines; `bank_workbench/demo.py` supplies synthetic data; `bank_workbench/notebook_builder.py` generates the notebook; `tests/test_*.py` and `benchmark.py` verify behavior. No license has been selected. Keep personal CSVs, environments, private exports, and secrets outside version control.
