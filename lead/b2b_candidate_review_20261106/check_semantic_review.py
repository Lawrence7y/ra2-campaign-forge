#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""check_semantic_review.py — B2b 候选语义复审交付件机械门禁（只读，只用标准库）。

运行方式（仓库根 + 隔离模式，参数为脚本自身路径）:
    cd D:/Project/ra2-campaign-forge
    python -I -X utf8 lead/b2b_candidate_review_20261106/check_semantic_review.py \
        lead/b2b_candidate_review_20261106/check_semantic_review.py

检查项：
1) 以下 6 件交付件都存在且非空:
     lead/b2b_candidate_review_20261106/CANDIDATE_SEMANTIC_REVIEW.md
     lead/b2b_candidate_review_20261106/_review_probe.py
     lead/b2b_candidate_review_20261106/_review_probe_out.txt
     lead/b2b_candidate_review_20261106/_test_rerun_out.txt
     lead/b2b_candidate_review_20261106/_gate_rerun_out.txt
     lead/b2b_candidate_review_20261106/review/SEMANTIC_REVIEW_AUDIT.md
2) 判定书头部含 4 个不同 64 位 hex 与 4 个字节数；
3) 含 ^verdict:\\s*(PASS|BLOCKED)\\s*$ 一行（必须恰好一行）；
4) 含五个小节标题（状态矩阵对照 / 调用传参核对 / 输出字段核对 /
   F/E 分离核对 / 范围限制核对）；
5) 含「## 阻断项」「## 未验」「## 证据等级说明」三个小节，
   且「## 未验」正文非空；
6) _test_rerun_out.txt 含 PASS= 与 FAIL=；_gate_rerun_out.txt 含 9 或 PASS；
7) review/SEMANTIC_REVIEW_AUDIT.md 含 checkedEveryRow: true、noOverreach: true；
8) 一致性：若 verdict=PASS，则「## 阻断项」小节正文必须含「无」
   且不含具体阻断条目（脚本粗筛，规则见 BLOCK_ITEM_HINTS）。

退出码：
  0 = PASS
  1 = 内容不合格（逐条打印原因；含「文件存在但 0 字节 / 仅空白」）
  2 = 文件缺失
脚本只读：全程只做 stat / read_text / read_bytes，不写任何文件。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Windows 控制台防御性 UTF-8 输出（与同仓 check_candidate.py 一致）
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ---------------------------------------------------------------- 路径解析
# 优先用命令行参数（脚本自身路径）定位；参数缺失时退回 __file__。
if len(sys.argv) > 1 and sys.argv[1].endswith(".py"):
    _script_path = Path(sys.argv[1]).resolve()
else:
    _script_path = Path(__file__).resolve()

BASE = _script_path.parent
if BASE.name != "b2b_candidate_review_20261106":
    fallback = Path.cwd() / "lead" / "b2b_candidate_review_20261106"
    if fallback.is_dir():
        BASE = fallback.resolve()

ROOT = BASE.parent.parent  # lead/ 的上一级 = 仓库根
if not (ROOT / "lead" / "b2b_candidate_review_20261106").is_dir():
    ROOT = Path.cwd()

REVIEW_DIR = ROOT / "lead" / "b2b_candidate_review_20261106"

# 相对仓库根的交付件清单（与 ask 给的路径逐字一致）
DELIVERY_FILES: list[tuple[str, str]] = [
    ("verdict",   "lead/b2b_candidate_review_20261106/CANDIDATE_SEMANTIC_REVIEW.md"),
    ("probe_py",  "lead/b2b_candidate_review_20261106/_review_probe.py"),
    ("probe_out", "lead/b2b_candidate_review_20261106/_review_probe_out.txt"),
    ("test_out",  "lead/b2b_candidate_review_20261106/_test_rerun_out.txt"),
    ("gate_out",  "lead/b2b_candidate_review_20261106/_gate_rerun_out.txt"),
    ("audit",     "lead/b2b_candidate_review_20261106/review/SEMANTIC_REVIEW_AUDIT.md"),
]
PATHS = {key: ROOT / rel for key, rel in DELIVERY_FILES}

# ---------------------------------------------------------------- 判据常量
# 判定书头部：文件开头到第一条 verdict 行之前（verdict 行是 §0 头部的天然界标）。
# 找不到 verdict 行时退回「第一个 ## 1 小节之前」，再退回前 120 行。
HEX64_RE = re.compile(r"\b[0-9a-fA-F]{64}\b")
BYTES_RE = re.compile(r"\b\d[\d,]*(?:\.\d+)?\s*B\b")
VERDICT_LINE_RE = re.compile(r"^verdict:\s*(PASS|BLOCKED)\s*$")
VERDICT_ANY_RE = re.compile(r"^\s*verdict\s*:", re.IGNORECASE)
H2_HEAD_RE = re.compile(r"^##\s+(.*?)\s*$")
ANY_HEAD_RE = re.compile(r"^#{1,6}\s+")

FIVE_SECTIONS = [
    "状态矩阵对照",
    "调用传参核对",
    "输出字段核对",
    "F/E 分离核对",
    "范围限制核对",
]
THREE_SECTIONS = ["阻断项", "未验", "证据等级说明"]

AUDIT_KEYS = ["checkedEveryRow: true", "noOverreach: true"]

# 检查 8 的「具体阻断条目」粗筛规则：(正则, 说明)。
# 粗筛 = 机械扫结构特征，不做语义判断；命中任一即视为存在具体阻断条目。
BLOCK_ITEM_HINTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^\s*#{3,}\s+\S"),
     "出现三级及以上小标题（疑似逐条列出的阻断子项）"),
    (re.compile(r"\b(?:B|C)-\d+\b"),
     "出现条目编号（如 B-1 / C-2）"),
    (re.compile(r"\b[\w./\\-]+\.(?:py|md|txt|json|diff|yaml|yml):\d+"),
     "出现「文件:行」证据引用"),
    (re.compile(r"关闭所需证据|后果\s*[:：]|\bBLOCKED\b"),
     "出现「关闭所需证据 / 后果 / BLOCKED」条目字段"),
]
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)(.*)$")
# 列表条目超过此长度且不含「无」→ 视为具体条目（粗筛阈值）
LIST_ITEM_LEN = 24


def exact_h2_body(lines: list[str], name: str) -> list[str] | None:
    """返回精确二级标题「## <name>」的正文行；小节不存在时返回 None。

    正文截止到下一个 ^##\\s+ 标题之前（三级 ### 标题属于正文，不截断）。
    """
    pat = re.compile(r"^##\s+" + re.escape(name) + r"\s*$")
    start = None
    for i, line in enumerate(lines):
        if pat.match(line):
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if re.match(r"^##\s+", lines[j]):
            end = j
            break
    return lines[start + 1:end]


def header_lines(lines: list[str]) -> list[str]:
    """截出「判定书头部」：首条 verdict 行之前；无 verdict 时按小节/行数退回。"""
    for i, line in enumerate(lines):
        if VERDICT_ANY_RE.match(line):
            return lines[:i]
    for i, line in enumerate(lines):
        if re.match(r"^##\s+1\s", line):
            return lines[:i]
    return lines[:120]


def coarse_block_items(body: list[str]) -> list[str]:
    """粗筛「## 阻断项」正文里的具体阻断条目，返回命中原因列表。"""
    reasons: list[str] = []
    for line in body:
        for pat, desc in BLOCK_ITEM_HINTS:
            if pat.search(line):
                reasons.append(f"{desc}: {line.strip()[:80]!r}")
        m = LIST_ITEM_RE.match(line)
        if m:
            item = m.group(1).strip()
            if len(item) >= LIST_ITEM_LEN and "无" not in item:
                reasons.append(f"出现非空长列表条目: {line.strip()[:80]!r}")
    # 去重，保序
    seen: set[str] = set()
    out: list[str] = []
    for r in reasons:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def main() -> int:
    print("=" * 70)
    print("B2b 候选语义复审交付件 · 确定性门禁自检")
    print("=" * 70)
    print(f"[BASE] {BASE}")
    print(f"[ROOT] {ROOT}")

    content_failures: list[str] = []
    passes: list[str] = []

    # ---- 检查 1a: 文件缺失 → 退出码 2 -----------------------------------
    missing = [rel for key, rel in DELIVERY_FILES if not PATHS[key].is_file()]
    if missing:
        for rel in missing:
            print(f"[MISSING] 交付件缺失: {rel} ({ROOT / rel})")
        print("=" * 70)
        print(f"FAILED (EXIT=2): 共有 {len(missing)} 个必要文件缺失")
        print("=" * 70)
        return 2

    # ---- 读入全部文件（只读）；0 字节 / 仅空白 → 内容不合格 --------------
    texts: dict[str, str] = {}
    for key, rel in DELIVERY_FILES:
        path = PATHS[key]
        try:
            if path.stat().st_size == 0:
                content_failures.append(f"[1] 交付件为 0 字节（空文件）: {rel}")
                texts[key] = ""
                continue
            txt = path.read_text(encoding="utf-8")
            if not txt.strip():
                content_failures.append(f"[1] 交付件内容为空（仅空白）: {rel}")
            texts[key] = txt
        except (OSError, UnicodeDecodeError) as exc:
            content_failures.append(f"[1] 无法读取交付件 {rel}: {exc}")
            texts[key] = ""

    passed_1 = not any(f.startswith("[1]") for f in content_failures)
    if passed_1:
        passes.append("[1] 6 件交付件均存在且非空")

    # 后续内容检查只在判定书成功读入时进行，避免连锁误报
    verdict_text = texts.get("verdict", "")
    vlines = verdict_text.splitlines()

    # ---- 检查 2: 头部 4 个不同 64-hex + 4 个字节数 -----------------------
    if verdict_text:
        hdr = "\n".join(header_lines(vlines))
        hexes = HEX64_RE.findall(hdr)
        distinct_hex = sorted(set(h.lower() for h in hexes))
        byte_tokens = BYTES_RE.findall(hdr)
        if len(distinct_hex) < 4:
            content_failures.append(
                f"[2] 判定书头部不同 64 位 hex 不足 4 个（实得 {len(distinct_hex)} 个: {distinct_hex}）"
            )
        if len(byte_tokens) < 4:
            content_failures.append(
                f"[2] 判定书头部字节数不足 4 个（实得 {len(byte_tokens)} 个: {byte_tokens}）"
            )
        if len(distinct_hex) >= 4 and len(byte_tokens) >= 4:
            passes.append(
                f"[2] 头部含 {len(distinct_hex)} 个不同 64-hex 与 {len(byte_tokens)} 个字节数"
                f"（hex 共 {len(hexes)} 处；字节数: {', '.join(byte_tokens[:8])}）"
            )

    # ---- 检查 3: ^verdict:\s*(PASS|BLOCKED)\s*$ 恰好一行 -----------------
    verdict_hits: list[tuple[int, str]] = []
    for lineno, line in enumerate(vlines, 1):
        m = VERDICT_LINE_RE.match(line)
        if m:
            verdict_hits.append((lineno, m.group(1)))
    if len(verdict_hits) != 1:
        any_verdict = [(i + 1, l.strip()) for i, l in enumerate(vlines)
                       if VERDICT_ANY_RE.match(l)]
        content_failures.append(
            f"[3] 判定书须恰含一行 '^verdict:\\s*(PASS|BLOCKED)\\s*$'，"
            f"实得 {len(verdict_hits)} 行（合法命中 {verdict_hits}；verdict 样行 {any_verdict}）"
        )
        verdict_value: str | None = None
    else:
        lineno, verdict_value = verdict_hits[0]
        passes.append(f"[3] 判定书含唯一 verdict 行（第 {lineno} 行）: {verdict_value}")

    # ---- 检查 4: 五个小节标题 --------------------------------------------
    if verdict_text:
        headings = [l for l in vlines if H2_HEAD_RE.match(l) or ANY_HEAD_RE.match(l)]
        absent = [name for name in FIVE_SECTIONS
                  if not any(name in h for h in headings)]
        if absent:
            content_failures.append(f"[4] 判定书缺失小节标题: {', '.join(absent)}")
        else:
            passes.append("[4] 五个小节标题齐全（状态矩阵 / 调用传参 / 输出字段 / F/E 分离 / 范围限制）")

    # ---- 检查 5: 三个小节 + 「## 未验」正文非空 ---------------------------
    bodies: dict[str, list[str] | None] = {}
    if verdict_text:
        for name in THREE_SECTIONS:
            bodies[name] = exact_h2_body(vlines, name)
        absent = [name for name in THREE_SECTIONS if bodies[name] is None]
        if absent:
            content_failures.append(f"[5] 判定书缺失小节: {', '.join('## ' + n for n in absent)}")
        unverified = bodies.get("未验")
        if unverified is not None and not any(l.strip() for l in unverified):
            content_failures.append("[5] 「## 未验」小节正文为空（要求非空）")
        if not absent and unverified is not None and any(l.strip() for l in unverified):
            nonblank = sum(1 for l in unverified if l.strip())
            passes.append(f"[5] 三个小节齐全，且「## 未验」正文非空（{nonblank} 个非空行）")

    # ---- 检查 6: 重跑输出痕迹 --------------------------------------------
    if texts.get("test_out"):
        t = texts["test_out"]
        miss = [tok for tok in ("PASS=", "FAIL=") if tok not in t]
        if miss:
            content_failures.append(f"[6] _test_rerun_out.txt 缺失: {', '.join(miss)}")
        else:
            passes.append("[6] _test_rerun_out.txt 同时含 PASS= 与 FAIL=")
    if texts.get("gate_out"):
        t = texts["gate_out"]
        if ("9" in t) or ("PASS" in t):
            passes.append("[6] _gate_rerun_out.txt 含 '9' 或 'PASS'（门禁重跑痕迹）")
        else:
            content_failures.append("[6] _gate_rerun_out.txt 既不含 '9' 也不含 'PASS'")

    # ---- 检查 7: 复核件两个键值 ------------------------------------------
    if texts.get("audit"):
        t = texts["audit"]
        miss = [k for k in AUDIT_KEYS if k not in t]
        if miss:
            content_failures.append(f"[7] review/SEMANTIC_REVIEW_AUDIT.md 缺失键值: {', '.join(miss)}")
        else:
            passes.append("[7] 复核件含 checkedEveryRow: true 与 noOverreach: true")

    # ---- 检查 8: verdict=PASS 时「## 阻断项」一致性（粗筛） ---------------
    if verdict_value == "PASS":
        body = bodies.get("阻断项")
        if body is None:
            content_failures.append("[8] verdict=PASS 但缺「## 阻断项」小节，无法核对一致性")
        else:
            text = "\n".join(body)
            if "无" not in text:
                content_failures.append("[8] verdict=PASS 但「## 阻断项」正文不含「无」")
            hits = coarse_block_items(body)
            if hits:
                content_failures.append(
                    f"[8] verdict=PASS 但「## 阻断项」正文疑似含具体阻断条目（粗筛命中 {len(hits)} 条）:"
                )
                for h in hits[:12]:
                    content_failures.append(f"      - {h}")
                if len(hits) > 12:
                    content_failures.append(f"      - ...另有 {len(hits) - 12} 条")
            if "无" in text and not hits:
                passes.append("[8] verdict=PASS 且「## 阻断项」正文含「无」、粗筛无具体阻断条目")
    elif verdict_value == "BLOCKED":
        passes.append("[8] verdict=BLOCKED，一致性检查（PASS 分支）不适用，跳过")
    else:
        # 检查 3 已失败；这里只标注未执行，不制造第二条假失败
        passes.append("[8] verdict 未取到合法值，一致性检查未执行（见 [3]）")

    # ---- 汇总 ------------------------------------------------------------
    for p in passes:
        print(f"PASS {p}")
    print("=" * 70)
    if content_failures:
        print(f"FAILED (EXIT=1): 共有 {len(content_failures)} 项内容不合格：")
        for cf in content_failures:
            print(f"  - {cf}")
        print("=" * 70)
        return 1
    print("ALL CHECKS PASSED! EXIT=0")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
