#!/usr/bin/env python3
"""核密度图：二维（散点+等高线+色带）与三维（曲面）。

输入 CSV：两列（x, y），或三列（x, y, z，用于三维）。
输出：kde2d.png / kde3d.png
"""
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import gaussian_kde
from skimage import measure

plt.rcParams.update({
    'font.sans-serif': ['Noto Sans CJK SC', 'Noto Sans CJK SC', 'DejaVu Sans'],
    'axes.unicode_minus': False,
    'font.size': 9,
    'axes.linewidth': 0.8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'xtick.direction': 'in', 'ytick.direction': 'in',
    'figure.dpi': 300,
})

# 蓝→白→橙（色盲友好、打印友好）
CMAP = LinearSegmentedColormap.from_list('bwo', ['#08306B', '#4292C6', '#FFFFFF', '#FDAE6B', '#A63603'])


def load(path):
    df = pd.read_csv(path)
    ncol = df.shape[1]
    if ncol < 2:
        raise SystemExit('至少两列（x, y）')
    cols = df.columns[:3] if ncol >= 3 else df.columns[:2]
    return df[cols].astype(float).values


def kde2d(pts, out='kde2d.png', n=220, bw=0.35):
    x, y = pts[:, 0], pts[:, 1]
    kde = gaussian_kde(np.vstack([x, y]), bw_method=bw)
    xi = np.linspace(x.min() - 0.1 * np.ptp(x), x.max() + 0.1 * np.ptp(x), n)
    yi = np.linspace(y.min() - 0.1 * np.ptp(y), y.max() + 0.1 * np.ptp(y), n)
    XX, YY = np.meshgrid(xi, yi)
    ZZ = kde(np.vstack([XX.ravel(), YY.ravel()])).reshape(XX.shape)

    fig, ax = plt.subplots(figsize=(3.4, 3.0))
    cf = ax.contourf(XX, YY, ZZ, levels=14, cmap=CMAP, alpha=.92)
    ax.contour(XX, YY, ZZ, levels=8, colors='white', linewidths=.45, alpha=.85)
    ax.scatter(x, y, s=5, c='black', alpha=.35, linewidths=0)
    ax.set_xlabel('X', fontsize=9)
    ax.set_ylabel('Y', fontsize=9)
    cb = fig.colorbar(cf, ax=ax, fraction=.046, pad=.03)
    cb.set_label('Density', fontsize=8)
    cb.ax.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(out, bbox_inches='tight', facecolor='white')
    print('→', out)


def kde3d(pts, out='kde3d.png', n=90, bw=0.45):
    from scipy import ndimage
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
    kde = gaussian_kde(np.vstack([x, y, z]), bw_method=bw)

    pad = 0.12
    xi = np.linspace(x.min() - pad*np.ptp(x), x.max() + pad*np.ptp(x), n)
    yi = np.linspace(y.min() - pad*np.ptp(y), y.max() + pad*np.ptp(y), n)
    zi = np.linspace(z.min() - pad*np.ptp(z), z.max() + pad*np.ptp(z), n)
    XX, YY, ZZ = np.meshgrid(xi, yi, zi, indexing='ij')
    D = kde(np.vstack([XX.ravel(), YY.ravel(), ZZ.ravel()])).reshape(XX.shape)
    D = ndimage.gaussian_filter(D, sigma=1.0)

    fig = plt.figure(figsize=(3.6, 3.2))
    ax = fig.add_subplot(111, projection='3d')

    # 两层等值面：外层淡、内层深
    for lvl, alpha, col in [(0.22, 0.13, '#9ECAE1'), (0.48, 0.26, '#4292C6')]:
        try:
            verts, faces, _, _ = measure.marching_cubes(D, level=lvl*D.max())
        except Exception:
            continue
        # marching_cubes 返回的是体素索引，映射回真实坐标
        v = verts.copy()
        v[:, 0] = xi[0] + v[:, 0]*(xi[1]-xi[0])
        v[:, 1] = yi[0] + v[:, 1]*(yi[1]-yi[0])
        v[:, 2] = zi[0] + v[:, 2]*(zi[1]-zi[0])
        mesh = Poly3DCollection(v[faces], alpha=alpha, facecolor=col, edgecolor='none')
        ax.add_collection3d(mesh)

    ax.scatter(x, y, z, s=2.5, c='#222222', alpha=0.22, linewidths=0, depthshade=False)
    ax.set_xlim(xi[0], xi[-1]); ax.set_ylim(yi[0], yi[-1]); ax.set_zlim(zi[0], zi[-1])
    ax.set_xlabel('X', fontsize=7, labelpad=-8)
    ax.set_ylabel('Y', fontsize=7, labelpad=-8)
    ax.set_zlabel('Z', fontsize=7, labelpad=-8)
    ax.tick_params(labelsize=6, pad=-3)
    ax.view_init(elev=22, azim=-56)
    fig.tight_layout()
    fig.savefig(out, bbox_inches='tight', facecolor='white')
    print('→', out)


def run(path, outdir='out'):
    import os
    os.makedirs(outdir, exist_ok=True)
    P = load(path)
    kde2d(P[:, :2], os.path.join(outdir, 'kde2d.png'))
    if P.shape[1] >= 3:
        kde3d(P, os.path.join(outdir, 'kde3d.png'))


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'demo_kde.csv'
    P = load(path)
    kde2d(P[:, :2])
    if P.shape[1] >= 3:
        kde3d(P)
