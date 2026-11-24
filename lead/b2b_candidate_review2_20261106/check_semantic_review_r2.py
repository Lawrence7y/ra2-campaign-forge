#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""check_semantic_review_r2.py — B2b 第二轮候选语义复审交付件机械门禁（只读，只用标准库）。

运行方式（仓库根 + 隔离模式，参数为脚本自身路径）:
    cd D:/Project/ra2-campaign-forge
    python -I -X utf8 lead/b2b_candidate_review2_20261106/check_semantic_review_r2.py \
        lead/b2b_candidate_review2_20261106/check_semantic_review_r2.py

检查项：
1) 以下 6 件交付件都存在且非空:
     lead/b2b_candidate_review2_20261106/CANDIDATE_SEMANTIC_REVIEW_R2.md
     lead/b2b_candidate_review2_20261106/_review2_probe.py
     lead/b2b_candidate_review2_20261106/_review2_probe_out.txt
     lead/b2b_candidate_review2_20261106/_test_rerun_out.txt
     lead/b2b_candidate_review2_20261106/_gate_rerun_out.txt
     lead/b2b_candidate_review2_20261106/review/SEMANTIC_REVIEW_R2_AUDIT.md
2) 判定书头部含 4 个不同 64 位 hex 与 4 个字节数；
3) 含 ^verdict:\\s*(PASS|BLOCKED)\\s*$ 一行（必须恰好一行）；
4) 含六个小节标题（上一轮 B-1/B-2 按修正口径的复判 / 状态矩阵与三态 /
   输出字段 / 接线与 F/E 分离 / 范围限制 / 上一轮遗留事项复核）；
5) 含「## 阻断项」「## 未验」「## 证据等级说明」三个小节，
   且「## 未验」正文非空；
6) _test_rerun_out.txt 含 PASS= 与 FAIL=；_gate_rerun_out.txt 含 9 或 PASS；
7) review/SEMANTIC_REVIEW_R2_AUDIT.md 含 checkedEveryRow: true、noOverreach: true
   （按字段名 + 值 true 机械匹配；接受本仓复核件的三种声明形式：
     `key: true` / `key = true` / 表格 `| `key` | `true` |`，见 FIELD_TRUE_RE）；
8) 一致性：若 verdict=PASS，则「## 阻断项」正文必须含「无」；
9) 「## 6 上一轮遗留事项复核」小节必须同时出现「引用精度」、
   「STATE_MATRIX」或「矩阵」、「键名」、「门禁读旧」四类词。

退出码：
  0 = PASS
  1 = 内容不合格（逐条打印原因；含「文件存在但 0 字节 / 仅空白」）
  2 = 文件缺失
脚本只读：全程只做 is_file / stat / read_text，不写任何文件、不建目录。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Windows 控制台防御性 UTF-8 输出（与同仓 check_semantic_review.py 一致）
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
if BASE.name != "b2b_candidate_review2_20261106":
    fallback = Path.cwd() / "lead" / "b2b_candidate_review2_20261106"
    if fallback.is_dir():
        BASE = fallback.resolve()

ROOT = BASE.parent.parent  # lead/ 的上一级 = 仓库根
if not (ROOT / "lead" / "b2b_candidate_review2_20261106").is_dir():
    ROOT = Path.cwd()

REVIEW_DIR = ROOT / "lead" / "b2b_candidate_review2_20261106"

# 相对仓库根的交付件清单（与 ask 给的路径逐字一致）
DELIVERY_FILES: list[tuple[str, str]] = [
    ("verdict",   "lead/b2b_candidate_review2_20261106/CANDIDATE_SEMANTIC_REVIEW_R2.md"),
    ("probe_py",  "lead/b2b_candidate_review2_20261106/_review2_probe.py"),
    ("probe_out", "lead/b2b_candidate_review2_20261106/_review2_probe_out.txt"),
    ("test_out",  "lead/b2b_candidate_review2_20261106/_test_rerun_out.txt"),
    ("gate_out",  "lead/b2b_candidate_review2_20261106/_gate_rerun_out.txt"),
    ("audit",     "lead/b2b_candidate_review2_20261106/review/SEMANTIC_REVIEW_R2_AUDIT.md"),
]
PATHS = {key: ROOT / rel for key, rel in DELIVERY_FILES}

# ---------------------------------------------------------------- 判据常量
# 判定书头部：文件开头到第一条 verdict 样行之前（verdict 行是 §0 头部的天然界标）。
# 找不到 verdict 行时退回「第一个 ## 1 小节之前」，再退回前 120 行。
HEX64_RE = re.compile(r"\b[0-9a-fA-F]{64}\b")
BYTES_RE = re.compile(r"\b\d[\d,]*(?:\.\d+)?\s*B\b")
VERDICT_LINE_RE = re.compile(r"^verdict:\s*(PASS|BLOCKED)\s*$")
VERDICT_ANY_RE = re.compile(r"^\s*verdict\s*:", re.IGNORECASE)
H2_HEAD_RE = re.compile(r"^##\s+(.*?)\s*$")
ANY_HEAD_RE = re.compile(r"^#{1,6}\s+")

# 检查 4：六个小节标题（按 ask 逐字；在 ^## 标题行内做子串匹配）
SIX_SECTIONS = [
    "上一轮 B-1/B-2 按修正口径的复判",
    "状态矩阵与三态",
    "输出字段",
    "接线与 F/E 分离",
    "范围限制",
    "上一轮遗留事项复核",
]
THREE_SECTIONS = ["阻断项", "未验", "证据等级说明"]

# 检查 7：复核件把两个字段声明为 true。
# R1 复核件用字面 `key: true`；R2 复核件用表格 `| `key` | `true` |` 与
# `key = true`。这里机械匹配「字段名 + 分隔符 + true」，分隔符只允许
# 空白/反引号/引号/竖线/冒号/等号/星号/下划线/逗号/连字符，且限长 16，
# 不允许字母数字、也不允许换行，故不会跨越到别的字段的 true 值，
# 也不会跨行误配；false 声明不匹配。
AUDIT_FIELDS = ("checkedEveryRow", "noOverreach")
FIELD_TRUE_RE = {
    key: re.compile(r"\b" + re.escape(key) + r"\b[\t `'\"|:=*_,\-]{0,16}true\b",
                    re.IGNORECASE)
    for key in AUDIT_FIELDS
}
FIELD_LITERAL_RE = {
    key: re.compile(r"\b" + re.escape(key) + r"\s*:\s*true\b", re.IGNORECASE)
    for key in AUDIT_FIELDS
}

# 检查 9：§6 小节内必须同时出现的四类词（每类给出可接受词，任一命中即可）
SECTION6_GROUPS: list[tuple[str, tuple[str, ...]]] = [
    ("引用精度",             ("引用精度",)),
    ("STATE_MATRIX/矩阵",    ("STATE_MATRIX", "矩阵")),
    ("键名",                 ("键名",)),
    ("门禁读旧",             ("门禁读旧",)),
]
SECTION6_HEAD_RE = re.compile(r"^##\s+6\s+上一轮遗留事项复核")


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


def section6_body(lines: list[str]) -> list[str] | None:
    """返回「## 6 上一轮遗留事项复核」小节正文；小节不存在时返回 None。"""
    start = None
    for i, line in enumerate(lines):
        if SECTION6_HEAD_RE.match(line):
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
    """截出「判定书头部」：首条 verdict 样行之前；无 verdict 时按小节/行数退回。"""
    for i, line in enumerate(lines):
        if VERDICT_ANY_RE.match(line):
            return lines[:i]
    for i, line in enumerate(lines):
        if re.match(r"^##\s+1\s", line):
            return lines[:i]
    return lines[:120]


def main() -> int:
    print("=" * 70)
    print("B2b 第二轮候选语义复审交付件 · 确定性门禁自检")
    print("=" * 70)
    print(f"[BASE] {BASE}")
    print(f"[ROOT] {ROOT}")

    content_failures: list[str] = []
    passes: list[str] = []
    skips: list[str] = []

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

    # ---- 检查 4: 六个小节标题 --------------------------------------------
    if verdict_text:
        headings = [l for l in vlines if H2_HEAD_RE.match(l) or ANY_HEAD_RE.match(l)]
        absent = [name for name in SIX_SECTIONS
                  if not any(name in h for h in headings)]
        if absent:
            content_failures.append(f"[4] 判定书缺失小节标题: {', '.join(absent)}")
        else:
            passes.append("[4] 六个小节标题齐全（复判 / 矩阵与三态 / 输出字段 / 接线与 F/E / 范围限制 / 遗留复核）")

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

    # ---- 检查 7: 复核件两个字段声明为 true --------------------------------
    if texts.get("audit"):
        t = texts["audit"]
        miss: list[str] = []
        forms: list[str] = []
        for key in AUDIT_FIELDS:
            m = FIELD_TRUE_RE[key].search(t)
            if not m:
                miss.append(f"{key}（未见字段名 + true 的声明；接受 `key: true` / `key = true` / 表格形式）")
            else:
                literal = bool(FIELD_LITERAL_RE[key].search(t))
                forms.append(f"{key}=true（{'字面 key: true' if literal else '表格/等号形式'}）")
        if miss:
            content_failures.append(f"[7] review/SEMANTIC_REVIEW_R2_AUDIT.md 缺失/不合格字段: {'; '.join(miss)}")
        else:
            passes.append(
                f"[7] 复核件含 checkedEveryRow: true、noOverreach: true（按字段值匹配: {', '.join(forms)}）"
            )

    # ---- 检查 8: verdict=PASS 时「## 阻断项」正文必须含「无」 --------------
    if verdict_value == "PASS":
        body = bodies.get("阻断项")
        if body is None:
            content_failures.append("[8] verdict=PASS 但缺「## 阻断项」小节，无法核对一致性")
        elif "无" not in "\n".join(body):
            content_failures.append("[8] verdict=PASS 但「## 阻断项」正文不含「无」")
        else:
            passes.append("[8] verdict=PASS 且「## 阻断项」正文含「无」")
    elif verdict_value == "BLOCKED":
        skips.append("[8] verdict=BLOCKED，一致性检查（PASS 分支）不适用，跳过")
    else:
        # 检查 3 已失败；这里只标注未执行，不制造第二条假失败
        skips.append("[8] verdict 未取到合法值，一致性检查未执行（见 [3]）")

    # ---- 检查 9: §6 小节四类词齐全 ---------------------------------------
    if verdict_text:
        s6 = section6_body(vlines)
        if s6 is None:
            content_failures.append("[9] 判定书缺失「## 6 上一轮遗留事项复核」小节")
        else:
            s6_text = "\n".join(s6)
            miss = []
            hits = []
            for label, words in SECTION6_GROUPS:
                found = [w for w in words if w in s6_text]
                if not found:
                    miss.append(label + "（需含 " + " 或 ".join(words) + "）")
                else:
                    hits.append(f"{label}:{'/'.join(found)}")
            if miss:
                content_failures.append(f"[9] §6 小节缺失词类: {'; '.join(miss)}")
            else:
                passes.append(f"[9] §6 小节四类词齐全（{'; '.join(hits)}）")

    # ---- 汇总 ------------------------------------------------------------
    for p in passes:
        print(f"PASS {p}")
    for s in skips:
        print(f"SKIP {s}")
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
