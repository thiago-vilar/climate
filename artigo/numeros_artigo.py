"""Extrai das tabelas finais todos os números citados no texto do artigo.

Lê `resultados/<modo>/tabelas` e `artigo/saidas/<modo>/diagnosticos_previsoes.csv` e grava
`artigo/saidas/<modo>/numeros.json`. O texto do manuscrito usa esses valores pelo nome, de modo
que artigo e execução não divirjam. Nenhum valor é digitado à mão.

Uso: python artigo/numeros_artigo.py [--modo completo|piloto]
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ALVOS, INDICES = ['NNEB', 'INEB', 'ENEB'], ['NINO3.4', 'TSA', 'AMM']
METODOS = ['Ridge', 'Random Forest', 'Rede neural']
CURTO = {'Ridge': 'ridge', 'Random Forest': 'rf', 'Rede neural': 'rede'}


def br(x, casas=1, sinal=False):
    """Número no formato do texto em português: vírgula decimal e sinal de menos tipográfico."""
    if round(x, casas) == 0:
        x = 0.0                                   # evita "−0,0" e "+0,0"
        sinal = False
    s = f'{x:+.{casas}f}' if sinal else f'{x:.{casas}f}'
    return s.replace('-', '−').replace('.', ',')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modo', default='completo')
    modo = ap.parse_args().modo
    raiz = Path(__file__).resolve().parents[1]
    tab = raiz / 'resultados' / modo / 'tabelas'
    saida = Path(__file__).resolve().parent / 'saidas' / modo
    T = lambda nome: pd.read_csv(next(tab.glob(f'T*_{nome}.csv')))   # pelo nome, não pelo número
    diag = pd.read_csv(saida / 'diagnosticos_previsoes.csv')
    N = {}

    # associação (Seção 2)
    a = T('associacao')
    det = a[a['detectado (q < 0,05)']]
    N['assoc_detectadas'] = len(det)
    N['assoc_total'] = len(a)
    for i in INDICES:
        N[f'assoc_{i}'] = int((det['índice'] == i).sum())
    N['assoc_r_min'] = br(det['r(L*)'].abs().min(), 2)
    N['assoc_r_max'] = br(det['r(L*)'].abs().max(), 2)
    for _, r in a.iterrows():
        k = f"{r.alvo}_{r.caso.split()[-1]}_{r['índice']}"
        N[f'r_{k}'] = br(r['r(L*)'], 2)
        N[f'ic_{k}'] = f"{br(r['IC95 inferior'], 2)} a {br(r['IC95 superior'], 2)}"
        N[f'L_{k}'] = int(r['L* (meses)'])
        N[f'q_{k}'] = br(r['q (BH)'], 3)
        N[f'ef_{k}'] = br(r['efeito em L* (p.p. de quantil por dp)'], 1)
        N[f'r2_{k}'] = br(100 * r['r(L*)'] ** 2, 0)
    alem = T('defasagem_alem_da_janela')
    N['picos_alem_janela'] = int(alem['pico além da janela'].sum())
    N['ganho_alem_janela'] = br(alem['ganho de |r| além da janela'].max(), 3)

    # índices: persistência e tendência
    ind = T('indices').set_index('índice')
    for i in INDICES:
        N[f'ac3_{i}'] = br(ind.loc[i, 'autocorrelação 3 meses'], 2)
        N[f'ac6_{i}'] = br(ind.loc[i, 'autocorrelação 6 meses'], 2)
        N[f'tend_{i}'] = br(ind.loc[i, 'variação pela tendência em 1981–2025 (dp)'], 1)
        N[f'tend_ic_{i}'] = (f"{br(ind.loc[i, 'IC95 inferior'], 1)} a "
                             f"{br(ind.loc[i, 'IC95 superior'], 1)}")

    # teste de campo nos mapas da estação chuvosa, na defasagem atribuída
    campo, lstar = T('teste_campo'), a.set_index(['alvo', 'caso', 'índice'])['L* (meses)']
    ch = campo[campo.caso == 'estação chuvosa']
    ch = ch[[lstar.loc[(r.alvo, r.caso, r['índice'])] == r.L for _, r in ch.iterrows()]]
    N['campo_chuvosa_detectados'] = int(ch['campo detectado'].sum())
    N['campo_chuvosa_lista'] = ', '.join(f"{r['índice']} no {r.alvo}"
                                         for _, r in ch[ch['campo detectado']].iterrows())
    hom = T('sanidade_homogeneidade').set_index('alvo')
    for al in ALVOS:
        N[f'suspeito_{al}'] = br(hom.loc[al, 'suspeito, 3–4 testes, marcado (% da área)'], 1)

    # hipótese (Seções 5 a 9)
    h = T('hipotese_tres_metodos')
    N['hipoteses'] = len(h)
    N['sustentadas'] = int(h['hipótese sustentada'].sum())
    N['piso_p'] = br(1 / 131, 4)
    N['ic_acima_zero'] = int((h['IC95 inferior'] > 0).sum())
    for m in METODOS:
        s = h[h['método'] == m]
        c = CURTO[m]
        N[f'qmin_{c}'] = br(s.q.min(), 3)
        N[f'no_piso_{c}'] = int((s['p (nulo)'] <= 1 / 131 + 1e-6).sum())     # tabela com 6 algarismos
        N[f'mediana_{c}'] = br(s['RPSS sobre o modelo sem índice (%)'].median(), 2, True)
        N[f'icsup_max_{c}'] = br(s['IC95 superior'].max(), 1)
        N[f'icsup_mediana_{c}'] = br(s['IC95 superior'].median(), 1)
        N[f'positivos_{c}'] = int((s['RPSS sobre o modelo sem índice (%)'] > 0).sum())
        for _, r in s.iterrows():
            k = f"{c}_{r.alvo}_{r.caso.split()[-1]}_{r['índice']}"
            N[f'rpss_{k}'] = br(r['RPSS sobre o modelo sem índice (%)'], 1, True)
            N[f'rpssic_{k}'] = f"{br(r['IC95 inferior'], 1)} a {br(r['IC95 superior'], 1)}"
            N[f'q_{k}'] = br(r.q, 3)
    v = T('validade_testes').set_index('método')
    for m in METODOS:
        N[f'largura_{CURTO[m]}'] = br(v.loc[m, 'largura mediana do IC95 do RPSS (p.p.)'], 1)
        N[f'troca_sinal_{CURTO[m]}'] = br(v.loc[m, 'troca de sinal com p < 0,05 sob o nulo (%)'], 1)
    b = T('sensibilidade_blocos')
    N['blocos_largura'] = f"{br(b['largura mediana do IC95 (p.p.)'].min(), 1)} a {br(b['largura mediana do IC95 (p.p.)'].max(), 1)}"

    # diagnósticos das previsões
    for m in METODOS:
        d, c = diag[diag['método'] == m], CURTO[m]
        sd = d[['dp de P(Q1) com índice (p.p.)', 'dp de P(Q5) com índice (p.p.)']].mean(axis=1)
        N[f'dp_mediana_{c}'] = br(sd.median(), 1)
        N[f'dp_max_{c}'] = br(sd.max(), 1)
        N[f'desvio_max_{c}'] = br(d['maior |P − 20 %| com índice (p.p.)'].max(), 1)
        N[f'rpssN_min_{c}'] = br(d['RPSS sobre N, com índice (%)'].min(), 1, True)
        N[f'rpssN_max_{c}'] = br(d['RPSS sobre N, com índice (%)'].max(), 1, True)
        N[f'rpssN_ctrl_absmax_{c}'] = br(d['RPSS sobre N, controle sem índice (%)'].abs().max(), 1)
    N['dp_controle_max'] = br(diag[['dp de P(Q1) do controle (p.p.)',
                                    'dp de P(Q5) do controle (p.p.)']].to_numpy().max(), 1)
    N['desvio_max_geral'] = br(diag['maior |P − 20 %| com índice (p.p.)'].max(), 1)

    # calibração e sinal plantado
    cal = T('calibracao_hiperparametros')
    for m in METODOS:
        s, c = cal[cal['método'] == m], CURTO[m]
        N[f'val_melhor_{c}'] = br(s['RPSS (%)'].max(), 2, True)
        N[f'val_escolhida_{c}'] = br(s.loc[s.escolhida, 'RPSS (%)'].iloc[0], 2, True)
        N[f'val_pior_{c}'] = br(s['RPSS (%)'].min(), 1, True)
        N[f'grade_{c}'] = len(s)
    sp = T('sinal_plantado')
    for m in METODOS:
        s, c = sp[sp['método'] == m].set_index('correlação plantada'), CURTO[m]
        N[f'plant0_{c}'] = br(s.loc[0.0, 'RPSS (%)'], 1, True)
        N[f'plant3_{c}'] = br(s.loc[0.3, 'RPSS (%)'], 1, True)
        N[f'plant3ep_{c}'] = br(s.loc[0.3, 'erro-padrão'], 1)
        N[f'plant3real_{c}'] = br(s.loc[0.3, 'RPSS com a configuração dos dados reais (%)'], 1, True)
    N['plant_L_recuperada'] = br(sp.loc[sp['correlação plantada'] == 0.3,
                                        'defasagem plantada recuperada (%)'].iloc[0], 0)

    # Brier, N-índice e comparação entre métodos
    br_ = T('confiabilidade')
    N['brier_dif_max'] = br((br_['Brier'] - br_['Brier da climatologia (20 %)']).abs().max(), 4)
    N['resol_min'] = br(br_['resolução agrupada (maior é melhor)'].min(), 5)
    N['resol_max'] = br(br_['resolução agrupada (maior é melhor)'].max(), 4)
    a0 = T('comparacao_A0')
    N['nind_q_min'] = br(a0['q (BH)'].min(), 2)
    N['nind_sig'] = int((a0['q (BH)'] < 0.05).sum())
    for _, r in a0.iterrows():
        k = f"{r.alvo}_{r.caso.split()[-1]}_{r['comparação'].split()[0][2:]}"
        N[f'nind_{k}'] = br(r['diferença de RPSS (p.p.)'], 1, True)
        N[f'nindic_{k}'] = f"{br(r['IC95 inferior'], 1)} a {br(r['IC95 superior'], 1)}"
    e = T('comparacao_E')
    col = 'diferença de habilidade normalizada por N (p.p.)'
    N['E_sig'] = int((e['q (BH)'] < 0.05).sum())
    N['E_n'] = len(e)
    N['E_min'], N['E_max'] = br(e[col].min(), 1, True), br(e[col].max(), 1, True)
    N['E_mediana'] = br(e[col].median(), 1, True)

    # verificação do teste por deslocamento (Ridge, alvo inteiro)
    vd = T('validade_deslocamento')
    lib = vd[vd.leitura == 'acima de 5 %']
    N['liberais'] = len(lib)
    N['liberais_TSA'] = int((lib['índice'] == 'TSA').sum())
    N['liberais_AMM'] = int((lib['índice'] == 'AMM').sum())
    N['liberal_taxa_min'] = br(lib['taxa de rejeição (%)'].min(), 1)
    N['liberal_taxa_max'] = br(lib['taxa de rejeição (%)'].max(), 1)
    N['substitutos'] = int(vd['realizações'].iloc[0])

    # cortes temporais (tabela de escolhas da calibração) e r(L*) sem tendência (descritivo)
    esc = T('calibracao_escolhas')
    for _, r in esc[esc['item'].str.startswith('cortes (')].iterrows():
        alvo, papel = r['item'][len('cortes ('):].split('): ')
        N[f"corte_{alvo}_{papel.replace(' ', '_')}"] = r['escolha']
    if 'r(L*) sem tendência linear (descritivo)' in a.columns:
        for _, r in a.iterrows():
            k = f"{r.alvo}_{r.caso.split()[-1]}_{r['índice']}"
            N[f'rst_{k}'] = br(r['r(L*) sem tendência linear (descritivo)'], 2)

    # ---- acréscimos da reescrita de 31/10/2026 ----
    MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
    NOME = dict(zip(MESES, ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho',
                            'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']))
    cal = T('calendario')
    lim = T('limites_quintis')
    alv = T('alvos').set_index('alvo')
    for al in ALVOS:
        c = cal[cal.alvo == al].set_index('mês')
        N[f'pico_{al}'] = NOME[c['normal 1981–2010 (mm)'].idxmax()]
        N[f'pico_mm_{al}'] = br(c['normal 1981–2010 (mm)'].max(), 0)
        seco = c['normal 1981–2010 (mm)'].idxmin()
        l = lim[(lim.alvo == al) & (lim['mês'] == seco)].iloc[0]
        N[f'mes_seco_{al}'] = NOME[seco]
        N[f'q1lim_seco_{al}'] = br(l['limite superior de Q1 (mm)'], 1)
        N[f'q4lim_seco_{al}'] = br(l['limite superior de Q4 (mm)'], 1)
        N[f'media_seco_{al}'] = br(l['média de referência 1981–2010 (mm)'], 1)
        pico = c['normal 1981–2010 (mm)'].idxmax()
        l = lim[(lim.alvo == al) & (lim['mês'] == pico)].iloc[0]
        N[f'q1lim_pico_{al}'] = br(l['limite superior de Q1 (mm)'], 0)
        N[f'q4lim_pico_{al}'] = br(l['limite superior de Q4 (mm)'], 0)
        N[f'municipios_{al}'] = int(alv.loc[al, 'municípios'])
        N[f'pixels_{al}'] = f"{int(alv.loc[al, 'pixels de 0,05°']):,}".replace(',', ' ')
        N[f'area_{al}'] = f"{int(alv.loc[al, 'área coberta (km²)']):,}".replace(',', ' ')
    am = T('amostras')
    for _, r in am.iterrows():
        N[f"meses_{r.papel}_{r.alvo}_{r.caso.split()[-1]}"] = int(r.meses)
    ct = T('classes_no_teste')
    N['u_teste_min'] = br(ct['quantil médio'].min(), 2)
    N['u_teste_max'] = br(ct['quantil médio'].max(), 2)
    cls = ct[[c for c in ct.columns if c.startswith('Q')]]
    N['classe_teste_min'] = br(cls.to_numpy().min(), 0)
    N['classe_teste_max'] = br(cls.to_numpy().max(), 0)
    for m in METODOS:
        s, c = h[h['método'] == m], CURTO[m]
        N[f'p05_{c}'] = int((s['p (nulo)'] < 0.05).sum())
        N[f'rpss_min_{c}'] = br(s['RPSS sobre o modelo sem índice (%)'].min(), 1, True)
        N[f'rpss_max_{c}'] = br(s['RPSS sobre o modelo sem índice (%)'].max(), 1, True)
        N[f'perda4_{c}'] = int((s['RPSS sobre o modelo sem índice (%)'] < -4).sum())
        N[f'icpos_{c}'] = int((s['IC95 inferior'] > 0).sum())
    for _, r in esc.iterrows():
        if r['item'].startswith('hiperparâmetros: '):
            N[f"cfg_{CURTO[r['item'][len('hiperparâmetros: '):]]}"] = json.loads(r['escolha'])
    e = T('comparacao_E')
    sig = e[e['q (BH)'] < 0.05]
    for _, r in e.iterrows():
        par = r['comparação'].replace('Random Forest', 'rf').replace('Rede neural', 'rede').replace('Ridge', 'ridge').replace(' − ', '_')
        k = f"{par}_{r.alvo}_{r.caso.split()[-1]}_{r['índice']}"
        N[f'E_{k}'] = br(r[col], 1, True)
        N[f'Eq_{k}'] = br(r['q (BH)'], 3)
    N['E_sig_lista'] = '; '.join(
        f"{r['comparação']}, {r.alvo}, {r.caso}, {r['índice']} ({br(r[col], 1, True)} p.p.; q = {br(r['q (BH)'], 3)})"
        for _, r in sig.iterrows())
    a0 = T('comparacao_A0')
    N['nind_p_piso'] = int((a0['p (nulo)'] <= 1 / 131 + 1e-6).sum())
    det = a[a['detectado (q < 0,05)']]
    if 'r(L*) sem tendência linear (descritivo)' in a.columns:
        d = (det['r(L*) sem tendência linear (descritivo)'].abs() - det['r(L*)'].abs())
        N['rst_dif_min'] = br(d.min(), 2, True)
        N['rst_dif_max'] = br(d.max(), 2, True)
    pix = T('pixel_habilidade')
    col_g = 'área com ganho significativo (%)'
    N['pix_ganho_max'] = br(pix[col_g].max(), 1)
    top = pix.loc[pix[col_g].idxmax()]
    N['pix_ganho_max_onde'] = f"{top['método']}, {top.alvo}, {top.caso}, {top['índice']}"
    N['pix_ganho_max_perda'] = br(top['área com perda significativa (%)'], 1)
    N['pix_ganho_max_rpss'] = br(top['RPSS agregado dos pixels sobre o controle sem índice (%)'], 2, True)
    N['pix_rpss_pos'] = int((pix['RPSS agregado dos pixels sobre o controle sem índice (%)'] > 0).sum())
    N['pix_ic_pos'] = int((pix['IC95 inferior'] > 0).sum())
    b = T('sensibilidade_blocos').set_index(['método', 'bloco (anos)'])
    for m in METODOS:
        N[f'bloco_larg_{CURTO[m]}'] = (f"{br(b.loc[(m, 2), 'largura mediana do IC95 (p.p.)'], 1)}, "
                                       f"{br(b.loc[(m, 3), 'largura mediana do IC95 (p.p.)'], 1)} e "
                                       f"{br(b.loc[(m, 4), 'largura mediana do IC95 (p.p.)'], 1)}")
    hom = T('sanidade_homogeneidade').set_index('alvo')
    for al in ALVOS:
        N[f'duvidoso_{al}'] = br(hom.loc[al, 'duvidoso, 2 testes (% da área)'], 1)

    # índice predominante por pixel (Figura 4; exploratório, sem teste)
    for _, r in T('indice_predominante').iterrows():
        k = f"{r.alvo}_{r.caso.split()[-1]}_{r['índice']}"
        N[f'pred_area_{k}'] = br(r['área em que predomina (%)'], 0)
        N[f'pred_r_{k}'] = br(r['|r| médio onde predomina'], 2)
        N[f'pred_L_{k}'] = int(r['defasagem mais frequente onde predomina'])
        N[f'pred_sinal_{k}'] = br(r['onde predomina, com o sinal esperado (%)'], 0)
    pr = T('indice_predominante')
    pr = pr[pr['área em que predomina (%)'] >= 5]           # faixa de |r| sem índices quase ausentes
    for al in ALVOS:
        g = pr[pr.alvo == al]['|r| médio onde predomina']
        N[f'pred_rmin_{al}'], N[f'pred_rmax_{al}'] = br(g.min(), 2), br(g.max(), 2)

    saida.mkdir(parents=True, exist_ok=True)
    (saida / 'numeros.json').write_text(json.dumps(N, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(N)} valores gravados em artigo/saidas/{modo}/numeros.json')


if __name__ == '__main__':
    main()
