#!/usr/bin/env python3
"""PCA 散点图 与 ROC 曲线。

PCA 输入：行=样本，列=特征，第一列是样本名（可选）
ROC 输入：两列 —— y_true（0/1）、y_score（概率/分数）

输出：pca.png / roc.png（可选 roc.csv 含 AUC）
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({
    'font.sans-serif': ['Noto Sans CJK SC', 'DejaVu Sans'],
    'axes.unicode_minus': False,
    'font.size': 9,
    'axes.linewidth': 0.8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'xtick.direction': 'in', 'ytick.direction': 'in',
    'figure.dpi': 300,
})

BLUE, ORANGE, GREEN, RED = '#0072B2', '#E69F00', '#009E73', '#D55E00'
PALETTE = [BLUE, ORANGE, GREEN, RED, '#7B8B9A', '#CC79A7', '#56B4E9']


# ---------------- PCA ----------------
def pca(path, out='pca.png', group_col=None):
    """行=样本，列=特征。非数值列自动当样本名/分组。"""
    df = pd.read_csv(path)
    num = df.select_dtypes(include=[np.number])

    # 自动找分组列：优先列名叫 group/cluster/label/class，否则取第一个非数值列
    groups = None
    if group_col is not None:
        g = df.iloc[:, group_col] if isinstance(group_col, int) else df[group_col]
    else:
        cand = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
        pref = [c for c in cand if c.lower() in ('group', 'cluster', 'label', 'class', 'type')]
        g = df[pref[0]] if pref else (df[cand[0]] if cand else None)

    if g is not None:
        groups = g.astype(str).values

    X = num.values.astype(float)
    if X.shape[1] < 2:
        raise ValueError("PCA 至少需要 2 个数值列")

    # 标准化 + SVD
    Xc = X - X.mean(axis=0)
    sd = Xc.std(axis=0)
    sd[sd == 0] = 1
    Xs = Xc / sd
    U, S, Vt = np.linalg.svd(Xs, full_matrices=False)
    var = (S ** 2) / (S ** 2).sum() * 100
    pc = U[:, :2] * S[:2]

    fig, ax = plt.subplots(figsize=(3.4, 3.0))
    if groups is None:
        ax.scatter(pc[:, 0], pc[:, 1], s=22, c=BLUE, alpha=.75,
                   edgecolor='white', linewidth=.5)
    else:
        for i, g in enumerate(pd.unique(groups)):
            m = groups == g
            ax.scatter(pc[m, 0], pc[m, 1], s=22, c=PALETTE[i % len(PALETTE)],
                       alpha=.8, edgecolor='white', linewidth=.5, label=str(g))
        ax.legend(fontsize=6, frameon=False, loc='best')

    ax.set_xlabel(f'PC1 ({var[0]:.1f}%)', fontsize=8)
    ax.set_ylabel(f'PC2 ({var[1]:.1f}%)', fontsize=8)
    ax.tick_params(labelsize=6)
    fig.tight_layout()
    fig.savefig(out, bbox_inches='tight', facecolor='white')
    print('→', out, f'(PC1 {var[0]:.1f}%, PC2 {var[1]:.1f}%)')


# ---------------- ROC ----------------
def roc(path, out='roc.png', label_col='y_true', score_col='y_score'):
    df = pd.read_csv(path)
    if label_col not in df.columns or score_col not in df.columns:
        # 退化为前两列
        label_col, score_col = df.columns[0], df.columns[1]

    y = df[label_col].values.astype(int)
    s = df[score_col].values.astype(float)

    if len(np.unique(y)) < 2:
        raise ValueError("y_true 需要同时包含 0 和 1")

    # 手算 ROC（不依赖 sklearn）
    order = np.argsort(-s)
    y = y[order]; s = s[order]
    P = (y == 1).sum(); N = (y == 0).sum()
    tps = np.cumsum(y == 1)
    fps = np.cumsum(y == 0)
    tpr = np.concatenate([[0], tps / P])
    fpr = np.concatenate([[0], fps / N])
    # numpy 2.0 把 trapz 改名成 trapezoid
    _trap = getattr(np, 'trapezoid', None) or getattr(np, 'trapz', None)
    auc = _trap(tpr, fpr)

    fig, ax = plt.subplots(figsize=(3.0, 3.0))
    ax.plot(fpr, tpr, color=BLUE, lw=1.6, label=f'AUC = {auc:.3f}')
    ax.plot([0, 1], [0, 1], '--', color='#999999', lw=.8)
    ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel('False positive rate', fontsize=8)
    ax.set_ylabel('True positive rate', fontsize=8)
    ax.legend(fontsize=7, frameon=False, loc='lower right')
    ax.tick_params(labelsize=6)
    ax.set_aspect('equal')
    fig.tight_layout()
    fig.savefig(out, bbox_inches='tight', facecolor='white')
    print('→', out, f'(AUC {auc:.3f})')
    return auc


# ---------------- 小提琴图 ----------------
def violin(path, out='violin.png', group_col='group', value_col='value'):
    df = pd.read_csv(path)
    if group_col not in df.columns:
        group_col, value_col = df.columns[0], df.columns[1]
    groups = list(pd.unique(df[group_col].astype(str)))
    data = [df.loc[df[group_col].astype(str) == g, value_col].dropna().values for g in groups]

    fig, ax = plt.subplots(figsize=(3.2, 2.8))
    parts = ax.violinplot(data, showmeans=False, showmedians=True, widths=.75)
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(PALETTE[i % len(PALETTE)])
        pc.set_alpha(.55)
        pc.set_edgecolor('black'); pc.set_linewidth(.6)
    for key in ('cmedians', 'cbars', 'cmins', 'cmaxes'):
        if key in parts:
            parts[key].set_color('black'); parts[key].set_linewidth(.7)

    rng = np.random.default_rng(5)
    for i, d in enumerate(data, 1):
        x = i + rng.uniform(-.09, .09, len(d))
        ax.scatter(x, d, s=3, c='black', alpha=.28, linewidths=0, zorder=3)

    ax.set_xticks(range(1, len(groups) + 1))
    ax.set_xticklabels(groups, fontsize=7)
    ax.set_ylabel(value_col, fontsize=8)
    ax.tick_params(labelsize=6)
    fig.tight_layout()
    fig.savefig(out, bbox_inches='tight', facecolor='white')
    print('→', out)


def run_pca(path, outdir='out'):
    import os
    os.makedirs(outdir, exist_ok=True)
    pca(path, os.path.join(outdir, 'pca.png'))


def run_roc(path, outdir='out'):
    import os
    os.makedirs(outdir, exist_ok=True)
    roc(path, os.path.join(outdir, 'roc.png'))


def run_violin(path, outdir='out'):
    import os
    os.makedirs(outdir, exist_ok=True)
    violin(path, os.path.join(outdir, 'violin.png'))
