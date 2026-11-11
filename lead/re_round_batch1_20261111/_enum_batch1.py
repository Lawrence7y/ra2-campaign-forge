# -*- coding: utf-8 -*-
"""批次1取证枚举脚本（只读既有件；仅在本写域内新建输出文件）。

实跑命令（Windows/PowerShell，绝对路径 + 隔离模式 + UTF-8）：
    python -I -X utf8 D:\\Project\\ra2-campaign-forge\\lead\\re_round_batch1_20261111\\_enum_batch1.py

行为：
  * 无 _fp_verify.flag：BASELINE，写 _fp_baseline.json 基线、_enum_batch1_stdout.txt（stdout 同步落盘）。
  * 有 _fp_verify.flag：VERIFY，写 _fp_check.txt（前后指纹比对 PASS/FAIL）、_enum_batch1_stdout_run2.txt。
  * 既有件一律以 'rb' 只读打开，指纹一律 hashlib.sha256 实算；零真机、零 attach、零进程注入。
"""
import os
import re
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

WDIR = Path(__file__).resolve().parent
LEAD = WDIR.parent
ROOT = LEAD.parent
assert WDIR.name == "re_round_batch1_20261111", "写域校验失败: %s" % WDIR
assert (LEAD / "re_round_disposition_20261111" / "DISPOSITION.md").is_file(), "DISPOSITION.md 缺失"

BATCH1 = [
    "re_crashwriter_static_20261110",
    "slot2_fullscan_20261111",
    "playerctrl_semantics_20261111",
    "re_loadbench_diff_20261110",
    "re_map_preset_decode_20261110",
]
CROSS = [
    "re_chain_synthesis_20261111",
    "slot2_fullscan_20261111",
    "re_orphan_owners_20261110",
]
FP_DIRS = [
    "re_crashwriter_static_20261110",
    "slot2_fullscan_20261111",
    "playerctrl_semantics_20261111",
    "re_loadbench_diff_20261110",
    "re_map_preset_decode_20261110",
    "re_chain_synthesis_20261111",
    "re_orphan_owners_20261110",
    "re_round_disposition_20261111",
    "stale_pass_20261109",
]

LINES = []


def emit(s=""):
    LINES.append(str(s))


def sha256_of(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stat_of(p):
    st = os.stat(p)
    utc = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    local = datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(timespec="seconds")
    return {
        "bytes": st.st_size,
        "mtime_epoch": st.st_mtime,
        "mtime_utc": utc,
        "mtime_local": local,
        "mtime_ns": st.st_mtime_ns,
        "sha256": sha256_of(p),
    }


def rel(p):
    return p.as_posix()


def read_text(p, encoding="utf-8"):
    with open(p, "r", encoding=encoding, errors="replace") as f:
        return f.read()


def numbered():
    return "\n".join("L%04d| %s" % (i + 1, ln) for i, ln in enumerate(LINES)) + "\n"


BASELINE = WDIR / "_fp_baseline.json"
FLAG = WDIR / "_fp_verify.flag"
# 两跑协议：无 flag -> BASELINE（写基线 + stdout 落盘）；造 flag 后复跑 -> VERIFY（前后比对 + _fp_check.txt）
MODE = "VERIFY" if (FLAG.exists() and BASELINE.exists()) else "BASELINE"

# ---------------------------------------------------------------- 头部
emit("=" * 78)
emit("批次1取证枚举 · 实跑输出（python -I -X utf8 <绝对路径>）")
emit("=" * 78)
emit("脚本绝对路径 : %s" % WDIR.joinpath("_enum_batch1.py").as_posix())
emit("仓库根       : %s" % ROOT.as_posix())
emit("唯一写域     : %s" % WDIR.as_posix())
emit("运行模式     : %s" % MODE)
emit("运行时刻     : %s" % datetime.now().astimezone().isoformat(timespec="seconds"))
emit("铁律         : 既有件只读(rb)/r；无进程启动、无 attach、无 hook、无采样、无 dump")
emit("指纹算法     : hashlib.sha256 逐块实算（1 MiB chunk）")
emit("")

# ------------------------------------------------- STEP1: MD Top-10 解析
md_path = LEAD / "re_round_disposition_20261111" / "DISPOSITION.md"
md_lines = read_text(md_path).splitlines()
emit("[STEP1-A] DISPOSITION.md §5 Top-10 表 —— 由脚本正则解析，非手抄")
emit("  解析规则: 行首 '| **N** | `目录名` |'")
top10 = []
for idx, ln in enumerate(md_lines, start=1):
    m = re.match(r"^\|\s*\*\*(\d+)\*\*\s*\|\s*`([^`]+)`\s*\|(.*)$", ln)
    if m:
        rank = int(m.group(1))
        name = m.group(2)
        rest = m.group(3).strip()
        top10.append((rank, name, idx, rest))
        emit("  DISPOSITION.md:L%04d | rank=%d | %s | %s" % (idx, rank, name, rest[:110]))
emit("  Top-10 解析条数 = %d" % len(top10))
emit("")

emit("[STEP1-B] DISPOSITION.md §5 mermaid 第一批 P0 / 第二批 P1 / 第三批 P2 原文行")
for idx, ln in enumerate(md_lines, start=1):
    if re.search(r'R\d+\["|subgraph P[012]', ln):
        emit("  DISPOSITION.md:L%04d | %s" % (idx, ln.strip()))
emit("")

emit("[STEP1-C] DISPOSITION.md §6 第一批路线图原文行（L164-L169 区段含 Top-1..Top-5 与同步登记 3 轮）")
for idx, ln in enumerate(md_lines, start=1):
    if 164 <= idx <= 169:
        emit("  DISPOSITION.md:L%04d | %s" % (idx, ln.strip()))
emit("")

emit("[STEP1-D] DISPOSITION.md §1 静态逆向轮点名行 / 入账数量行 / 附录X降级行")
for idx, ln in enumerate(md_lines, start=1):
    if idx in (18, 21, 250, 256, 264, 268, 272) or (247 <= idx <= 272 and re.search(r"降级|未验|正确表述|不受影响", ln)):
        emit("  DISPOSITION.md:L%04d | %s" % (idx, ln.strip()[:180]))
emit("")

# ------------------------------------------------- STEP1: CSV 建议批次解析
csv_path = LEAD / "re_round_disposition_20261111" / "DISPOSITION.csv"
csv_lines = read_text(csv_path, encoding="utf-8-sig").splitlines()
emit("[STEP1-E] DISPOSITION.csv 全表结构 + 「第一批」行（由 csv 模块解析，非手抄）")
emit("  CSV 总行数(含表头) = %d" % len(csv_lines))
emit("  CSV 表头 = %s" % csv_lines[0])
import csv as _csv
rows = list(_csv.DictReader(csv_lines))
emit("  CSV 数据行数 = %d" % len(rows))
emit("  CSV 是否存在 Top-10/排序列 = %s" % ("是" if any("top" in k.lower() or "排序" in k for k in rows[0].keys()) else "否（无排名列，仅建议批次列）"))
batch_col = "建议批次"
first_batch_rows = []
for lineno, row in enumerate(rows, start=2):
    if "第一批" in (row.get(batch_col) or ""):
        first_batch_rows.append((lineno, row["目录名"], row[batch_col]))
emit("  CSV 中「第一批」行数 = %d" % len(first_batch_rows))
for lineno, name, b in first_batch_rows:
    emit("  DISPOSITION.csv:L%04d | %s | %s" % (lineno, name, b))
emit("")
emit("[STEP1-F] Top-10 逐条 ↔ CSV「建议批次」映射（差异如实列出，不择一）")
top10_names = [n for _, n, _, _ in top10]
for rank, name, mdline, _rest in top10:
    hit = [(ln, r) for ln, r in enumerate(rows, start=2) if r["目录名"] == name]
    if hit:
        ln, r = hit[0]
        emit("  Top-%d %-36s MD:L%04d  CSV:L%04d  类别=%s 判定=%s 批次=%s"
             % (rank, name, mdline, ln, r["类别"], r["判定"], r[batch_col]))
    else:
        emit("  Top-%d %-36s MD:L%04d  CSV=未找到" % (rank, name, mdline))
fb_names = [n for _, n, _ in first_batch_rows]
emit("  CSV 第一批但不在 MD Top-10 的轮次 = %s" % ", ".join(n for n in fb_names if n not in top10_names))
emit("  MD Top-10 但 CSV 非第一批的轮次 = %s"
     % ", ".join(r["目录名"] for r in rows if r["目录名"] in top10_names and "第一批" not in (r.get(batch_col) or "")))
emit("")

# ------------------------------------------------- STEP2: 5 轮目录全文件枚举
emit("[STEP2-A] 第一批 5 轮「全部文件」清单（相对路径 + 字节数 + mtime + sha256）")
emit("  字段: rel_repo = 相对仓库根; rel_round = 相对该轮目录; B=bytes; mtime 给 UTC 与本地; sha256=hashlib 实算")
round_files = {}
for d in BATCH1:
    base = LEAD / d
    fs = sorted([p for p in base.rglob("*") if p.is_file()], key=lambda x: x.as_posix())
    round_files[d] = fs
    emit("  ---- 轮次 %s : 文件数=%d ----" % (d, len(fs)))
    for p in fs:
        s = stat_of(p)
        emit("    %s | rel_round=%s | B=%d | mtime_utc=%s | mtime_local=%s | sha256=%s"
             % (rel(p.relative_to(ROOT)), rel(p.relative_to(base)), s["bytes"], s["mtime_utc"],
                s["mtime_local"], s["sha256"]))
emit("")

# ------------------------------------------------- STEP2: 交叉核对目录文件枚举
emit("[STEP2-B] 交叉核对目录（3 份后续/旁证件）文件清单")
for d in CROSS:
    base = LEAD / d
    fs = sorted([p for p in base.rglob("*") if p.is_file()], key=lambda x: x.as_posix())
    emit("  ---- %s : 文件数=%d ----" % (d, len(fs)))
    for p in fs:
        s = stat_of(p)
        emit("    %s | B=%d | mtime_utc=%s | sha256=%s"
             % (rel(p.relative_to(ROOT)), s["bytes"], s["mtime_utc"], s["sha256"]))
emit("")

# ------------------------------------------------- 既有件指纹总表
fp = {}
for d in FP_DIRS:
    base = LEAD / d
    if not base.is_dir():
        continue
    for p in sorted([x for x in base.rglob("*") if x.is_file()], key=lambda x: x.as_posix()):
        key = rel(p.relative_to(ROOT))
        fp[key] = stat_of(p)
emit("[FP] 本次取证涉及的全部既有件指纹总表（hashlib.sha256 实算；共 %d 件）" % len(fp))
for k in sorted(fp):
    s = fp[k]
    emit("    %s | B=%d | mtime_ns=%d | sha256=%s" % (k, s["bytes"], s["mtime_ns"], s["sha256"]))
emit("")

# ------------------------------------------------- 与 DISPOSITION.md §9 已登记指纹比对
emit("[FP-§9] 与 DISPOSITION.md §9 / 附录X 已登记 sha256 逐条比对（外部既有件，先于本任务存在）")
recorded = {}
for idx, ln in enumerate(md_lines, start=1):
    for m in re.finditer(r"`([^`]+)`[：:]\s*([\d,]+)\s*B[，,]\s*sha256=`([0-9a-f]{64})`", ln):
        recorded[m.group(1)] = (int(m.group(2).replace(",", "")), m.group(3), idx)
    for m in re.finditer(r"\|\s*`([^`]+)`\s*\|\s*([\d,]+)\s*\|\s*`([0-9a-f]{64})`", ln):
        recorded[m.group(1)] = (int(m.group(2).replace(",", "")), m.group(3), idx)
emit("  §9/附录X 解析到已登记指纹条数 = %d" % len(recorded))
for path in sorted(recorded):
    rec_b, rec_h, ln = recorded[path]
    p = ROOT / path
    if p.is_file():
        cur = stat_of(p)
        emit("    %s | 登记处=DISPOSITION.md:L%04d | 登记B=%d 实算B=%d B匹配=%s | 登记sha=%s 实算sha=%s sha匹配=%s"
             % (path, ln, rec_b, cur["bytes"], "是" if rec_b == cur["bytes"] else "否",
                rec_h, cur["sha256"], "是" if rec_h == cur["sha256"] else "否"))
    else:
        emit("    %s | 登记处=DISPOSITION.md:L%04d | 文件不存在(未验)" % (path, ln))
emit("")

# ------------------------------------------------- 输出 / 复核
# 注意：numbered() 必须在所有 emit() 之后计算，保证落盘文件与真实 stdout 逐字节一致。
if MODE == "BASELINE":
    emit("[MODE=BASELINE] 将写 _fp_baseline.json（首跑基线）与 _enum_batch1_stdout.txt（stdout 同步落盘）")
else:
    emit("[MODE=VERIFY] 将写 _fp_check.txt 与 _enum_batch1_stdout_run2.txt")
    with open(BASELINE, "r", encoding="utf-8") as f:
        base = json.load(f)["fp"]
    emit("[MODE=VERIFY] 前后两次指纹逐件比对（size / mtime_ns / sha256）")
    ok = 0
    bad = 0
    for k in sorted(set(list(base.keys()) + list(fp.keys()))):
        b = base.get(k)
        c = fp.get(k)
        if b is None or c is None:
            emit("    %s | 状态=新增/缺失(需人工确认)" % k)
            bad += 1
            continue
        same = (b["bytes"] == c["bytes"] and b["mtime_ns"] == c["mtime_ns"] and b["sha256"] == c["sha256"])
        emit("    %s | B %d->%d | mtime_ns %d->%d | sha %s -> %s | 判定=%s"
             % (k, b["bytes"], c["bytes"], b["mtime_ns"], c["mtime_ns"], b["sha256"][:12], c["sha256"][:12],
                "PASS 未改动" if same else "FAIL 已变化"))
        ok += 1 if same else 0
        bad += 0 if same else 1
    emit("  汇总: PASS=%d FAIL/异常=%d 比对件数=%d" % (ok, bad, ok + bad))
    emit("  结论: %s" % ("本任务全过程未修改任何既有件（在所测 %d 件范围内）" % (ok + bad) if bad == 0 else "存在变化项，需复核"))

OUT = numbered()
if MODE == "BASELINE":
    with open(WDIR / "_enum_batch1_stdout.txt", "w", encoding="utf-8", newline="\n") as f:
        f.write(OUT)
    with open(BASELINE, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"created": datetime.now().astimezone().isoformat(timespec="seconds"), "fp": fp}, f,
                  ensure_ascii=False, indent=1)
else:
    with open(WDIR / "_fp_check.txt", "w", encoding="utf-8", newline="\n") as f:
        f.write(OUT)
    with open(WDIR / "_enum_batch1_stdout_run2.txt", "w", encoding="utf-8", newline="\n") as f:
        f.write(OUT)

sys.stdout.write(OUT)
sys.stdout.flush()
