#!/usr/bin/env python3
"""生信三图：热图 / 火山图 / 箱线图。

每个图独立，用不同的输入：
  heatmap:  expression.csv（行=基因，列=样本）
  volcano:  deg.csv（列名含 log2FC, pvalue 或 padj）
  boxplot:  groups.csv（列名含 group, value）
"""
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch

plt.rcParams.update({
    'font.sans-serif': ['Noto Sans CJK SC', 'DejaVu Sans'],
    'axes.unicode_minus': False,
    'font.size': 8,
    'axes.linewidth': 0.8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'xtick.direction': 'in', 'ytick.direction': 'in',
    'figure.dpi': 300,
})

BLUE, ORANGE, GREEN = '#0072B2', '#E69F00', '#009E73'
RED = '#D55E00'
HMAP = LinearSegmentedColormap.from_list('hm', ['#08306B', '#4292C6', '#FFFFFF', '#FDAE6B', '#A63603'])


# ---------------- 热图 ----------------
def heatmap(path, out='heatmap.png', top=40):
    df = pd.read_csv(path, index_col=0)
    if df.shape[0] > top:                       # 取方差最大的前 N 行
        df = df.loc[df.var(axis=1).sort_values(ascending=False).index[:top]]
    z = df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1).replace(0, 1), axis=0)

    fig, ax = plt.subplots(figsize=(3.6, 4.2))
    im = ax.imshow(z.values, aspect='auto', cmap=HMAP, vmin=-2, vmax=2,
                   interpolation='nearest')
    ax.set_xticks(range(df.shape[1]))
    ax.set_xticklabels(df.columns, rotation=45, ha='right', fontsize=6)
    if df.shape[0] <= 45:
        ax.set_yticks(range(df.shape[0]))
        ax.set_yticklabels(df.index, fontsize=5)
    else:
        ax.set_yticks([])
    ax.set_ylabel('Genes', fontsize=7)
    cb = fig.colorbar(im, ax=ax, fraction=.05, pad=.03)
    cb.set_label('Row z-score', fontsize=7)
    cb.ax.tick_params(labelsize=6)
    fig.tight_layout()
    fig.savefig(out, bbox_inches='tight', facecolor='white')
    print('→', out)


# ---------------- 火山图 ----------------
def volcano(path, out='volcano.png', fc=1.0, p=0.05, n_label=8):
    df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}
    fc_col = cols.get('log2fc') or cols.get('log2fc'.replace('fc', 'foldchange'))
    p_col = next((cols[k] for k in ('padj', 'pvalue', 'p', 'p_val') if k in cols), None)
    if fc_col is None or p_col is None:
        raise SystemExit('需要 log2FC 和 pvalue/padj 两列')

    lfc = df[fc_col].astype(float).values
    pv = df[p_col].astype(float).clip(1e-300).values
    y = -np.log10(pv)

    up = (lfc >= fc) & (pv <= p)
    dn = (lfc <= -fc) & (pv <= p)
    ns = ~(up | dn)

    fig, ax = plt.subplots(figsize=(3.4, 3.0))
    ax.scatter(lfc[ns], y[ns], s=7, c='#C8CDD3', linewidths=0, alpha=.75)
    ax.scatter(lfc[dn], y[dn], s=8, c=BLUE, linewidths=0, alpha=.9)
    ax.scatter(lfc[up], y[up], s=8, c=RED, linewidths=0, alpha=.9)
    ax.axvline(fc, ls='--', lw=.6, c='#888')
    ax.axvline(-fc, ls='--', lw=.6, c='#888')
    ax.axhline(-np.log10(p), ls='--', lw=.6, c='#888')
    ax.set_xlabel('log$_2$ fold change', fontsize=8)
    ax.set_ylabel('-log$_{10}$ P', fontsize=8)

    # 标注最显著的几个（只标显著的；竖直方向错开避免重叠）
    cand = np.where(up | dn)[0]
    cand = cand[np.argsort(-y[cand])][:n_label]
    used = []
    for i in cand:
        yy = y[i]
        if any(abs(yy - u) < 0.12 * y.max() for u in used):
            continue
        used.append(yy)
        ax.annotate(df.iloc[i, 0], (lfc[i], yy), fontsize=5,
                    xytext=(3, 2), textcoords='offset points',
                    arrowprops=dict(arrowstyle='-', lw=.35, color='#666'))
    ax.legend(handles=[Patch(color=RED, label=f'Up ({up.sum()})'),
                       Patch(color=BLUE, label=f'Down ({dn.sum()})'),
                       Patch(color='#C8CDD3', label=f'NS ({(~up & ~dn).sum()})')],
              fontsize=6, loc='upper left', frameon=False)
    fig.tight_layout()
    fig.savefig(out, bbox_inches='tight', facecolor='white')
    print('→', out)


# ---------------- 箱线图 ----------------
def boxplot(path, out='boxplot.png', jitter=True):
    df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}
    g_col = next((cols[k] for k in ('group', 'condition', 'label') if k in cols), df.columns[0])
    v_col = next((cols[k] for k in ('value', 'expr', 'expression', 'score') if k in cols),
                 df.columns[1])
    groups = list(pd.unique(df[g_col]))
    data = [df.loc[df[g_col] == g, v_col].astype(float).values for g in groups]

    fig, ax = plt.subplots(figsize=(2.8, 2.6))
    bp = ax.boxplot(data, patch_artist=True, widths=.55,
                    medianprops=dict(color='black', lw=1.0),
                    flierprops=dict(marker='', linestyle='none'))
    palette = [BLUE, ORANGE, GREEN, RED, '#7B8B9A']
    for i, patch in enumerate(bp['boxes']):
        patch.set_facecolor(palette[i % len(palette)])
        patch.set_alpha(.55)
        patch.set_edgecolor('black'); patch.set_linewidth(.7)
    if jitter:
        rng = np.random.default_rng(3)
        for i, d in enumerate(data, 1):
            x = i + rng.uniform(-.13, .13, len(d))
            ax.scatter(x, d, s=4, c='black', alpha=.35, linewidths=0, zorder=3)
    ax.set_xticks(range(1, len(groups) + 1))
    ax.set_xticklabels(groups, fontsize=7)
    ax.set_ylabel(v_col, fontsize=8)
    fig.tight_layout()
    fig.savefig(out, bbox_inches='tight', facecolor='white')
    print('→', out)


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'demo'
    path = sys.argv[2] if len(sys.argv) > 2 else 'demo_omics.csv'
    if what == 'heatmap':
        heatmap(path)
    elif what == 'volcano':
        volcano(path)
    elif what == 'boxplot':
        boxplot(path)
    else:
        raise SystemExit('用法: omics_plots.py heatmap|volcano|boxplot <csv>')
