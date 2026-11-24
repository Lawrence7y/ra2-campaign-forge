# -*- coding: utf-8 -*-
"""撰写员独立复核 B：36 处「加固版方案 A」模板逐处验证。
只读历史 payload；还原 GATE_CODE → 套模板 → 预初始化 else-only 变量 → compile
→ 主件在场/缺失两态实跑（沙盒副本，importlib+redirect_stdout，无子进程）。
产出逐处 before/after 片段与断言汇总，只写本写域。
用法: python -I -X utf8 <绝对路径>"""
import json, re, pathlib, hashlib, shutil, importlib.util, io, contextlib, collections

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
WFDIR = ROOT / ".zcode/workflow-runs"
BASE = ROOT / "lead/gate_doc_name_fix_20261109/_dnw_sandbox"
OUT = ROOT / "lead/gate_doc_name_fix_20261109/_dnw_template_out.json"

DEFECT_RE = re.compile(r"DOC\s*=\s*max\s*\(\s*cands\s*,\s*key\s*=\s*lambda\s+p\s*:\s*p\.stat\(\)\.st_size\s*\)")
GATE_HEAD = re.compile(r"const\s+GATE_CODE\s*=\s*\[")

def decode_js(s):
    out = []; i = 0
    mp = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "v": "\v", "\\": "\\", '"': '"', "'": "'", "0": "\0"}
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            c = s[i + 1]
            if c == "u" and i + 5 < len(s):
                try: out.append(chr(int(s[i+2:i+6], 16))); i += 6; continue
                except ValueError: pass
            out.append(mp.get(c, c)); i += 2
        else:
            out.append(s[i]); i += 1
    return "".join(out)

def split_top_level(s):
    elems, buf, i, in_str = [], [], 0, None
    while i < len(s):
        c = s[i]
        if in_str:
            buf.append(c)
            if c == "\\" and i + 1 < len(s):
                buf.append(s[i+1]); i += 2; continue
            if c == in_str: in_str = None
            i += 1; continue
        if c in ('"', "'"):
            in_str = c; buf.append(c); i += 1; continue
        if c == ",":
            elems.append("".join(buf)); buf = []; i += 1; continue
        buf.append(c); i += 1
    if "".join(buf).strip(): elems.append("".join(buf))
    return elems

def reconstruct(e):
    """JS 字符串字面量 + 标识符拼接 → 一条 Python 源码行；运行期 JS 变量用 64 个 0 占位。"""
    out, i = [], 0
    while i < len(e):
        c = e[i]
        if c in ('"', "'"):
            q, j, buf = c, i + 1, []
            while j < len(e):
                if e[j] == "\\" and j + 1 < len(e):
                    buf.append(e[j:j+2]); j += 2; continue
                if e[j] == q: break
                buf.append(e[j]); j += 1
            out.append(decode_js("".join(buf))); i = j + 1
        elif c == "+":
            k = i + 1
            while k < len(e) and (e[k].isspace() or e[k] == "+"): k += 1
            if k < len(e) and e[k] not in ('"', "'"):
                out.append("0" * 64)
                while k < len(e) and not e[k].isspace() and e[k] != "+": k += 1
                i = k
            else:
                i += 1
        else:
            i += 1
    return "".join(out)

def gate_lines(lowered):
    m = GATE_HEAD.search(lowered)
    if not m: return None
    st = m.end()
    j = re.search(r"\]\s*\.join\s*\(", lowered[st:])
    if not j: return None
    return [reconstruct(e) for e in split_top_level(lowered[st:st+j.start()])]

DELIVER_RE = re.compile(r"【交付】[^\[\]]*?([A-Z][A-Z0-9_]*\.md)")

# 采集 36 处原始 GATE_CODE
recs = []
for p in sorted(WFDIR.glob("*.mjs")):
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"export\s+const\s+payload\s*=\s*", text)
    if not m: continue
    obj, _ = json.JSONDecoder().raw_decode(text, m.end())
    low = obj.get("lowered", "")
    lines = gate_lines(low)
    if lines is None: continue
    if not any(DEFECT_RE.search(ln) for ln in lines): continue
    dc = re.findall(r'const\s+DOC\s*=\s*"([^"]+\.md)"', low)
    main = dc[0].split("/")[-1] if dc else (DELIVER_RE.findall(low) or [None])[0]
    wdm = re.search(r"wd\s*=\s*root\s*/\s*'([^']+)'", "\n".join(lines))
    domain = wdm.group(1).split("/")[-1] if wdm else "?"
    si = next((i for i, ln in enumerate(lines) if re.search(r"cands\s*=", ln)), None)
    ei = next((i for i in range(si, len(lines)) if "NB=" in lines[i]), None) if si is not None else None
    seg = lines[si:ei+1] if si is not None and ei is not None else []
    recs.append({"file": p.name, "domain": domain, "main": main, "lines": lines,
                 "si": si, "ei": ei, "before": seg,
                 "is_CAND": bool(seg and "startswith(" in seg[0])})

# before 形态分组
shapes = collections.OrderedDict()
for r in recs:
    shapes.setdefault("\n".join(r["before"]), []).append(r["file"])

def after_segment(main):
    """加固版方案 A 选择段：显式命名 + 缺失即 FAIL + 同次 read_bytes 算 sha256。"""
    return [
        "DOC=wd/'" + main + "';SHA='MISSING'",
        "if not DOC.is_file(): P.append('主件缺失 " + main + "（写域='+wd.name+'）')",
        "else:",
        " raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()",
        " t=raw.decode('utf-8',errors='replace')",
    ]

def else_only_vars(src_lines, print_idx):
    """print 行引用、且在缩进块内赋值（else: 不执行即未定义）的变量名。"""
    pl = src_lines[print_idx]
    names = set(re.findall(r"\b([A-Za-z_]\w*)\b", pl))
    inner = set()
    for ln in src_lines:
        if ln.startswith(" "):
            mm = re.match(r"\s*([A-Za-z_]\w*)\s*=", ln)
            if mm: inner.add(mm.group(1))
    # 顶层已初始化 / 选择段已给 / 模块与内置，一律排除
    top_assigned = set()
    for ln in src_lines:
        if ln and not ln.startswith(" "):
            for nm in re.findall(r"\b([A-Za-z_]\w*)\s*=", ln): top_assigned.add(nm)
    reserved = {"P", "SHA", "NB", "DOC", "t", "B", "raw", "json", "len", "print",
                "pathlib", "re", "hashlib", "root", "wd", "ensure_ascii", "s", "k", "bad",
                "cur", "pre", "lbl", "rel", "p", "i", "j", "mm", "BINDING_RE"}
    return sorted((names & inner) - reserved - top_assigned)

if BASE.exists(): shutil.rmtree(BASE)
BASE.mkdir(parents=True)

def run_module(py):
    spec = importlib.util.spec_from_file_location("_dnw_gate", str(py))
    mod = importlib.util.module_from_spec(spec)
    buf = io.StringIO(); err = None
    try:
        with contextlib.redirect_stdout(buf):
            spec.loader.exec_module(mod)
    except Exception as e:
        err = type(e).__name__ + ": " + str(e)
    last = buf.getvalue().strip().splitlines()[-1] if buf.getvalue().strip() else ""
    try: return json.loads(last), err
    except Exception: return {"ok": None, "raw": last[:160]}, err

rows = []
for r in recs:
    lines = list(r["lines"])
    si, ei, main = r["si"], r["ei"], r["main"]
    # 1) 替换选择段
    new = lines[:si] + after_segment(main) + lines[ei+1:]
    # 2) print 行插入 docSha256:SHA
    print_idx = next(i for i, ln in enumerate(new) if "print(json.dumps(" in ln)
    pl = new[print_idx]
    new[print_idx] = pl.replace("'problems':P,", "'problems':P,'docSha256':SHA,", 1)
    # 3) 预初始化 else-only 变量（顶格，插在 DOC=wd/ 之前）——加固的关键一行
    risky = else_only_vars(new, print_idx)
    anchor = next(i for i, ln in enumerate(new) if "DOC=wd/" in ln)
    toks = []
    for nm in risky:
        toks.append(nm + "=[]" if re.search(r"\blen\(\s*" + re.escape(nm) + r"\s*\)", pl) else nm + "=0")
    init_line = ";".join(toks)
    if init_line:
        new.insert(anchor, init_line)
    src = "\n".join(new)
    rec = {"file": r["file"], "domain": r["domain"], "main": main,
           "is_CAND": r["is_CAND"], "else_only_vars": risky, "init_line": init_line,
           "before": r["before"], "after": after_segment(main),
           "after_print_line": new[print_idx + (1 if init_line else 0)]}
    try:
        compile(src, "<gate:" + r["file"] + ">", "exec"); rec["compile"] = True
    except SyntaxError as e:
        rec["compile"] = False; rec["compile_err"] = str(e)
    # 落盘可执行版：wd 指沙盒、PRE_* 占位换现值 sha
    wd = BASE / r["domain"]
    if not wd.exists(): wd.mkdir(parents=True)
    real = ROOT / "lead" / r["domain"] / main
    (wd / main).write_bytes(real.read_bytes() if real.is_file() else b"")
    runnable = re.sub(r"wd\s*=\s*root\s*/\s*'[^']*'",
                      "wd=pathlib.Path('" + wd.as_posix() + "')", src)
    tup = re.search(r"for\s+lbl,rel,pre\s+in\s*\[(.*?)\]\s*:", runnable, re.S)
    if tup:
        for label, rel, var in re.findall(r"\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*([A-Za-z_]\w*)\s*\)", tup.group(1)):
            f = ROOT / rel
            sha = hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else "MISSING"
            runnable = re.sub(r"(" + re.escape(var) + r"\s*=\s*)'0{64}'",
                              lambda mm: mm.group(1) + "'" + sha + "'", runnable)
    py = wd / "_dnw_gate.py"
    py.write_text(runnable, encoding="utf-8")
    # 在场态
    present, perr = run_module(py)
    rec["present"] = {"ok": present.get("ok"), "doc": present.get("doc"),
                      "sha_head": str(present.get("docSha256", ""))[:12], "err": perr}
    # 缺失态（沙盒副本改名，绝不碰历史）
    absent = wd / ("_absent_" + main)
    os_rename = None
    try:
        import os
        os.rename(wd / main, absent)
        out, aerr = run_module(py)
        probs = out.get("problems") or []
        rec["absent"] = {"ok": out.get("ok"),
                         "has_missing": any("主件缺失" in x for x in probs),
                         "shaMISSING": out.get("docSha256") == "MISSING",
                         "docBytes0": out.get("docBytes") == 0, "err": aerr,
                         "parsed": out.get("ok") is not None}
    finally:
        import os
        if absent.exists() and not (wd / main).exists():
            os.rename(absent, wd / main)
    rows.append(rec)

summary = {
    "sites": len(rows),
    "distinct_before_shapes": len(shapes),
    "before_shape_counts": [len(v) for v in shapes.values()],
    "CAND_variants": [r["file"] for r in rows if r["is_CAND"]],
    "compile_ok": sum(1 for r in rows if r["compile"]),
    "sites_need_init": sum(1 for r in rows if r["else_only_vars"]),
    "present_doc_is_main": sum(1 for r in rows if r["present"]["doc"] == r["main"]),
    "present_no_error": sum(1 for r in rows if r["present"]["err"] is None),
    "absent_parsed": sum(1 for r in rows if r["absent"]["parsed"]),
    "absent_ok_false": sum(1 for r in rows if r["absent"]["ok"] is False),
    "absent_has_missing_msg": sum(1 for r in rows if r["absent"]["has_missing"]),
    "absent_shaMISSING": sum(1 for r in rows if r["absent"]["shaMISSING"]),
    "absent_no_error": sum(1 for r in rows if r["absent"]["err"] is None),
    "absent_errors": [r["file"] for r in rows if r["absent"]["err"]],
}
summary["all_checks_pass"] = (
    summary["sites"] == 36 and summary["compile_ok"] == 36 and
    summary["present_doc_is_main"] == 36 and summary["present_no_error"] == 36 and
    summary["absent_parsed"] == 36 and summary["absent_ok_false"] == 36 and
    summary["absent_has_missing_msg"] == 36 and summary["absent_shaMISSING"] == 36 and
    summary["absent_no_error"] == 36)
out = {"summary": summary,
       "before_shapes": {str(i): {"count": len(v), "files": v, "lines": k.split("\n")}
                         for i, (k, v) in enumerate(shapes.items())},
       "rows": rows}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
print("BEFORE_SHAPES")
for i, (k, v) in enumerate(shapes.items()):
    print(" shape%d count=%d" % (i, len(v)))
    for ln in k.split("\n"): print("   |" + ln)
