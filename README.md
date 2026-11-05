# climate

Ocean indices (NINO3.4, TSA and AMM) and monthly quintile forecasts of rainfall in Northeast Brazil: assessed lags, calibration and three models (ridge regression, random forest and a dense neural network).

This repository holds the notebook, the runner, the checks and the article scripts used to test whether lagged associations between three ocean indices and monthly CHIRPS rainfall in three regions of Northeast Brazil translate into out-of-sample monthly forecast skill. Each model is compared with the same model without the index. The notebook downloads all input data from the original sources, fixes every random seed and writes a SHA-256 manifest of its outputs.

*Resumo em português:* o repositório reúne o notebook, o executor, as conferências e os scripts do artigo que testam se as associações defasadas entre três índices oceânicos e a chuva mensal do CHIRPS no Nordeste do Brasil se traduzem em habilidade de previsão fora da amostra.

## Research question

Do the lagged associations between each index and monthly rainfall translate into out-of-sample forecast skill? Each index is evaluated alone, in three targets (NNEB, INEB and ENEB), three cases (hydrological year, wet season and dry season), for the whole target and for each 0.05° pixel.

Three families of predictive models are evaluated: regularized linear regression (ridge), an ensemble of trees (random forest) and a neural network with one hidden layer.

The design separates three things:

- **Association:** lagged correlation, assessed in 1981–2010.
- **Predictive skill:** RPSS of each model over the standard climatology N (20% in each quintile), the common reference that allows the models to be compared, and over the same model without the index (attribution test), in 2011–2025.
- **Physical interpretation:** a reading of the evidence, with no causal effect estimated.

## Main result and limits

Numbers from the published full run (tables in `resultados/completo/tabelas`; checks in `conferencia_publicacao_completo.md`):

- **Association (1981–2010):** detected in 11 of the 27 combinations of target, case and index after correction for multiple testing (NINO3.4 in 6, TSA in 4, AMM in 1), with |r| from 0.19 to 0.39.
- **Forecast (2011–2025):** over the standard climatology, ridge regression gained +1.0% to +1.8% RPSS in the north (NNEB), with NINO3.4 four months ahead and TSA two months ahead, with 95% CI above zero; the neural network repeated the gain, and without the index the gain disappears (`artigo/saidas/completo/rpss_climatologia.csv`). None of the 81 gain hypotheses passed the multiple-testing correction (q ≥ 0.069).
- **Models:** ridge regression was the most stable (−0.5% to +1.8% over climatology), followed by the neural network (−0.6% to +1.5%); the random forest ranged from −16.7% to +5.5%.
- **Forecasts close to climatology:** for ridge regression and the neural network, probabilities stay within 3.9 percentage points of 20%, and the ridge confidence intervals (conditional on the forecasts, not simultaneous) exclude gains above 3.1% RPSS. In the evaluated configuration, the random forest departs up to 20.5 points from 20% and ranges from −16.6% to +5.6% RPSS over its control, with no confirmed gain.
- **Reading:** lagged association did not imply confirmable monthly skill with single indices, under this protocol and in this test period. Absence of confirmation is not absence of effect.

The limits are listed under "Declared scope and limits" and in `artigo/README.md`.

## Periods

| use | years |
|---|---|
| rainfall data (monthly CHIRPS v2.0) | 1981–2025 (45 years) |
| final reference: quintiles, classes, climatology N, lags and final fit | Jan 1981–Dec 2010 |
| inner calibration: input form and hyperparameters | training Jan 1981–Dec 1995 and validation Jan 1996–Dec 2010, with quantiles from the inner training period |
| test | Jan 2011–Dec 2025 |

Each role is a calendar window common to the three targets, and only hydrological years with all 12 months inside it are used. NNEB (year from January to December) therefore has 30 reference years, 15 + 15 for calibration and 15 for testing, and INEB (November to October) and ENEB (March to February) have 29, 14 + 14 and 14. No test month of any target enters the shared calibration choice.

## Declared scope and limits

- The test period was examined during the development of the study. Configuration choices were fixed with 1981–2010, but the evaluation is not an entirely unseen test.
- The p-value of the hypothesis comes from circular shifts of the index, in 4-month steps for computational cost. The smallest possible p-value is 1/131; with Benjamini–Hochberg over 27 combinations, q < 0.05 therefore requires at least five combinations of the same method with the p-value at the floor.
- The shift test was checked only with ridge regression, only for whole targets and in one scenario containing the index trend. Under the stated null hypothesis, a shared trend counts as information from the index; rejections in that scenario measure the sensitivity of the test to the trend, not type I error. The check does not extend to the other models or to the maps.
- Inference is conditional on the configuration chosen in calibration, and confidence intervals are marginal, not simultaneous.
- Pixel maps are exploratory: significance is controlled by the false discovery rate and read together with magnitude.

## Contents

| file | what it is |
|---|---|
| `climate.ipynb` | the study notebook, executed and with all outputs (tables, figures and text): methodological cover, Acquisition, Sections 1 to 10 and Closing |
| `executar_tudo.bat`, `executar_tudo.py` | full pipeline: kernel, pilot, pilot check, full study, release check and article scripts |
| `rodar_climate.py` | terminal runner for the notebook, with a completion estimate for each section every 2 h; at the end of the full run, it writes the outputs into `climate.ipynb` |
| `conferir_publicacao.py`, `conferencia_publicacao_completo.md` | release check (see below) and its report for this run |
| `requirements.txt` | direct dependencies, with pinned versions |
| `requirements-lock-windows.txt` | full environment of the reference run on Windows |
| `resultados/completo/` | tables, figures, forecasts, maps, logs and SHA-256 manifest (included in the release) |
| `dados/registro.json` | URL, access date, size and SHA-256 of each data file used |
| `artigo/` | scripts that read the results and generate the diagnostics, numbers, figures and tables of the article (`artigo/README.md`) |
| `LICENSE`, `LICENSE-RESULTADOS.md`, `CITATION.cff` | licences and citation |

Documentation, the notebook's text cells and the comments, docstrings and messages of the scripts are in English. Code identifiers, file names and the column names of the result tables are in Portuguese: the notebook code cells are part of the signed code of the published run (the code hash in `resultados/completo/registros/assinatura.json`), and the result tables are covered by the SHA-256 manifest, so changing them would require re-running the full study.

## Environment

Reference run: Windows 11, Python 3.13.15, PyTorch 2.14.1 (CPU), 12 cores. The pilot was also checked on Linux with Python 3.13.17.

The commands below are for PowerShell, inside the repository folder. They call the environment's Python directly, without `Activate.ps1`. On Linux or macOS, replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m ipykernel install --user --name climate --display-name "Python (climate)"
```

To reproduce the reference environment exactly on Windows, use `requirements-lock-windows.txt` instead of the two installation lines for PyTorch and `requirements.txt`.

To check the kernel, run the two commands below. The `climate` line must appear, and `argv` must start with the `python.exe` of `.venv`.

```powershell
.\.venv\Scripts\python.exe -m jupyter kernelspec list
.\.venv\Scripts\python.exe -c "from jupyter_client.kernelspec import KernelSpecManager as K; print(K().get_kernel_spec('climate').argv)"
```

The runner also checks this before starting: it only runs with the `.venv` Python and with the `climate` kernel pointing to that same Python.

## Running

The whole pipeline runs with one command, which stops at the first step with an error:

```powershell
.\executar_tudo.bat
```

There are ten steps: kernel, pilot, pilot check, full study, release check and the five article scripts (diagnostics, RPSS over climatology, numbers, figures and tables). To run only the notebook:

```powershell
.\.venv\Scripts\python.exe rodar_climate.py --modo piloto   # quick check, resultados/piloto
.\.venv\Scripts\python.exe rodar_climate.py                 # full study, resultados/completo
```

- **Data:** on the first run, the notebook downloads the data from the original sources (CHIRPS, NOAA PSL and IBGE) into `dados/` and records each file. Internet access is needed for this step. Nothing is read from outside the folder.
- **Progress:** the terminal shows the completion estimate for each section every 2 h.
- **Resuming:** Ctrl+C interrupts, and the same command resumes where it stopped. The results folder is reused only if the data (values), code, configuration, library versions and execution environment are the same. Each stored file is checked by content before reuse; whatever fails is redone.
- **Time:** the full study takes about 5 h 30 min on the reference machine (12 cores).
- **Notebook outputs:** at the end of the full run, `climate.ipynb` receives the outputs (tables, figures and summaries), and a local copy (`climate_executado.ipynb`, outside the repository) is used by the release check.

## Randomness

- **Seeds:** the root seed is 42. Each task uses a seed derived from the root and the task name (SHA-256), identical on any machine.
- **PyTorch:** runs in strict deterministic mode (`torch.use_deterministic_algorithms(True)`), on the CPU.
- **Environment record:** the notebook records the device and the number of threads of PyTorch, BLAS/OpenMP and joblib. These values enter the run signature.
- **Limit:** identical seeds do not guarantee identical numbers across platforms or library versions. On the same machine and with the same versions, the numbers repeat. Between Windows and Linux, the neural network differed by up to 1e-5 in the pilot, without changing any conclusion.

## Provenance

- **Data:** each downloaded file has its URL, access date and SHA-256 in `dados/registro.json`. Downloads on different dates or systems may have different bytes with the same values; the run signature therefore uses a SHA-256 of the values read.
- **Results:** every file in `resultados/completo/` is in the SHA-256 manifest (`resultados/completo/registros/manifesto.json`), together with the configuration, the environment and the numbering of tables and figures.

## Release check

After the full run:

```powershell
.\.venv\Scripts\python.exe conferir_publicacao.py
```

The script checks nine points and writes the report to `conferencia_publicacao_completo.md`:

1. the notebook ran without errors and in order;
2. the code of the executed notebook is the same as the source and as the signature;
3. the SHA-256 manifest matches the files;
4. the RPSS of each model, recomputed from the stored forecasts, equals that of the hypothesis table;
5. the verdict follows the declared rule;
6. each figure exists in PNG and PDF;
7. the outputs contain no machine paths;
8. the temporal cuts: the shared calibration choice ends before validation, validation and final training end by December 2010, and the test of every target starts after that;
9. no model with the index is identical to its no-index control (a model that does not use the index does not test the hypothesis).

## Citation and licence

Cite via `CITATION.cff`. The code is under the MIT licence, and the results under CC BY 4.0 (`LICENSE-RESULTADOS.md`).
