# 独立复核员脚本 ③：把设计回件 §2.1 模板原样套到 36 处，验证可粘贴性 + 主件缺失即 FAIL
# 不使用被核方的 _dn_glm_patch36_out.json；自己从 payload 还原 GATE_CODE 行 → 替换 → compile → 实跑
import json, re, pathlib, hashlib, subprocess, tempfile, os, ast, sys, shutil

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
WFDIR = ROOT / ".zcode/workflow-runs"
OUT = ROOT / "lead/gate_doc_name_fix_20261109/_dnv_patch36_out.json"
DEFECT_RE = re.compile(r"DOC\s*=\s*max\s*\(\s*cands\s*,\s*key\s*=\s*lambda\s+p\s*:\s*p\.stat\(\)\.st_size\s*\)")
GATE_HEAD = re.compile(r"const\s+GATE_CODE\s*=\s*\[")
JS_STR = re.compile(r'"(?:[^"\\]|\\.)*"')

def decode_js(tok):
    s = tok[1:-1]; out = []; i = 0
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

def gate_lines(lowered):
    m = GATE_HEAD.search(lowered)
    if not m: return None
    st = m.end()
    j = re.search(r"\]\s*\.join\s*\(", lowered[st:])
    if not j: return None
    return [decode_js(t) for t in JS_STR.findall(lowered[st:st+j.start()])]

# 设计回件声称的「改前 5 行」（§2.1，逐字）
CLAIMED_BEFORE = [
    "cands=sorted(wd.glob('*.md')) if wd.is_dir() else []",
    "if not cands: P.append('写域内无 md 交付件')",
    "else:",
    " DOC=max(cands,key=lambda p:p.stat().st_size)",
    " t=DOC.read_text(encoding='utf-8');NB=DOC.stat().st_size",
]

def make_after(main):
    # 设计回件 §2.1「改后 5 行」逐字，<MAIN> 代入
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
    # 找选择段：从 cands= 行到 NB= 行（含）
    si = next((i for i, ln in enumerate(lines) if re.search(r"cands\s*=", ln)), None)
    ei = next((i for i in range(si, len(lines)) if "NB=" in lines[i]), None) if si is not None else None
    seg = lines[si:ei+1] if si is not None and ei is not None else []
    rec = {"file": p.name, "domain": domain, "main": main, "seg_start": si, "seg_end": ei,
           "seg": seg, "seg_len": len(seg)}
    rec["claimed_before_exact"] = (seg == CLAIMED_BEFORE)
    rec["cands_line"] = seg[0] if seg else None
    rec["is_CAND_variant"] = bool(seg and "startswith(" in seg[0])
    rec["gate_lines_count"] = len(lines)
    rec["all_lines"] = lines
    recs.append(rec)

# 统计「改前 5 行」逐字相符几处
shapes = {}
for r in recs:
    k = "\n".join(r["seg"])
    shapes.setdefault(k, []).append(r["file"])

# 逐处替换（按设计描述：删 seg，插改后 5 行；print 行插 'docSha256':SHA,）
rows = []
for r in recs:
    lines = list(r["all_lines"])
    si, ei = r["seg_start"], r["seg_end"]
    after = make_after(r["main"])
    new = lines[:si] + after + lines[ei+1:]
    # print 行最小插入
    nprint = 0
    for i, ln in enumerate(new):
        if "print(json.dumps(" in ln and "'problems':P," in ln:
            new[i] = ln.replace("'problems':P,", "'problems':P,'docSha256':SHA,", 1)
            nprint += 1
    src = "\n".join(new)
    r2 = {"file": r["file"], "domain": r["domain"], "main": r["main"],
          "claimed_before_exact": r["claimed_before_exact"], "is_CAND_variant": r["is_CAND_variant"],
          "print_inserted": nprint, "src_lines": len(new)}
    try:
        compile(src, "<gate:" + r["file"] + ">", "exec")
        r2["python_compiles"] = True
    except SyntaxError as e:
        r2["python_compiles"] = False
        r2["compile_error"] = str(e)
    r2["after_no_docmax"] = not any("DOC=max(" in ln for ln in new)
    r2["after_explicit"] = any("DOC=wd/'" + r["main"] + "'" in ln for ln in new)
    r2["after_fail_on_missing"] = any("if not DOC.is_file()" in ln and "主件缺失" in ln for ln in new)
    r2["after_sha"] = any("hashlib.sha256(raw)" in ln for ln in new)
    r2["preserves_init"] = lines[3] == new[3] if len(lines) > 3 and len(new) > 3 else None
    r2["src"] = src
    rows.append(r2)

# 实跑：把改后门禁施于沙盒（主件在场 / 主件改名为 absent），检验 ok 与 problems
# 用真实域的 main 内容填充沙盒主件（只读拷贝），wd 指向沙盒目录；PRE_* 指纹段指向真实台账，现值相符故不干扰
sandbox_base = ROOT / "lead/gate_doc_name_fix_20261109/_dnv_sandbox36"
if sandbox_base.exists(): shutil.rmtree(sandbox_base)
sandbox_base.mkdir(parents=True)
run_rows = []
for r2 in rows:
    wd = sandbox_base / r2["domain"]
    if not wd.exists(): wd.mkdir(parents=True)
    # 主件内容：从真实域复制（只读）
    real = ROOT / "lead" / r2["domain"] / r2["main"]
    content = real.read_bytes() if real.is_file() else b""
    (wd / r2["main"]).write_bytes(content)
    src = r2["src"].replace("wd=root/'lead/" + r2["domain"] + "'", "wd=pathlib.Path('" + wd.as_posix() + "')")
    # 若原 wd 写法不同，做通用替换
    src = re.sub(r"wd\s*=\s*root\s*/\s*'[^']*'", "wd=pathlib.Path('" + wd.as_posix() + "')", src)
    # 场景 A：主件在场
    try:
        cp = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", src], capture_output=True, text=True, timeout=30)
        outA = cp.stdout.strip().splitlines()[-1] if cp.stdout.strip() else ""
        a = json.loads(outA)
    except Exception as e:
        a = {"ok": None, "parse_error": str(e), "stderr": cp.stderr[-400:] if 'cp' in locals() else ""}
    # 场景 B：主件改名（模拟缺失），不动真实域
    os.rename(wd / r2["main"], wd / ("_absent_" + r2["main"]))
    try:
        cp2 = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", src], capture_output=True, text=True, timeout=30)
        outB = cp2.stdout.strip().splitlines()[-1] if cp2.stdout.strip() else ""
        b = json.loads(outB)
    except Exception as e:
        b = {"ok": None, "parse_error": str(e)}
    os.rename(wd / ("_absent_" + r2["main"]), wd / r2["main"])
    run_rows.append({"file": r2["file"], "main": r2["main"],
                     "present": {"ok": a.get("ok"), "doc": a.get("doc"), "docSha256": (a.get("docSha256") or "")[:16],
                                 "problems": a.get("problems"), "exit": cp.returncode if 'cp' in locals() else None},
                     "absent": {"ok": b.get("ok"), "doc": b.get("doc"), "problems": b.get("problems"),
                                "docBytes": b.get("docBytes"), "shaMISSING": b.get("docSha256") == "MISSING"}})

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
    "absent_ok_false": sum(1 for r in run_rows if r["absent"]["ok"] is False),
    "absent_problem_has_missing": sum(1 for r in run_rows if r["absent"]["problems"] and any("主件缺失" in x for x in r["absent"]["problems"])),
    "absent_shaMISSING": sum(1 for r in run_rows if r["absent"]["shaMISSING"]),
    "present_all_parsed": sum(1 for r in run_rows if r["present"]["ok"] is not None),
}
OUT.write_text(json.dumps({"summary": summary, "rows": [{k: v for k, v in r.items() if k != "src"} for r in rows],
                           "run_rows": run_rows, "before_shapes": {str(i): {"count": len(v), "files": v, "seg": k.split("\n")} for i, (k, v) in enumerate(shapes.items())}},
                          ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
