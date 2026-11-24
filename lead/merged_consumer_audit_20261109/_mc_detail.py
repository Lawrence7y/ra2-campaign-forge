# -*- coding: utf-8 -*-
"""_mc_detail.py — 逐件判定消费面（只读）。
对每个相关 .py 抽取：
  * 模块装载语句（importlib spec_from_file_location / from X import / import X）
  * 装载路径指向哪一实现（_re_linked / _sl_link / _f2_r11plus / 其它）
  * link()/link_triple()/r11_scan_plus() 调用行
  * 字段读取行（match/path/verified_path/recomputed/bytes/tier），带原文
  * 「match=True 后用 path」局部窗口判定
只读，不改被扫件。
"""
import os
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "lead"
DEPTH_CAP = 6
PRUNE_DIRS = {".git", "__pycache__", ".mimosa", "node_modules", ".tmp"}
MAX_BYTES = 400_000

# 装载路径识别
LOAD_PATH = re.compile(r"spec_from_file_location|SourceFileLoader|exec_module|sys\.path|import_module|__import__")
IMPORT_LINE = re.compile(r"^\s*(?:from|import)\s+.+")
PATH_MENTION = re.compile(r"[A-Za-z0-9_\-/\\.]*(_re_linked|_sl_link|_f2_r11plus|r11_scan_plus|_eq_proto|_rev_core)[A-Za-z0-9_\-/\\.]*")
CALL_LINK = re.compile(r"(?<![A-Za-z_])link\s*\(")
CALL_TRIPLE = re.compile(r"link_triple\s*\(")
CALL_R11 = re.compile(r"r11_scan_plus\s*\(")
FIELD_READ = re.compile(r"""(\[\s*['"](match|path|verified_path|recomputed|bytes|tier|members|reverify|verdict|eq|samedoc_link)['"]\s*\]|\.get\(\s*['"](match|path|verified_path|members|tier)['"])""")


def targets():
    """只聚焦：调用 link/triple/r11 或 importlib 装载三类实现之一的 .py。"""
    out = []
    base = len(LEAD.parts)
    for dp, dns, fns in os.walk(LEAD):
        d = Path(dp)
        dns[:] = [x for x in dns if x not in PRUNE_DIRS]
        if len(d.parts) - base > DEPTH_CAP:
            dns[:] = []
            continue
        for fn in fns:
            if not fn.endswith(".py"):
                continue
            p = d / fn
            try:
                sz = p.stat().st_size
            except OSError:
                continue
            if sz > MAX_BYTES:
                continue
            try:
                t = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if (CALL_LINK.search(t) or CALL_TRIPLE.search(t) or CALL_R11.search(t)
                    or (LOAD_PATH.search(t) and PATH_MENTION.search(t))):
                out.append((p, t))
    return out


def classify_load(t):
    """返回装载的实现标签集合。"""
    labels = set()
    for m in PATH_MENTION.finditer(t):
        s = m.group(0)
        if "_re_linked" in s:
            labels.add("RE_LINKED(merged)")
        if "_sl_link" in s:
            labels.add("SL_LINK(orig)")
        if "_f2_r11plus" in s or "r11_scan_plus" in s:
            labels.add("R11_PLUS(prod)")
        if "_eq_proto" in s:
            labels.add("EQ_PROTO(proto)")
    return labels


def main():
    items = targets()
    print("=== DETAIL_META === depthCap=%d maxBytes=%d candidateFiles=%d" % (DEPTH_CAP, MAX_BYTES, len(items)))
    for p, t in sorted(items, key=lambda x: str(x[0])):
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        lines = t.splitlines()
        labels = classify_load(t)
        # 装载语句行（含 importlib / from / import 且提及目标）
        load_lines = []
        for i, ln in enumerate(lines, 1):
            if LOAD_PATH.search(ln) or (IMPORT_LINE.match(ln) and PATH_MENTION.search(ln)):
                load_lines.append((i, ln.strip()[:160]))
        # 调用行
        call_lines = []
        for i, ln in enumerate(lines, 1):
            if CALL_TRIPLE.search(ln) or CALL_LINK.search(ln) or CALL_R11.search(ln):
                call_lines.append((i, ln.strip()[:160]))
        # 字段读取行 + 危险窗口（match 后 5 行内出现 path/verified_path 读取）
        field_lines = []
        danger_lines = []
        for i, ln in enumerate(lines, 1):
            if FIELD_READ.search(ln):
                field_lines.append((i, ln.strip()[:160]))
        for i, ln in enumerate(lines):
            if re.search(r"""\[\s*['"]match['"]\s*\]|\.get\(\s*['"]match['"]""", ln):
                for j in range(i, min(i + 6, len(lines))):
                    if re.search(r"""\[\s*['"](path|verified_path)['"]\s*\]|\.get\(\s*['"](path|verified_path)['"]""", lines[j]):
                        danger_lines.append((j + 1, lines[j].strip()[:160]))
                        break
        print("\n--- %s ---" % rel)
        print("  LOAD_LABELS=%s" % (sorted(labels) if labels else "NONE"))
        if load_lines:
            print("  LOAD_STMTS:")
            for i, s in load_lines[:8]:
                print("    L%d: %s" % (i, s))
        if call_lines:
            print("  CALLS:")
            for i, s in call_lines[:10]:
                print("    L%d: %s" % (i, s))
        if field_lines:
            print("  FIELD_READS:")
            for i, s in field_lines[:14]:
                print("    L%d: %s" % (i, s))
        if danger_lines:
            print("  *** DANGER_WINDOW(match→path/verified_path within 6 lines) ***")
            for i, s in danger_lines[:10]:
                print("    L%d: %s" % (i, s))


if __name__ == "__main__":
    main()
