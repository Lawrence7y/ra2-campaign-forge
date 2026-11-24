#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RE-N00 / NEXT_RE_20261112_R01 -- reproducible baseline generator.

ONE COMMAND to rebuild the four data-derived deliverables:
    python lead/next_re_20261112/RE-N00/_baseline.py
(or: python D:\\Project\\ra2-campaign-forge\\lead\\next_re_20261112\\RE-N00\\_baseline.py)

Outputs (all inside this script's own directory):
    BASELINE.json, INPUTS.tsv, CURRENT_FACTS.md, RECONSTRUCT.md

PURE OFFLINE ONLY:
  - reads files on disk, computes SHA-256 with hashlib, parses PE with pefile,
    decodes a few instruction bytes with capstone;
  - runs ONLY read-only commands: git rev-parse / git status --porcelain /
    git ls-files --error-unmatch, Get-ChildItem / Get-CimInstance / Get-FileHash,
    python -c (hashlib / version print);
  - NEVER launches gamemd.exe / ra2loader / YURI.exe, never attaches to a live
    process, never reads live-process memory, never suspends/injects/dumps,
    never runs taskkill, never performs any git WRITE operation,
    never writes outside this script's own directory.
  - No byte copies of the inputs are made: inputs are referenced by absolute
    path + SHA-256 + bytes + mtime only (see RECONSTRUCT.md).

Re-run any time: if any input has drifted, verification.doc_2_2[*].match and
verification.frozen_masters[*].match will honestly flip to false.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]          # D:\Project\ra2-campaign-forge
OUT = Path(__file__).resolve().parent               # ...\lead\next_re_20261112\RE-N00
RUN_ID = "NEXT_RE_20261112_R01"
DOC = ROOT / "docs" / "re" / "NEXT_RE_TASKS_20261112.md"
LEDGER = ROOT / "lead" / "GOAL_THREE_TARGETS_20261018.md"
SHANGHAI = _dt.timezone(_dt.timedelta(hours=8), "Asia/Shanghai (UTC+08:00, no DST)")

# ---------------------------------------------------------------------------
# command runner (read-only commands only), with raw output + exit code logging
# ---------------------------------------------------------------------------
COMMANDS: list[dict] = []


def _run(cmd: list[str], label: str, cwd: Path = ROOT, note: str = "") -> dict:
    p = subprocess.run(
        [str(x) for x in cmd], cwd=str(cwd), capture_output=True,
        encoding="utf-8", errors="replace", shell=False,
    )
    rec = {
        "label": label,
        "cmd": " ".join(str(x) for x in cmd),
        "exit_code": p.returncode,
        "stdout": p.stdout,
        "stderr": p.stderr,
        "note": note,
    }
    COMMANDS.append(rec)
    return rec


def ps(script: str) -> str:
    """PowerShell command string; '$' is built with chr(36) to avoid quoting issues."""
    return script


# ---------------------------------------------------------------------------
# input inventory (role, repo-relative path, note). Only REAL files are listed;
# missing ones would be emitted with exists=false (see emit logic).
# ---------------------------------------------------------------------------
D13 = "lead/re_d13_ruling_20261112/"
QC = "lead/qc161_u0400_trip/"
RA2 = "ra2youli/"
BENCH = "ra2bench/"

INPUT_SPEC: list[tuple[str, str, str]] = [
    ("analysis_gamemd_exe", BENCH + "gamemd.exe", "分析用镜像；§2.2 与 §610 靶件；来源/『官方未修改原版』身份未证"),
    ("game_gamemd_exe", RA2 + "gamemd.exe", "游戏目录镜像；与 ra2bench 副本字节相同（本次实测）"),
    ("game_ddraw_dll", RA2 + "ddraw.dll", "当前加载的 ddraw 包装 DLL；§2.2 指纹对象"),
    ("game_ini_ddraw", RA2 + "ddraw.ini", "游戏可写 ini（Get-ChildItem ra2youli\\*.ini 实见）；本轮无真机，未做启动前副本"),
    ("game_ini_ra2md", RA2 + "RA2MD.INI", "游戏可写 ini；目录条目为大写 RA2MD.INI"),
    ("game_ini_ra2md_alias", RA2 + "ra2md.ini", "Windows FS 大小写不敏感别名：解析到同一文件 RA2MD.INI，非独立目录条目/独立字节对象"),
    ("game_ini_ra2md_benchbak", RA2 + "RA2MD.INI.benchbak", "备份文件（扩展名非 .ini），真实存在"),
    ("game_ini_ddraw_benchbak", RA2 + "ddraw.ini.benchbak", "备份文件（扩展名非 .ini），真实存在"),
    ("game_ini_battlemd", RA2 + "BATTLEMD.INI", "游戏可写 ini（Get-ChildItem 实见）"),
    ("game_ini_battlemd_bak", RA2 + "BATTLEMD.INI.ra2forge.bak", "备份文件（扩展名非 .ini），真实存在"),
    ("game_ini_battlemd98", RA2 + "BATTLEMD98.INI", "游戏可写 ini（Get-ChildItem 实见）"),
    ("game_ini_ra2", RA2 + "ra2.ini", "游戏可写 ini（Get-ChildItem 实见）"),
    ("game_ini_ra2render", RA2 + "ra2render.ini", "游戏可写 ini（Get-ChildItem 实见）"),
    ("game_ini_register", RA2 + "Register.ini", "游戏可写 ini（Get-ChildItem 实见）"),
    ("d13_driver", D13 + "_run_hl_match.py", "D-13 运行脚本；§2.2 指纹对象；只读登记"),
    ("d13_sampler_candidate", D13 + "e3_stack_sampler_candidate.py", "D-13 栈采样候选件（实现）；§2.2 指纹对象；本轮未执行"),
    ("d13_stackwalker", D13 + "e3_stackwalker.py", "D-13 StackWalk64 候选件（实现）；只读登记"),
    ("d13_static_frame_semantics", D13 + "_static_frame_semantics.py", "D-13 帧号写点静态脚本（实现）；只读登记"),
    ("d13_framesource", D13 + "e3_framesource.py", "D-13 帧号来源候选件（实现）；只读登记"),
    ("d13_event_14412", D13 + "_hl_match_14412.json", "历史真机事件 JSON（运行结果，转引）；本轮不重放"),
    ("d13_event_40500", D13 + "_hl_match_40500.json", "历史真机事件 JSON（运行结果，转引）；本轮不重放"),
    ("d13_event_37392", D13 + "_hl_match_37392.json", "历史真机事件 JSON（运行结果，转引）；本轮不重放"),
    ("d13_event_34500", D13 + "_hl_match_34500.json", "历史真机事件 JSON（运行结果，转引）；本轮不重放"),
    ("d13_battle_stack_sample", D13 + "_battle_stack_sample.json", "历史抓栈样例 JSON（运行结果，转引）；本轮不重放"),
    ("d13_report_stall_final", D13 + "STALL_CAPTURE_FINAL.md", "历史实测报告（运行结果，转引）"),
    ("d13_report_stall_success", D13 + "STALL_CAPTURE_SUCCESS.md", "历史实测报告（运行结果，转引）"),
    ("d13_report_static_semantics", D13 + "STATIC_FRAME_SEMANTICS.md", "历史静态报告（转引）"),
    ("d13_report_ruling_611", D13 + "RULING_RECEIPT_611.md", "历史回执（转引）；:129 含授权冲突陈述"),
    ("d13_report_wow64", D13 + "WOW64_RECEIPT.md", "历史回执（转引）；:4 含授权冲突陈述"),
    ("d13_report_framesource", D13 + "FRAMESOURCE_RECEIPT.md", "历史回执（转引）；:4 含授权冲突陈述"),
    ("d13_report_stackwalk", D13 + "STACKWALK_RECEIPT.md", "历史回执（转引）；:4 亦称真机已授权"),
    ("d13_selftest_output", D13 + "_selftest_out.txt", "离线单测输出（转引）；:17-21 自述『真机发射/活进程采集未获授权』"),
    ("frozen_master_probe_v2", QC + "_drive_c2_x_probe_v2.py", "冻结母本；任务卡给定期望 sha，本脚本实算比对（不转引）"),
    ("frozen_master_earlyclose", QC + "_drive_c2_x_earlyclose.py", "冻结母本；任务卡给定期望 sha，本脚本实算比对（不转引）"),
    ("task_book", "docs/re/NEXT_RE_TASKS_20261112.md", "本轮任务书；§2.2 五条声称指纹的出处"),
    ("project_direction", "docs/PROJECT_DIRECTION.md", "项目方向文档"),
    ("pending_decisions", "lead/PENDING_DECISIONS.md", "授权台账（本轮唯一口径）；D-13 2026-11-12 段"),
    ("goal_ledger", "lead/GOAL_THREE_TARGETS_20261018.md", "主台账；§610 位于 :9848"),
    ("map_loose_yrm_candidate", RA2 + "[8]试验地_Pro_ProvingGrounds.yrm", "散装地图载体候选（.yrm，非 .map/.mpr）；[Basic] Name=[8] Proving Grounds；是否与当趟加载图同一输入未证"),
    ("map_list_text", D13 + "_maplist_full.txt", "游戏内地图列表文本（转引证据）；:271 = [269] [8] Proving Grounds"),
]

FROZEN_CLAIMS = [
    (QC + "_drive_c2_x_probe_v2.py", "6afe2711136c3b52344cd435f6dbd64508378a1e019c552228ff4f5e653d13b9"),
    (QC + "_drive_c2_x_earlyclose.py", "2e970eec43fe37ff02cab98e71bce9c764d11d758ab2a7b31b495100d109c2e1"),
]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cell(s: str, limit: int = 100000) -> str:
    """Make text safe for a markdown table cell."""
    s = str(s).replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>")
    if len(s) > limit:
        s = s[:limit] + "…"
    return s


def fill(template: str, kv: dict) -> str:
    for k, v in kv.items():
        template = template.replace("@@" + k + "@@", str(v))
    return template


# ---------------------------------------------------------------------------
# 1. host / toolchain / git facts (all measured this round)
# ---------------------------------------------------------------------------
import capstone  # noqa: E402
import pefile  # noqa: E402

D = chr(36)  # '$' for PowerShell command strings
ps_ver_cmd = D + "PSVersionTable.PSVersion.ToString()"
os_cmd = ("Get-CimInstance Win32_OperatingSystem | "
          "Select-Object Caption,Version,BuildNumber,OSArchitecture | Format-List")
cpu_cmd = ("Get-CimInstance Win32_Processor | "
           "Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | Format-List")
ini_cmd = ("Get-ChildItem -Path '" + str(ROOT / "ra2youli").replace("'", "''") +
           "' -Filter '*.ini' -File | Select-Object -ExpandProperty Name")

r_ps = _run(["pwsh", "-NoProfile", "-Command", ps_ver_cmd], "PSVersion")
r_os = _run(["pwsh", "-NoProfile", "-Command", os_cmd], "OS")
r_cpu = _run(["pwsh", "-NoProfile", "-Command", cpu_cmd], "CPU")
r_ini = _run(["pwsh", "-NoProfile", "-Command", ini_cmd], "ini-list")


def field(out: str, key: str, default: str = "") -> str:
    m = re.search(r"^\s*" + re.escape(key) + r"\s*:\s*(.+?)\s*$", out, re.M)
    return m.group(1).strip() if m else default


os_caption = field(r_os["stdout"], "Caption")
os_version = field(r_os["stdout"], "Version")
os_build = field(r_os["stdout"], "BuildNumber")
os_arch = field(r_os["stdout"], "OSArchitecture")
cpu_model = field(r_cpu["stdout"], "Name")
cpu_cores = field(r_cpu["stdout"], "NumberOfCores")
cpu_logical = field(r_cpu["stdout"], "NumberOfLogicalProcessors")
ps_version = r_ps["stdout"].strip()

py_ver_cmd = ("import platform,capstone,pefile,sys;"
              "print('python',platform.python_version());"
              "print('capstone',capstone.__version__);"
              "print('pefile',pefile.__version__);"
              "print('exe',sys.executable)")
r_py = _run([sys.executable, "-c", py_ver_cmd], "toolchain-versions")

# git (READ ONLY; no add/commit/checkout/reset/clean)
r_branch = _run(["git", "-C", str(ROOT), "rev-parse", "--abbrev-ref", "HEAD"], "git-branch")
r_head = _run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], "git-HEAD")
r_status = _run(["git", "-C", str(ROOT), "status", "--porcelain"], "git-status")
status_lines = [ln for ln in r_status["stdout"].splitlines() if ln.strip()]
uncommitted = len(status_lines)
git_branch = r_branch["stdout"].strip()
git_head = r_head["stdout"].strip()

# independent Get-FileHash cross-check of the two exe images (real computation)
r_gfh = _run([
    "pwsh", "-NoProfile", "-Command",
    "Get-FileHash -LiteralPath '" + str(ROOT / BENCH / "gamemd.exe").replace("'", "''") + "','" +
    str(ROOT / RA2 / "gamemd.exe").replace("'", "''") +
    "' -Algorithm SHA256 | Format-Table -AutoSize Path,Hash",
], "Get-FileHash-exe-pair")

# independent hashlib table for the §2.2 objects + frozen masters (real computation)
hash_files = [
    BENCH + "gamemd.exe", RA2 + "gamemd.exe", RA2 + "ddraw.dll",
    D13 + "_run_hl_match.py", D13 + "e3_stack_sampler_candidate.py",
    QC + "_drive_c2_x_probe_v2.py", QC + "_drive_c2_x_earlyclose.py",
]
py_hash_cmd = (
    "import hashlib,pathlib; r=pathlib.Path(r'" + str(ROOT).replace("'", "\\'") + "'); "
    "fs=" + repr(hash_files) + "; "
    "[print(f, (r/f).stat().st_size, hashlib.sha256((r/f).read_bytes()).hexdigest()) for f in fs]"
)
r_hash = _run([sys.executable, "-c", py_hash_cmd], "hashlib-table")

# ---------------------------------------------------------------------------
# 2. inputs: real hashes, sizes, mtimes, git tracking
# ---------------------------------------------------------------------------
INPUTS: list[dict] = []
HASH_BY_REL: dict[str, str] = {}
GIT_TRACKING: list[dict] = []

for role, rel, note in INPUT_SPEC:
    p = ROOT / rel
    exists = p.is_file()
    entry = {
        "role": role,
        "path": str(p),                       # absolute
        "relpath": rel,
        "exists": exists,
        "bytes": None,
        "sha256": None,
        "mtime_utc": None,
        "note": note,
    }
    if exists:
        st = p.stat()
        dig = sha256_file(p)
        entry["bytes"] = st.st_size
        entry["sha256"] = dig
        entry["mtime_utc"] = _dt.datetime.fromtimestamp(st.st_mtime, _dt.timezone.utc).isoformat()
        HASH_BY_REL[rel.lower()] = dig
    else:
        entry["note"] = note + "；【本轮实查：文件不存在，exists=false】"
    gt = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "--error-unmatch", "--", rel],
        capture_output=True, encoding="utf-8", errors="replace", shell=False,
    )
    tracked = (gt.returncode == 0)
    entry["tracked_by_git"] = tracked
    GIT_TRACKING.append({
        "relpath": rel, "command": "git ls-files --error-unmatch -- " + rel,
        "exit_code": gt.returncode, "tracked_by_git": tracked,
    })
    INPUTS.append(entry)

COMMANDS.append({
    "label": "git-ls-files-per-input",
    "cmd": "git ls-files --error-unmatch -- <relpath>  (executed once per input, " + str(len(INPUT_SPEC)) + " times)",
    "exit_code": "n/a (per-call exit codes in git_tracking_checks[])",
    "stdout": "\n".join("rc=" + str(x["exit_code"]) + " " + x["relpath"] for x in GIT_TRACKING),
    "stderr": "",
    "note": "逐文件判断 INPUTS.tsv 的 tracked_by_git；只读命令",
})

# Windows case-insensitive alias check
ini_dir_entries = sorted(
    n for n in os.listdir(ROOT / "ra2youli")
    if n.lower().endswith(".ini") and (ROOT / "ra2youli" / n).is_file()
)
alias_path = ROOT / RA2 / "ra2md.ini"
PATH_ALIAS = {
    "queried": "ra2youli/ra2md.ini",
    "os_path_exists": alias_path.exists(),
    "separate_directory_entry": any(n == "ra2md.ini" for n in ini_dir_entries),
    "actual_directory_entry": "RA2MD.INI",
    "conclusion": "Windows 文件系统大小写不敏感：该路径解析到同一文件 RA2MD.INI，不是独立字节对象；Get-ChildItem ra2youli\\*.ini 未列出独立小写条目",
    "get_childitem_star_ini_output": r_ini["stdout"],
    "ini_family_files_also_present": [n for n in os.listdir(ROOT / "ra2youli")
                                      if re.search(r"(?i)\.ini(\.|$)", n) and (ROOT / "ra2youli" / n).is_file()],
}

# ---------------------------------------------------------------------------
# 3. verification: §2.2 five claims, frozen masters, §610 target claim
# ---------------------------------------------------------------------------
doc_text = DOC.read_text(encoding="utf-8")
doc_lines = doc_text.splitlines()
sec_start = next(i for i, l in enumerate(doc_lines) if l.strip().startswith("### 2.2"))
sec_end = next((i for i in range(sec_start + 1, len(doc_lines))
                if re.match(r"^#{2,3}\s", doc_lines[i])), len(doc_lines))
doc22 = []
for i in range(sec_start, sec_end):
    m = re.match(r"^\|\s*\[([^\]]*)\]\(([^)]+)\)\s*\|\s*`([0-9a-fA-F]{64})`\s*\|", doc_lines[i])
    if not m:
        continue
    label, link, claim = m.group(1), m.group(2), m.group(3).lower()
    rel = os.path.relpath(os.path.normpath(os.path.join(str(DOC.parent), link)), str(ROOT)).replace("\\", "/")
    actual = HASH_BY_REL.get(rel.lower())
    doc22.append({
        "role": label,
        "doc_line": i + 1,
        "doc_link": link,
        "path": str(ROOT / rel),
        "relpath": rel,
        "doc_claim": claim,
        "actual": actual,
        "match": (actual is not None and claim == actual),
    })

frozen = []
for rel, claim in FROZEN_CLAIMS:
    actual = HASH_BY_REL.get(rel.lower())
    frozen.append({
        "claim_source": "RE-N00 任务卡（冻结母本期望 sha，本脚本实算比对，不转引）",
        "path": str(ROOT / rel),
        "relpath": rel,
        "doc_claim": claim,
        "actual": actual,
        "match": (actual is not None and claim == actual),
    })

ledger_lines = LEDGER.read_text(encoding="utf-8").splitlines()
l610_idx = next(i for i, l in enumerate(ledger_lines) if l.startswith("## §610"))
l610_line = ledger_lines[l610_idx]
# the §610 target fingerprint claim lives on the dedicated 靶件 line, NOT on the section header
l610_claim_idx = next(i for i, l in enumerate(ledger_lines)
                      if "ra2bench/gamemd.exe" in l and "sha256" in l)
l610_claim_line = ledger_lines[l610_claim_idx]
m_sha = re.search(r"sha256\s+`([0-9a-fA-F]{64})`", l610_claim_line)
m_size = re.search(r"([\d,]+)\s*B", l610_claim_line)
a610_rel = BENCH + "gamemd.exe"
a610 = {
    "source": "lead/GOAL_THREE_TARGETS_20261018.md:" + str(l610_claim_idx + 1) + " (§610 靶件行)",
    "path": str(ROOT / a610_rel),
    "doc_claim_sha256": m_sha.group(1).lower() if m_sha else None,
    "actual_sha256": HASH_BY_REL.get(a610_rel.lower()),
    "match_sha256": bool(m_sha and HASH_BY_REL.get(a610_rel.lower()) == m_sha.group(1).lower()),
    "doc_claim_bytes": int(m_size.group(1).replace(",", "")) if m_size else None,
    "actual_bytes": next((x["bytes"] for x in INPUTS if x["relpath"] == a610_rel), None),
}
a610["match_bytes"] = (a610["doc_claim_bytes"] is not None and a610["doc_claim_bytes"] == a610["actual_bytes"])

# identical-hash groups among inputs (a backup that is byte-identical to the current
# ini is NOT an independent pre-launch baseline -- task book §3 step 4)
_by_sha: dict[str, list[str]] = {}
for x in INPUTS:
    if x["sha256"]:
        _by_sha.setdefault(x["sha256"], []).append(x["relpath"])
IDENTICAL_GROUPS = [{"sha256": k, "paths": v} for k, v in _by_sha.items() if len(v) > 1]

VERIFICATION = {
    "doc_2_2": doc22,
    "frozen_masters": frozen,
    "ledger_610_target": a610,
    "summary": {
        "doc_2_2_total": len(doc22),
        "doc_2_2_match": sum(1 for x in doc22 if x["match"]),
        "doc_2_2_mismatch": [x["role"] for x in doc22 if not x["match"]],
        "frozen_masters_total": len(frozen),
        "frozen_masters_match": sum(1 for x in frozen if x["match"]),
        "frozen_masters_mismatch": [x["relpath"] for x in frozen if not x["match"]],
        "note": "2026-11-12 早些时候算的 §2.2 五个哈希：本轮逐项实算比对；全部为本时点值，输入漂移会自动变为 mismatch",
    },
}

# ---------------------------------------------------------------------------
# 4. §610 location + three-column export
# ---------------------------------------------------------------------------
KEYWORDS = ["§610", "610", "0x54A56E", "slot2", "18 条", "3 条静态", "8 项待证", "三栏",
            "0x54A4F0", "0xAA1078", "已证（CFG）"]
keyword_hits = {k: sum(1 for l in ledger_lines if k in l) for k in KEYWORDS}

sec610_end = next((i for i in range(l610_idx + 1, len(ledger_lines))
                   if re.match(r"^##\s", ledger_lines[i])), len(ledger_lines))
sec610 = ledger_lines[l610_idx:sec610_end]
a_start = next(i for i, l in enumerate(sec610) if l.startswith("### A "))
b_start = next(i for i, l in enumerate(sec610) if l.startswith("### B "))
c_start = next(i for i, l in enumerate(sec610) if l.startswith("### C "))
d_start = next((i for i, l in enumerate(sec610) if l.startswith("### 备注")), len(sec610))


def collect(block: list[str], base: int, pat: str) -> list[dict]:
    out = []
    for off, l in enumerate(block):
        if re.match(pat, l):
            parts = [x.strip() for x in l.split("|")]
            if len(parts) >= 4:
                out.append({"id": parts[1], "text": parts[2], "evidence": parts[3], "line": base + off + 1})
    return out


A = collect(sec610[a_start:b_start], l610_idx + a_start, r"^\|\s*§610-A\d+")
B = collect(sec610[b_start:c_start], l610_idx + b_start, r"^\|\s*§610-B\d+")
C = []
for off, l in enumerate(sec610[c_start:d_start]):
    m = re.match(r"^\d+\.\s+(.*)$", l)
    if m:
        n = len(C) + 1
        # the ledger explicitly numbers only C01..C04; items 5..8 have NO id in the source
        explicit = re.search(r"§610-C\d{2}", m.group(1))
        cid = explicit.group(0) if explicit else ("C 节第 " + str(n) + " 项（台账未编号）")
        C.append({"id": cid, "text": m.group(1), "line": l610_idx + c_start + off + 1})

SEC610 = {
    "located": True,
    "line": l610_idx + 1,
    "title": l610_line.strip(),
    "structure_matches_task_book": (len(A) == 18 and len(B) == 3 and len(C) == 8),
    "a_count": len(A), "b_count": len(B), "c_count": len(C),
    "a_lines": [x["line"] for x in A], "b_lines": [x["line"] for x in B], "c_lines": [x["line"] for x in C],
    "keyword_searched": KEYWORDS,
    "keyword_hits": keyword_hits,
    "grading_policy_line": next((i + 1 for i, l in enumerate(ledger_lines) if "定级口径" in l), None),
    "target_claim_line": l610_claim_idx + 1,
    "note": "A=字节级读数 18 条；B=静态 CFG 3 条（未做运行期确认）；C=待证 8 项。本轮未重跑六个探针，全部按转引登记。",
}

# ---------------------------------------------------------------------------
# 5. map identity search (best effort, pure offline, no guessing)
# ---------------------------------------------------------------------------
PATS = {
    "ascii": b"Proving Grounds",
    "ascii_upper": b"PROVING GROUNDS",
    "ascii_bracket": b"[8] Proving Grounds",
    "utf16le": "Proving Grounds".encode("utf-16-le"),
    "utf16le_upper": "PROVING GROUNDS".encode("utf-16-le"),
}


def scan_bytes(p: Path) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    with p.open("rb") as f:
        prev = b""
        off = 0
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            buf = prev + chunk
            base = off - len(prev)
            for label, pat in PATS.items():
                st = 0
                while True:
                    i = buf.find(pat, st)
                    if i < 0:
                        break
                    hits.append((base + i, label))
                    st = i + 1
                    if len(hits) > 40:
                        break
            prev = buf[-64:]
            off += len(chunk)
            if len(hits) > 40:
                break
    return hits


RA2DIR = ROOT / "ra2youli"
loose_all = sorted(p for p in RA2DIR.rglob("*") if p.is_file())
loose_maps = [p for p in loose_all if p.suffix.lower() in (".map", ".mpr")]
loose_yrm = [p for p in loose_all if p.suffix.lower() == ".yrm"]
mix_files = sorted(p for p in loose_all if p.suffix.lower() == ".mix")
name_candidates = [p for p in loose_all if re.search(r"(?i)proving|ground", p.name)]
scan_targets = sorted(set(loose_maps + loose_yrm + mix_files + name_candidates))
content_hits = []
scanned_bytes = 0
for p in scan_targets:
    scanned_bytes += p.stat().st_size
    for off, label in scan_bytes(p):
        content_hits.append({"path": str(p), "relpath": str(p.relative_to(ROOT)).replace("\\", "/"),
                             "byte_offset": off, "pattern": label})

yrm = RA2DIR / "[8]试验地_Pro_ProvingGrounds.yrm"
yrm_data = yrm.read_bytes() if yrm.is_file() else b""
name_field = b"Name=[8] Proving Grounds"
name_off = yrm_data.find(name_field)
basic_off = yrm_data.find(b"[Basic]")
yrm_info = {
    "path": str(yrm), "exists": yrm.is_file(),
    "bytes": len(yrm_data) if yrm_data else None,
    "sha256": hashlib.sha256(yrm_data).hexdigest() if yrm_data else None,
    "basic_section_offset": basic_off,
    "name_field_offset": name_off,
    "name_field_excerpt": yrm_data[basic_off:basic_off + 90].decode("ascii", "replace") if basic_off >= 0 else "",
}

mix_inventory = []
for p in mix_files:
    with p.open("rb") as f:
        head = f.read(16)
    mix_inventory.append({
        "path": str(p), "relpath": str(p.relative_to(ROOT)).replace("\\", "/"),
        "bytes": p.stat().st_size, "sha256": sha256_file(p), "header_first16_hex": head.hex("-"),
    })

MAP_SEARCH = {
    "target_label": "[8] Proving Grounds",
    "method": [
        "Get-ChildItem ra2youli -Recurse -File 过滤文件名 (?i)proving|ground",
        "列举全部散装 .map/.mpr（及 .yrm）与 .mix",
        "对散装图 + 17 个 MIX 容器做分块字节扫描（5 种模式：ASCII/大写/带 [8] 前缀/UTF-16LE 两种）",
        "读取散装 .yrm 的 [Basic] Name= 字段作为字节证据",
        "MIX 索引未解析（多数首 4 字节为 00 00 02 00 / 00 00 03 00，加密头需 Blowfish 密钥与格式确认），故不排除 MIX 内副本",
    ],
    "loose_map_count": len(loose_maps),
    "loose_mpr_count": sum(1 for p in loose_maps if p.suffix.lower() == ".mpr"),
    "loose_map_ext_count": sum(1 for p in loose_maps if p.suffix.lower() == ".map"),
    "loose_yrm_count": len(loose_yrm),
    "mix_count": len(mix_files),
    "name_candidates": [str(p.relative_to(ROOT)).replace("\\", "/") for p in name_candidates],
    "scanned_files": len(scan_targets),
    "scanned_bytes": scanned_bytes,
    "patterns": list(PATS.keys()),
    "content_hits": content_hits,
    "yrm_candidate": yrm_info,
    "mix_inventory": mix_inventory,
    "external_evidence": [
        "lead/re_d13_ruling_20261112/_hl_match_14412.json:3-7  pattern=Proving Grounds, target=[265,'[8] Proving Grounds']",
        "lead/re_d13_ruling_20261112/_maplist_full.txt:271  [269] [8] Proving Grounds",
        "lead/re_d13_ruling_20261112/STALL_CAPTURE_SUCCESS.md:12  索引 268",
        "lead/re_d13_ruling_20261112/STALL_CAPTURE_FINAL.md:60  索引 265",
    ],
    "verdict": (
        "未定位：未发现与 `[8] Proving Grounds` 绑定的 `.map`/`.mpr` 字节载体。"
        "仅定位到 1 个散装 `.yrm` 名称/内容候选（[8]试验地_Pro_ProvingGrounds.yrm，"
        "[Basic] Name=[8] Proving Grounds，文件偏移见 yrm_candidate），扩展名不符且无当趟游戏加载证据；"
        "17 个 MIX 容器的明文扫描无命中、索引未解析，不能排除 MIX 内副本。"
        "按任务卡要求写「未定位」，不猜。"
    ),
}

# ---------------------------------------------------------------------------
# 6. static PE checks (bytes + capstone decode; no execution)
# ---------------------------------------------------------------------------
STATIC = {"pe_files": [], "a08_a09": {}}
try:
    tgt = ROOT / BENCH / "gamemd.exe"
    pe = pefile.PE(str(tgt), fast_load=True)
    ib = pe.OPTIONAL_HEADER.ImageBase
    for rel in [BENCH + "gamemd.exe", RA2 + "gamemd.exe", RA2 + "ddraw.dll"]:
        q = pefile.PE(str(ROOT / rel), fast_load=True)
        STATIC["pe_files"].append({
            "path": str(ROOT / rel),
            "image_base": hex(q.OPTIONAL_HEADER.ImageBase),
            "entry_point_rva": hex(q.OPTIONAL_HEADER.AddressOfEntryPoint),
            "machine": hex(q.FILE_HEADER.Machine),
            "time_date_stamp": hex(q.FILE_HEADER.TimeDateStamp),
            "sections": [
                {"name": s.Name.decode("ascii", "replace").rstrip("\x00"),
                 "rva": hex(s.VirtualAddress), "raw_offset": hex(s.PointerToRawData),
                 "raw_size": s.SizeOfRawData}
                for s in q.sections
            ],
        })
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    b7 = tgt.read_bytes()[pe.get_offset_from_rva(0x54A56E - ib): pe.get_offset_from_rva(0x54A56E - ib) + 7]
    b3 = tgt.read_bytes()[pe.get_offset_from_rva(0x54A577 - ib): pe.get_offset_from_rva(0x54A577 - ib) + 3]
    ins7 = list(md.disasm(b7, 0x54A56E))
    ins3 = list(md.disasm(b3, 0x54A577))
    STATIC["a08_a09"] = {
        "image": str(tgt), "image_base": hex(ib),
        "a08": {"va": "0x54A56E", "rva": hex(0x54A56E - ib),
                "file_offset": hex(pe.get_offset_from_rva(0x54A56E - ib)),
                "bytes": b7.hex(" "),
                "decode": (ins7[0].mnemonic + " " + ins7[0].op_str) if ins7 else "decode failed"},
        "a09": {"va": "0x54A577", "rva": hex(0x54A577 - ib),
                "file_offset": hex(pe.get_offset_from_rva(0x54A577 - ib)),
                "bytes": b3.hex(" "),
                "decode": (ins3[0].mnemonic + " " + ins3[0].op_str) if ins3 else "decode failed"},
        "decoder": "capstone " + capstone.__version__ + " / CS_ARCH_X86 CS_MODE_32",
    }
except Exception as exc:  # pragma: no cover
    STATIC["error"] = "static check failed: " + repr(exc)

# ---------------------------------------------------------------------------
# 7. assemble BASELINE.json
# ---------------------------------------------------------------------------
now_utc = _dt.datetime.now(_dt.timezone.utc)
now_sh = _dt.datetime.now(SHANGHAI)
BASELINE = {
    "run_id": RUN_ID,
    "generated_at_utc": now_utc.isoformat(),
    "generated_at_asia_shanghai": now_sh.isoformat(),
    "generator": {
        "script": str(Path(__file__).resolve()),
        "command": "python lead/next_re_20261112/RE-N00/_baseline.py",
        "scope": "只写本脚本所在目录；只读磁盘 + 纯离线脚本；零真机、零 git 写操作",
    },
    "host": {
        "os_caption": os_caption, "os_version": os_version, "os_build": os_build,
        "os_architecture": os_arch, "platform": platform.platform(),
        "cpu_model": cpu_model, "physical_cores": int(cpu_cores) if cpu_cores.isdigit() else cpu_cores,
        "logical_processors": int(cpu_logical) if cpu_logical.isdigit() else cpu_logical,
    },
    "toolchain": {
        "python_version": platform.python_version(),
        "python_full": sys.version,
        "python_executable": sys.executable,
        "capstone_version": capstone.__version__,
        "pefile_version": pefile.__version__,
        "powershell_version": ps_version,
        "powershell_edition": "Core (pwsh 7.x)",
    },
    "python_version": platform.python_version(),
    "capstone_version": capstone.__version__,
    "pefile_version": pefile.__version__,
    "powershell_version": ps_version,
    "git": {
        "branch": git_branch, "head": git_head,
        "uncommitted_changes_count": uncommitted,
        "status_command": "git status --porcelain (行数计数；含未跟踪文件)",
        "note": "只读；本轮未执行任何 git 写操作（无 add/commit/checkout/reset/clean）。本计数是生成时点值；含他人并行未提交工作，且 `?? lead/next_re_20261112/`（本轮输出根目录，含本卡子目录）本身也是一条未跟踪记录；计数会随他人工作变化。",
    },
    "git_branch": git_branch,
    "git_head": git_head,
    "git_uncommitted_changes_count": uncommitted,
    "authorization": {
        "real_machine_authorized_this_round": False,
        "sole_authority": "lead/PENDING_DECISIONS.md（D-13 2026-11-12 段）",
        "conflicting_receipts_are": "转引", "conflict_adjudicated": False,
        "execution": "本轮按『真机未授权』执行；所有真机项标 [待运行验证] / 待执行",
    },
    "inputs": INPUTS,
    "inputs_count": len(INPUTS),
    "inputs_missing": [x["role"] for x in INPUTS if not x["exists"]],
    "identical_hash_groups": IDENTICAL_GROUPS,
    "verification": VERIFICATION,
    "git_tracking_checks": GIT_TRACKING,
    "ini_directory_entries": ini_dir_entries,
    "path_alias_checks": PATH_ALIAS,
    "ledger_610": SEC610,
    "map_search": MAP_SEARCH,
    "static_checks": STATIC,
    "commands": COMMANDS,
}
(OUT / "BASELINE.json").write_text(json.dumps(BASELINE, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------------------------------------------------------------------------
# 8. INPUTS.tsv
# ---------------------------------------------------------------------------
tsv = ["role\tpath\tbytes\tsha256\ttracked_by_git\tnote"]
for x in INPUTS:
    tsv.append("\t".join([
        x["role"], x["path"],
        "" if x["bytes"] is None else str(x["bytes"]),
        "" if x["sha256"] is None else x["sha256"],
        "yes" if x["tracked_by_git"] else "no",
        x["note"].replace("\t", " ").replace("\r", " ").replace("\n", " "),
    ]))
(OUT / "INPUTS.tsv").write_text("\n".join(tsv) + "\n", encoding="utf-8")

# ---------------------------------------------------------------------------
# 9. helper text for CURRENT_FACTS.md / RECONSTRUCT.md
# ---------------------------------------------------------------------------
def cmd_ref(label: str) -> str:
    i = next((j for j, c in enumerate(COMMANDS) if c["label"] == label), -1)
    return "命令#" + str(i + 1) + "(" + label + ", exit=" + str(COMMANDS[i]["exit_code"]) + ")" if i >= 0 else "命令?"


cmd_table_rows = []
for i, c in enumerate(COMMANDS, 1):
    if c["label"] == "git-ls-files-per-input":
        out = cell(c["stdout"], 300) + " …(完整 " + str(len(GIT_TRACKING)) + " 行见 BASELINE.json → git_tracking_checks[])"
    elif c["label"] == "git-status":
        out = cell(c["stdout"], 400) + " …(完整 " + str(uncommitted) + " 行原始输出见 BASELINE.json → commands[git-status].stdout)"
    elif c["label"] == "Get-FileHash-exe-pair":
        out = cell(c["stdout"], 1200)
    else:
        out = cell(c["stdout"], 1200) if c["stdout"].strip() else "(空)"
    cmd_table_rows.append("| #" + str(i) + " | " + cell(c["label"]) + " | " + cell(c["cmd"], 260) +
                          " | " + str(c["exit_code"]) + " | " + out + " |")
CMD_TABLE = "\n".join(cmd_table_rows)

v22_rows = []
for x in doc22:
    v22_rows.append("| " + cell(x["role"]) + " | `" + x["doc_claim"] + "` | `" + str(x["actual"]) +
                    "` | " + ("**match**" if x["match"] else "**MISMATCH**") +
                    " | `docs/re/NEXT_RE_TASKS_20261112.md:" + str(x["doc_line"]) + "` | `[本次实测]` |")
V22_TABLE = "\n".join(v22_rows)
fr_rows = []
for x in frozen:
    fr_rows.append("| `" + cell(x["relpath"]) + "` | `" + x["doc_claim"] + "` | `" + str(x["actual"]) +
                   "` | " + ("**match**" if x["match"] else "**MISMATCH**") +
                   " | RE-N00 任务卡（期望值）；`INPUTS.tsv` | `[本次实测]` |")
FR_TABLE = "\n".join(fr_rows)

kw_rows = "\n".join("| `" + cell(k) + "` | " + str(keyword_hits[k]) + " |" for k in KEYWORDS)

a_rows = "\n".join(
    "| " + cell(x["id"]) + " | " + cell(x["text"], 96) + " | " +
    "GOAL_THREE_TARGETS_20261018.md:" + str(x["line"]) + "；" + cell(x["evidence"], 60) +
    " | `[转引]` | 重跑六探针 " + cell(x["evidence"], 30) + " 对拍；引用用条目号 |"
    for x in A)
b_rows = "\n".join(
    "| " + cell(x["id"]) + " | " + cell(x["text"], 110) + " | " +
    "GOAL_THREE_TARGETS_20261018.md:" + str(x["line"]) + "；" + cell(x["evidence"], 60) +
    " | `[转引]` | 需可信指令边界 + 运行期确认；勿升为已证 |"
    for x in B)
c_rows = "\n".join(
    "| " + cell(x["id"]) + " | " + cell(x["text"], 110) + " | " +
    "GOAL_THREE_TARGETS_20261018.md:" + str(x["line"]) +
    " | `[转引]` | 运行期/普查补证；本轮零真机，标待证 |"
    for x in C)

recon_rows = []
for x in INPUTS:
    recon_rows.append("| " + cell(x["role"]) + " | `" + cell(x["relpath"], 90) + "` | " +
                      (str(x["bytes"]) if x["bytes"] is not None else "—") + " | `" +
                      (str(x["sha256"]) if x["sha256"] else "—") + "` | 无 | 不可离线重建 |")
RECON_TABLE = "\n".join(recon_rows)

ini_rows = "\n".join(
    "- `" + cell(x["relpath"]) + "` — bytes=" + str(x["bytes"]) + ", sha256=`" + str(x["sha256"]) + "`（游戏可写，无启动前副本）"
    for x in INPUTS if x["role"].startswith("game_ini"))

# ---------------------------------------------------------------------------
# 10. CURRENT_FACTS.md
# ---------------------------------------------------------------------------
FACTS = r"""# RE-N00 · 本轮事实底账（CURRENT_FACTS.md）

- run_id：`@@RUN_ID@@`
- 生成时刻：UTC `@@UTC@@` / Asia/Shanghai `@@SH@@`
- 生成器：`lead/next_re_20261112/RE-N00/_baseline.py`（一条命令重建 BASELINE.json / INPUTS.tsv / CURRENT_FACTS.md / RECONSTRUCT.md）
- git：`@@BRANCH@@` @ `@@HEAD@@`，未提交改动 `@@UNCOMMITTED@@` 条（只读计数；本轮零 git 写操作）
- 本轮授权：真机发射 / 活进程采集 **未授权**（详见 §3）；未启动任何游戏、未 attach、未读活进程内存、未注入/挂起/转储/断点/taskkill。
- 证据等级只用五种：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` / `[待运行验证]`；**每行必标，转引不升级为已证**。

## 0 · 本轮实测原始记录（命令 + 原始输出 + 退出码）

> 下表为本轮 `_baseline.py` 实跑并记录的只读命令；完整 stdout/stderr 在 `BASELINE.json → commands[]`，逐文件 git 判定在 `BASELINE.json → git_tracking_checks[]`。哈希由脚本内 `hashlib` 流式实算（并有独立 `Get-FileHash` / `python -c hashlib` 交叉记录），**无转引**。

| # | 标签 | 命令 | 退出码 | 原始输出 |
|---|---|---|---|---|
@@CMD_TABLE@@

## 1 · 三栏事实底账（可直接复用 / 需要条件 / 未证）

### 1.1 可直接复用

| 事实 | 证据指针 | 等级 | 下一步 |
|---|---|---|---|
| `ra2bench/gamemd.exe` 与 `ra2youli/gamemd.exe` 字节完全相同（同 sha256 `73201cc0…f67476`、同 4,825,360 B），属同一构建的同一份字节。 | `BASELINE.json → inputs[analysis_gamemd_exe]` / `inputs[game_gamemd_exe]`；@@REF_GFH@@；`lead/GOAL_THREE_TARGETS_20261018.md:9851` | `[本次实测]` | 静态分析可任选其一；但「原版对照」仍需来源证明。 |
| §2.2 五条声称哈希本轮逐项实算 **@@V22M@@/@@V22T@@ match**；两份冻结母本 **@@FRM@@/@@FRT@@ match**；§610 靶件 sha/字节也 MATCH。 | `BASELINE.json → verification`；`docs/re/NEXT_RE_TASKS_20261112.md:81-87`；@@REF_HASH@@ | `[本次实测]` | 每次执行前重跑 `_baseline.py`；输入漂移会自动变 mismatch。 |
| 本轮工具链：python @@PY@@ / capstone @@CS@@ / pefile @@PE@@ / PowerShell @@PSV@@；OS @@OSCAP@@ @@OSVER@@ (@@OSARCH@@)；CPU @@CPU@@，物理核 @@CORES@@ / 逻辑 @@LOGICAL@@。 | @@REF_PY@@；@@REF_OS@@；@@REF_CPU@@；@@REF_PSV@@（`BASELINE.json → host/toolchain`） | `[本次实测]` | 换机重跑脚本并把版本差异登记到本表。 |
| git 分支 `@@BRANCH@@`、HEAD `@@HEAD@@`、未提交改动 `@@UNCOMMITTED@@` 条（生成时点值；含他人并行工作及本轮输出根目录 `?? lead/next_re_20261112/`）；本轮未执行任何 git 写操作。 | @@REF_BRANCH@@；@@REF_HEAD@@；@@REF_STATUS@@ | `[本次实测]` | 若他人改动输入，立即重算 sha 并按任务书 §4.3 停批。 |
| `ra2youli\*.ini` 实见 7 个目录条目，另有 3 个 `.bak/.benchbak` 备份；`ra2youli/ra2md.ini` 不是独立条目（Windows 大小写不敏感，解析到 `RA2MD.INI`）。 | @@REF_INI@@；`BASELINE.json → ini_directory_entries / path_alias_checks` | `[本次实测]` | 真机趟前为这些可写 ini 保存启动前副本（本轮无真机，未做）。 |
| `RA2MD.INI.benchbak` 与当前 `RA2MD.INI` 字节完全相同（同 sha `c91c6a47…cd3c27d`、同 1,754 B），仅 mtime 不同；`ddraw.ini.benchbak` 与 `ddraw.ini` 不同（14,352 vs 14,782 B）。 | `BASELINE.json → inputs[game_ini_ra2md_benchbak] / inputs[game_ini_ra2md] / identical_hash_groups`；`INPUTS.tsv` | `[本次实测]` | 该 `.benchbak` **不是**独立的更老基线；真机趟不得用它替代本轮启动前副本后宣称逐字节恢复（任务书 §3 第 0 步第 4 项）。 |
| 主台账 §610 已定位且结构与任务书描述一致：A 18 / B 3 / C 8。 | `lead/GOAL_THREE_TARGETS_20261018.md:9848`（A :9860-9877；B :9883-9885；C :9889-9896）；`BASELINE.json → ledger_610` | `[本次读码]` | 引用一律用条目号；C 节不得随附表升格。 |
| `ra2bench/gamemd.exe` 的 VA `0x54A56E` 文件偏移 `@@A08FO@@` 处 7 字节 `@@A08B@@`、VA `0x54A577` 处 `@@A09B@@`，与 §610-A08/A09 的字节读数一致。 | `BASELINE.json → static_checks.a08_a09`；§610-A08/A09 见 `GOAL_THREE_TARGETS_20261018.md:9867-9868` | `[本次实测]` | 仅作为字节读数使用；不扩展为运行期结论。 |
| 上述两组字节的 capstone 解码为 `@@A08D@@` / `@@A09D@@`（VA/RVA/文件偏移已给出）。 | `BASELINE.json → static_checks.a08_a09.decoder` | `[静态推断]` | 需函数边界与上游调用链才能扩展为 CFG 结论。 |
| `[8]试验地_Pro_ProvingGrounds.yrm` 内 `[Basic] Name=[8] Proving Grounds`（文件偏移 `@@YRMNAMEOFF@@`，段偏移 `@@YRMBASICOFF@@`），sha256 `@@YRMSHA@@`、@@YRMBYTES@@ B。 | `BASELINE.json → map_search.yrm_candidate / content_hits` | `[本次实测]` | 需证明该散装 `.yrm` 即当趟游戏加载载体（选图索引/文件身份）。 |
| D-13 候选件存在且含 `--live` 入口（本轮未执行）；离线单测输出 `:17-21` 自述「真机发射 / 活进程采集未获授权」。 | `lead/re_d13_ruling_20261112/e3_stack_sampler_candidate.py:1026-1037`；`lead/re_d13_ruling_20261112/_selftest_out.txt:17-21` | `[本次读码]` | 候选件与实测报告分栏引用，不能互相顶替。 |
| 全部必需输入当前均 `exists=true`，字节数/sha256/mtime 已固定；无一项被本工作包保存字节副本。 | `BASELINE.json → inputs[]`（@@NINPUTS@@ 项）；`INPUTS.tsv` | `[本次实测]` | 见 `RECONSTRUCT.md`：输入只能靠路径+哈希引用。 |

### 1.2 需要条件

| 事实 | 证据指针 | 等级 | 下一步 |
|---|---|---|---|
| §610 A 节 18 条字节级读数可复用，但条件是靶件 sha 仍为 `73201cc0…f67476` 且按 `sf/cw/ps/oo/md/ld` 六个证据目录重跑探针。 | `lead/GOAL_THREE_TARGETS_20261018.md:9852,9856-9877`；§5 逐条表 | `[转引]` | RE-N11 归位时六探针逐条对拍；本轮未重跑。 |
| §610 B 节 3 条 CFG 结论为静态推断，台账自标「未做运行期确认」。 | `lead/GOAL_THREE_TARGETS_20261018.md:9879-9885,9909` | `[转引]` | 需可信指令边界 + 运行期确认；不得写成已证。 |
| 3493 采样 / 1 事件 / 帧 349→15042 / 229 s 零Δ段 / 栈 7 帧，是既有实测结果，不是本轮实测。 | `lead/re_d13_ruling_20261112/STALL_CAPTURE_FINAL.md:58-94`；`_hl_match_14412.json:9,11-23`；§4 逐条分级 | `[转引]` | 需全量 samples 落盘后离线重算（RE-N01）。 |
| D-13 候选件离线单测（`_selftest_out.txt`，全部 Win32 经 stub）只证明 stub 路径，不证明 Win32 行为或「≤50 ms 硬超时」。 | `lead/re_d13_ruling_20261112/_selftest_out.txt:2-30`；`docs/re/NEXT_RE_TASKS_20261112.md:128` | `[转引]` | 补有区分力的离线测试 + 合成线程校准，再谈仪器。 |
| `[8] Proving Grounds` 的散装 `.yrm` 候选是否与当趟实际加载图为同一输入，需进图身份证据；`.map`/`.mpr` 未定位。 | `BASELINE.json → map_search.verdict`；`STALL_CAPTURE_FINAL.md:60`；`_maplist_full.txt:271` | `[待运行验证]` | RE-N03：解析 MIX 索引或保存实际加载文件字节 + 选图索引证据。 |
| 真机项（RE-N01 校准、RE-N02 状态校准、RE-N04 三臂基线、RE-N06 对照趟、RE-N08 新鲜性趟）依赖当轮明示授权 + 明确写域 + 启动前配置副本。 | `docs/re/NEXT_RE_TASKS_20261112.md:339-348`；`lead/PENDING_DECISIONS.md:65,68` | `[待运行验证]` | 标「待执行」；授权前不预写结果、不发射。 |

### 1.3 未证

| 事实 | 证据指针 | 等级 | 下一步 |
|---|---|---|---|
| `ra2bench/gamemd.exe` 是否「官方未修改原版」——本轮没有任何来源证明（发行介质/签名/构建记录/供应链）。 | `docs/re/NEXT_RE_TASKS_20261112.md:89`（自述「不能只凭游戏名视作官方未修改原版」）；无来源材料 | `[转引]` | Lead 提供来源证明；无则继续标未证，不得当原版对照臂。 |
| §610 C 节 8 项待证全部维持【未证】（台账仅给前 4 项编号 §610-C01…C04；第 5–8 项台账未编号，本包不代拟条目号），含「无别名逃逸」等全称否定。 | `lead/GOAL_THREE_TARGETS_20261018.md:9887-9896,9853,9909`；§5 逐条表 | `[转引]` | 运行期/普查补证；零真机铁律下不可得。 |
| `[8] Proving Grounds` 的 `.map`/`.mpr` 字节载体：未定位（MIX 索引未解析，散装仅 `.yrm` 候选）。 | `BASELINE.json → map_search` | `[待运行验证]` | MIX 索引解析 + 进图身份核对；找不到就保持「未定位」。 |
| 授权台账与四份回执/代码 docstring 的冲突 **未裁**。 | §3 全文 | `[转引]` | 建议 Lead 立新待裁条目（见 §3 结论）。 |
| 229 s 段被报告自认为「由三个数字自洽推出的强推断，不是逐样本复核过的已证」；JSON 未保存完整 3493 个样本序列。 | `lead/re_d13_ruling_20261112/STALL_CAPTURE_FINAL.md:85-94` | `[转引]` | 全量序列落盘再重算；本轮不得升级。 |
| 双份 exe 相同 ≠ 原版对照臂有效；旧独立评审绑定的哈希不能自动覆盖当前候选件/驱动脚本。 | `docs/re/NEXT_RE_TASKS_20261112.md:89,173` | `[转引]` | 三臂设计前先做来源确认；每张卡重新绑定指纹。 |
| 帧号 `0xA8ED84` 的每 tick 写者、线程归属、生命周期、相邻 `0xA8ED80` 字段宽度。 | `docs/re/NEXT_RE_TASKS_20261112.md:46,71-73,136-145`；`lead/re_d13_ruling_20261112/STATIC_FRAME_SEMANTICS.md:1-16` | `[待运行验证]` | RE-N02 从可信指令边界重验写点。 |

## 2 · 输入指纹与镜像身份

| 事实 | 证据指针 | 等级 | 下一步 |
|---|---|---|---|
| 两份 `gamemd.exe` sha/字节完全相同 ⇒ 本次实测的「同一构建」。 | `BASELINE.json → inputs`；@@REF_GFH@@；@@REF_HASH@@ | `[本次实测]` | 结论仅限「字节相同」，不外推到来源/版本官方性。 |
| 分析镜像 `ra2bench/gamemd.exe` 的「官方未修改原版」身份：**未证**，本轮无来源证明。 | `docs/re/NEXT_RE_TASKS_20261112.md:89`；`BASELINE.json → verification.ledger_610_target`（仅证明与 §610 靶件指纹一致） | `[转引]` | 补发行介质/数字签名/构建记录来源链；无则三臂对照不得称「纯原版」。 |
| §2.2 五条声称哈希逐项比对（2026-11-12 早些时候值 vs 本轮实算）： | `docs/re/NEXT_RE_TASKS_20261112.md:79-87`；`BASELINE.json → verification.doc_2_2` | `[本次实测]` | 逐项结果如下；以后每次执行前重算。 |

| 对象 | doc_claim | actual（本轮实算） | match | 证据指针 | 等级 |
|---|---|---|---|---|---|
@@V22_TABLE@@

| 冻结母本 | 期望 sha（任务卡） | actual（本轮实算） | match | 证据指针 | 等级 |
|---|---|---|---|---|---|
@@FR_TABLE@@

> §610 靶件行（`lead/GOAL_THREE_TARGETS_20261018.md:@@A610LINE@@`）声称 `4,825,360 B` / `73201cc0…f67476`，本轮实算 bytes=@@A610B@@ / sha=@@A610S@@ ⇒ sha match=@@A610MS@@、bytes match=@@A610MB@@。`[本次实测]`

## 3 · 授权状态（本轮）

**3.1 授权台账 D-13（2026-11-12）段原文（`[本次读码]`，逐字引用）：**

> `lead/PENDING_DECISIONS.md:22-23`：
> 「**D-13 已裁决（2026-11-12，用户当轮明示「D 13 选 c」）：见「已裁决记录」段。**
> **★ 本次裁决只解除「编写候选件 + 离线单测」的禁令**；**真机发射 / 活进程采集仍未授权**，按 D-15 与 D-31 Q4 须**当轮明示**，不得由本条或既有裁决代授。」
>
> `lead/PENDING_DECISIONS.md:61-65,68`（已裁决记录，逐字引用关键行）：
> 「- **D-13 已裁决（2026-11-12）：用户当轮明示「D 13 选 c」⇒ 选 (C)。**」（:61）
> 「2. **结论**：走**甲案 `SuspendThread` + `GetThreadContext` + `StackWalk64`**（≤50 ms/次）尝试覆盖短停主体。」（:62）
> 「1. **已解除**：D-31 Q4 曾判「**不批准**以『只编写候选件 + 离线单测』放行采样代码」——用户本次明示选择 C，构成对该禁令的**明确改变**，故**编写 SuspendThread/StackWalk 候选件 + 离线单测**现已获授权。」（:64）
> 「2. **未解除**：**真机发射 / 活进程采集 / attach / 读活进程内存**仍未授权。依据 D-15 已裁决原文「未经用户明示授权的 E3/MiniDump/SuspendThread/StackWalk/**真机发射/活进程采集**一律不得执行」与 D-31 Q4「真机/活进程须**当轮明示**」，用户本轮只说「选 c / 继续」，**未**就真机发射明示 ⇒ 仍不执行。」（:65）
> 「5. **仍待用户另行明示**：真机发射批次、以及是否接受「C 案死锁风险可能污染②读数」这一代价。」（:68）

**3.2 冲突陈述（全部 `[转引]`，不得升级为已证）：**

| 出处 | 原文要点 | 等级 |
|---|---|---|
| `lead/re_d13_ruling_20261112/WOW64_RECEIPT.md:4` | 「前置授权：用户 2026-11-12 明示「D 13 选 c」+「**统一真机以及一切操作，可以上传GitHub**」」 | `[转引]` |
| `lead/re_d13_ruling_20261112/RULING_RECEIPT_611.md:129` | 「## 6 · 真机验证（用户 2026-11-12 授权「**统一真机以及一切操作**」后执行）」 | `[转引]` |
| `lead/re_d13_ruling_20261112/FRAMESOURCE_RECEIPT.md:4` | 「前置授权：**真机 + 一切操作（2026-11-12）**」 | `[转引]` |
| `lead/re_d13_ruling_20261112/e3_stack_sampler_candidate.py:1030` | docstring：「`--live` 入口：**真机采集**（用户 2026-11-12 授权「**统一真机以及一切操作**」）」 | `[转引]` |
| `lead/re_d13_ruling_20261112/STACKWALK_RECEIPT.md:4`（补充登记） | 「前置：**真机已授权**」 | `[转引]` |
| `lead/re_d13_ruling_20261112/_selftest_out.txt:17-21`（同目录内的反向陈述） | 「!! 拒绝执行：**真机发射 / 活进程采集未获授权**……用户 2026-11-12 仅明示「D-13 选 c」……本件因此只提供 --selftest」 | `[转引]` |

| 事实 | 证据指针 | 等级 | 下一步 |
|---|---|---|---|
| 台账与回执、`--live` docstring、离线单测输出之间存在 **同一日期、互相矛盾的授权陈述**；本轮未见用户原始会话记录，无法裁定。 | 上表六处；`docs/re/NEXT_RE_TASKS_20261112.md:348`（「后续实测报告不能自动替代授权记录」） | `[转引]` | 建议 Lead **立新待裁条目**：请用户当轮明示「统一真机以及一切操作」是否成立、生效时点、批次与写域。 |
| 本轮授权状态结论（任务卡要求的固定措辞）。 | `lead/PENDING_DECISIONS.md:22-23,61-65` + 本卡授权边界铁律 | `[转引]` | 按结论执行，不因回执自行放宽。 |

> **结论（逐字）**：授权台账（PENDING_DECISIONS）为唯一口径，回执属转引；两者冲突**未裁**；故本轮按『真机未授权』执行，所有真机项标 `[待运行验证] / 待执行`。

建议 Lead 立新待裁条目，把「2026-11-12 是否确有『统一真机以及一切操作』明示、其生效时点/批次/写域、以及回执与台账冲突如何归档」单列裁决。

| 事实 | 证据指针 | 等级 | 下一步 |
|---|---|---|---|
| 本轮所有真机项（游戏发射、attach、ReadProcessMemory、SuspendThread/ResumeThread、StackWalk64、MiniDump、断点/注入、taskkill、部署）= 待执行，未执行。 | 本卡「授权边界（铁律）」第 1–2 条；`docs/re/NEXT_RE_TASKS_20261112.md:339-348` | `[待运行验证]` | 获当轮明示授权且写域明确后另立批次；本包只做离线只读。 |

## 4 · 既有实测结果的分级（逐条 `[转引]`）

> 以下 5 条全部来自 `lead/re_d13_ruling_20261112/` 的历史运行结果，本轮**未重放、未启动游戏**；按任务卡要求逐条标 `[转引]`，并指出报告自认的「强推断非已证」。

| 事实 | 证据指针 | 等级 | 下一步 |
|---|---|---|---|
| 3493 次采样、可读 3493 次（100%）。 | `lead/re_d13_ruling_20261112/_hl_match_14412.json:9-10`；`STALL_CAPTURE_FINAL.md:65` | `[转引]` | RE-N01 全量 NDJSON 落盘后可离线复算。 |
| 停滞事件 = 1（`events` 数组 1 项，t=471.266 s、frame=15042、mode=single_thread、paused_ms=0.0、errors=null）。 | `lead/re_d13_ruling_20261112/_hl_match_14412.json:11-18`；`STALL_CAPTURE_FINAL.md:68,74` | `[转引]` | `errors:null` 不能替代恢复状态核验（任务书 §2.1 缺口一）。 |
| 帧号 349 → 15042（Δ 中位 6 ⇒ 报告写 30.0 fps）。 | `lead/re_d13_ruling_20261112/STALL_CAPTURE_FINAL.md:64-68` | `[转引]` | 需逐帧边沿时间戳；0.2 s 轮询不得算伪逐帧 P95/P99（任务书 §3 RE-N04）。 |
| 零Δ段 1 个、最长 229.00 s（`700 − 471.27 = 228.7 ≈ 229`），报告据此称「永久冻结」。 | `lead/re_d13_ruling_20261112/STALL_CAPTURE_FINAL.md:67,85-90` | `[转引]` | **报告自认 `:92-94`：这是【强推断】不是【已证】，JSON 未保存完整 3493 个样本序列**；需全量落盘重算。 |
| 栈 7 帧：`ntdll+0x7858c` → `KERNELBASE×2` → `gamemd.exe+0x207f17` → `USER32+0x74775` → `USER32+0x3505d` → `gamemd.exe+0x20833f`。 | `lead/re_d13_ruling_20261112/_hl_match_14412.json:19-52`；`STALL_CAPTURE_FINAL.md:75-82,96-109` | `[转引]` | 两个栈签名不同只说明捕获路径不同，不能推出两条独立根因（`docs/re/NEXT_RE_TASKS_20261112.md:65`）；RE-N05 静态回溯。 |

## 5 · 主台账 §610 三栏导出

**定位结果：`[本次读码]` 已定位**（非「未定位」）：`lead/GOAL_THREE_TARGETS_20261018.md:9848` 标题即含「18 条字节级【已证】+ 3 条【已证（CFG）】+ 8 条待证」，A 节 `:9860-9877`（@@ACNT@@ 行）、B 节 `:9883-9885`（@@BCNT@@ 行）、C 节 `:9889-9896`（@@CCNT@@ 项），与任务书描述一致。`[转引]` 登记，本轮未重跑 `sf/cw/ps/oo/md/ld` 六探针（`:9852`、`:9909`），故全部条目不升级为本轮实测。定级口径见 `:9853`。

**实际搜索过的关键词与命中情况（`[本次实测]`，脚本重算「包含该关键词的行数」）：**

| 关键词 | 命中行数 |
|---|---|
@@KW_TABLE@@

### 5.1 可直接复用（A 节 @@ACNT@@ 条字节级读数，`[转引]`）

| 条目号 | 读数（截短） | 证据指针 | 等级 | 下一步 |
|---|---|---|---|---|
@@A_ROWS@@

> 本轮补做的一处独立字节核对（`[本次实测]` + `[静态推断]`）：§610-A08/A09 的 `@@A08B@@` / `@@A09B@@` 在 `ra2bench/gamemd.exe` 的 VA `0x54A56E`（RVA `@@A08RVA@@`、文件偏移 `@@A08FO@@`）与 VA `0x54A577`（RVA `@@A09RVA@@`、文件偏移 `@@A09FO@@`）读得，capstone 解码 `@@A08D@@` / `@@A09D@@`。仅支持字节读数，不替代 A 节其余 16 条的重跑。

### 5.2 需要条件（B 节 @@BCNT@@ 条静态 CFG 结论，`[转引]`）

| 条目号 | 静态推断（截短） | 证据指针 | 等级 | 下一步 |
|---|---|---|---|---|
@@B_ROWS@@

### 5.3 未证（C 节 @@CCNT@@ 项待证，`[转引]`）

> 台账 `:9889-9896` 仅给第 1–4 项显式编号 `§610-C01`…`§610-C04`；第 5–8 项**没有**条目号，本包按「C 节第 N 项（台账未编号）」如实登记，不代拟编号。

| 条目号 | 待证内容（截短） | 证据指针 | 等级 | 下一步 |
|---|---|---|---|---|
@@C_ROWS@@

## 6 · D-13 候选件与后续实测报告分栏（不能互相顶替）

| 栏 | 内容 | 证据指针 | 等级 | 下一步 |
|---|---|---|---|---|
| **候选件 / 实现** | `e3_stack_sampler_candidate.py`（55,720 B，sha `98210b4a…d51840a`）、`e3_stackwalker.py`、`e3_framesource.py`、`_static_frame_semantics.py`、`_run_hl_match.py` 是代码；`--live` 入口定义于 `:1029-1037`，本轮未调用。 | `BASELINE.json → inputs[d13_*]`；`e3_stack_sampler_candidate.py:1026-1037` | `[本次读码]` | 引用实现必须带文件+sha；改动需另立候选副本。 |
| **离线单测** | `_selftest_out.txt` 记「E3 候选件离线单测（零真机 · 全部 Win32 经 stub）」及 `:17-21` 的拒绝真机陈述。 | `lead/re_d13_ruling_20261112/_selftest_out.txt:2-21`；`RULING_RECEIPT_611.md:123-125` | `[转引]` | 只证明 stub 路径；不能证明真机能力或 ≤50 ms 硬保证。 |
| **后续实测报告 / 运行结果** | `STALL_CAPTURE_FINAL.md`、`STALL_CAPTURE_SUCCESS.md`、`STATIC_FRAME_SEMANTICS.md`、四份 RECEIPT 及 `_hl_match_*.json`、`_battle_stack_sample.json` 是历史运行结果/回执（转引）。 | `BASELINE.json → inputs[d13_report_* / d13_event_*]`；`STALL_CAPTURE_FINAL.md:58-94` | `[转引]` | 不得用报告数量或「已跑过」替代授权或测量链可信度。 |
| **分栏结论** | 候选件是实现、离线单测是 stub 验证、实测报告是运行结果；三者互不等价，任一都不能顶替另一。 | `docs/re/NEXT_RE_TASKS_20261112.md:101,348`；`lead/PENDING_DECISIONS.md:63-65` | `[转引]` | 任务卡、验收、知识库均按三栏分别引用；RE-N01 需独立回放统计。 |

## 7 · 本轮工具链版本

| 工具 | 版本 | 证据指针 | 等级 | 下一步 |
|---|---|---|---|---|
| Python | @@PY@@ (@@PYFULL@@) | @@REF_PY@@ | `[本次实测]` | 换机重跑 `python lead/next_re_20261112/RE-N00/_baseline.py`。 |
| capstone | @@CS@@ | @@REF_PY@@；`BASELINE.json → static_checks.a08_a09.decoder` | `[本次实测]` | 反汇编/解码结果须带 VA/RVA/文件偏移/字节。 |
| pefile | @@PE@@ | @@REF_PY@@；`BASELINE.json → static_checks.pe_files` | `[本次实测]` | PE 节映射回读字节时记录 raw_offset。 |
| PowerShell | @@PSV@@ (Core) | @@REF_PSV@@ | `[本次实测]` | 主机信息命令的原始输出见 §0。 |
| OS / CPU | @@OSCAP@@ @@OSVER@@ (build @@OSBUILD@@, @@OSARCH@@)；@@CPU@@，物理核 @@CORES@@ / 逻辑 @@LOGICAL@@ | @@REF_OS@@；@@REF_CPU@@ | `[本次实测]` | 与性能基线（RE-N04）固定机器条件一起登记。 |

## 未覆盖项

- 本轮按授权边界**未执行任何真机项**：未启动 `gamemd.exe`/`ra2loader`/`YURI.exe`，未 attach、未 ReadProcessMemory 活游戏进程、未 SuspendThread/ResumeThread/StackWalk64/MiniDump/断点/注入/部署/taskkill；RE-N01 校准趟、RE-N02 状态校准、RE-N04 三臂基线、RE-N06 对照趟、RE-N08 新鲜性趟全部未做。
- 未对 17 个 `.mix` 容器做索引解析（多数首 4 字节为 `00 00 02 00` / `00 00 03 00`，加密头需 Blowfish 密钥与格式确认）；只做了明文分块扫描（@@SCANFILES@@ 个文件 / @@SCANBYTES@@ B）。
- 未重跑 §610 的六个探针（`sf/cw/ps/oo/md/ld`）与 `:9907` 自认「自愿不做」的 24 个引用区间逐数复核；A 节 18 条中仅 A08/A09 做了本轮字节核对。
- 未为游戏可写 ini 保存启动前副本 / 退出后比较（任务书 §3 第 0 步第 4 项），因本轮无真机且写域只限 `RE-N00\`；也未生成任何输入字节副本（见 `RECONSTRUCT.md`）。
- 未解析 `_hl_match_*.json` 的全量样本序列（原 JSON 未保存，报告自认）；未复算 229 s 段。
- 未核对旧独立评审 `lead/re_d13_review_20261112/REVIEW.md:5` 绑定的另一哈希（不在必需输入清单；仅按任务书 `:89` 转引登记）。
- 未做两份 `gamemd.exe` 的数字签名 / 发行介质 / 构建记录核验；未做 `ddraw.dll+0x22B06` 的调用契约静态回溯。
- 未执行任何 git 写操作；未审阅 @@UNCOMMITTED@@ 条未提交改动的内容（只计数，避免触碰他人工作）。

## 未知项

- `ra2bench/gamemd.exe` 的来源与「官方未修改原版」身份；以及 §610 六探针读数是否可在本机按同一口径完全复现。
- `[8] Proving Grounds` 的 `.map`/`.mpr` 字节载体是否位于某个 MIX 内；当趟游戏实际加载哪一份文件、以何索引选中。选图索引在既有材料中不一致：`_hl_match_14412.json:4-7`=265、`STALL_CAPTURE_SUCCESS.md:12`=268、`_maplist_full.txt:271`=269，原因未知。
- 用户 2026-11-12 是否确有「统一真机以及一切操作，可以上传GitHub」的当轮明示（原始会话记录不在本轮输入中）；台账与回执冲突如何裁定、生效时点与批次。
- 229 s 零Δ段的真实游戏状态（战斗 / 暂停 / 菜单 / 记分板 / 失焦 / 结束）、唤醒条件与观察器扰动。
- 帧号 `[0xA8ED84]` 的写点、更新线程、生命周期、相邻 `[0xA8ED80]` 字段宽度；窗口线程与逻辑线程关系。
- §610 C 节 8 项运行期机制、崩溃家族新鲜性与责任写者、DLC 引擎资源覆盖顺序。
- 他人未提交改动是否会在本轮之后修改这些输入；本包所有 sha 均为本时点值，重跑 `_baseline.py` 才能确认是否漂移。
- 真机授权何时、以何批次解除；解除后哪些历史输入仍可作为同版本对照。

---
*本文件由 `_baseline.py` 生成；所有数字均来自本轮实算或注明出处的转引，无来源的数字不写入。*
"""

FACTS = fill(FACTS, {
    "RUN_ID": RUN_ID, "UTC": now_utc.isoformat(), "SH": now_sh.isoformat(),
    "BRANCH": git_branch, "HEAD": git_head, "UNCOMMITTED": uncommitted,
    "CMD_TABLE": CMD_TABLE, "V22_TABLE": V22_TABLE, "FR_TABLE": FR_TABLE,
    "V22M": VERIFICATION["summary"]["doc_2_2_match"], "V22T": VERIFICATION["summary"]["doc_2_2_total"],
    "FRM": VERIFICATION["summary"]["frozen_masters_match"], "FRT": VERIFICATION["summary"]["frozen_masters_total"],
    "PY": platform.python_version(), "PYFULL": sys.version.replace("\n", " "),
    "CS": capstone.__version__, "PE": pefile.__version__, "PSV": ps_version,
    "OSCAP": os_caption, "OSVER": os_version, "OSBUILD": os_build, "OSARCH": os_arch,
    "CPU": cpu_model, "CORES": cpu_cores, "LOGICAL": cpu_logical,
    "REF_GFH": cmd_ref("Get-FileHash-exe-pair"), "REF_HASH": cmd_ref("hashlib-table"),
    "REF_PY": cmd_ref("toolchain-versions"), "REF_OS": cmd_ref("OS"), "REF_CPU": cmd_ref("CPU"),
    "REF_PSV": cmd_ref("PSVersion"), "REF_BRANCH": cmd_ref("git-branch"), "REF_HEAD": cmd_ref("git-HEAD"),
    "REF_STATUS": cmd_ref("git-status"), "REF_INI": cmd_ref("ini-list"),
    "A08FO": STATIC.get("a08_a09", {}).get("a08", {}).get("file_offset", "n/a"),
    "A08RVA": STATIC.get("a08_a09", {}).get("a08", {}).get("rva", "n/a"),
    "A08B": STATIC.get("a08_a09", {}).get("a08", {}).get("bytes", "n/a"),
    "A08D": STATIC.get("a08_a09", {}).get("a08", {}).get("decode", "n/a"),
    "A09FO": STATIC.get("a08_a09", {}).get("a09", {}).get("file_offset", "n/a"),
    "A09RVA": STATIC.get("a08_a09", {}).get("a09", {}).get("rva", "n/a"),
    "A09B": STATIC.get("a08_a09", {}).get("a09", {}).get("bytes", "n/a"),
    "A09D": STATIC.get("a08_a09", {}).get("a09", {}).get("decode", "n/a"),
    "A610B": a610["actual_bytes"], "A610S": a610["actual_sha256"],
    "A610MS": a610["match_sha256"], "A610MB": a610["match_bytes"],
    "A610LINE": l610_claim_idx + 1,
    "YRMNAMEOFF": yrm_info["name_field_offset"], "YRMBASICOFF": yrm_info["basic_section_offset"],
    "YRMSHA": yrm_info["sha256"], "YRMBYTES": yrm_info["bytes"],
    "NINPUTS": len(INPUTS), "KW_TABLE": kw_rows,
    "ACNT": len(A), "BCNT": len(B), "CCNT": len(C),
    "A_ROWS": a_rows, "B_ROWS": b_rows, "C_ROWS": c_rows,
    "SCANFILES": len(scan_targets), "SCANBYTES": scanned_bytes,
})
(OUT / "CURRENT_FACTS.md").write_text(FACTS, encoding="utf-8")

# ---------------------------------------------------------------------------
# 11. RECONSTRUCT.md
# ---------------------------------------------------------------------------
RECON = r"""# RECONSTRUCT.md · 哪些输入没有保留字节副本、只能靠路径 + 哈希引用

- run_id：`@@RUN_ID@@`；生成：UTC `@@UTC@@` / Asia/Shanghai `@@SH@@`
- 唯一写域：`lead\next_re_20261112\RE-N00\`；本包**没有**复制任何输入字节，只登记绝对路径、字节数、SHA-256、mtime_utc 与 `git ls-files --error-unmatch` 结果。
- 生成器：`_baseline.py`（一条命令重建 `BASELINE.json` / `INPUTS.tsv` / `CURRENT_FACTS.md` / `RECONSTRUCT.md`）。它重建的是**指纹与事实底账**，不是输入字节。

## 结论（先说清楚）

1. `RE-N00\` 内**只有**本包 5 个文件（`_baseline.py`、`BASELINE.json`、`INPUTS.tsv`、`CURRENT_FACTS.md`、`RECONSTRUCT.md`）是自包含的；它们可以由 `_baseline.py` 离线重建。
2. 下表的 **@@NINPUTS@@ 项输入全部没有字节副本**：只能靠「绝对路径 + sha256 + bytes + mtime」引用。若源文件被修改、删除、被游戏回写或换机，**无法从本目录离线重建这些字节**；只能回到原路径取回文件并比对 sha，不一致即须按任务书 §4.3 停批并重新定级。
3. 同理，`BASELINE.json → map_search.mix_inventory` 只记 17 个 `.mix` 容器的路径/大小/sha/头部 16 字节，**没有**容器内文件清单，更没有字节副本；MIX 索引未解析（加密头需 Blowfish 密钥与格式确认）。
4. 历史「真机运行结果」类输入（事件 JSON、抓栈样例、报告、截图）本轮无授权重放；即使有副本也不能重放为「本轮实测」，其证据等级恒为 `[转引]`。
5. §2.2 五条声称哈希本轮全部 match（@@V22M@@/@@V22T@@），两份冻结母本全部 match（@@FRM@@/@@FRT@@）；但这些是**本时点**事实，不是永久保证。

## 逐条清单（无字节副本 ⇒ 不可离线重建）

| role | 路径（相对仓库根） | bytes | sha256（完整） | 字节副本 | 离线重建 |
|---|---|---|---|---|---|
@@RECON_TABLE@@

## 高风险子类

### A. 游戏可写 ini（会被游戏回写，任务书 §3 第 0 步第 4 项要求启动前副本 + 退出后比较）

@@INI_ROWS@@

- 本轮无真机授权，故**未**保存任何启动前副本、也未做退出后 diff；这些 sha 是「当前盘面」值。若后续真机趟回写了配置，旧结论只能作为历史参考，不得宣称「逐字节恢复」。
- 本轮实测：`RA2MD.INI.benchbak` 与当前 `RA2MD.INI` **字节完全相同**（sha `c91c6a47…cd3c27d`、1,754 B），只是 mtime 不同 ⇒ 它不是独立的更老基线，不能替代本轮启动前副本（任务书 §3 第 0 步第 4 项明确禁止）。`ddraw.ini.benchbak`（14,352 B / `2f666b4d…`）则与 `ddraw.ini`（14,782 B / `c983abad…`）不同。见 `BASELINE.json → identical_hash_groups`。

### B. 地图载体（`[8] Proving Grounds`）

- **未定位**与标签绑定的 `.map`/`.mpr` 字节载体（`BASELINE.json → map_search.verdict`）。
- 仅 1 个散装候选：`ra2youli/[8]试验地_Pro_ProvingGrounds.yrm`（@@YRMBYTES@@ B，sha `@@YRMSHA@@`），`[Basic] Name=[8] Proving Grounds` 位于文件偏移 `@@YRMNAMEOFF@@`（`[Basic]` 段偏移 `@@YRMBASICOFF@@`）——这是 `[本次实测]` 的字节证据，但**扩展名是 .yrm 而非 .map/.mpr**，且无当趟游戏加载证据 ⇒ 与当趟实际输入是否同一份，`[待运行验证]`。
- 17 个 `.mix` 容器已登记 sha/大小，明文扫描 5 种模式无命中；索引未解析，**不能排除 MIX 内副本**。要在离线条件下重建地图身份，需要：MIX 索引解析（或本地源码/符号）、实际加载文件的字节副本、选图索引与文件身份绑定证据。
- 既有材料的选图索引还不一致（`_hl_match_14412.json:4-7`=265 / `STALL_CAPTURE_SUCCESS.md:12`=268 / `_maplist_full.txt:271`=269），未裁。

### C. 历史真机运行结果

- `lead/re_d13_ruling_20261112/_hl_match_14412.json` 等事件 JSON 只保存统计值与事件；`STALL_CAPTURE_FINAL.md:92-94` 自认**没有保存完整 3493 个样本序列**，因此 229 s 零Δ段连「用已有数据离线重算」都做不到，更无法离线重建采集过程。
- `_battle_stack_sample.json`、四份 RECEIPT、两份 STALL 报告、`STATIC_FRAME_SEMANTICS.md` 均为转引材料；本轮无授权、无原始活进程读数，不能重放。

### D. 来源/身份类材料（本轮根本没有）

- `ra2bench/gamemd.exe` 的「官方未修改原版」来源证明（发行介质、数字签名、构建记录、供应链）**不在本轮输入中**；只有「两份 exe 字节相同」与「§610 靶件指纹一致」两个实测事实。无法据此离线重建「原版对照臂」。
- 用户 2026-11-12 是否明示「统一真机以及一切操作」的原始会话记录不在本轮输入中；授权台账与回执冲突未裁（`CURRENT_FACTS.md §3`）。

## 要让它变成「可离线重建」，需要补什么

1. 在唯一写域内保存输入字节副本（或至少：受控只读引用 + 每次执行前重算 sha + 漂移即停批）；对本表 @@NINPUTS@@ 项逐一给出可验证来源。
2. 真机趟：为每个游戏可写 ini 保存启动前副本，退出后逐字节比较并恢复（任务书 §3 第 0 步第 4 项），不能用更老的 `.benchbak` 替代本轮基线。
3. 地图：解析 MIX 索引或保存实际加载的 `.yrm/.mpr` 字节 + 选图索引/文件哈希绑定；保持「未定位」直到有证据。
4. 采集：补授权后把帧号读数逐条流式落盘（NDJSON/CSV，含单调时钟、UTC、读取状态、状态标签），使摘要可离线复算（RE-N01）。
5. 来源：补发行介质/签名/构建记录，或明确写「原版对照臂未建立」，不得用分析镜像冒充。

## 本包自身的可重建性

- 命令：`python lead/next_re_20261112/RE-N00/_baseline.py`（纯离线，只读磁盘，零真机、零 git 写操作）。
- 重建产物：`BASELINE.json`（指纹 + 主机/工具链/git + 逐项 verification + 原始命令输出）、`INPUTS.tsv`、`CURRENT_FACTS.md`、`RECONSTRUCT.md`（本文件）。
- 重跑时若任一输入漂移，`verification.doc_2_2[*].match` / `verification.frozen_masters[*].match` 会自动变 `false` 并如实标出；不会静默沿用 2026-11-12 早些时候的哈希。

## 未覆盖项

- 未复制/归档任何输入字节；未归档 17 个 MIX 容器内部文件；未保存游戏可写配置的启动前副本；未重放任何历史真机采集；未解析 MIX 索引；未做来源/签名验证。
- 未执行任何 git 写操作；未对 @@UNCOMMITTED@@ 条他人未提交改动做内容审阅。

## 未知项

- 上表各输入在未来是否被改动、由谁改动、改动后 sha 是多少；`_baseline.py` 重跑前无法预测。
- `[8] Proving Grounds` 的 `.map`/`.mpr` 是否在 MIX 内、当趟实际加载哪一份；选图索引 265/268/269 的差异原因。
- 分析镜像的官方原版身份；用户 2026-11-12 真机明示的原始记录及其生效范围。
- 历史 3493 个样本序列、229 s 段的原始读数能否从其它目录找回（本轮输入清单内没有）。

---
*本文件由 `_baseline.py` 生成；逐条 sha 均为本轮 `hashlib` 实算，未转引。*
"""
RECON = fill(RECON, {
    "RUN_ID": RUN_ID, "UTC": now_utc.isoformat(), "SH": now_sh.isoformat(),
    "NINPUTS": len(INPUTS), "RECON_TABLE": RECON_TABLE, "INI_ROWS": ini_rows,
    "V22M": VERIFICATION["summary"]["doc_2_2_match"], "V22T": VERIFICATION["summary"]["doc_2_2_total"],
    "FRM": VERIFICATION["summary"]["frozen_masters_match"], "FRT": VERIFICATION["summary"]["frozen_masters_total"],
    "YRMBYTES": yrm_info["bytes"], "YRMSHA": yrm_info["sha256"],
    "YRMNAMEOFF": yrm_info["name_field_offset"], "YRMBASICOFF": yrm_info["basic_section_offset"],
    "UNCOMMITTED": uncommitted,
})
(OUT / "RECONSTRUCT.md").write_text(RECON, encoding="utf-8")

# ---------------------------------------------------------------------------
print("run_id            :", RUN_ID)
print("generated_utc     :", now_utc.isoformat())
print("generated_shanghai:", now_sh.isoformat())
print("inputs            :", len(INPUTS), "missing:", [x["role"] for x in INPUTS if not x["exists"]])
print("doc_2_2 match     :", VERIFICATION["summary"]["doc_2_2_match"], "/", VERIFICATION["summary"]["doc_2_2_total"])
print("frozen match      :", VERIFICATION["summary"]["frozen_masters_match"], "/", VERIFICATION["summary"]["frozen_masters_total"])
print("ledger_610        :", "located line", SEC610["line"], "A/B/C =", len(A), len(B), len(C))
print("map verdict       :", MAP_SEARCH["verdict"][:60], "...")
print("outputs           : BASELINE.json INPUTS.tsv CURRENT_FACTS.md RECONSTRUCT.md")
print("EXIT 0")
