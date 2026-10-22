"""R0-b: extract VA -> symbol candidates from the corpus, section-validated.

The corpus is table-dominated, so rows are split into cells rather than
matched with one monolithic regex. Every candidate address is validated
against the PE section table, which rejects raw-RVA columns and hex-byte
noise instead of letting them pollute the map.

Read-only; prints JSON.
"""

import json
import os
import re
import struct

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
CORPUS_DIRS = ["docs/re", "docs/re/atlas_rev", "lead/goal3_audit"]

VA_TOKEN = re.compile(r"0x([0-9A-Fa-f]{8})")
BACKTICK_ID = re.compile(r"`([^`]{2,80})`")
BOLD_ID = re.compile(r"\*\*([^*]{2,80})\*\*")
# prose: 0x00xxxxxx 为/是/对应 Name    or    Name (0x00xxxxxx)
PROSE_FWD = re.compile(r"0x([0-9A-Fa-f]{8})\s*(?:为|是|即|对应|=)\s*[`*]?([A-Za-z_][A-Za-z0-9_:~<>*&\- ]{2,60})")
PROSE_PAREN = re.compile(r"([A-Za-z_][A-Za-z0-9_:~]{2,60})[`*]*\s*[（(]\s*0x([0-9A-Fa-f]{8})")
# claims-style: 0x<site> = <bytes>  # <semantic name> ...
CLAIM_LINE = re.compile(r"^(?:0x)?([0-9A-Fa-f]{8})\s*=\s*((?:[0-9A-Fa-f]{2}\s+)+)#\s*(.+)$")

NOISE_EXACT = {
    "va", "ok", "none", "nop", "ret", "mov", "call", "jmp", "lea", "push", "pop",
    "cmp", "test", "add", "sub", "xor", "and", "or", "inc", "dec", "byte", "ptr",
    "dword", "word", "the", "and", "for", "with", "see", "line", "file", "row",
    "size", "base", "addr", "offset", "self", "true", "false", "null", "bss",
    "va:", "addr:", "地址", "见", "参见", "n/a", "todo", "tbd",
}
HEXSTR = re.compile(r"^[0-9A-Fa-f]{2}(\s+[0-9A-Fa-f]{2})*$")
# anything that reads like disassembly rather than a symbol name
ASMISH = re.compile(
    r"\b(?:mov|call|jmp|lea|push|pop|cmp|test|xor|add|sub|jle|jge|je|jne|ja|jb|"
    r"ret|nop|inc|dec|shl|shr|and|or|imul|div|fld|fstp|fadd|fmul|movzx|movsx)\b"
    r"|ptr\s*\[|\[\s*0x|^\s*(?:db|dw|dd)\b",
    re.I,
)
IDENT_SHAPE = re.compile(r"^[A-Za-z_?$@][A-Za-z0-9_?$@:~<>*&\- ]*$")
# words that describe a calling convention or a literal, never a symbol
LITERAL_WORDS = {
    "thiscall", "cdecl", "stdcall", "fastcall", "nullptr", "return", "const",
    "static", "void", "int", "bool", "unsigned", "struct", "class", "template",
    "typename", "uint32_t", "uint8_t", "uintptr_t", "int32_t", "char", "float",
    "double", "long", "short", "extern", "inline", "virtual", "public", "private",
}


def is_asmish(name):
    return bool(ASMISH.search(name)) or name.count(";") >= 1


def load_sections(path):
    with open(path, "rb") as fh:
        blob = fh.read()
    e = struct.unpack_from("<I", blob, 0x3C)[0]
    nsec = struct.unpack_from("<H", blob, e + 6)[0]
    opt_size = struct.unpack_from("<H", blob, e + 20)[0]
    opt = e + 24
    image_base = struct.unpack_from("<I", blob, opt + 28)[0]
    sec_tab = opt + opt_size
    secs = []
    for i in range(nsec):
        off = sec_tab + i * 40
        name = blob[off:off + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", blob, off + 8)
        secs.append((name, image_base + vaddr, image_base + max(vsize, rawsize)))
    return image_base, secs


IMAGE_BASE, SECS = load_sections(EXE)


def in_image(va):
    for name, lo, hi in SECS:
        if lo <= va < hi:
            return name
    return None


def clean(name):
    n = name.strip().strip("`*_ ").strip()
    n = n.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", n)


def plausible(name):
    if not name or len(name) < 3 or len(name) > 70:
        return False
    low = name.lower().rstrip(":：")
    if low in NOISE_EXACT:
        return False
    if HEXSTR.match(name):
        return False
    if re.fullmatch(r"0x[0-9A-Fa-f]+", name):
        return False
    if is_asmish(name):
        return False
    if not re.search(r"[A-Za-z]{2}", name):
        return False
    if "(" in name and ")" in name:
        return False
    if re.search(r"[=<>{}]", name):
        return False
    if name.lower() in LITERAL_WORDS:
        return False
    if " = " in name or name.startswith(("vptr", "file", "site")):
        return False
    if re.search(r"\.(?:md|txt|json|py|cpp|h)\b", name):
        return False
    return True


def row_cells(line):
    if not line.lstrip().startswith("|"):
        return None
    parts = [c for c in line.split("|")]
    if len(parts) < 3:
        return None
    # drop leading/trailing empties produced by the outer pipes
    return [p.strip() for p in parts[1:-1]]


def mine(text, rel):
    hits = []
    for line in text.splitlines():
        s = line.rstrip()

        m = CLAIM_LINE.match(s.strip())
        if m:
            va = int(m.group(1), 16)
            comment = m.group(3)
            # a claim comment names its subject before the first ':' separator,
            # e.g. "CurrentFrame 读取: mov edx, ..." -> "CurrentFrame 读取"
            head = re.split(r"[:：]", comment, maxsplit=1)[0]
            head = re.sub(r"^(?:0x[0-9A-Fa-f]{8}\s*)", "", head).strip()
            if in_image(va) and plausible(clean(head)):
                hits.append((va, clean(head), "claim", rel))

        cells = row_cells(s)
        if cells:
            cell_vas = []
            for idx, c in enumerate(cells):
                for vm in VA_TOKEN.finditer(c):
                    v = int(vm.group(1), 16)
                    if in_image(v):
                        cell_vas.append((idx, v))
            if cell_vas:
                # Bind each address to the nearest name cell, preferring the
                # cell to its left. Corpus tables are overwhelmingly
                # "name | address | notes", so text to the right of an address
                # is description and can name a *different* (called) symbol.
                def name_in(ci):
                    if not (0 <= ci < len(cells)):
                        return None
                    c = cells[ci]
                    if VA_TOKEN.search(c):
                        return None
                    for bm in BACKTICK_ID.finditer(c):
                        cand = clean(bm.group(1))
                        if plausible(cand):
                            return cand
                    for bm in BOLD_ID.finditer(c):
                        cand = clean(bm.group(1))
                        if plausible(cand):
                            return cand
                    cand = clean(c)
                    return cand if plausible(cand) else None

                for idx, v in cell_vas:
                    nm = name_in(idx - 1) or name_in(idx + 1) or name_in(0)
                    if nm:
                        hits.append((v, nm, "row", rel))

        for pm in PROSE_FWD.finditer(s):
            v, nm = int(pm.group(1), 16), clean(pm.group(2))
            if in_image(v) and plausible(nm):
                hits.append((v, nm, "prose", rel))
        for pm in PROSE_PAREN.finditer(s):
            v, nm = int(pm.group(2), 16), clean(pm.group(1))
            if in_image(v) and plausible(nm):
                hits.append((v, nm, "paren", rel))
    return hits


def main():
    all_hits = []
    for d in CORPUS_DIRS:
        full = os.path.join(ROOT, d)
        if not os.path.isdir(full):
            continue
        for name in sorted(os.listdir(full)):
            if not name.lower().endswith((".md", ".txt")):
                continue
            try:
                with open(os.path.join(full, name), "r", encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue
            rel = os.path.relpath(os.path.join(full, name), ROOT).replace("\\", "/")
            all_hits.extend(mine(text, rel))

    agg = {}
    for va, sym, how, rel in all_hits:
        rec = agg.setdefault(va, {})
        srec = rec.setdefault(sym, {"count": 0, "srcs": [], "how": []})
        srec["count"] += 1
        if rel not in srec["srcs"]:
            srec["srcs"].append(rel)
        if how not in srec["how"]:
            srec["how"].append(how)

    flat = {}
    for va, syms in agg.items():
        flat[f"0x{va:08X}"] = {
            "section": in_image(va),
            "symbols": {s: {"count": v["count"], "srcs": sorted(v["srcs"]), "how": sorted(v["how"])}
                        for s, v in sorted(syms.items(), key=lambda kv: -kv[1]["count"])},
        }

    print(json.dumps({"total_hits": len(all_hits), "distinct_va": len(flat), "map": flat},
                     ensure_ascii=False, indent=1, sort_keys=True))


main()
