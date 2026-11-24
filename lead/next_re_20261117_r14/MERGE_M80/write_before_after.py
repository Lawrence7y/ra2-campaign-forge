# -*- coding: utf-8 -*-
"""M80: Capture AFTER state and write BEFORE_AFTER.txt."""
import os, sys, json, hashlib, datetime
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
MERGE = os.path.join(ROOT, "MERGE_M80")
FILES = {
    "coverage.tsv": os.path.join(ROOT, "COVERAGE", "coverage.tsv"),
    "PANEL.md": os.path.join(ROOT, "COVERAGE", "PANEL.md"),
}

before = json.load(open(os.path.join(MERGE, "_before_state.json"), encoding="utf-8"))
after = {}
for name, path in FILES.items():
    st = os.stat(path)
    raw = open(path, "rb").read()
    iso = datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone(datetime.timedelta(hours=8))).isoformat()
    after[name] = {
        "path": os.path.relpath(path, PROJ),
        "mtime_float": st.st_mtime,
        "mtime_iso": iso,
        "bytes": st.st_size,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    print(f"{name}: AFTER mtime={st.st_mtime!r} ({iso}) bytes={st.st_size} sha256={after[name]['sha256']}")

with open(os.path.join(MERGE, "_after_state.json"), "w", encoding="utf-8") as f:
    json.dump(after, f, ensure_ascii=False, indent=2)

L = []
L.append("M80 BEFORE_AFTER — coverage.tsv（3 行 name 更正：改第 3/4 列）与 PANEL.md（追加 M80 披露）")
L.append("记录口径：BEFORE 采集于 merge.py 之前（承接盘上状态）；AFTER 复算于 merge.py 之后。")
L.append("本机时区：Asia/Shanghai (+08:00)。")
L.append("BEFORE coverage.tsv sha256 66830c3f… 与 MERGE_M79\\BEFORE_AFTER.txt 记录的 coverage.tsv 改后 sha256 一致，确认起点无中间写者介入。")
L.append("BEFORE PANEL.md sha256 2317d26e… 与 MERGE_M79\\BEFORE_AFTER.txt 记录的 PANEL.md 改后 sha256 一致，确认起点无中间写者介入。")
L.append("本轮唯一 COVERAGE 写者：agent-265；未 git commit；未碰 R14_COMMON / STATUS_BOARD / 台账 / BOARD_ARCHIVE / HYGIENE_R11 / PROBE_746 / 任何 R4_* / D47_SURFACE（HYGIENE_R11\\rows.tsv 仅读取，未写）；改动仅限 COVERAGE\\coverage.tsv、COVERAGE\\PANEL.md 与新建 MERGE_M80 目录。")
L.append("")
for name in ("coverage.tsv", "PANEL.md"):
    b, a = before[name], after[name]
    L.append("=" * 72)
    L.append(f"FILE: COVERAGE\\{name}")
    L.append("=" * 72)
    L.append(f"  BEFORE mtime  : {b['mtime_float']}  ({b['mtime_iso']})")
    L.append(f"  BEFORE bytes  : {b['bytes']}")
    L.append(f"  BEFORE sha256 : {b['sha256']}")
    L.append(f"  AFTER  mtime  : {a['mtime_float']}  ({a['mtime_iso']})")
    L.append(f"  AFTER  bytes  : {a['bytes']}")
    L.append(f"  AFTER  sha256 : {a['sha256']}")
    L.append(f"  DELTA  bytes  : {a['bytes'] - b['bytes']:+d}")
    L.append(f"  sha256 changed: {a['sha256'] != b['sha256']}")
    L.append("")
L.append("说明：coverage.tsv 18,498 行 / 8 列 / TAB 分隔 / 无 BOM / 仅 LF / 无末尾换行，均保持；仅 3 行第 3 列（name 旧名→新名）与第 4 列（原文末尾追加 M80 名更正句）变更，第 1/2/4 列既有文字、第 5 列 grade、第 6/7/8 列逐字未动；数据行数不变。")
L.append("说明：PANEL.md 无 BOM / 仅 LF / 末尾换行保持；在 M79 披露（原 L183-186）之后、M77 并表实算说明之前新插入 M80 披露 7 行（新 L187-193）。")

with open(os.path.join(MERGE, "BEFORE_AFTER.txt"), "w", encoding="utf-8", newline="") as f:
    f.write("\n".join(L) + "\n")
print("BEFORE_AFTER.txt written, lines:", len(L))
