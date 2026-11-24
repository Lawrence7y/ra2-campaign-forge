#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only census of literal `EXIT=0` lines in the three ledgers.

口径（严格按题面）：
  - 三本台账按 `\\n` 切行；只认精确子串 `EXIT=0`（大小写敏感，不做正则/归一化）。
    因此 `exit=0`、`final_exit=0`、`EXIT = 0` 等近形写法一律不计。
    题面提到 `EXIT=0，K1–K10`：本口径下它同样命中（因为确实含精确子串），
    前提是该行也含 `EXIT=0`；不以 `EXIT=0` 后跟什么字符作为排除条件。
  - 每行用正则 `([A-Za-z0-9_]+\\.py)` 抽所有 .py 文件名（basename 形式，
    因为该正则不匹配 `/` 与 `\\`）。重复名字在本行内去重、保序。
  - 普查名单取 `_ce_final_out.json` 的 `rows`；以 `rel` 的 basename 建索引，
    同一 basename 的所有同名件全部列出（记录 `rel`/`cls`/名单出处行号）。
  - 归类：无 .py -> NO_PY_NAME；有一个都没找到 -> NOT_CENSUSED（不猜测
    「其实说的是另一个脚本」）；命中件全同类 -> 该类；命中件异类 -> MIXED。
  - 只读输入；唯一写入为本目录下 `_lc_out.json` 与 `_lc_out.txt`。
"""
import sys

sys.dont_write_bytecode = True

import json
import re
from collections import Counter, OrderedDict
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent

LEDGERS = [
    PROJECT / "lead" / "GOAL_THREE_TARGETS_20261018.md",
    PROJECT / "lead" / "PENDING_DECISIONS.md",
    PROJECT / "lead" / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md",
]
CENSUS = PROJECT / "lead" / "const_exit_20261109" / "_ce_final_out.json"
OUT_JSON = HERE / "_lc_out.json"
OUT_TXT = HERE / "_lc_out.txt"

NEEDLE = "EXIT=0"
PY_RE = re.compile(r"([A-Za-z0-9_]+\.py)")
KNOWN = ("NO_EXIT_AT_ALL", "CONDITIONAL_EXIT", "CONSTANT_EXIT")
SPECIAL = ("NOT_CENSUSED", "NO_PY_NAME", "MIXED")
ALL_CLS = KNOWN + SPECIAL


def relpath(p):
    try:
        return p.resolve().relative_to(PROJECT).as_posix()
    except ValueError:
        return str(p)


def read_lines_exact_lf(path, why):
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    why.append(
        "read %s (%d bytes, BOM=%s, CRLF=%d, LF=%d); split('\\n') -> %d lines"
        % (
            relpath(path),
            len(raw),
            raw[:3] == b"\xef\xbb\xbf",
            raw.count(b"\r\n"),
            raw.count(b"\n"),
            len(text.split("\n")),
        )
    )
    return text.split("\n")


def load_census(path, why):
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    obj = json.loads(text)
    why.append(
        "read %s (%d bytes, parsed JSON, rows=%d)"
        % (relpath(path), len(raw), len(obj["rows"]))
    )
    clines = text.split("\n")
    # 该名单文件中每个 row 的 "rel" 与 "cls" 各占一行；按行号精确取出处。
    line_of_rel = {}
    line_of_cls = {}
    for i, line in enumerate(clines, 1):
        s = line.strip().rstrip(",")
        if s.startswith('"rel"'):
            value = json.loads("{" + s + "}")["rel"]
            line_of_rel.setdefault(value, []).append(i)
        elif s.startswith('"cls"'):
            value = json.loads("{" + s + "}")["cls"]
            line_of_cls.setdefault(value, []).append(i)
    why.append(
        "census line index: %d '\"rel\"' lines, %d '\"cls\"' lines; "
        "per-row lines located by exact field text"
        % (sum(len(v) for v in line_of_rel.values()), sum(len(v) for v in line_of_cls.values()))
    )
    index = OrderedDict()
    ann = []
    for r in obj["rows"]:
        rel = r["rel"]
        bn = PurePosixPath(rel.replace("\\", "/")).name
        cls = r["cls"]
        # 出处行号：优先用 rel 值定位（唯一），否则用 cls 值，再否则仅给文件名。
        if rel in line_of_rel and len(line_of_rel[rel]) == 1:
            src = "%s:%d" % (relpath(path), line_of_rel[rel][0])
        elif cls in line_of_cls and len(line_of_cls[cls]) == 1:
            src = "%s:%d" % (relpath(path), line_of_cls[cls][0])
        else:
            src = relpath(path)
        index.setdefault(bn, []).append(
            {"rel": rel, "cls": cls, "census_src": src}
        )
        ann.append({"rel": rel, "basename": bn, "cls": cls, "census_src": src})
    why.append(
        "built basename index: %d rows -> %d distinct basenames; "
        "basename field mismatch=%d; cls values=%s"
        % (
            len(obj["rows"]),
            len(index),
            sum(1 for r, a in zip(obj["rows"], ann) if "basename" in r and r["basename"] != a["basename"]),
            dict(Counter(r["cls"] for r in obj["rows"])),
        )
    )
    return index, ann


def main():
    why = []
    census_index, census_ann = load_census(CENSUS, why)

    rows = []
    stats = Counter()
    for ledger in LEDGERS:
        lines = read_lines_exact_lf(ledger, why)
        ledger_rel = relpath(ledger)
        hits = 0
        for line_no, line in enumerate(lines, 1):
            if NEEDLE not in line:
                continue
            hits += 1
            py_names = []
            for m in PY_RE.finditer(line):
                if m.group(1) not in py_names:
                    py_names.append(m.group(1))
            matches = []
            reasons = []
            for bn in py_names:
                found = census_index.get(bn, [])
                for f in found:
                    matches.append(
                        {
                            "py_name": bn,
                            "rel": f["rel"],
                            "cls": f["cls"],
                            "census_src": f["census_src"],
                        }
                    )
                    reasons.append(
                        "%s -> %s [%s] (%s)"
                        % (bn, f["cls"], f["rel"], f["census_src"])
                    )
                if not found:
                    reasons.append(
                        "%s -> 对不上：已查 %s 的 rows 全部 %d 个 basename 索引，无同名件"
                        % (bn, relpath(CENSUS), len(census_ann))
                    )
            if not py_names:
                cls = "NO_PY_NAME"
                w = "该行用正则 %s 未抽出任何 .py 名" % PY_RE.pattern
            elif not matches:
                cls = "NOT_CENSUSED"
                w = "抽出的 .py 名在普查名单 rows 中一个同名件都没有；不推断别的脚本"
            else:
                classes = sorted({m["cls"] for m in matches})
                if len(classes) == 1 and classes[0] in KNOWN:
                    cls = classes[0]
                    w = "命中 %d 个同名件，全部同类" % len(matches)
                elif len(classes) > 1:
                    cls = "MIXED"
                    w = "同名件分属不同类：%s" % ", ".join(classes)
                else:
                    cls = "MIXED"
                    w = "命中件 cls 非三种规定类别：%s" % ", ".join(classes)
            row_why = (
                "%s:%d 含精确子串 %r；正则抽名=%s；%s；%s"
                % (ledger_rel, line_no, NEEDLE, py_names, w, " | ".join(reasons))
            )
            rows.append(
                {
                    "ledger": ledger_rel,
                    "line_no": line_no,
                    "text": line[:200],
                    "text_truncated": len(line) > 200,
                    "py_names": py_names,
                    "matches": matches,
                    "cls": cls,
                    "why": row_why,
                }
            )
            stats[cls] += 1
        why.append(
            "%s: literal %r hit %d/%d lines (case-sensitive, no regex/normalization)"
            % (ledger_rel, NEEDLE, hits, len(lines))
        )

    summary = OrderedDict()
    summary["scope"] = (
        "三本台账按 '\\n' 切行；只认精确子串 'EXIT=0'（大小写敏感）。"
        "'exit=0'、'final_exit=0'、'EXIT = 0' 等近形写法不计。"
        "'EXIT=0，K1–K10' 一类只要含精确子串即计入，且不因后续字符排除；"
        "本脚本不以 'EXIT=0' 后跟什么作为过滤条件。"
    )
    summary["ledgers"] = [relpath(p) for p in LEDGERS]
    summary["census"] = relpath(CENSUS)
    summary["census_rows"] = len(census_ann)
    summary["n_lines_with_EXIT_eq_0"] = len(rows)
    summary["cls_counts"] = OrderedDict((k, stats.get(k, 0)) for k in ALL_CLS)
    summary["NOT_CENSUSED_count"] = stats.get("NOT_CENSUSED", 0)
    summary["NO_PY_NAME_count"] = stats.get("NO_PY_NAME", 0)
    summary["NOT_CENSUSED_plus_NO_PY_NAME"] = (
        stats.get("NOT_CENSUSED", 0) + stats.get("NO_PY_NAME", 0)
    )
    summary["per_ledger"] = []
    for p in LEDGERS:
        lr = [r for r in rows if r["ledger"] == relpath(p)]
        c = Counter(r["cls"] for r in lr)
        summary["per_ledger"].append(
            {
                "ledger": relpath(p),
                "hits": len(lr),
                "cls_counts": OrderedDict((k, c.get(k, 0)) for k in ALL_CLS),
            }
        )
    summary["notes"] = why
    summary["census_annotation"] = census_ann

    payload = OrderedDict()
    payload["summary"] = summary
    payload["rows"] = rows
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    out = []
    out.append("LEDGER EXIT=0 CENSUS (literal substring only)")
    out.append("cwd-relative paths from: %s" % relpath(PROJECT))
    out.append("scope: %s" % summary["scope"])
    out.append("census: %s (rows=%d)" % (summary["census"], summary["census_rows"]))
    out.append("total lines with EXIT=0: %d" % len(rows))
    out.append("")
    out.append("== cls counts (all three ledgers) ==")
    for k in ALL_CLS:
        out.append("%-20s %d" % (k, stats.get(k, 0)))
    out.append(
        "NOT_CENSUSED + NO_PY_NAME = %d + %d = %d"
        % (
            stats.get("NOT_CENSUSED", 0),
            stats.get("NO_PY_NAME", 0),
            summary["NOT_CENSUSED_plus_NO_PY_NAME"],
        )
    )
    out.append("")
    out.append("== per ledger ==")
    for e in summary["per_ledger"]:
        out.append("%s hits=%d" % (e["ledger"], e["hits"]))
        for k in ALL_CLS:
            out.append("  %-20s %d" % (k, e["cls_counts"][k]))
    out.append("")
    out.append("== rows ==")
    for i, r in enumerate(rows, 1):
        out.append(
            "[%03d] %s:%d cls=%s py_names=%s"
            % (i, r["ledger"], r["line_no"], r["cls"], ",".join(r["py_names"]) or "-")
        )
        out.append("      text: %s" % r["text"].replace("\r", "\\r"))
        out.append("      why : %s" % r["why"])
        for m in r["matches"]:
            out.append(
                "      hit : %s -> %s [%s] (%s)"
                % (m["py_name"], m["cls"], m["rel"], m["census_src"])
            )
    out.append("")
    out.append("== notes ==")
    for n in why:
        out.append("- %s" % n)
    OUT_TXT.write_text("\n".join(out) + "\n", encoding="utf-8")

    print("n_rows=%d" % len(rows))
    for k in ALL_CLS:
        print("%s=%d" % (k, stats.get(k, 0)))
    print(
        "NOT_CENSUSED_plus_NO_PY_NAME=%d"
        % summary["NOT_CENSUSED_plus_NO_PY_NAME"]
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
