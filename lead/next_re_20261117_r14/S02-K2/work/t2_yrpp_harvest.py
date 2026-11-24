# -*- coding: utf-8 -*-
"""S02-K2 / T2 evidence harvest: extract YRpp address macros (JMP_STD/JMP/CALL/CALL_STD/...)
from all YRpp files, keep addresses that are S02 TARGETS, parse the preceding C/C++ function
signature to get the symbol name, and verify the address is a real function boundary.
This is EXTERNAL SYMBOL-TABLE evidence (not byte-shape matching)."""
import os, re, csv, json, sys
sys.path.insert(0, os.path.dirname(__file__))
import s02_common as C

YRPP = os.path.join(C.ROOT, "YRpp")
MACRO_RE = re.compile(r'\b(JMP_STD|JMP|CALL_STD|CALL|SET_REG|JMP_VFUNC|CALL_VFUNC)\s*\(\s*0x([0-9A-Fa-f]{1,8})\b')
# function signature: capture the identifier immediately before the '(' of the signature,
# line(s) before the macro. We look at a window of the previous up-to-4 non-empty lines.
NAME_RE = re.compile(r'\b(?:static\s+)?[\w:<>,\s\*&]+?\b([A-Za-z_]\w*)\s*\([^;]*\)\s*(?:const\s*)?(?:noexcept\s*)?\{?\s*$')

def load_target_set():
    rows = C.load_targets()
    return {r["entry"]: r for r in rows}

def harvest():
    targets = load_target_set()
    hits = {}   # addr8 -> list of {file,line,macro,name,rawline,window}
    for root, dirs, files in os.walk(YRPP):
        for fn in files:
            if not fn.lower().endswith((".h", ".hpp", ".cpp", ".inl", ".c")):
                continue
            path = os.path.join(root, fn)
            try:
                lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
            except Exception:
                continue
            for i, line in enumerate(lines):
                for m in MACRO_RE.finditer(line):
                    macro, addr = m.group(1), m.group(2).upper().zfill(8)
                    if addr not in targets:
                        continue
                    # window of previous up to 5 non-empty lines
                    prev = []
                    j = i - 1
                    while j >= 0 and len(prev) < 5:
                        s = lines[j].strip()
                        if s:
                            prev.append((j+1, s))
                        j -= 1
                    prev.reverse()
                    # find function name: scan window lines CLOSEST-first (the signature is on
                    # the line immediately before the JMP_STD), then current line.
                    name = None
                    sig_line = None
                    for (ln, s) in list(reversed(prev)) + [(i+1, line[:m.start()])]:
                        # strip comments
                        s2 = re.sub(r'//.*$', '', s)
                        # match an identifier directly followed by '('
                        for nm in re.finditer(r'\b([A-Za-z_]\w*)\s*\(', s2):
                            cand = nm.group(1)
                            if cand in ("JMP_STD","JMP","CALL_STD","CALL","if","for","while","switch","sizeof","__declspec"):
                                continue
                            name = cand
                            sig_line = ln
                            break
                        if name:
                            break
                    rel = os.path.relpath(path, C.ROOT)
                    hits.setdefault(addr, []).append(dict(
                        file=rel, line=i+1, macro=macro, name=name, sig_line=sig_line,
                        raw=line.strip(), window=prev))
    return targets, hits

def is_boundary(va):
    """check the 16-byte-aligned-ish entry: first bytes decodable and function-like prologue-ish.
    We only assert 'decodable instruction boundary at exact address' via capstone one-instruction decode."""
    b = C.read_bytes(va, 16)
    ins = list(C.md.disasm(b, va, count=1))
    return ins[0] if ins else None

if __name__ == "__main__":
    targets, hits = load_target_set(), None
    targets, hits = harvest()
    print("S02 targets with a YRpp address macro:", len(hits))
    out = []
    for addr in sorted(hits):
        r = targets[addr]
        first = is_boundary(int(addr,16))
        dec = ("%s %s" % (first.mnemonic, first.op_str)) if first else "UNDECODABLE"
        cur_name = r["cov_name"]
        names = sorted(set(h["name"] for h in hits[addr] if h["name"]))
        files = sorted(set((h["file"], h["line"]) for h in hits[addr]))
        out.append((addr, cur_name, names, files, dec))
        print("0x%s current=%-28s yrpp_names=%-24s first=%-24s files=%s" %
              (addr, cur_name, ",".join(names), dec, files[:3]))
    # dump json
    with open(os.path.join(C.CARD, "work", "yrpp_hits.json"), "w", encoding="utf-8") as f:
        json.dump({a: hits[a] for a in hits}, f, ensure_ascii=False, indent=1)
    print("\nTOTAL", len(hits))
