"""oplot — 生信/科研绘图与熵值法的小工具集。

每个子模块都能单独用：
    from oplot.omics import heatmap, volcano, boxplot
    from oplot.kde import kde2d, kde3d
    from oplot.entropy import entropy_weight, topsis
"""
from .omics import heatmap, volcano, boxplot
from .kde import kde2d, kde3d
from .entropy import entropy_weight, topsis
from .ml import pca, roc, violin

__version__ = '0.1.0'
__all__ = ['heatmap', 'volcano', 'boxplot', 'kde2d', 'kde3d',
           'entropy_weight', 'topsis', 'pca', 'roc', 'violin']
