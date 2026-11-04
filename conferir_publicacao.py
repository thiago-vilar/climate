r"""Conferência para a release do climate. Lê só esta pasta e não altera nada nela.

Uso (PowerShell, dentro da pasta do repositório, depois da execução completa):
    .\.venv\Scripts\python.exe conferir_publicacao.py            # resultados/completo
    .\.venv\Scripts\python.exe conferir_publicacao.py --modo piloto

Confere:
 1. o notebook executado rodou do início ao fim, sem erro, em ordem;
 2. o código do notebook executado é o mesmo do notebook fonte e o da assinatura dos resultados;
 3. cada arquivo do manifesto SHA-256 existe com o mesmo tamanho e hash, e não há arquivo
    fora do manifesto (nem .invalido ou .tmp de retomada);
 4. o RPSS de cada modelo sobre o seu controle, recalculado das previsões gravadas, é igual ao da
    tabela da hipótese;
 5. o veredito segue a regra declarada (RPSS > 0, q < 0,05 e verificação do teste sem rejeição
    acima de 5 % no cenário com tendência);
 6. cada figura do inventário existe em PNG e PDF;
 7. as saídas não contêm caminhos absolutos da máquina;
 8. os cortes temporais: a calibração compartilhada termina antes da validação, a validação e o
    treino final terminam até dez/2010, e o teste de todos os alvos começa depois disso;
 9. nenhum modelo com índice é idêntico ao seu controle sem índice (um modelo que não usa o
    índice daria RPSS = 0 exato e não testaria a hipótese).
Escreve o relatório em conferencia_publicacao_<modo>.md e termina com código 1 se algo falhar.
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
    if modo == 'completo' and not executado.exists():   # clone do repositório: só climate.ipynb
        executado = PASTA / 'climate.ipynb'
    linhas, falhas = [], 0

    def registrar(ok, item, detalhe=''):
        nonlocal falhas
        falhas += not ok
        linhas.append(f"| {'ok' if ok else 'FALHA'} | {item} | {detalhe} |")

    # 1. execução completa, sem erro, em ordem
    nb = json.loads(executado.read_text(encoding='utf-8'))
    cod = [c for c in nb['cells'] if c['cell_type'] == 'code']
    erros = sum(o.get('output_type') == 'error' for c in cod for o in c.get('outputs', []))
    ordem = [c.get('execution_count') for c in cod]
    registrar(erros == 0 and ordem == list(range(1, len(cod) + 1)),
              'notebook executado do início ao fim, sem erro',
              f'{len(cod)} células de código; {erros} erros')

    # 2. fonte = executado = assinatura
    fonte = json.loads((PASTA / 'climate.ipynb').read_text(encoding='utf-8'))
    assin = json.loads((saida / 'registros' / 'assinatura.json').read_text(encoding='utf-8'))
    c_f, c_e = codigo(fonte), codigo(nb)
    registrar(c_f == c_e == assin['codigo'], 'código do fonte, do executado e da assinatura',
              f'{c_f[:16]}')

    # 3. manifesto
    man = json.loads((saida / 'registros' / 'manifesto.json').read_text(encoding='utf-8'))
    listados = man['arquivos']
    ruins = [p for p, v in listados.items() if not (PASTA / p).exists()
             or (PASTA / p).stat().st_size != v['bytes'] or sha256(PASTA / p) != v['sha256']]
    presentes = {p.relative_to(PASTA).as_posix() for p in saida.rglob('*') if p.is_file()
                 and p.name not in VOLATEIS               # a tabela do manifesto é gravada
                 and not p.name.endswith('_manifesto_saidas.csv')}   # depois dele
    extras = sorted(presentes - set(listados))
    registrar(not ruins and not extras, 'manifesto SHA-256 confere com os arquivos',
              f'{len(listados)} arquivos; {len(ruins)} divergentes; {len(extras)} fora do '
              'manifesto' + (f' (ex.: {extras[0]})' if extras else ''))

    # 4. previsões gravadas -> tabela da hipótese
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
    registrar(max(difs) < 1e-6, 'RPSS recalculado das previsões = tabela da hipótese',
              f'{len(difs)} combinações; maior diferença {max(difs):.1e} p.p.')

    # 5. veredito
    lib = hip['teste por deslocamento (Ridge)'] == 'acima de 5 %'
    ganho = (hip['RPSS sobre o modelo sem índice (%)'] > 0) & (hip['q'] < 0.05)
    esperado = np.where(ganho & ~lib, 'sustentada',
                        np.where(ganho, 'inconclusiva (sensível à tendência)', 'não detectada'))
    registrar(bool((hip['veredito'] == esperado).all()), 'veredito segue a regra declarada',
              ', '.join(f'{k}: {v}' for k, v in hip['veredito'].value_counts().items()))

    # 6. figuras
    inv = pd.read_csv(saida / 'tabelas' / sorted(p.name for p in (saida / 'tabelas').glob(
        'T*_inventario_figuras.csv'))[0])
    faltam = [a for a in inv['arquivo'] for e in ('png', 'pdf')
              if not (saida / 'figuras' / f'{a}.{e}').exists()]
    registrar(not faltam, 'figuras do inventário em PNG e PDF',
              f'{len(inv)} figuras; {len(faltam)} arquivos ausentes')

    # 7. caminhos absolutos
    textos = [json.dumps([c.get('outputs', []) for c in nb['cells']], ensure_ascii=False)]
    for p in saida.rglob('*'):
        if p.is_file() and p.suffix in ('.csv', '.json', '.md', '.log', '.txt'):
            textos.append(p.read_text(encoding='utf-8', errors='replace'))
    achados = sum(len(CAMINHO_ABS.findall(t)) for t in textos)
    registrar(achados == 0, 'saídas sem caminhos absolutos da máquina', f'{achados} ocorrências')

    # 8. cortes temporais (tabela de escolhas da calibração)
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
        det = (f'calibração até {fim_cal[1]:02d}/{fim_cal[0]}; validação {ini_val[1]:02d}/'
               f'{ini_val[0]}–{fim_val[1]:02d}/{fim_val[0]}; treino final até {fim_tr[1]:02d}/'
               f'{fim_tr[0]}; teste desde {teste0[1]:02d}/{teste0[0]} (3 alvos)')
    else:
        det = 'cortes ausentes na tabela de escolhas da calibração'
    registrar(ok, 'cortes temporais comuns aos três alvos', det)

    # 9. modelos que não usam o índice
    registrar(not iguais, 'todo modelo com índice difere do seu controle',
              f'{len(hip)} combinações; idênticas ao controle: '
              + ('; '.join(iguais) if iguais else 'nenhuma'))

    rel = [f'# Conferência para publicação — modo {modo}', '',
           f"- Assinatura: `{assin['assinatura'][:16]}`; código `{c_f[:16]}`; dados "
           f"`{str(assin.get('dados'))[:16]}`",
           f"- Ambiente: Python {assin['versoes'].get('python')}, PyTorch "
           f"{assin['versoes'].get('torch')}, {assin['versoes'].get('sistema')}, threads "
           f"{assin['versoes'].get('threads')}", '',
           '| situação | conferência | detalhe |', '|---|---|---|', *linhas, '',
           f'Resultado: {"aprovado" if not falhas else f"{falhas} falha(s)"}.']
    (PASTA / f'conferencia_publicacao_{modo}.md').write_text('\n'.join(rel) + '\n',
                                                            encoding='utf-8')
    print('\n'.join(rel))
    sys.exit(1 if falhas else 0)


if __name__ == '__main__':
    main()
