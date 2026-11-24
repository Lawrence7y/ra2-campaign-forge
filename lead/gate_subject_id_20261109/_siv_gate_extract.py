# -*- coding: utf-8 -*-
# _siv_gate_extract.py v2 — 还原件忠实性双步闭合：
#  步1：payload GATE_CODE 模板（字面块+变量拼接）用还原件常量值重建 -> 应与还原件逐字节一致；
#  步2：还原件 PRE_* 常量 -> 与当前文件实算 sha256 比对（也证明被指纹件未被改动）。只读。
import hashlib, json, re
from pathlib import Path

BASE = Path(r"D:\Project\ra2-campaign-forge")
WD = BASE / r"lead\gate_subject_id_20261109"
RUNS = BASE / r".zcode\workflow-runs"

def load_payload(p: Path):
    t = p.read_text(encoding="utf-8", errors="ignore")
    i = t.find("export const payload")
    j = t.find("{", i)
    depth = 0
    k = j
    in_str = False
    esc = False
    while k < len(t):
        c = t[k]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(t[j:k + 1])
        k += 1
    return None

def js_unescape(s):
    r = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            n = s[i + 1]
            if n == "n":
                r.append("\n")
            elif n == "t":
                r.append("\t")
            elif n == "r":
                r.append("\r")
            elif n == "'":
                r.append("'")
            elif n == '"':
                r.append('"')
            elif n == "\\":
                r.append("\\")
            elif n == "u" and i + 5 < len(s):
                try:
                    r.append(chr(int(s[i + 2:i + 6], 16)))
                    i += 6
                    continue
                except ValueError:
                    r.append(c)
            else:
                r.append(n)
            i += 2
        else:
            r.append(c)
            i += 1
    return "".join(r)

def extract_template(low):
    """返回 (parts, joiner)：parts 为 [(kind,text)]，kind in lit/ident。"""
    m = re.search(r"const GATE_CODE = \[", low)
    if not m:
        return None, None
    i = m.end()
    n = len(low)
    elements = []
    while i < n:
        while i < n and low[i] in " \t\r\n,":
            i += 1
        if i >= n or low[i] == "]":
            break
        parts = []
        while i < n:
            while i < n and low[i] in " \t\r\n":
                i += 1
            if low[i] == '"':
                i += 1
                buf = []
                while i < n:
                    c = low[i]
                    if c == "\\":
                        buf.append(low[i:i + 2])
                        i += 2
                        continue
                    if c == '"':
                        i += 1
                        break
                    buf.append(c)
                    i += 1
                parts.append(("lit", js_unescape("".join(buf))))
            elif low[i] == "+":
                i += 1
                continue
            else:
                m2 = re.match(r"[A-Za-z_$][A-Za-z0-9_$]*", low[i:])
                if not m2:
                    break
                parts.append(("ident", m2.group(0)))
                i += len(m2.group(0))
            # 元素边界：下一个非空白字符是 , 或 ]
            j2 = i
            while j2 < n and low[j2] in " \t\r\n":
                j2 += 1
            if j2 >= n or low[j2] in ",]":
                i = j2
                break
        elements.append(parts)
    m3 = re.search(r"\]\.join\(", low[m.end():])
    joiner_m = re.search(r'\]\.join\("([^"]*)"\)', low)
    joiner = joiner_m.group(1).encode().decode("unicode_escape") if joiner_m else "\n"
    return elements, joiner

def sha256_file(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()

out = {}
cases = [
    (RUNS / "dwfrun-636adfc5-7ca1-4948-a711-f8027d8de9e2.mjs", WD / "_si_gate_counterpart_extracted.py",
     {"matSha": r"lead\b2b_design_20261106\STATE_MATRIX.json",
      "desSha": r"lead\b2b_design_20261106\B2B_DESIGN.md",
      "candSha": r"lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py",
      "v2Sha": r"lead\n4_yi_final_20261108\_n4v2_B_EXECUTION_SPEC_V2.md",
      "motherSha": r"out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py"}),
    (RUNS / "dwfrun-a7468d6e-e9f6-4050-896a-7bff15c96903.mjs", WD / "_si_gate_self_extracted.py", {}),
]
for mjs, extracted, varfile in cases:
    pl = load_payload(mjs)
    low = pl["lowered"]
    elements, joiner = extract_template(low)
    ext = extracted.read_text(encoding="utf-8")
    idents = sorted({t for e in elements for k2, t in e if k2 == "ident"})
    # 步1：ident -> 还原件常量值（按 GATE_CODE 内 PRE_X= 顺序对应）
    rebuilt_parts = []
    ext_hash_map = {}
    for m4 in re.finditer(r"PRE_([A-Z]{1,2})='([0-9a-f]{64})'", ext):
        ext_hash_map["PRE_" + m4.group(1)] = m4.group(2)
    ident2val = {}
    # 顺序约定：payload 模板里 ident 出现顺序 == 还原件 PRE_ 行顺序
    pre_order = re.findall(r"PRE_([A-Z]{1,3})='([0-9a-f]{64})'", ext)
    ident_seq = [t for e in elements for k2, t in e if k2 == "ident"]
    if len(ident_seq) == len(pre_order):
        for iid, (px, hv) in zip(ident_seq, pre_order):
            ident2val[iid] = hv
    rebuilt = []
    for e in elements:
        s = ""
        for k2, t in e:
            if k2 == "lit":
                s += t
            else:
                s += ident2val.get(t, "<UNRESOLVED:" + t + ">")
        rebuilt.append(s)
    mine = joiner.join(rebuilt)
    identical = (mine == ext)
    print("=== " + mjs.name)
    print("  elements=" + str(len(elements)) + " idents=" + repr(ident_seq) + " joiner=" + repr(joiner))
    print("  step1 rebuilt == extracted: " + str(identical) + "  (mine len=" + str(len(mine)) + " ext len=" + str(len(ext)) + ")")
    if not identical:
        d = 0
        n = min(len(mine), len(ext))
        while d < n and mine[d] == ext[d]:
            d += 1
        print("  first_diff@" + str(d) + " mine=" + repr(mine[max(0, d - 50):d + 50]) + " ext=" + repr(ext[max(0, d - 50):d + 50]))
    # 步2：常量值 vs 当前文件实算
    checks = {}
    if varfile:
        for var, rel in varfile.items():
            cur = sha256_file(BASE / rel)
            used = ident2val.get(var)
            checks[var] = {"file": rel, "currentSha": cur, "extractedConstant": used, "match": cur == used}
            print("  step2 " + var + ": current=" + cur[:16] + "... extractedConst=" + (used[:16] + "..." if used else "None") + " match=" + str(cur == used))
    else:
        for px, hv in [("PRE_H", r"lead\PENDING_DECISIONS.md"), ("PRE_GO", r"lead\GOAL_THREE_TARGETS_20261018.md")]:
            cur = sha256_file(BASE / px and BASE / hv)
            used = ext_hash_map.get(px)
            checks[px] = {"file": hv, "currentSha": cur, "extractedConstant": used, "match": cur == used}
            print("  step2 " + px + ": current=" + cur[:16] + "... extractedConst=" + (used[:16] + "..." if used else "None") + " match=" + str(cur == used))
    out[mjs.name] = {"identical": identical, "identSeq": ident_seq, "preOrder": [p[0] for p in pre_order], "checks": checks}

w = WD / "_siv_gate_extract_out.json"
w.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("written=" + str(w))
