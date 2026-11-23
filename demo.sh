#!/usr/bin/env bash
# 一键跑完所有示例，输出到 out/
set -e
cd "$(dirname "$0")"

# 优先用能找到 numpy 的解释器
pick_python() {
  for cand in "$PYTHON" "$HOME/.venv/pptenv/bin/python" python3 python; do
    [ -z "$cand" ] && continue
    if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import numpy,pandas,matplotlib,scipy' >/dev/null 2>&1; then
      echo "$cand"; return 0
    fi
  done
  echo "python3"; return 1
}
PY=$(pick_python) || { echo "没找到带 numpy/pandas/matplotlib/scipy 的 python"; exit 1; }
OUT=${1:-out}
mkdir -p "$OUT"

echo "用: $PY"
echo "出: $OUT"
echo

run() {
  printf '%-10s %s\n' "$1" "→ $OUT/$2"
  "$PY" -m oplot.cli "$1" "examples/$3" "$OUT" >/dev/null
}

run heatmap  heatmap.png  expression.csv
run volcano  volcano.png  deg.csv
run boxplot  boxplot.png  groups.csv
run kde      kde2d.png    points.csv
run entropy  fig.png      matrix.csv
run pca      pca.png      pca.csv
run roc      roc.png      roc.csv
run violin   violin.png   groups.csv

echo
echo "全部完成。图在 $OUT/"
ls -1 "$OUT"
