# Article: scripts and products

This folder links the manuscript to the notebook run. The scripts only **read** `resultados/<mode>/`: they do not refit models, redo tests or change the notebook or the results, which have their own SHA-256 manifest. Tables are read by name (`T*_hipotese_tres_metodos.csv`), not by number.

## Manuscript files

The manuscript (`Article_climate_IJoC.docx`) and its Supporting Information (`Supporting_information_climate_IJoC.docx`) are kept locally in this folder, next to the Portuguese source (version 1), and are not tracked in the repository until publication.

## How to generate

`executar_tudo.py` (or `executar_tudo.bat`) runs the five scripts at the end of the pipeline. To run them separately, from the repository folder:

```powershell
.\.venv\Scripts\python.exe artigo\diagnosticos_artigo.py
.\.venv\Scripts\python.exe artigo\rpss_climatologia.py
.\.venv\Scripts\python.exe artigo\numeros_artigo.py
.\.venv\Scripts\python.exe artigo\figuras_artigo.py
.\.venv\Scripts\python.exe artigo\tabelas_artigo.py
```

Outputs in `artigo/saidas/completo/`:

| file | content |
|---|---|
| `diagnosticos_previsoes.csv` | RPSS over climatology N of the model and of the control; standard deviation of the Q1 and Q5 probabilities in the test period; checks the RPSS over the control against the hypothesis table |
| `rpss_climatologia.csv` | RPSS of each model and of its control over the standard climatology N, with 95% CI (2000 resamples of circular 3-year blocks), and RPSS over the control; the reference common to the three models, used in the text, the graphical abstract and Table S8 |
| `numeros.json` | every number quoted in the text, extracted from the final tables (Portuguese number format) |
| `figuras/fig1…fig6`, `resumo_grafico` | main-text figures and graphical abstract in PNG (300 dpi) and PDF, with the data of each panel in `*_dados.csv` |
| `tab2.json`, `supl.json` | Table 3 of the text and Tables S1 to S7 of the Supporting Information (Table S8 comes from `rpss_climatologia.csv`), with cells already formatted |

## Main-text figures

| figure | file | content |
|---|---|---|
| 1 | `fig1_alvos_ciclo` | map of the targets (a) and mean monthly rainfall in 1981–2010 for each target (b–d), with months in hydrological-year order, the wet season in the target colour and the line of the mean monthly rainfall of the year |
| 2 | `fig2_perfis_defasagem` | correlation between each index and the rainfall rank `u` as a function of lag, by target and case |
| 3 | `fig3_mapas_chuvosa` | pixel correlation in the wet season; figure F09 of the notebook, copied unchanged |
| 4 | `fig4_predominio_defasagem` | dominant index in each pixel, with intensity given by \|r\| (a–c), and the lag of that index (d–f); built from F13 of the notebook, with the \|r\| scale drawn by the same colour rule (intensity \|r\|/0.5, between 0.15 and 1). `numeros_artigo.py` records the area, mean \|r\|, most frequent lag and fraction with the expected sign of each dominant index (table `indice_predominante`) |
| 5 | `fig5_habilidade_regional` | RPSS of each model over the same model without the index, with 95% CI, in the 27 combinations |
| 6 | `fig6_regularizacao_detectabilidade` | calibration, synthetic experiment and variation of the issued probabilities |
| GA | `resumo_grafico` | graphical abstract, exactly 50 × 60 mm, English labels |

## Procedures and limits assumed by the numbers

- **Temporal cuts.** Each role (reference, calibration training and validation, test) is a calendar window common to the three targets, and only hydrological years with all 12 months inside it are used. The notebook stops if the shared calibration choice uses any month after the start of the test of any target, and the release check verifies the cuts.
- **Random forest grid.** Minimum leaf of 30, 20, 10 and 5% of the training months. A 50% leaf is excluded: at depth 1 it only allows a split exactly at the median of the drawn months, and many trees would have no split. The notebook stops if any model with the index comes out identical to its control (item 9 of the release check).
- **Correlation.** Pearson between the raw index and the rainfall rank `u`; r² refers to `u`. The "detrended r" column is descriptive.
- **q-value.** The 4-month step gives 130 shifts and p ≥ 1/131. With Benjamini–Hochberg over 27 combinations, q < 0.05 requires at least five combinations of the same method with the p-value at the floor. q-values are shown with 3 decimals.
- **Shared trend.** Under the stated null hypothesis, the trend counts as information from the index. Rejections with surrogate indices that contain only the trend measure the sensitivity of the test to it, not type I error. Labels: "above 5%", "compatible with 5%", "below 5%".
- **Synthetic experiment.** Repeats the lag search, the grid and the one-standard-error rule, keeps the input form of the real data, uses one noise realization and does not repeat the hypothesis test; it does not estimate power.
- **Confidence intervals.** Conditional on the forecasts (configuration, L* and training fixed), marginal and not simultaneous.
- **Maps.** Pixel RPSS on a continuous diverging scale centred on zero. Pixels suspected of a break in CHIRPS stay in the analyses and are not marked; the list is in `resultados/<mode>/registros/pixels_suspeitos.csv`.
- **Exposure to the test period.** The test period was examined during the development of the study. Configuration choices were fixed with 1981–2010, but the evaluation is not an entirely unseen test.
