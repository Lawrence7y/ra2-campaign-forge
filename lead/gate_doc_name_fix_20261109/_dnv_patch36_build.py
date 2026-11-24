# 独立复核员脚本 ③-A：从零还原 36 处 GATE_CODE，套用 §2.1 模板，compile 校验并落盘为纯门禁 .py 文件
# 不在本脚本内动态执行/调用子进程；产出 .py 由 Bash 以 python -I -X utf8 <绝对路径> 直接跑
# 不使用被核方 _dn_glm_patch36_out.json
import json, re, pathlib, hashlib, shutil

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
WFDIR = ROOT / ".zcode/workflow-runs"
BASE = ROOT / "lead/gate_doc_name_fix_20261109/_dnv_sandbox36"
OUT = ROOT / "lead/gate_doc_name_fix_20261109/_dnv_patch36_out.json"
DEFECT_RE = re.compile(r"DOC\s*=\s*max\s*\(\s*cands\s*,\s*key\s*=\s*lambda\s+p\s*:\s*p\.stat\(\)\.st_size\s*\)")
GATE_HEAD = re.compile(r"const\s+GATE_CODE\s*=\s*\[")

def decode_js(s):
    out = []; i = 0
    mp = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "v": "\v", "\\": "\\", '"': '"', "'": "'", "0": "\0"}
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            c = s[i+1]
            if c == "u" and i + 5 < len(s):
                try: out.append(chr(int(s[i+2:i+6], 16))); i += 6; continue
                except ValueError: pass
            out.append(mp.get(c, c)); i += 2
        else: out.append(s[i]); i += 1
    return "".join(out)

def split_top_level(s):
    elems = []; buf = []; i = 0; in_str = None
    while i < len(s):
        c = s[i]
        if in_str:
            buf.append(c)
            if c == "\\" and i + 1 < len(s):
                buf.append(s[i+1]); i += 2; continue
            if c == in_str: in_str = None
            i += 1; continue
        if c == '"' or c == "'":
            in_str = c; buf.append(c); i += 1; continue
        if c == ",":
            elems.append("".join(buf)); buf = []; i += 1; continue
        buf.append(c); i += 1
    if "".join(buf).strip(): elems.append("".join(buf))
    return elems

def reconstruct(e):
    """字符串字面量 + 标识符拼接 → 一条 Python 源码行；JS 运行期变量用 64 个 0 占位"""
    out = []; i = 0
    while i < len(e):
        c = e[i]
        if c == '"' or c == "'":
            q = c; j = i + 1; buf = []
            while j < len(e):
                if e[j] == "\\" and j + 1 < len(e):
                    buf.append(e[j:j+2]); j += 2; continue
                if e[j] == q: break
                buf.append(e[j]); j += 1
            out.append(decode_js("".join(buf)))
            i = j + 1
        elif c == "+":
            k = i + 1
            while k < len(e) and (e[k].isspace() or e[k] == "+"): k += 1
            if k < len(e) and e[k] not in "\"'":
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

CLAIMED_BEFORE = [
    "cands=sorted(wd.glob('*.md')) if wd.is_dir() else []",
    "if not cands: P.append('写域内无 md 交付件')",
    "else:",
    " DOC=max(cands,key=lambda p:p.stat().st_size)",
    " t=DOC.read_text(encoding='utf-8');NB=DOC.stat().st_size",
]

def make_after(main):
    return [
        "DOC=wd/'" + main + "';SHA='MISSING'",
        "if not DOC.is_file(): P.append('主件缺失 " + main + "（写域='+wd.name+'）')",
        "else:",
        " raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()",
        " t=raw.decode('utf-8',errors='replace')",
    ]

recs = []
for p in sorted(WFDIR.glob("*.mjs")):
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"export\s+const\s+payload\s*=\s*", text)
    if not m: continue
    obj, _ = json.JSONDecoder().raw_decode(text, m.end())
    lowered = obj.get("lowered", "")
    lines = gate_lines(lowered)
    if lines is None: continue
    if not any(DEFECT_RE.search(ln) for ln in lines): continue
    dc = re.findall(r'const\s+DOC\s*=\s*"([^"]+)"', lowered)
    DELIVER_RE = re.compile(r"【交付】[^\[\]]*?([A-Z][A-Z0-9_]*\.md)")
    main = dc[0].split("/")[-1] if dc else (DELIVER_RE.findall(lowered) or [None])[0]
    wdm = re.search(r"wd\s*=\s*root\s*/\s*'([^']+)'", "\n".join(lines))
    domain = wdm.group(1).split("/")[-1] if wdm else "?"
    si = next((i for i, ln in enumerate(lines) if re.search(r"cands\s*=", ln)), None)
    ei = next((i for i in range(si, len(lines)) if "NB=" in lines[i]), None) if si is not None else None
    seg = lines[si:ei+1] if si is not None and ei is not None else []
    recs.append({"file": p.name, "domain": domain, "main": main, "seg_start": si, "seg_end": ei,
                 "seg": seg, "is_CAND_variant": bool(seg and "startswith(" in seg[0]),
                 "claimed_before_exact": (seg == CLAIMED_BEFORE), "all_lines": lines})

shapes = {}
for r in recs:
    shapes.setdefault("\n".join(r["seg"]), []).append(r["file"])

if BASE.exists(): shutil.rmtree(BASE)
BASE.mkdir(parents=True)
rows = []
for r in recs:
    lines = list(r["all_lines"])
    si, ei = r["seg_start"], r["seg_end"]
    new = lines[:si] + make_after(r["main"]) + lines[ei+1:]
    nprint = 0
    for i, ln in enumerate(new):
        if "print(json.dumps(" in ln and "'problems':P," in ln:
            new[i] = ln.replace("'problems':P,", "'problems':P,'docSha256':SHA,", 1)
            nprint += 1
    src = "\n".join(new)
    rec = {"file": r["file"], "domain": r["domain"], "main": r["main"],
           "claimed_before_exact": r["claimed_before_exact"], "is_CAND_variant": r["is_CAND_variant"],
           "print_inserted": nprint, "src_lines": len(new)}
    try:
        compile(src, "<gate:" + r["file"] + ">", "exec"); rec["python_compiles"] = True
    except SyntaxError as e:
        rec["python_compiles"] = False; rec["compile_error"] = str(e)
    rec["after_no_docmax"] = not any("DOC=max(" in ln for ln in new)
    rec["after_explicit"] = any("DOC=wd/'" + r["main"] + "'" in ln for ln in new)
    rec["after_fail_on_missing"] = any("if not DOC.is_file()" in ln and "主件缺失" in ln for ln in new)
    rec["after_sha"] = any("hashlib.sha256(raw)" in ln for ln in new)
    # 落盘为可直接执行的 .py：wd 指向沙盒域；PRE_* 占位符换成上游文件现值 sha
    wd = BASE / r["domain"]
    if not wd.exists(): wd.mkdir(parents=True)
    real = ROOT / "lead" / r["domain"] / r["main"]
    (wd / r["main"]).write_bytes(real.read_bytes() if real.is_file() else b"")
    runnable = re.sub(r"wd\s*=\s*root\s*/\s*'[^']*'", "wd=pathlib.Path('" + wd.as_posix() + "')", src)
    tup = re.search(r"for\s+lbl,rel,pre\s+in\s*\[(.*?)\]\s*:", runnable, re.S)
    if tup:
        for label, rel, var in re.findall(r"\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*([A-Za-z_]\w*)\s*\)", tup.group(1)):
            f = ROOT / rel
            sha = hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else "MISSING"
            runnable = re.sub(r"(" + re.escape(var) + r"\s*=\s*)'0{64}'", lambda mm: mm.group(1) + "'" + sha + "'", runnable)
    gate_py = wd / "_dnv_gate.py"
    gate_py.write_text(runnable, encoding="utf-8")
    rec["gate_py"] = gate_py.as_posix()
    rec["wd"] = wd.as_posix()
    rows.append(rec)

summary = {
    "sites": len(rows),
    "claimed_before_exact_count": sum(1 for r in rows if r["claimed_before_exact"]),
    "claimed_before_exact_false": [r["file"] for r in rows if not r["claimed_before_exact"]],
    "distinct_before_segments": len(shapes),
    "distinct_before_segments_counts": [len(v) for v in shapes.values()],
    "CAND_variant_files": [r["file"] for r in rows if r["is_CAND_variant"]],
    "python_compiles": sum(1 for r in rows if r["python_compiles"]),
    "compile_errors": [{"file": r["file"], "err": r.get("compile_error")} for r in rows if not r["python_compiles"]],
    "print_inserted": sum(1 for r in rows if r["print_inserted"] == 1),
    "after_no_docmax": sum(1 for r in rows if r["after_no_docmax"]),
    "after_explicit": sum(1 for r in rows if r["after_explicit"]),
    "after_fail_on_missing": sum(1 for r in rows if r["after_fail_on_missing"]),
    "after_sha": sum(1 for r in rows if r["after_sha"]),
}
OUT.write_text(json.dumps({"summary": summary, "rows": rows,
                           "before_shapes": {str(i): {"count": len(v), "files": v, "seg": k.split("\n")} for i, (k, v) in enumerate(shapes.items())}},
                          ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
