"""命令行入口：oplot <命令> <输入.csv> [输出目录]"""
import sys
import os

def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        print("""命令：
  heatmap   expression.csv     行=基因，列=样本
  volcano   deg.csv            列名含 log2FC 和 pvalue/padj
  boxplot   groups.csv         列名含 group 和 value
  kde       points.csv         两列(x,y) 或 三列(x,y,z)
  entropy   matrix.csv         第一列=方案名，其余列=指标
  pca       matrix.csv         行=样本，列=特征
  roc       scores.csv         两列 y_true(0/1) 与 y_score
  violin    groups.csv         列名含 group 和 value

例：
  oplot heatmap examples/expression.csv out/
  oplot kde     examples/points.csv      out/
  oplot entropy examples/matrix.csv      out/
""")
        return 0

    cmd = argv[0]
    src = argv[1] if len(argv) > 1 else None
    outdir = argv[2] if len(argv) > 2 else 'out'
    if not src:
        print(f"{cmd}: 缺少输入文件"); return 1
    os.makedirs(outdir, exist_ok=True)

    if cmd == 'heatmap':
        from .omics import heatmap
        heatmap(src, os.path.join(outdir, 'heatmap.png'))
    elif cmd == 'volcano':
        from .omics import volcano
        volcano(src, os.path.join(outdir, 'volcano.png'))
    elif cmd == 'boxplot':
        from .omics import boxplot
        boxplot(src, os.path.join(outdir, 'boxplot.png'))
    elif cmd == 'kde':
        from .kde import run
        run(src, outdir)
    elif cmd == 'entropy':
        from .entropy import run
        run(src, outdir)
    elif cmd == 'pca':
        from .ml import run_pca
        run_pca(src, outdir)
    elif cmd == 'roc':
        from .ml import run_roc
        run_roc(src, outdir)
    elif cmd == 'violin':
        from .ml import run_violin
        run_violin(src, outdir)
    else:
        print(f"未知命令: {cmd}"); return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
