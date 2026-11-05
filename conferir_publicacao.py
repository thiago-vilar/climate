r"""Release check for climate. Reads only this folder and changes nothing in it.

Usage (PowerShell, inside the repository folder, after the full run):
    .\.venv\Scripts\python.exe conferir_publicacao.py            # resultados/completo
    .\.venv\Scripts\python.exe conferir_publicacao.py --modo piloto

Checks:
 1. the executed notebook ran from start to end, without errors, in order;
 2. the code of the executed notebook is the same as the source notebook and as the results signature;
 3. every file in the SHA-256 manifest exists with the same size and hash, and no file lies
    outside the manifest (nor any resume .invalido or .tmp file);
 4. the RPSS of each model over its control, recomputed from the stored forecasts, equals that of
    the hypothesis table;
 5. the verdict follows the declared rule (RPSS > 0, q < 0.05 and a test check without rejection
    above 5% in the trend scenario);
 6. every figure in the inventory exists in PNG and PDF;
 7. the outputs contain no absolute machine paths;
 8. the temporal cuts: the shared calibration ends before validation, validation and final
    training end by Dec 2010, and the test of every target starts after that;
 9. no model with the index is identical to its no-index control (a model that does not use the
    index would give RPSS = 0 exactly and would not test the hypothesis).
Writes the report to conferencia_publicacao_<modo>.md and exits with code 1 if anything fails.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PASTA = Path(__file__).resolve().parent
K = 5
VOLATEIS = {'relatorio_parcial.md', 'relatorio_atual.md', 'execucao.log', 'manifesto.json'}
CAMINHO_ABS = re.compile(r'([A-Za-z]:\\\\[A-Za-z]|/home/[a-z]|/Users/[A-Za-z]|/tmp/[a-z])')


def sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, 'rb') as f:
        for parte in iter(lambda: f.read(1 << 20), b''):
            h.update(parte)
    return h.hexdigest()


def codigo(nb):
    return hashlib.sha256('\n'.join(''.join(c['source']) for c in nb['cells']
                                    if c['cell_type'] == 'code').encode()).hexdigest()


def rps(prob, classe):
    acum = np.cumsum(prob, -1)[..., :-1]
    obs = (np.asarray(classe)[..., None] <= np.arange(K - 1)).astype(float)
    return ((acum - obs) ** 2).sum(-1) / (K - 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--modo', choices=['completo', 'piloto'], default='completo')
    modo = ap.parse_args().modo
    saida = PASTA / 'resultados' / modo
    executado = PASTA / ('climate_executado.ipynb' if modo == 'completo' else 'climate_piloto.ipynb')
    if modo == 'completo' and not executado.exists():   # repository clone: only climate.ipynb
        executado = PASTA / 'climate.ipynb'
    linhas, falhas = [], 0

    def registrar(ok, item, detalhe=''):
        nonlocal falhas
        falhas += not ok
        linhas.append(f"| {'ok' if ok else 'FAIL'} | {item} | {detalhe} |")

    # 1. full run, without errors, in order
    nb = json.loads(executado.read_text(encoding='utf-8'))
    cod = [c for c in nb['cells'] if c['cell_type'] == 'code']
    erros = sum(o.get('output_type') == 'error' for c in cod for o in c.get('outputs', []))
    ordem = [c.get('execution_count') for c in cod]
    registrar(erros == 0 and ordem == list(range(1, len(cod) + 1)),
              'executed notebook ran from start to end, without errors',
              f'{len(cod)} code cells; {erros} errors')

    # 2. source = executed = signature
    fonte = json.loads((PASTA / 'climate.ipynb').read_text(encoding='utf-8'))
    assin = json.loads((saida / 'registros' / 'assinatura.json').read_text(encoding='utf-8'))
    c_f, c_e = codigo(fonte), codigo(nb)
    registrar(c_f == c_e == assin['codigo'], 'code of source, executed notebook and signature',
              f'{c_f[:16]}')

    # 3. manifest
    man = json.loads((saida / 'registros' / 'manifesto.json').read_text(encoding='utf-8'))
    listados = man['arquivos']
    ruins = [p for p, v in listados.items() if not (PASTA / p).exists()
             or (PASTA / p).stat().st_size != v['bytes'] or sha256(PASTA / p) != v['sha256']]
    presentes = {p.relative_to(PASTA).as_posix() for p in saida.rglob('*') if p.is_file()
                 and p.name not in VOLATEIS               # the manifest table is written
                 and not p.name.endswith('_manifesto_saidas.csv')}   # after it
    extras = sorted(presentes - set(listados))
    registrar(not ruins and not extras, 'SHA-256 manifest matches the files',
              f'{len(listados)} files; {len(ruins)} mismatched; {len(extras)} outside the '
              'manifest' + (f' (e.g. {extras[0]})' if extras else ''))

    # 4. stored forecasts -> hypothesis table
    hip = pd.read_csv(saida / 'registros' / 'hipotese_consolidada.csv')
    pre = saida / 'preditos'
    difs, iguais = [], []
    for _, r in hip.iterrows():
        m = r['método'].replace(' ', '')
        base = f"{m}_{r['alvo']}_{r['caso']}_{r['índice'].replace('.', '')}"
        with np.load(pre / f"amostras_{r['alvo']}_{r['caso']}.npz") as f:
            cl = f['cl']
        with np.load(pre / f'{base}_aferida.npz') as f:
            p = f['teste'].astype('float64')
        with np.load(pre / f'{base}_controle.npz') as f:
            p0 = f['teste'].astype('float64')
        rpss = 100 * (1 - rps(p, cl).sum() / rps(p0, cl).sum())
        difs.append(abs(rpss - r['RPSS sobre o modelo sem índice (%)']))
        if np.abs(p - p0).max() < 1e-12:
            iguais.append(f"{r['método']} {r['alvo']} {r['caso']} {r['índice']}")
    registrar(max(difs) < 1e-6, 'RPSS recomputed from forecasts = hypothesis table',
              f'{len(difs)} combinations; largest difference {max(difs):.1e} p.p.')

    # 5. verdict
    lib = hip['teste por deslocamento (Ridge)'] == 'acima de 5 %'
    ganho = (hip['RPSS sobre o modelo sem índice (%)'] > 0) & (hip['q'] < 0.05)
    esperado = np.where(ganho & ~lib, 'sustentada',
                        np.where(ganho, 'inconclusiva (sensível à tendência)', 'não detectada'))
    registrar(bool((hip['veredito'] == esperado).all()), 'verdict follows the declared rule',
              ', '.join(f'{k}: {v}' for k, v in hip['veredito'].value_counts().items()))

    # 6. figures
    inv = pd.read_csv(saida / 'tabelas' / sorted(p.name for p in (saida / 'tabelas').glob(
        'T*_inventario_figuras.csv'))[0])
    faltam = [a for a in inv['arquivo'] for e in ('png', 'pdf')
              if not (saida / 'figuras' / f'{a}.{e}').exists()]
    registrar(not faltam, 'inventory figures in PNG and PDF',
              f'{len(inv)} figures; {len(faltam)} missing files')

    # 7. absolute paths
    textos = [json.dumps([c.get('outputs', []) for c in nb['cells']], ensure_ascii=False)]
    for p in saida.rglob('*'):
        if p.is_file() and p.suffix in ('.csv', '.json', '.md', '.log', '.txt'):
            textos.append(p.read_text(encoding='utf-8', errors='replace'))
    achados = sum(len(CAMINHO_ABS.findall(t)) for t in textos)
    registrar(achados == 0, 'outputs without absolute machine paths', f'{achados} occurrences')

    # 8. temporal cuts (calibration choices table)
    esc = pd.read_csv(saida / 'tabelas' / sorted(p.name for p in (saida / 'tabelas').glob(
        'T*_calibracao_escolhas.csv'))[0])
    cortes = {}
    for _, r in esc[esc['item'].str.startswith('cortes (')].iterrows():
        alvo, papel = re.match(r'cortes \((\w+)\): (.+)', r['item']).groups()
        m = re.match(r'(\d{2})/(\d{4})–(\d{2})/(\d{4})', r['escolha'])
        ini, fim = (int(m[2]), int(m[1])), (int(m[4]), int(m[3]))
        cortes.setdefault(alvo, {})[papel] = (ini, fim)
    ok = len(cortes) == 3 and all(len(c) == 4 for c in cortes.values())
    if ok:
        teste0 = min(c['teste'][0] for c in cortes.values())
        fim_cal = max(c['treino da calibração'][1] for c in cortes.values())
        ini_val = min(c['validação da calibração'][0] for c in cortes.values())
        fim_val = max(c['validação da calibração'][1] for c in cortes.values())
        fim_tr = max(c['treino final'][1] for c in cortes.values())
        ok = (fim_cal <= (1995, 12) < ini_val and fim_val <= (2010, 12)
              and fim_tr <= (2010, 12) < teste0)
        det = (f'calibration up to {fim_cal[1]:02d}/{fim_cal[0]}; validation {ini_val[1]:02d}/'
               f'{ini_val[0]}–{fim_val[1]:02d}/{fim_val[0]}; final training up to {fim_tr[1]:02d}/'
               f'{fim_tr[0]}; test from {teste0[1]:02d}/{teste0[0]} (3 targets)')
    else:
        det = 'cuts missing from the calibration choices table'
    registrar(ok, 'temporal cuts common to the three targets', det)

    # 9. models that do not use the index
    registrar(not iguais, 'every model with the index differs from its control',
              f'{len(hip)} combinations; identical to the control: '
              + ('; '.join(iguais) if iguais else 'none'))

    rel = [f'# Release check — mode {modo}', '',
           f"- Signature: `{assin['assinatura'][:16]}`; code `{c_f[:16]}`; data "
           f"`{str(assin.get('dados'))[:16]}`",
           f"- Environment: Python {assin['versoes'].get('python')}, PyTorch "
           f"{assin['versoes'].get('torch')}, {assin['versoes'].get('sistema')}, threads "
           f"{assin['versoes'].get('threads')}", '',
           '| status | check | detail |', '|---|---|---|', *linhas, '',
           f'Result: {"passed" if not falhas else f"{falhas} failure(s)"}.']
    (PASTA / f'conferencia_publicacao_{modo}.md').write_text('\n'.join(rel) + '\n',
                                                            encoding='utf-8')
    print('\n'.join(rel))
    sys.exit(1 if falhas else 0)


if __name__ == '__main__':
    main()
