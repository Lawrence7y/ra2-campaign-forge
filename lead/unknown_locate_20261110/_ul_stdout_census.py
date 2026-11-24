# -*- coding: utf-8 -*-
"""_ul_stdout_census.py — 只读普查：263 件 NO_EXIT_AT_ALL 的 stdout 产物通道。

问题：在 263 件 NO_EXIT_AT_ALL 里，有多少件的产物通道是
      sys.stdout.write(...) / sys.stdout.buffer.write(...) 而不是 print(...)？

只读输入：
  lead/exit_criterion_20261110/_ec_s4_results.json 的 results[*].rel（名单）
  同一 json 的 results[*].class / verdict / reasons（原判据结论）
  名单里的 263 个 .py 源文件（仅 open 'rb' + ast.parse，不 import、不执行）
唯一写入：lead/unknown_locate_20261110/_ul_stdout_census_out.txt
"""
import sys
sys.dont_write_bytecode = True

import ast
import collections
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, "lead", "exit_criterion_20261110", "_ec_s4_results.json")
OUT = os.path.join(HERE, "_ul_stdout_census_out.txt")


def dotted(node):
    """把 Name/Attribute 链还原成点号串；含 Call/Subscript 等则 None。"""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def scan(rel):
    path = os.path.join(ROOT, rel.replace("/", os.sep))
    with open(path, "rb") as f:
        raw = f.read()
    tree = ast.parse(raw, filename=rel)  # bytes 形式自动尊重 PEP 263 编码声明

    # 第一遍：绑定名（import sys as s / from sys import stdout as o）
    sys_aliases = {"sys"}
    stdout_names = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name == "sys":
                    sys_aliases.add(a.asname or "sys")
        elif isinstance(n, ast.ImportFrom) and n.module == "sys":
            for a in n.names:
                if a.name == "stdout":
                    stdout_names.add(a.asname or "stdout")

    rec = {
        "sw": [],            # sys.stdout.write(...)
        "bw": [],            # sys.stdout.buffer.write(...)
        "alias": [],         # 别名形式（import sys as s / from sys import stdout）
        "prints": [],        # print(...)
        "parse": "OK",
    }
    sw_recv = {"%s.stdout" % a for a in sys_aliases}
    bw_recv = {"%s.stdout.buffer" % a for a in sys_aliases}
    alias_sw_recv = {n for n in stdout_names}
    alias_bw_recv = {"%s.buffer" % n for n in stdout_names}

    # 第二遍：调用点
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        if isinstance(f, ast.Name) and f.id == "print":
            rec["prints"].append(n.lineno)
        elif isinstance(f, ast.Attribute) and f.attr == "write":
            d = dotted(f.value)
            if d in sw_recv:
                rec["sw"].append((n.lineno, d + ".write"))
            elif d in bw_recv:
                rec["bw"].append((n.lineno, d + ".write"))
            elif d in alias_sw_recv or d in alias_bw_recv:
                rec["alias"].append((n.lineno, d + ".write"))

    # 纯文本提及（如字符串字面量里的 "sys.stdout.write"）——不作为调用计入
    text = raw.decode("utf-8", "replace").splitlines()
    call_lines = {ln for ln, _ in rec["sw"] + rec["bw"] + rec["alias"]}
    rec["text_only"] = [
        (i, ln.strip()[:150])
        for i, ln in enumerate(text, 1)
        if ("sys.stdout.write" in ln or "sys.stdout.buffer.write" in ln)
        and i not in call_lines
    ]
    return rec


def main():
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    rows = data["results"]
    lines = []
    emit = lines.append

    emit("== 263 件 NO_EXIT_AT_ALL 的 stdout.write 产物通道普查 ==")
    emit("名单来源: %s 的 results[*].rel" % os.path.relpath(SRC, ROOT).replace(os.sep, "/"))
    emit("名单件数(results 长度) = %d ; 文件内 n_no_exit = %s" % (len(rows), data.get("n_no_exit")))
    emit("判据结论来源: 同一 json 的 results[*].class / verdict / reasons")
    emit("检测方式: ast.parse(源码 bytes) 后遍历 ast.Call；匹配 func=sys.stdout.write / sys.stdout.buffer.write（含 import sys as s、from sys import stdout 的等价别名）")
    emit("脚本约束: sys.dont_write_bytecode=True；唯一写入文件 = %s" % os.path.relpath(OUT, ROOT).replace(os.sep, "/"))
    emit("")

    rels = [r["rel"] for r in rows]
    emit("rel 去重后 = %d ; 重复 rel 数 = %d" % (len(set(rels)), len(rels) - len(set(rels))))
    emit("缺失文件数 = %d" % sum(1 for rel in rels if not os.path.isfile(os.path.join(ROOT, rel.replace("/", os.sep)))))
    emit("")

    scanned = {}
    parse_fail = []
    for r in rows:
        try:
            scanned[r["rel"]] = scan(r["rel"])
        except Exception as e:
            parse_fail.append((r["rel"], repr(e)))
    emit("ast 解析成功 = %d ; 解析失败 = %d" % (len(scanned), len(parse_fail)))
    for rel, err in parse_fail:
        emit("  PARSE_FAIL %s %s" % (rel, err))
    emit("")

    # 按 class 分组计数
    by_cls = collections.defaultdict(list)
    for r in rows:
        by_cls[r["class"]].append(r)

    header = ("%-10s %7s %9s %9s %9s %9s %9s %11s %9s" %
              ("class", "n_total", "n_sw", "n_bw", "n_either", "n_print", "n_both", "n_chan_only", "n_calls"))
    emit("== 按 class 分组计数表 ==")
    emit("  n_sw      = 含 >=1 个 sys.stdout.write(...) 的件数")
    emit("  n_bw      = 含 >=1 个 sys.stdout.buffer.write(...) 的件数")
    emit("  n_either  = 含任一类 stdout 写调用的件数（去重后的件数）")
    emit("  n_print   = 含 >=1 个 print(...) 的件数")
    emit("  n_both    = 同时含 stdout 写调用与 print(...) 的件数")
    emit("  n_chan_only = 含 stdout 写调用且全件无 print(...) 的件数（严格『而不是 print』）")
    emit("  n_calls   = 两类 stdout 写调用的总调用点数")
    emit("")
    emit(header)
    emit("-" * len(header))

    tot = collections.Counter()
    for cls in sorted(by_cls):
        group = by_cls[cls]
        n_sw = n_bw = n_either = n_print = n_both = n_chan_only = n_calls = 0
        for r in group:
            s = scanned.get(r["rel"])
            if s is None:
                continue
            has_sw, has_bw = bool(s["sw"]), bool(s["bw"])
            has_either = has_sw or has_bw
            has_print = bool(s["prints"])
            n_sw += has_sw
            n_bw += has_bw
            n_either += has_either
            n_print += has_print
            n_both += has_either and has_print
            n_chan_only += has_either and not has_print
            n_calls += len(s["sw"]) + len(s["bw"])
        emit("%-10s %7d %9d %9d %9d %9d %9d %11d %9d" %
             (cls, len(group), n_sw, n_bw, n_either, n_print, n_both, n_chan_only, n_calls))
        for k, v in (("n_total", len(group)), ("n_sw", n_sw), ("n_bw", n_bw),
                     ("n_either", n_either), ("n_print", n_print), ("n_both", n_both),
                     ("n_chan_only", n_chan_only), ("n_calls", n_calls)):
            tot[k] += v
    emit("-" * len(header))
    emit("%-10s %7d %9d %9d %9d %9d %9d %11d %9d" %
         ("TOTAL", tot["n_total"], tot["n_sw"], tot["n_bw"], tot["n_either"],
          tot["n_print"], tot["n_both"], tot["n_chan_only"], tot["n_calls"]))
    emit("")
    emit("直答: 263 件中，产物通道为 sys.stdout.write(...) / sys.stdout.buffer.write(...) 的 = %d 件" % tot["n_either"])
    emit("      其中全件无 print(...) 调用（确为『而不是 print(...)』的通道） = %d 件" % tot["n_chan_only"])
    emit("      严格 sys.stdout.write(...) 形式 = %d 件；sys.stdout.buffer.write(...) 形式 = %d 件" %
         (tot["n_sw"], tot["n_bw"]))
    emit("")

    # 全量命中清单（按 class 分组，附原判据结论）
    emit("== 全量命中清单（%d 件，含两类形式；class/verdict 取自原 json）==" % tot["n_either"])
    for cls in sorted(by_cls):
        for r in by_cls[cls]:
            s = scanned.get(r["rel"])
            if s is None or not (s["sw"] or s["bw"]):
                continue
            calls = sorted(s["sw"] + s["bw"])
            emit("  [%s/%s] %s" % (r["class"], r["verdict"], r["rel"]))
            emit("    stdout写 = %s" % ", ".join("%s@L%d" % (how, ln) for ln, how in calls))
            emit("    print(...)调用数 = %d ; AST别名形式stdout写 = %d" % (len(s["prints"]), len(s["alias"])))
    emit("")

    # class=UNKNOWN 且带 sys.stdout.write 的完整清单
    unk = by_cls.get("UNKNOWN", [])
    unk_hit = [r for r in unk
               if scanned.get(r["rel"]) and (scanned[r["rel"]]["sw"] or scanned[r["rel"]]["bw"])]
    unk_sw = [r for r in unk_hit if scanned[r["rel"]]["sw"]]
    unk_bw_only = [r for r in unk_hit if not scanned[r["rel"]]["sw"]]
    emit("== class=UNKNOWN 且带 sys.stdout.write 的完整清单（含 buffer 形式，共 %d 件）==" % len(unk_hit))
    emit("   UNKNOWN 总件数 = %d ; 命中 = %d ; 未命中 = %d" % (len(unk), len(unk_hit), len(unk) - len(unk_hit)))
    emit("   其中严格 sys.stdout.write(...) = %d 件；仅 sys.stdout.buffer.write(...) = %d 件" %
         (len(unk_sw), len(unk_bw_only)))
    for r in unk_hit:
        s = scanned[r["rel"]]
        calls = sorted(s["sw"] + s["bw"])
        emit("  - %s" % r["rel"])
        emit("      class=%s verdict=%s" % (r["class"], r["verdict"]))
        emit("      行号/形式 = %s" % ", ".join("L%d %s" % (ln, how) for ln, how in calls))
        emit("      n_print=%d ; 原判据 reasons 码 = %s" %
             (len(s["prints"]), ",".join(sorted({x[0] for x in r.get("reasons", [])}))))
    emit("")
    emit("  [严格形式清单，不含 sys.stdout.buffer.write 的 %d 件]" % len(unk_sw))
    for r in unk_sw:
        s = scanned[r["rel"]]
        emit("    %s  %s" % (r["rel"], ",".join("L%d" % ln for ln, _ in sorted(s["sw"]))))
    emit("")
    emit("  [UNKNOWN 中未命中任一 stdout 写调用的 %d 件 —— 用于证明清单完整性]" %
         (len(unk) - len(unk_hit)))
    for r in unk:
        if r not in unk_hit:
            emit("    %s (class=%s verdict=%s)" % (r["rel"], r["class"], r["verdict"]))
    emit("")

    # 误报/漏报自检：文本提及但非 AST 调用；别名形式
    emit("== 自检 ==")
    text_only = [(r, s) for r in rows for s in [scanned.get(r["rel"])]
                 if s and s["text_only"]]
    emit("  文本含 'sys.stdout.write' 但 AST 无对应调用的行 = %d 处（不计入命中）" %
         sum(len(s["text_only"]) for _, s in text_only))
    for r, s in text_only:
        for ln, txt in s["text_only"]:
            emit("    %s:L%d  %s" % (r["rel"], ln, txt))
    alias = [(r, s) for r in rows for s in [scanned.get(r["rel"])] if s and s["alias"]]
    emit("  import sys as / from sys import stdout 的别名形式 stdout 写调用 = %d 处" %
         sum(len(s["alias"]) for _, s in alias))
    for r, s in alias:
        for ln, how in s["alias"]:
            emit("    %s:L%d %s" % (r["rel"], ln, how))
    emit("")

    body = "\n".join(lines) + "\n"
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
