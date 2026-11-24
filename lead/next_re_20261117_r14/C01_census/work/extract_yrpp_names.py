"""Parse YRpp headers -> address->ClassName::Method mappings.
Handles JMP_THIS(0x...), JMP_STD(0x...), JMP(0x...) macros.
The declaration line is the nearest preceding line ending in ')' with an identifier before '('.
"""
import os, re, json

PROJECT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
YRPP = os.path.join(PROJECT, "YRpp")

MACRO_RE = re.compile(r'\b(JMP_THIS|JMP_STD|JMP)\s*\(\s*0x([0-9A-Fa-f]{6,8})\s*\)')
# FIX (C01 FIX round): original regex only matched `class X;` / `class X :`,
# so forward declarations leaked into cur_class and subsequent `class X {`
# definitions were missed (VocClass:: / TechnoClass:: / Status:: / HouseClass::
# / BombClass ctor name leaks, 23-24 rows). Match `;` `:` AND `{`.
# `class X` / `struct X` with `{` on the NEXT line is common in YRpp
# (struct AudioController\n{ , class BaseClass\n{ , class BombListClass\n{ ),
# so also accept end-of-line. `\s*$` avoids matching pointer params like `class X* p`.
CLASS_RE = re.compile(r'\b(?:class|struct)\s+(?:NOVTABLE\s+)?([A-Za-z_]\w*)\s*(?::|;|\{|$)')
# function decl: last identifier before '(' on the declaration line (may contain params)
NAME_RE = re.compile(r'([~A-Za-z_]\w*)\s*\(')

def iter_h_files(root):
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if fn.endswith('.h') or fn.endswith('.hpp'):
                yield os.path.join(dirpath, fn)

def find_decl(lines, jmp_idx):
    # Walk backward to find decl line: choose the closest line that has an identifier '('
    # and is not a macro line, not a comment, not #define, not 'if'
    for k in range(jmp_idx - 1, max(-1, jmp_idx - 12), -1):
        s = lines[k].strip()
        if not s or s.startswith('//') or s.startswith('#') or s.startswith('{'):
            continue
        # FIX: skip C++ ctor initializer-list continuation lines (": Base(...)")
        # else find_decl picks the base name instead of the ctor name
        # (BombClass() noexcept : AbstractClass(noinit_t()) -> was "AbstractClass").
        if s.startswith(':'):
            continue
        if MACRO_RE.search(s):
            continue
        # strip trailing comments
        s2 = re.sub(r'//.*$', '', s).strip()
        # skip lines that are pure keywords/attributes
        m = NAME_RE.findall(s2)
        if not m:
            continue
        # pick the token right before the first '(' that's a plausible name
        # NAME_RE findall returns list of identifiers that are followed by '('
        # the function name is typically the last such before params start, or first
        # Take the first candidate that's not a control keyword
        cand = None
        for mm in re.finditer(r'([~A-Za-z_]\w*)\s*\(', s2):
            tok = mm.group(1)
            if tok in ('if','for','while','switch','sizeof','return','static_assert','decltype'):
                continue
            cand = tok
            break
        if cand:
            return cand, s2, k
    return None, None, None

def main():
    out = {}
    stats = {}
    for path in iter_h_files(YRPP):
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.read().splitlines()
        cur_class = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            # FIX: `enum class Status : int {` is not a class with methods;
            # matching it leaked "Status::" onto BounceClass methods.
            enum_class = stripped.startswith('enum class ') or stripped.startswith('enum struct ')
            cm = CLASS_RE.search(line) if not enum_class else None
            if cm:
                cur_class = cm.group(1)
            for mm in MACRO_RE.finditer(line):
                macro, addrhex = mm.group(1), mm.group(2)
                addr = int(addrhex, 16)
                # normalize to 8 hex
                name, decl, declline = find_decl(lines, i)
                full = (cur_class + '::' + name) if (cur_class and name) else (name or '')
                rec = dict(addr=addr, addrhex=addrhex.upper().zfill(8),
                           macro=macro, cls=cur_class, name=name,
                           full=full, decl=decl or '', declline=(declline+1 if declline is not None else None),
                           file=os.path.relpath(path, PROJECT), line=i+1)
                out.setdefault(addr, []).append(rec)
    # dedup: prefer the one with a class
    with open(os.path.join(os.path.dirname(__file__), 'yrpp_names.json'), 'w', encoding='utf-8') as f:
        json.dump({str(k):v for k,v in out.items()}, f, ensure_ascii=False, indent=1)
    print('total addresses with YRpp JMP macros:', len(out))
    # stats by class
    cc = {}
    for addr, recs in out.items():
        for r in recs:
            cc[r['cls'] or '(none)'] = cc.get(r['cls'] or '(none)', 0) + 1
    print('classes:', len(cc))
    # show sample
    for a in sorted(out)[:5]:
        print('%08X' % a, [r['full'] for r in out[a]])

if __name__ == '__main__':
    main()
