#!/bin/bash
# t628 侧采集：把 R17 逆向成果的文本类文件打成 tar.gz 到 stdout。
# 由本机 tools/t628_sync.ps1 通过 ssh stdin 传入执行。
# 口径（与 .gitignore / 本机过滤一致）：
#   - 只收文本结论与脚本：md py tsv txt json sh
#   - 排除写前备份（*.bak* / SUPERSEDED / *.before_* / *.broken_* / R17_LEAD_BASELINE）
#   - 排除证据大件（EVIDENCE/ _audit/）
#   - 排除单文件 >= 1 MB
#   - 排除 Windows 保留设备名（com1..9 / lpt1..9 / con / prn / aux / nul）
set -euo pipefail

ROOT=/home/t628/projects/ra2-campaign-forge
LIST=/tmp/t628_sync_list.$$.txt
trap 'rm -f "$LIST"' EXIT

cd "$ROOT"

{
  # 五件套无条件收（体积豁免）：结论台账是本库核心交付物，
  # GOAL_THREE_TARGETS 已达 4.8 MB，若被 1 MB 阈值挡住则永远同步不到。
  for f in ./lead/next_re_20261117_r14/R14_COMMON.md \
           ./lead/next_re_20261117_r14/STATUS_BOARD.md \
           ./lead/next_re_20261117_r14/BOARD_ARCHIVE.md \
           ./lead/next_re_20261117_r14/COMPACT_STATE.md \
           ./lead/LEAD_LOCK \
           ./lead/GOAL_THREE_TARGETS_20261018.md ; do
    [ -f "$f" ] && echo "$f"
  done | sed 's|^\./||'

  find ./lead -type f \
    \( -name '*.md' -o -name '*.py' -o -name '*.tsv' -o -name '*.txt' \
       -o -name '*.json' -o -name '*.sh' \) \
    -size -1048576c \
    ! -path '*R17_LEAD_BASELINE*' \
    ! -path '*/EVIDENCE/*' \
    ! -path '*/_audit/*' \
    ! -name '*.bak*' \
    ! -name '*SUPERSEDED*' \
    ! -name '*.before_*' \
    ! -name '*.broken_*' \
    ! -name 'com[0-9]*' \
    ! -name 'lpt[0-9]*' \
    ! -name 'con.*' \
    ! -name 'prn.*' \
    ! -name 'aux.*' \
    ! -name 'nul.*' \
    2>/dev/null || true

  # 各轮次产物目录（_r100 .. _r199）
  find ./_r1[0-9][0-9] -type f \
    \( -name '*.md' -o -name '*.py' -o -name '*.tsv' -o -name '*.txt' -o -name '*.json' \) \
    -size -1048576c \
    ! -name '*.pkl' ! -name '*.pyc' \
    ! -name 'com[0-9]*' ! -name 'lpt[0-9]*' \
    2>/dev/null || true

  # 仓库根级说明文档
  find . -maxdepth 1 -type f -name '*.md' -size -1048576c 2>/dev/null || true
} | sed 's|^\./||' | sort -u > "$LIST"

COUNT=$(wc -l < "$LIST")
echo "[remote] files=$COUNT" >&2

if [ "$COUNT" -eq 0 ]; then
  echo "[remote] nothing to send" >&2
  exit 0
fi

tar czf - -T "$LIST"
