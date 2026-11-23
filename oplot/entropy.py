#!/usr/bin/env python3
"""熵值法 + TOPSIS 完整实现（含结果表和权重图）。

输入 CSV：第一列是方案名，其余列是指标（默认全部正向）。
    方案,指标1,指标2,...
输出：
    weights.csv   各指标权重
    scores.csv    各方案得分与排名
    fig.png       权重条形图 + 得分排名图
"""
import sys
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.sans-serif': ['Noto Sans CJK SC', 'Noto Sans CJK', 'DejaVu Sans'],
                     'axes.unicode_minus': False, 'font.size': 9,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.linewidth': 0.8, 'xtick.direction': 'in',
                     'ytick.direction': 'in', 'figure.dpi': 300})

BLUE, ORANGE = '#0072B2', '#E69F00'


def entropy_weight(X):
    """X: n_samples x m_indicators（已正向化、非负）"""
    n, m = X.shape
    P = X / X.sum(axis=0, keepdims=True)
    P = np.where(P <= 0, 1e-12, P)          # 避免 log(0)
    k = 1.0 / np.log(n)
    E = -k * (P * np.log(P)).sum(axis=0)    # 信息熵
    d = 1 - E                                # 差异系数
    w = d / d.sum()
    return w, E, d


def topsis(X, w):
    """X: 已正向化。返回贴近度 C（越大越好）"""
    V = X * w                                # 加权标准化矩阵
    best = V.max(axis=0)
    worst = V.min(axis=0)
    d_pos = np.sqrt(((V - best) ** 2).sum(axis=1))
    d_neg = np.sqrt(((V - worst) ** 2).sum(axis=1))
    return d_neg / (d_pos + d_neg)


def main(path, outdir='.'):
    df = pd.read_csv(path)
    names = df.iloc[:, 0].astype(str).values
    raw = df.iloc[:, 1:].astype(float).values

    # 极差标准化（min-max）→ 全部转成"越大越好"的非负值
    mn, mx = raw.min(axis=0), raw.max(axis=0)
    span = np.where(mx - mn == 0, 1.0, mx - mn)
    X = (raw - mn) / span
    X = X + 1e-6                              # 避免 0

    w, E, d = entropy_weight(X)
    C = topsis(X, w)

    order = np.argsort(-C)
    res = pd.DataFrame({
        'scheme': names,
        'score': np.round(C, 4),
        'rank': np.empty(len(names), dtype=int),
    })
    res.loc[order, 'rank'] = np.arange(1, len(names) + 1)
    res = res.sort_values('rank')

    wt = pd.DataFrame({
        'indicator': df.columns[1:],
        'entropy': np.round(E, 4),
        'diff_coef': np.round(d, 4),
        'weight': np.round(w, 4),
    })

    wt.to_csv(os.path.join(outdir, 'weights.csv'), index=False, encoding='utf-8-sig')
    res.to_csv(os.path.join(outdir, 'scores.csv'), index=False, encoding='utf-8-sig')

    # ---- 图 ----
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6),
                             gridspec_kw={'width_ratios': [1.5, 1]})

    ax = axes[0]
    x = np.arange(len(w))
    ax.bar(x, w, color=BLUE, edgecolor='black', linewidth=0.5, width=0.6)
    for i, v in enumerate(w):
        ax.text(i, v + 0.008, f'{v:.3f}', ha='center', va='bottom', fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels(df.columns[1:], rotation=30, ha='right', fontsize=7)
    ax.set_ylabel('Weight', fontsize=8)
    ax.set_title('Entropy weights', fontsize=9)
    ax.set_ylim(0, max(w) * 1.25)

    ax = axes[1]
    o = np.argsort(C)
    ax.barh(np.arange(len(C)), C[o], color=ORANGE, edgecolor='black', linewidth=0.5, height=0.6)
    ax.set_yticks(np.arange(len(C)))
    ax.set_yticklabels(names[o], fontsize=7)
    ax.set_xlabel('Closeness coefficient', fontsize=8)
    ax.set_title('TOPSIS ranking', fontsize=9)
    ax.set_xlim(0, max(C) * 1.2)

    fig.tight_layout()
    fig.savefig(os.path.join(outdir, 'fig.png'), bbox_inches='tight', facecolor='white')
    print(os.path.join(outdir, 'weights.csv'), '/ scores.csv / fig.png 已生成')
    print('\n权重：')
    print(wt.to_string(index=False))
    print('\n排名：')
    print(res.to_string(index=False))


def run(path, outdir='out'):
    os.makedirs(outdir, exist_ok=True)
    main(path, outdir)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'demo.csv')
