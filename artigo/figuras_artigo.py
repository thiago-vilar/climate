"""Main figures of the article and graphical abstract, from the outputs of the published run.

Does not recompute the study. Reads `resultados/<modo>/tabelas`, `resultados/<modo>/figuras` (map of the
targets and seasonal maps, drawn by the notebook) and `artigo/saidas/<modo>/diagnosticos_previsoes.csv`
(from `diagnosticos_artigo.py`). Writes to `artigo/saidas/<modo>/figuras/` each figure in PNG (300 dpi)
and PDF and, alongside, the source data of each panel in CSV. Figure 4 reuses the notebook maps
(F13) and only adds the |r| scale, drawn with the same colour rule.

Usage: python artigo/figuras_artigo.py [--modo completo|piloto]
"""
import argparse
import json
import shutil
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

mm = 1 / 25.4
mpl.rcParams.update({
    # sans-serif, like the notebook figures used in the article (Figures 1a, 3 and 4)
    'font.family': 'sans-serif', 'font.sans-serif': ['DejaVu Sans', 'Arial', 'Liberation Sans'],
    'font.size': 8, 'axes.titlesize': 8, 'axes.labelsize': 8, 'xtick.labelsize': 7.5,
    'ytick.labelsize': 7.5, 'legend.fontsize': 7.5, 'axes.spines.top': False,
    'axes.spines.right': False, 'axes.linewidth': 0.6, 'xtick.major.width': 0.6,
    'ytick.major.width': 0.6, 'savefig.bbox': 'tight', 'savefig.pad_inches': 0.02,
    'pdf.fonttype': 42, 'mathtext.fontset': 'dejavusans'})

# Paul Tol palette (colour-blind safe, no red with green), the same as the notebook
COR = {'NINO3.4': '#BB5566', 'TSA': '#004488', 'AMM': '#DDAA33',
       'Ridge': '#004488', 'Random Forest': '#DDAA33', 'Rede neural': '#BB5566',
       'NNEB': '#44AA99', 'INEB': '#DDCC77', 'ENEB': '#004488'}
MARCA = {'NINO3.4': 'o', 'TSA': 's', 'AMM': '^', 'Ridge': 'o', 'Random Forest': 's',
         'Rede neural': 'D'}
LINHA = {'NINO3.4': '-', 'TSA': '--', 'AMM': '-.'}
EN = {'Ridge': 'Ridge', 'Random Forest': 'Random forest', 'Rede neural': 'Neural network',
      'ano hidrológico': 'Hydrological year', 'estação chuvosa': 'Wet season',
      'estação seca': 'Dry season'}
ALVOS, INDICES = ['NNEB', 'INEB', 'ENEB'], ['NINO3.4', 'TSA', 'AMM']
CASOS = ['ano hidrológico', 'estação chuvosa', 'estação seca']
METODOS = ['Ridge', 'Random Forest', 'Rede neural']
MESES_EN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
MESES_PT = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']


def letra(ax, s, x=-0.02, y=1.02):
    ax.text(x, y, f'({s})', transform=ax.transAxes, fontweight='bold', ha='right', va='bottom')


def salvar(fig, saida, nome, dados=None):
    for ext in ('png', 'pdf'):
        fig.savefig(saida / f'{nome}.{ext}', dpi=300)
    plt.close(fig)
    if dados is not None:
        dados.to_csv(saida / f'{nome}_dados.csv', index=False, encoding='utf-8-sig')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modo', default='completo')
    modo = ap.parse_args().modo
    raiz = Path(__file__).resolve().parents[1]
    res = raiz / 'resultados' / modo
    tab, fig_nb = res / 'tabelas', res / 'figuras'
    saida = Path(__file__).resolve().parent / 'saidas' / modo / 'figuras'
    saida.mkdir(parents=True, exist_ok=True)
    T = lambda nome: pd.read_csv(next(tab.glob(f'T*_{nome}.csv')))   # by name, not by number
    diag = pd.read_csv(saida.parent / 'diagnosticos_previsoes.csv')

    # ---------- Figure 1: targets and annual cycle with the wet season ----------
    cal = T('calendario')
    fig = plt.figure(figsize=(174 * mm, 92 * mm))
    gs = fig.add_gridspec(3, 2, width_ratios=[1.0, 1.25], wspace=0.30, hspace=0.42)
    ax = fig.add_subplot(gs[:, 0])
    ax.imshow(Image.open(fig_nb / 'F01_mapa_alvos.png'))
    ax.set_axis_off()
    letra(ax, 'a', x=0.02, y=0.98)
    dados1 = []
    for i, alvo in enumerate(ALVOS):
        ax = fig.add_subplot(gs[i, 1])
        c = cal[cal.alvo == alvo].set_index('mês').reindex(MESES_PT)
        chuv = (c['estação'] == 'chuvosa').to_numpy()
        # each panel starts at the beginning of the target's hydrological year (first month of the
        # wet season); Q (Liebmann and Marengo, 2001) is summed from it and written to the CSV.
        ini = next(k for k in range(12) if chuv[k] and not chuv[k - 1])
        ordem = [(ini + k) % 12 for k in range(12)]
        p = c['normal 1981–2010 (mm)'].to_numpy()[ordem]
        q = np.cumsum(p - p.mean())
        ax.bar(range(12), p, color=np.where(chuv[ordem], COR[alvo], '#BBBBBB'),
               edgecolor='k', linewidth=0.3, width=0.75)
        ax.set_xticks(range(12), [MESES_EN[k][0] for k in ordem])
        ax.tick_params(axis='x', pad=1.5)
        if i == 1:
            ax.set_ylabel('Rainfall, 1981–2010 (mm/month)')
        ax.set_title(alvo, loc='left', fontweight='bold', pad=2, x=0.03)
        # wet-season rule made visible: months above the mean monthly rainfall of the year. It is the same
        # rule as the cumulative anomaly Q (Q rises in those months), whose values go to the CSV.
        ax.axhline(p.mean(), color='k', lw=0.9, ls='--')
        ax.text(11.45, p.mean(), f'{p.mean():.0f} mm', ha='right', va='bottom', fontsize=6.5)
        letra(ax, 'bcd'[i])
        dados1.append(pd.DataFrame({'alvo': alvo, 'mês': [MESES_PT[k] for k in ordem],
                                    'normal 1981–2010 (mm)': p,
                                    'anomalia acumulada Q desde o início do ano hidrológico (mm)': q,
                                    'estação': c['estação'].to_numpy()[ordem]}))
    fig.legend(handles=[mpl.patches.Patch(facecolor='white', edgecolor='k', lw=0.3,
                                          label='wet-season month (target colour)'),
                        mpl.patches.Patch(facecolor='#BBBBBB', edgecolor='k', lw=0.3,
                                          label='dry-season month'),
                        mpl.lines.Line2D([], [], color='k', ls='--', lw=0.9,
                                         label='mean monthly rainfall of the year')],
               frameon=False, fontsize=7, loc='upper center', ncol=3, handlelength=1.6,
               bbox_to_anchor=(0.66, 0.035), columnspacing=1.0)
    salvar(fig, saida, 'fig1_alvos_ciclo', pd.concat(dados1, ignore_index=True))

    # ---------- Figure 2: correlation profiles by lag ----------
    per, asso = T('perfil_defasagens'), T('associacao')
    fig, axs = plt.subplots(3, 3, figsize=(174 * mm, 120 * mm), sharex=True, sharey=True)
    for i, alvo in enumerate(ALVOS):
        for j, caso in enumerate(CASOS):
            ax = axs[i, j]
            ax.axhline(0, color='k', lw=0.5)
            ax.axvspan(-0.5, 0.5, color='#EEEEEE', lw=0)
            for ind in INDICES:
                p = per[(per.alvo == alvo) & (per.caso == caso) & (per['índice'] == ind)]
                ax.plot(p.L, p.r, color=COR[ind], ls=LINHA[ind], lw=1.0)
                a = asso[(asso.alvo == alvo) & (asso.caso == caso) & (asso['índice'] == ind)].iloc[0]
                det = bool(a['detectado (q < 0,05)'])
                ax.errorbar(a['L* (meses)'], a['r(L*)'],
                            yerr=[[a['r(L*)'] - a['IC95 inferior']], [a['IC95 superior'] - a['r(L*)']]],
                            fmt=MARCA[ind], color=COR[ind], mfc=COR[ind] if det else 'white',
                            ms=4.5, elinewidth=0.8, capsize=1.5, zorder=3)
            ax.set_xticks([0, 2, 4, 6, 8, 10, 12])
            if i == 0:
                ax.set_title(EN[caso])
            if j == 0:
                ax.set_ylabel(f'{alvo}\nCorrelation, r')
            if i == 2:
                ax.set_xlabel('Lag, L (months)')
            letra(ax, 'abcdefghi'[3 * i + j])
    hs = [mpl.lines.Line2D([], [], color=COR[k], ls=LINHA[k], marker=MARCA[k], ms=4, label=k)
          for k in INDICES]
    hs += [mpl.lines.Line2D([], [], color='k', marker='o', ls='', ms=4, label='L*, q < 0.05'),
           mpl.lines.Line2D([], [], color='k', marker='o', ls='', ms=4, mfc='white',
                            label='L*, q ≥ 0.05')]
    fig.legend(handles=hs, loc='lower center', ncol=5, frameon=False, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    salvar(fig, saida, 'fig2_perfis_defasagem', per.merge(
        asso[['alvo', 'caso', 'índice', 'L* (meses)', 'r(L*)', 'IC95 inferior', 'IC95 superior',
              'q (BH)', 'detectado (q < 0,05)']], on=['alvo', 'caso', 'índice']))

    # ---------- Figure 3: wet-season maps (drawn by the notebook) ----------
    for ext in ('png', 'pdf'):
        shutil.copyfile(fig_nb / f'F09_mapas_r_chuvosa.{ext}', saida / f'fig3_mapas_chuvosa.{ext}')

    # ---------- Figure 4: dominant index and its lag in each pixel ----------
    # The maps are those of the notebook (F13): in each pixel, the index with the largest |r| among the three, each
    # at its strongest lag (L1 to L12, 1981–2010), and that lag. In the notebook, the colour of the
    # index lightens with |r| by the rule 1 − a·(1 − colour), with a = |r|/0.5 limited to [0.15; 1].
    # Here the notebook colour legend (top strip of the image) is replaced by an |r| scale
    # drawn with that same rule, so that local strength can be read on the map.
    img = np.asarray(Image.open(fig_nb / 'F13_indice_predominante.png').convert('RGB'))
    branco = (img > 245).all(2).all(1)                     # linhas inteiramente brancas
    topo = 0
    while branco[topo]:                                    # white margin above the legend
        topo += 1
    while not branco[topo]:                                # the legend itself
        topo += 1
    img = img[topo:]
    alt_img = 174 * img.shape[0] / img.shape[1]             # height of the maps in mm
    alt_esc = 14.5
    fig = plt.figure(figsize=(174 * mm, (alt_img + alt_esc) * mm))
    ax = fig.add_axes([0, 0, 1, alt_img / (alt_img + alt_esc)])
    ax.imshow(img, interpolation='lanczos')
    ax.set_axis_off()
    niveis = [0.1, 0.2, 0.3, 0.4, 0.5]
    for j, nome in enumerate(INDICES):
        cor = np.array(mpl.colors.to_rgb(COR[nome]))
        ex = fig.add_axes([0.10 + 0.29 * j, 1 - 8.2 / (alt_img + alt_esc), 0.16,
                           3.6 / (alt_img + alt_esc)])
        for k, r in enumerate(niveis):
            a = min(max(r / 0.5, 0.15), 1.0)
            ex.add_patch(mpl.patches.Rectangle((k, 0), 1, 1, color=1 - a * (1 - cor)))
        ex.set_xlim(0, len(niveis)), ex.set_ylim(0, 1)
        ex.set_xticks(np.arange(len(niveis)) + 0.5,
                      [f'{r:.1f}' if r < 0.5 else '≥0.5' for r in niveis], fontsize=7)
        ex.set_yticks([])
        ex.tick_params(length=0, pad=1.5)
        for lado in ex.spines.values():
            lado.set_visible(False)
        ex.text(-0.15, 0.5, nome, ha='right', va='center', fontsize=8, fontweight='bold',
                transform=ex.transData)
    fig.text(0.5, 1 - 2.2 / (alt_img + alt_esc),
             'Dominant index; colour intensity = |r| of that index at its strongest lag',
             ha='center', va='center', fontsize=8)
    with mpl.rc_context({'savefig.bbox': 'standard'}):
        for ext in ('png', 'pdf'):
            fig.savefig(saida / f'fig4_predominio_defasagem.{ext}', dpi=600)
    plt.close(fig)
    T('indice_predominante').to_csv(saida / 'fig4_predominio_defasagem_dados.csv', index=False,
                                    encoding='utf-8-sig')

    # ---------- Figure 5: gain of each model over its own control ----------
    # One panel per method, each with its own scale: the RPSS of different models are not
    # comparable (each has its own control), and the random forest varies an order of
    # magnitude more than the other two.
    hip = T('hipotese_tres_metodos')
    linhas = [(a, c, i) for a in ALVOS for c in CASOS for i in INDICES]
    CURTO_CASO = {'ano hidrológico': 'year', 'estação chuvosa': 'wet', 'estação seca': 'dry'}
    rot = [f'{a} · {CURTO_CASO[c]} · {i}' for a, c, i in linhas]
    y0 = np.arange(len(linhas))[::-1]
    fig, axs = plt.subplots(1, 3, figsize=(174 * mm, 150 * mm), sharey=True,
                            gridspec_kw=dict(wspace=0.10, width_ratios=[1, 1.35, 1]))
    reg = []
    for k, m in enumerate(METODOS):
        ax = axs[k]
        h = hip[hip['método'] == m].set_index(['alvo', 'caso', 'índice']).loc[linhas]
        r = h['RPSS sobre o modelo sem índice (%)'].to_numpy()
        lo, hi = h['IC95 inferior'].to_numpy(), h['IC95 superior'].to_numpy()
        tend = (h['teste por deslocamento (Ridge)'] == 'acima de 5 %').to_numpy()
        ind = np.array([l[2] for l in linhas])
        for g in range(1, 9):
            ax.axhline(y0[0] - 3 * g + 0.5, color='#E6E6E6', lw=0.5, zorder=0)
        for g in (1, 2):
            ax.axhline(y0[0] - 9 * g + 0.5, color='#999999', lw=0.7, zorder=0)
        ax.axvline(0, color='k', lw=0.6, zorder=1)
        for i_ in INDICES:
            sel = ind == i_
            ax.errorbar(r[sel], y0[sel], xerr=[r[sel] - lo[sel], hi[sel] - r[sel]], fmt='none',
                        ecolor=COR[i_], elinewidth=0.8, capsize=1.3, zorder=2)
            ax.scatter(r[sel & ~tend], y0[sel & ~tend], marker=MARCA[i_], color=COR[i_], s=16,
                       zorder=3)
            ax.scatter(r[sel & tend], y0[sel & tend], marker=MARCA[i_], facecolors='white',
                       edgecolors=COR[i_], s=16, lw=0.9, zorder=3)
        ax.set_title(f"{EN[m]}\n(smallest q = {h['q'].min():.3f})")
        ax.set_xlabel('RPSS vs the same model\nwithout the index (%)')
        ax.set_ylim(-0.8, len(linhas) - 0.2)
        ax.tick_params(axis='y', length=0)
        letra(ax, 'abc'[k], x=0.0)
        reg.append(pd.DataFrame({'método': m, 'alvo': [l[0] for l in linhas],
                                 'caso': [l[1] for l in linhas], 'índice': ind,
                                 'RPSS sobre o controle (%)': r, 'IC95 inferior': lo,
                                 'IC95 superior': hi, 'p (nulo)': h['p (nulo)'].to_numpy(),
                                 'q': h['q'].to_numpy(),
                                 'verificação acima de 5 % (Ridge)': tend}))
    axs[0].set_yticks(y0, rot)
    hs = [mpl.lines.Line2D([], [], color=COR[i_], marker=MARCA[i_], ls='', ms=4, label=i_)
          for i_ in INDICES]
    hs += [mpl.lines.Line2D([], [], color='k', marker='o', ls='', ms=4, mfc='white',
                            label='trend-sensitivity check above 5 % (Ridge)')]
    fig.legend(handles=hs, loc='lower center', ncol=4, frameon=False,
               bbox_to_anchor=(0.55, -0.035))
    salvar(fig, saida, 'fig5_habilidade_regional', pd.concat(reg))

    # ---------- Figure 6: regularization, planted signal and variation of the probabilities ----------
    cal5, sp = T('calibracao_hiperparametros'), T('sinal_plantado')
    cfg = cal5['configuração'].map(json.loads)
    fig = plt.figure(figsize=(174 * mm, 105 * mm))
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.05], hspace=0.62, wspace=0.42)
    dados5 = []
    # (a)-(c) validation RPSS (1996–2010) along the regularization path, ± 1 standard error
    eixos = {'Ridge': ('penalidade_por_mes', None, 'Penalty per training month'),
             'Random Forest': ('folha', 'profundidade', 'Minimum leaf fraction'),
             'Rede neural': ('decaimento', 'oculta', 'Weight decay')}
    escolhida = {m: cal5.loc[(cal5['método'] == m) & cal5.escolhida, 'configuração'].map(json.loads).iloc[0]
                 for m in METODOS}
    for k, m in enumerate(METODOS):
        ax = fig.add_subplot(gs[0, k])
        sub = cal5[cal5['método'] == m].assign(**pd.DataFrame(list(cfg[cal5['método'] == m]),
                                                               index=cal5.index[cal5['método'] == m]))
        x, grupo, rotx = eixos[m]
        if m == 'Rede neural':          # activation and passes of the chosen configuration
            sub = sub[(sub.ativacao == escolhida[m]['ativacao'])
                      & (sub.passagens == escolhida[m]['passagens'])]
        grupos = [None] if grupo is None else sorted(sub[grupo].dropna().unique().tolist()) + (
            [None] if sub[grupo].isna().any() else [])
        estilos = ['-', '--', ':', '-.']
        for g, ls in zip(grupos, estilos):
            s = sub if grupo is None else (sub[sub[grupo].isna()] if g is None else sub[sub[grupo] == g])
            s = s.sort_values(x)
            lab = None if grupo is None else (f'{"depth" if grupo == "profundidade" else "hidden units"} '
                                              f'{"unlimited" if g is None else int(g)}')
            ax.errorbar(s[x], s['RPSS (%)'], yerr=s['erro-padrão'], color=COR[m], ls=ls,
                        marker=MARCA[m], ms=3, lw=0.9, elinewidth=0.6, capsize=1.2, label=lab)
            esc = s[s.escolhida]
            ax.plot(esc[x], esc['RPSS (%)'], marker='*', ms=9, color='k', ls='', zorder=5)
            dados5.append(s.assign(painel='abc'[k]).drop(columns=['configuração']))
        ax.set_xscale('log')
        marcas = {'Ridge': [0.01, 0.1, 1, 10, 100], 'Random Forest': [0.05, 0.1, 0.2, 0.3],
                  'Rede neural': [0.001, 0.01, 0.1, 1, 10]}[m]
        ax.set_xticks(marcas, [f'{v:g}' for v in marcas])
        ax.xaxis.set_minor_locator(mpl.ticker.NullLocator())
        ax.axhline(0, color='k', lw=0.5)
        ax.set_xlabel(rotx)
        ax.set_title(EN[m])
        if k == 0:
            ax.set_ylabel('Validation RPSS,\n1996–2010 (%)')
        if grupo is not None:
            ax.set_ylim(bottom={'Random Forest': -17, 'Rede neural': -12}[m])
            ax.legend(frameon=False, fontsize=6.3, loc='lower right', handlelength=2.0,
                      borderaxespad=0.1, labelspacing=0.25)
        letra(ax, 'abc'[k])
    # (d) sinal plantado
    ax = fig.add_subplot(gs[1, 0:2])
    xs = np.arange(3)
    for k, m in enumerate(METODOS):
        s = sp[sp['método'] == m].set_index('correlação plantada')
        vals = [s.loc[0.0, 'RPSS (%)'], s.loc[0.3, 'RPSS (%)'],
                s.loc[0.3, 'RPSS com a configuração dos dados reais (%)']]
        ses = [s.loc[0.0, 'erro-padrão'], s.loc[0.3, 'erro-padrão'], np.nan]
        ax.errorbar(xs + (k - 1) * 0.18, vals, yerr=ses, fmt=MARCA[m], color=COR[m], ms=4,
                    elinewidth=0.7, capsize=1.5, label=EN[m])
    ax.axhline(0, color='k', lw=0.5)
    ax.set_xticks(xs, ['ρ = 0\nselected on\nsynthetic data', 'ρ = 0.3\nselected on\nsynthetic data',
                       'ρ = 0.3\nselected on\nreal data'])
    ax.set_ylabel('Validation RPSS,\n1996–2010 (%)')
    ax.set_xlim(-0.5, 2.5)
    ax.legend(frameon=False, ncol=3, loc='lower center', bbox_to_anchor=(0.5, 1.0),
              columnspacing=1.2, handletextpad=0.3)
    letra(ax, 'd')
    dados5.append(sp.assign(painel='d'))
    # (e) variation of the probabilities issued in the test period
    ax = fig.add_subplot(gs[1, 2])
    rng = np.random.default_rng(0)                    # only to spread the points horizontally
    for k, m in enumerate(METODOS):
        v = diag.loc[diag['método'] == m, ['dp de P(Q1) com índice (p.p.)',
                                           'dp de P(Q5) com índice (p.p.)']].mean(axis=1)
        ax.scatter(k + rng.uniform(-0.18, 0.18, len(v)), v, marker=MARCA[m], color=COR[m], s=9,
                   alpha=0.85)
        ax.plot([k - 0.25, k + 0.25], [np.median(v)] * 2, color='k', lw=1.2)
    ax.set_xticks(range(3), ['Ridge', 'Random\nforest', 'Neural\nnetwork'])
    ax.set_ylabel('SD of P(Q1), P(Q5) (p.p.)')
    ax.set_ylim(bottom=0)
    letra(ax, 'e')
    dados5.append(diag.assign(painel='e'))
    salvar(fig, saida, 'fig6_regularizacao_detectabilidade', pd.concat(dados5, ignore_index=True))

    # ---------- Graphical abstract: exactly 50 × 60 mm, English labels ----------
    fig = plt.figure(figsize=(50 * mm, 60 * mm))
    ax = fig.add_axes([0.25, 0.20, 0.71, 0.70])
    r_l = asso.set_index(['alvo', 'caso', 'índice'])['r(L*)'].abs()
    det = asso.set_index(['alvo', 'caso', 'índice'])['detectado (q < 0,05)']
    # gain over the reference climatology N (artigo/rpss_climatologia.py)
    rn = pd.read_csv(saida.parent / 'rpss_climatologia.csv')
    rn['caso'] = rn['caso'].map({'ano hidrológico': 'ano hidrológico', 'estação chuvosa': 'estação chuvosa',
                                 'estação seca': 'estação seca'})
    rid = rn[rn['método'] == 'Ridge'].set_index(['alvo', 'caso', 'índice']).rename(
        columns={'RPSS sobre N (%)': 'RPSS sobre o modelo sem índice (%)'})
    for ind in INDICES:
        idx = [k for k in r_l.index if k[2] == ind]
        x, y = r_l.loc[idx].to_numpy(), rid.loc[idx, 'RPSS sobre o modelo sem índice (%)'].to_numpy()
        ax.errorbar(x, y, yerr=[y - rid.loc[idx, 'IC95 inferior'], rid.loc[idx, 'IC95 superior'] - y],
                    fmt='none', ecolor=COR[ind], elinewidth=0.5, alpha=0.7)
        ax.scatter(x, y, marker=MARCA[ind], s=10, zorder=3, lw=0.6, edgecolors=COR[ind],
                   facecolors=[COR[ind] if det.loc[k] else 'white' for k in idx])
    ax.axhline(0, color='k', lw=0.5)
    ax.set_xlim(0, 0.42)
    ax.set_xlabel('Lagged association, |r|', fontsize=6.5, labelpad=1)
    ax.set_ylabel('Gain over\nclimatology, RPSS (%)', fontsize=6.5, labelpad=1)
    ax.tick_params(labelsize=6, length=2, pad=1)
    ax.legend(handles=[mpl.lines.Line2D([], [], color=COR[i_], marker=MARCA[i_], ls='', ms=3,
                                        label=i_) for i_ in INDICES],
              frameon=False, fontsize=5.5, loc='upper left', handletextpad=0.1, borderaxespad=0.2,
              labelspacing=0.2)
    fig.text(0.5, 0.975, f"{int(det.sum())} of {len(det)} associations detected", ha='center',
             va='top', fontsize=6.2, fontweight='bold')
    fig.text(0.5, 0.01, 'Ridge, 2011–2025; filled: association\ndetected; bars: 95% CI',
             ha='center', va='bottom', fontsize=5.2, linespacing=1.0)
    with mpl.rc_context({'savefig.bbox': 'standard'}):         # exact size of 50 × 60 mm
        for ext in ('png', 'pdf'):
            fig.savefig(saida / f'resumo_grafico.{ext}', dpi=300)
    plt.close(fig)
    pd.DataFrame({'|r(L*)|': r_l, 'associação detectada': det,
                  'RPSS da Ridge sobre a climatologia N (%)': rid['RPSS sobre o modelo sem índice (%)'],
                  'IC95 inferior': rid['IC95 inferior'], 'IC95 superior': rid['IC95 superior']}
                 ).reset_index().to_csv(saida / 'resumo_grafico_dados.csv', index=False,
                                        encoding='utf-8-sig')
    print('figures written to', saida.relative_to(raiz))


if __name__ == '__main__':
    main()
