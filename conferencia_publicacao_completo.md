# Release check — mode completo

- Signature: `23f3260ccb7c4117`; code `8c8b2bfcc5bec2e1`; data `f636abc3aa900ce9`
- Environment: Python 3.13.15, PyTorch 2.14.1+cpu, Windows AMD64, threads {'pytorch (intra-op)': 12, 'pytorch (inter-op)': 6, 'BLAS e OpenMP': 'openblas 12; openmp 1; openmp 12', 'processos paralelos (joblib)': 12}

| status | check | detail |
|---|---|---|
| ok | executed notebook ran from start to end, without errors | 25 code cells; 0 errors |
| ok | code of source, executed notebook and signature | 8c8b2bfcc5bec2e1 |
| ok | SHA-256 manifest matches the files | 794 files; 0 mismatched; 0 outside the manifest |
| ok | RPSS recomputed from forecasts = hypothesis table | 81 combinations; largest difference 7.3e-14 p.p. |
| ok | verdict follows the declared rule | não detectada: 81 |
| ok | inventory figures in PNG and PDF | 32 figures; 0 missing files |
| ok | outputs without absolute machine paths | 0 occurrences |
| ok | temporal cuts common to the three targets | calibration up to 12/1995; validation 01/1996–12/2010; final training up to 12/2010; test from 01/2011 (3 targets) |
| ok | every model with the index differs from its control | 81 combinations; identical to the control: none |

Result: passed.
