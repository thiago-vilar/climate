"""RPSS de cada modelo sobre a climatologia de referência N, com IC95, a partir das previsões
gravadas pela execução publicada.

Não reajusta modelos nem refaz testes: só lê `resultados/<modo>/preditos/`. O IC95 segue o
procedimento do notebook (Seção 9): 2 000 reamostragens conjuntas de blocos circulares de 3 anos
hidrológicos de teste (Politis e Romano, 1992), com o numerador e o denominador recalculados em
cada réplica e semente derivada da raiz 42 e do nome da tarefa (SHA-256). Para comparação, a
tabela traz também o RPSS sobre o controle sem índice, que deve coincidir com a tabela da
hipótese.

Produz `artigo/saidas/<modo>/rpss_climatologia.csv`, com uma linha por método, alvo, caso e
índice. O teste de hipótese (valores p e q) continua sendo o do notebook, sobre o controle.

Uso: python artigo/rpss_climatologia.py [--modo completo|piloto]
"""
import argparse
import hashlib
import itertools
from pathlib import Path

import numpy as np
import pandas as pd

K, R_AVAL, BLOCO_ANOS, SEMENTE_RAIZ = 5, 2000, 3, 42
ALVOS, CASOS = ['NNEB', 'INEB', 'ENEB'], {'ano': 'ano hidrológico', 'chuvosa': 'estação chuvosa',
                                          'seca': 'estação seca'}
METODOS = {'Ridge': 'Ridge', 'Random Forest': 'RandomForest', 'Rede neural': 'Redeneural'}
INDICES = {'NINO3.4': 'NINO34', 'TSA': 'TSA', 'AMM': 'AMM'}


def semente(nome):
    return int(hashlib.sha256(f'{SEMENTE_RAIZ}:{nome}'.encode()).hexdigest()[:8], 16)


def rps(p, classe):
    """RPS de Epstein por mês, normalizado para [0, 1]."""
    obs = np.zeros_like(p)
    obs[np.arange(len(classe)), classe] = 1.0
    return ((np.cumsum(p, 1) - np.cumsum(obs, 1)) ** 2).sum(1) / (K - 1)


def blocos_de_anos(n, nome):
    rng = np.random.default_rng(semente(nome))
    n_blocos = int(np.ceil(n / BLOCO_ANOS))
    inicios = rng.integers(0, n, size=(R_AVAL, n_blocos))
    return ((inicios[:, :, None] + np.arange(BLOCO_ANOS)) % n).reshape(R_AVAL, -1)[:, :n]


def rpss_ic(r_mod, r_ref, anos, nome):
    """100 × (1 − Σ RPS do modelo / Σ RPS da referência), com IC95 por blocos de anos."""
    unicos = np.unique(anos)
    num = np.array([r_mod[anos == a].sum() for a in unicos])
    den = np.array([r_ref[anos == a].sum() for a in unicos])
    idx = blocos_de_anos(len(unicos), nome)
    est = 100 * (1 - num.sum() / den.sum())
    rep = 100 * (1 - num[idx].sum(1) / den[idx].sum(1))
    return est, np.percentile(rep, 2.5), np.percentile(rep, 97.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modo', default='completo')
    modo = ap.parse_args().modo
    raiz = Path(__file__).resolve().parents[1]
    pasta = raiz / 'resultados' / modo / 'preditos'
    saida = Path(__file__).resolve().parent / 'saidas' / modo
    saida.mkdir(parents=True, exist_ok=True)
    carregar = lambda nome: np.load(pasta / f'{nome}.npz')['teste'].astype(float)
    linhas = []
    for (metodo, mcod), alvo, caso, (indice, icod) in itertools.product(
            METODOS.items(), ALVOS, CASOS, INDICES.items()):
        am = np.load(pasta / f'amostras_{alvo}_{caso}.npz')
        cl, anos = am['cl'].astype(int), am['h']
        r_mod = rps(carregar(f'{mcod}_{alvo}_{caso}_{icod}_aferida'), cl)
        r_ctl = rps(carregar(f'{mcod}_{alvo}_{caso}_{icod}_controle'), cl)
        r_n = rps(carregar(f'Climatologia_{alvo}_{caso}_-_N'), cl)
        n_est, n_lo, n_hi = rpss_ic(r_mod, r_n, anos, f'rpss_N:{metodo}:{alvo}:{caso}:{indice}')
        c_est, c_lo, c_hi = rpss_ic(r_ctl, r_n, anos, f'rpss_N:controle:{metodo}:{alvo}:{caso}:{indice}')
        linhas.append({'método': metodo, 'alvo': alvo, 'caso': CASOS[caso], 'índice': indice,
                       'anos de teste': len(np.unique(anos)), 'meses de teste': len(cl),
                       'RPSS sobre N (%)': n_est, 'IC95 inferior': n_lo, 'IC95 superior': n_hi,
                       'IC95 acima de zero': bool(n_lo > 0),
                       'RPSS do controle sobre N (%)': c_est,
                       'RPSS sobre o controle (%)': 100 * (1 - r_mod.sum() / r_ctl.sum())})
    tab = pd.DataFrame(linhas)
    tab.to_csv(saida / 'rpss_climatologia.csv', index=False, encoding='utf-8-sig')
    print(f'{len(tab)} combinações gravadas em', (saida / 'rpss_climatologia.csv').relative_to(raiz))


if __name__ == '__main__':
    main()
