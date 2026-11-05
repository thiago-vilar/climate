"""Tables of the article (Table 3) and of the Supporting Information (Tables S1 to S7), from the outputs
of the published run.

Only reads `resultados/<modo>/tabelas` and `artigo/saidas/<modo>/diagnosticos_previsoes.csv`. Writes to
`artigo/saidas/<modo>/` the files `tab2.json` and `supl.json`, with the text of each cell already
formatted (decimal comma, typographic minus sign). No value is typed by hand.

Usage: python artigo/tabelas_artigo.py [--modo completo|piloto]
"""
import argparse
import json
from pathlib import Path

import pandas as pd

ALVOS, INDICES = ['NNEB', 'INEB', 'ENEB'], ['NINO3.4', 'TSA', 'AMM']
CASOS = ['ano hidrológico', 'estação chuvosa', 'estação seca']
CASO = {'ano hidrológico': 'ano', 'estação chuvosa': 'chuvosa', 'estação seca': 'seca',
        'ano': 'ano', 'chuvosa': 'chuvosa', 'seca': 'seca'}
METODOS = ['Ridge', 'Random Forest', 'Rede neural']
MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']


def br(x, casas=1, sinal=False):
    if pd.isna(x):
        return '—'
    if round(x, casas) == 0:
        x, sinal = 0.0, False
    s = f'{x:+.{casas}f}' if sinal else f'{x:.{casas}f}'
    return s.replace('-', '−').replace('.', ',')


def ic(lo, hi, casas=1):
    return f'{br(lo, casas)} a {br(hi, casas)}'


def cfg(txt):
    d = json.loads(txt)
    nomes = {'penalidade_por_mes': 'penalidade', 'profundidade': 'profundidade', 'folha': 'folha',
             'oculta': 'neurônios', 'decaimento': 'decaimento', 'passagens': 'passagens',
             'ativacao': 'ativação'}
    partes = []
    for k, v in d.items():
        if k in ('arvores', 'taxa'):
            continue
        if v is None:
            v = 'livre'
        elif isinstance(v, float):
            v = f'{v:g}'.replace('.', ',')
        partes.append(f'{nomes.get(k, k)} {v}')
    return '; '.join(partes)


def ordenar(df, chaves):
    ordem = {'alvo': ALVOS, 'índice': INDICES, 'método': METODOS,
             'caso': CASOS if df['caso'].iloc[0] in CASOS else ['ano', 'chuvosa', 'seca']}
    for k in chaves:
        df = df.assign(**{f'_{k}': df[k].map({v: i for i, v in enumerate(ordem[k])})})
    return df.sort_values([f'_{k}' for k in chaves])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modo', default='completo')
    modo = ap.parse_args().modo
    raiz = Path(__file__).resolve().parents[1]
    tab = raiz / 'resultados' / modo / 'tabelas'
    saida = Path(__file__).resolve().parent / 'saidas' / modo
    T = lambda nome: pd.read_csv(next(tab.glob(f'T*_{nome}.csv')))
    diag = pd.read_csv(saida / 'diagnosticos_previsoes.csv')

    # Table 3: lagged association (file tab2.json)
    a = ordenar(T('associacao'), ['alvo', 'caso', 'índice'])
    tab2 = [[r.alvo, CASO[r.caso], r['índice'], str(int(r['L* (meses)'])), br(r['r(L*)'], 2),
             ic(r['IC95 inferior'], r['IC95 superior'], 2),
             br(r['r(L*) sem tendência linear (descritivo)'], 2), br(r['q (BH)'], 3),
             'sim' if r['detectado (q < 0,05)'] else 'não'] for _, r in a.iterrows()]

    S = {}
    lim = T('limites_quintis')
    lim = lim.assign(_a=lim.alvo.map({v: i for i, v in enumerate(ALVOS)}),
                     _m=lim['mês'].map({v: i for i, v in enumerate(MESES)})).sort_values(['_a', '_m'])
    S['S1'] = {'cab': ['Alvo', 'Mês', 'Estação', 'Q1 ≤', 'Q2 ≤', 'Q3 ≤', 'Q4 ≤', 'Média (mm)'],
               'lin': [[r.alvo, r['mês'], r['estação'], br(r['limite superior de Q1 (mm)']),
                        br(r['limite superior de Q2 (mm)']), br(r['limite superior de Q3 (mm)']),
                        br(r['limite superior de Q4 (mm)']),
                        br(r['média de referência 1981–2010 (mm)'])] for _, r in lim.iterrows()]}

    h = ordenar(T('hipotese_tres_metodos'), ['método', 'alvo', 'caso', 'índice'])
    S['S2'] = {'cab': ['Método', 'Alvo', 'Caso', 'Índice', 'L*', 'RPSS (%)', 'IC95', 'p', 'q',
                       'Tendência (Ridge)'],
               'lin': [[r['método'], r.alvo, CASO[r.caso], r['índice'], str(int(r['L* (meses)'])),
                        br(r['RPSS sobre o modelo sem índice (%)'], 2, True),
                        ic(r['IC95 inferior'], r['IC95 superior'], 2), br(r['p (nulo)'], 4),
                        br(r.q, 3), r['teste por deslocamento (Ridge)']] for _, r in h.iterrows()]}

    e = T('calibracao_entrada')
    S['S3a'] = {'cab': ['Forma de entrada', 'Interação com o mês', 'Filtro', 'RPSS (%)',
                        'Erro-padrão', 'Escolhida'],
                'lin': [[r.entrada, 'sim' if r.sazonal else 'não',
                         'sem tendência' if r.filtro == 'sem_tendencia' else 'bruto',
                         br(r['RPSS (%)'], 2, True), br(r['erro-padrão'], 2),
                         'sim' if r.escolhida else ''] for _, r in e.iterrows()]}
    c = T('calibracao_hiperparametros')
    S['S3b'] = {'cab': ['Método', 'Configuração', 'RPSS (%)', 'Erro-padrão', 'Escolhida'],
                'lin': [[r['método'], cfg(r['configuração']), br(r['RPSS (%)'], 2, True),
                         br(r['erro-padrão'], 2), 'sim' if r.escolhida else '']
                        for _, r in c.iterrows()]}
    sp = T('sinal_plantado')
    S['S3c'] = {'cab': ['ρ', 'Método', 'Configuração escolhida', 'RPSS (%)', 'Erro-padrão',
                        'Melhor da grade (%)', 'Configuração dos dados reais (%)',
                        'L* recuperada (%)'],
                'lin': [[br(r['correlação plantada'], 1), r['método'],
                         cfg(r['configuração escolhida']), br(r['RPSS (%)'], 2, True),
                         br(r['erro-padrão'], 2), br(r['melhor RPSS da grade (%)'], 2, True),
                         br(r['RPSS com a configuração dos dados reais (%)'], 2, True),
                         br(r['defasagem plantada recuperada (%)'], 0)] for _, r in sp.iterrows()]}

    vd = ordenar(T('validade_deslocamento'), ['alvo', 'caso', 'índice'])
    S['S4a'] = {'cab': ['Alvo', 'Caso', 'Índice', 'Realizações', 'p < 0,05', 'Taxa (%)',
                        'IC95 (%)', 'Leitura'],
                'lin': [[r.alvo, r.caso, r['índice'], str(int(r['realizações'])),
                         str(int(r['p < 0,05'])), br(r['taxa de rejeição (%)'], 1),
                         ic(r['IC95 inferior (%)'], r['IC95 superior (%)'], 1), r.leitura]
                        for _, r in vd.iterrows()]}
    b = T('sensibilidade_blocos')
    S['S4b'] = {'cab': ['Método', 'Bloco (anos)', 'Largura mediana do IC95 (p.p.)'],
                'lin': [[r['método'], str(int(r['bloco (anos)'])),
                         br(r['largura mediana do IC95 (p.p.)'], 2)] for _, r in b.iterrows()]}

    a0 = ordenar(T('comparacao_A0'), ['alvo', 'caso'])
    S['S5a'] = {'cab': ['Alvo', 'Caso', 'Comparação', 'Diferença de RPSS (p.p.)', 'IC95',
                        'p (nulo)', 'q'],
                'lin': [[r.alvo, CASO[r.caso], r['comparação'],
                         br(r['diferença de RPSS (p.p.)'], 2, True),
                         ic(r['IC95 inferior'], r['IC95 superior'], 2), br(r['p (nulo)'], 4),
                         br(r['q (BH)'], 3)] for _, r in a0.iterrows()]}
    col = 'diferença de habilidade normalizada por N (p.p.)'
    ec = ordenar(T('comparacao_E'), ['alvo', 'caso', 'índice'])
    S['S5b'] = {'cab': ['Alvo', 'Caso', 'Índice', 'Comparação', 'Diferença (p.p.)', 'IC95', 'q'],
                'lin': [[r.alvo, CASO[r.caso], r['índice'], r['comparação'], br(r[col], 2, True),
                         ic(r['IC95 inferior'], r['IC95 superior'], 2), br(r['q (BH)'], 3)]
                        for _, r in ec.iterrows()]}

    d = ordenar(diag, ['método', 'alvo', 'caso', 'índice'])
    S['S6'] = {'cab': ['Método', 'Alvo', 'Caso', 'Índice', 'RPSS sobre N, com índice (%)',
                       'RPSS sobre N, controle (%)', 'dp P(Q1) (p.p.)', 'dp P(Q5) (p.p.)',
                       'Maior |P − 20 %| (p.p.)'],
               'lin': [[r['método'], r.alvo, CASO[r.caso], r['índice'],
                        br(r['RPSS sobre N, com índice (%)'], 2, True),
                        br(r['RPSS sobre N, controle sem índice (%)'], 2, True),
                        br(r['dp de P(Q1) com índice (p.p.)'], 1),
                        br(r['dp de P(Q5) com índice (p.p.)'], 1),
                        br(r['maior |P − 20 %| com índice (p.p.)'], 1)] for _, r in d.iterrows()]}

    p = ordenar(T('pixel_habilidade'), ['método', 'alvo', 'caso', 'índice'])
    S['S7'] = {'cab': ['Método', 'Alvo', 'Caso', 'Índice', 'RPSS agregado dos pixels (%)', 'IC95',
                       'Área com ganho sig. (%)', 'Área com perda sig. (%)', 'RPSS regional (%)'],
               'lin': [[r['método'], r.alvo, CASO[r.caso], r['índice'],
                        br(r['RPSS agregado dos pixels sobre o controle sem índice (%)'], 2, True),
                        ic(r['IC95 inferior'], r['IC95 superior'], 2),
                        br(r['área com ganho significativo (%)'], 1),
                        br(r['área com perda significativa (%)'], 1),
                        br(r['RPSS do modelo regional sobre o seu controle sem índice (%)'], 2, True)]
                       for _, r in p.iterrows()]}
    v = T('pixel_validacao')
    S['nulo_pixel'] = {
        'media': br(v['área com ganho significativo sob o nulo (%) (média)'].mean(), 1),
        'max': br(v['área com ganho significativo sob o nulo (%) (máximo)'].max(), 1),
        'pos': br(v['área com RPSS > 0 sob o nulo (%) (média)'].mean(), 0)}

    saida.mkdir(parents=True, exist_ok=True)
    (saida / 'tab2.json').write_text(json.dumps(tab2, ensure_ascii=False), encoding='utf-8')
    (saida / 'supl.json').write_text(json.dumps(S, ensure_ascii=False), encoding='utf-8')
    print(f'tabelas gravadas em artigo/saidas/{modo}: tab2.json ({len(tab2)} linhas), supl.json')


if __name__ == '__main__':
    main()
