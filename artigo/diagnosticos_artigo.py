"""Diagnósticos do artigo calculados a partir das previsões gravadas pela execução publicada.

Não reajusta modelos nem refaz testes: só lê `resultados/<modo>/preditos/` e as tabelas da
mesma execução. Produz `artigo/saidas/<modo>/diagnosticos_previsoes.csv`, com uma linha por
método, alvo, caso e índice:

- RPSS (%) da previsão com o índice e do controle sem índice sobre a climatologia de referência N
  (RPS de Epstein, normalizado por K − 1 e somado nos meses de teste), para separar a habilidade
  contra a climatologia comum do ganho sobre o controle próprio;
- RPSS (%) sobre o controle, recalculado, que deve coincidir com a tabela da hipótese;
- desvio-padrão, ao longo dos meses de teste, das probabilidades emitidas para Q1 e Q5 (p.p.),
  para descrever o quanto cada previsão se afasta de uma probabilidade constante.

Uso: python artigo/diagnosticos_artigo.py [--modo completo|piloto]
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
CASOS = {'ano hidrológico': 'ano', 'estação chuvosa': 'chuvosa', 'estação seca': 'seca'}
METODOS = {'Ridge': 'Ridge', 'Random Forest': 'RandomForest', 'Rede neural': 'Redeneural'}
INDICES = {'NINO3.4': 'NINO34', 'TSA': 'TSA', 'AMM': 'AMM'}
K = 5


def rps(p, classe):
    """RPS de Epstein por mês, normalizado para [0, 1]."""
    obs = np.zeros_like(p)
    obs[np.arange(len(classe)), classe] = 1.0
    return ((np.cumsum(p, 1) - np.cumsum(obs, 1)) ** 2).sum(1) / (K - 1)


def carregar(pasta, nome):
    with np.load(pasta / f'{nome}.npz') as f:
        p = f['teste'].astype(float)
    info = json.loads((pasta / f'{nome}.json').read_text(encoding='utf-8'))
    return p, info.get('hash_teste')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modo', default='completo')
    modo = ap.parse_args().modo
    raiz = Path(__file__).resolve().parents[1] / 'resultados' / modo
    tab, pre = raiz / 'tabelas', raiz / 'preditos'
    T = lambda nome: next(tab.glob(f'T*_{nome}.csv'))          # pelo nome, não pelo número
    serie = pd.read_csv(T('serie_teste'), parse_dates=['mês'])
    casos = pd.read_csv(T('casos'))
    hip = pd.read_csv(T('hipotese_tres_metodos'))
    linhas = []
    for _, c in casos.iterrows():
        meses = [MESES.index(m.strip()) + 1 for m in c['meses (ordem do ano hidrológico)'].split(',')]
        obs = serie[(serie.alvo == c.alvo) & serie['mês'].dt.month.isin(meses)].sort_values('mês')
        classe = obs['classe'].str[1].astype(int).to_numpy() - 1
        caso = CASOS[c.caso]
        pn, _ = carregar(pre, f'Climatologia_{c.alvo}_{caso}_-_N')
        assert len(pn) == len(classe), (c.alvo, caso, len(pn), len(classe))
        rps_n = rps(pn, classe).sum()
        for metodo, mcod in METODOS.items():
            for indice, icod in INDICES.items():
                pa, _ = carregar(pre, f'{mcod}_{c.alvo}_{caso}_{icod}_aferida')
                pc, _ = carregar(pre, f'{mcod}_{c.alvo}_{caso}_{icod}_controle')
                ra, rc = rps(pa, classe).sum(), rps(pc, classe).sum()
                ref = hip[(hip['método'] == metodo) & (hip.alvo == c.alvo) & (hip.caso == c.caso)
                          & (hip['índice'] == indice)]
                linhas.append({
                    'método': metodo, 'alvo': c.alvo, 'caso': c.caso, 'índice': indice,
                    'meses de teste': len(classe),
                    'RPSS sobre N, com índice (%)': 100 * (1 - ra / rps_n),
                    'RPSS sobre N, controle sem índice (%)': 100 * (1 - rc / rps_n),
                    'RPSS sobre o controle, recalculado (%)': 100 * (1 - ra / rc),
                    'RPSS sobre o controle, tabela da hipótese (%)':
                        float(ref['RPSS sobre o modelo sem índice (%)'].iloc[0]),
                    'dp de P(Q1) com índice (p.p.)': 100 * pa[:, 0].std(),
                    'dp de P(Q5) com índice (p.p.)': 100 * pa[:, 4].std(),
                    'dp de P(Q1) do controle (p.p.)': 100 * pc[:, 0].std(),
                    'dp de P(Q5) do controle (p.p.)': 100 * pc[:, 4].std(),
                    'maior |P − 20 %| com índice (p.p.)': 100 * np.abs(pa - 0.2).max(),
                })
    d = pd.DataFrame(linhas)
    dif = (d['RPSS sobre o controle, recalculado (%)']
           - d['RPSS sobre o controle, tabela da hipótese (%)']).abs().max()
    if not dif < 1e-4:                          # a tabela guarda 6 algarismos significativos
        raise SystemExit(f'RPSS recalculado difere da tabela da hipótese em {dif:.2e} p.p.')
    saida = Path(__file__).resolve().parent / 'saidas' / modo        # fora de resultados/, que
    saida.mkdir(parents=True, exist_ok=True)                           # tem manifesto próprio
    d.to_csv(saida / 'diagnosticos_previsoes.csv', index=False, encoding='utf-8-sig')
    print(f'{len(d)} linhas; maior diferença para a tabela da hipótese: {dif:.1e} p.p.; '
          f'gravado em artigo/saidas/{modo}/diagnosticos_previsoes.csv')


if __name__ == '__main__':
    main()
