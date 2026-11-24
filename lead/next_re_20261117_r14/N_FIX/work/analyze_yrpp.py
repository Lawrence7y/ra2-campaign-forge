#!/usr/bin/env python3
"""Full YRpp analysis:
 (A) census of noinit_t line -> next-line JMP_THIS instances (real constructors),
     extracting real ctor signature/class and the misjudged noinit name.
 (B) BASELINE: for every JMP_THIS(0x...) line, categorize the IMMEDIATE previous
     line -> noinit_t delegating line / normal signature line / other.
     This tests whether 'JMP_THIS on next line' is specific to noinit_t.
"""
import os, re, json

YRPP = r"D:\Project\ra2-campaign-forge\YRpp"
OUTDIR = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\N_FIX\EVIDENCE"

files = []
for dp, dn, fn in os.walk(YRPP):
    dn[:] = [d for d in dn if d not in ('.git','.mimosa')]
    for f in fn:
        if f.lower().endswith(('.h','.hpp','.cpp','.inl')):
            files.append(os.path.join(dp,f))
files.sort()

JMP_RE = re.compile(r'JMP_THIS\s*\(\s*0x([0-9A-Fa-f]+)\s*\)')
# match a delegating init line: ': SomeClass(noinit_t...)' possibly preceded by signature text
DELEG_RE = re.compile(r':\s*([A-Za-z_][A-Za-z0-9_:]*)\s*\(\s*noinit_t\s*(?:\(\s*\))?\s*\)')
# match noinit stub def line: 'explicit __forceinline SomeClass(noinit_t)'
STUB_RE = re.compile(r'(?:explicit\s+)?(?:__forceinline\s+)?([A-Za-z_][A-Za-z0-9_:]*)\s*\(\s*noinit_t\s*\)')

census = []          # real constructor instances (noinit line + next-line JMP)
pure_stubs = []      # noinit stub definitions with no JMP (empty inline)
baseline = []        # per JMP_THIS line previous-line category
jmp_lines_total = 0

for path in files:
    rel = os.path.relpath(path, YRPP).replace('\\','/')
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        lines = fh.read().splitlines()
    for i, ln in enumerate(lines):
        # ---- baseline: every JMP_THIS line, look at previous line ----
        mj = JMP_RE.search(ln)
        if mj:
            jmp_lines_total += 1
            prev = lines[i-1].strip() if i > 0 else ''
            if 'noinit_t' in prev:
                cat = 'prev_noinit'
            elif re.search(r'\w\s*\([^;]*\)\s*(?:noexcept|const)?\s*:?\s*$', prev) or re.search(r'\)\s*(noexcept|const)?\s*:?\s*$', prev):
                cat = 'prev_signature'   # normal ctor/method signature line
            elif prev.endswith(':') or re.search(r':\s*[\w:]+\s*\(', prev):
                cat = 'prev_initializer'
            elif prev in ('{',''):
                cat = 'prev_brace_or_blank'
            else:
                cat = 'prev_other'
            baseline.append({'file':rel,'jmp_line':i+1,'addr':int(mj.group(1),16),'prev_cat':cat,'prev':prev})

        # ---- census: noinit_t line with JMP_THIS on immediate next line ----
        if 'noinit_t' not in ln:
            continue
        nxt = lines[i+1] if i+1 < len(lines) else ''
        mn = JMP_RE.search(nxt)
        dm = DELEG_RE.search(ln)
        if mn and dm:
            deleg_cls = dm.group(1)
            # walk backwards to find real ctor signature (Class::Class or Class(...))
            sig = None; sig_line = None
            for j in range(i-1, max(-1,i-6), -1):
                s = lines[j].strip()
                if not s or s.startswith('//') or s.startswith('/*') or s.startswith('*'):
                    continue
                # constructor signature: ClassName::ClassName(  OR ClassName(  (inline in class)
                cm = re.search(r'([A-Za-z_][A-Za-z0-9_:]*)\s*::\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(', s)
                if cm and cm.group(1)==cm.group(2):
                    sig=s; sig_line=j+1; real_cls=cm.group(1); break
                cm2 = re.match(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(', s)
                if cm2:
                    sig=s; sig_line=j+1; real_cls=cm2.group(1); break
            if sig is None:
                real_cls = deleg_cls; sig = ln.strip(); sig_line = i+1
            census.append({
                'file':rel,'noinit_line':i+1,'jmp_line':i+2,
                'deleg_cls':deleg_cls,'real_cls':real_cls,
                'addr':int(mn.group(1),16),
                'noinit_text':ln.strip(),'next_text':nxt.strip(),
                'sig_text':sig,'sig_line':sig_line,
                'misjudged_name':deleg_cls+'::noinit_t',
            })
        elif ('noinit_t' in ln and not mn):
            # pure stub check: this line is an explicit noinit_t stub definition
            sm = STUB_RE.search(ln)
            if sm and 'noinit_t' in ln:
                # look ahead up to 3 lines for empty body '{ }' and no jmp
                window = lines[i:i+4]
                has_jmp = any(JMP_RE.search(w) for w in window)
                body_empty = any(re.search(r'\{\s*\}', w) for w in window)
                if not has_jmp:
                    pure_stubs.append({'file':rel,'line':i+1,'cls':sm.group(1),
                                       'text':ln.strip(),
                                       'window':' | '.join(w.strip() for w in window)})

with open(os.path.join(OUTDIR,'census_detailed.json'),'w',encoding='utf-8') as fh:
    json.dump({'census':census,'pure_stubs':pure_stubs,'baseline':baseline,
               'jmp_lines_total':jmp_lines_total}, fh, ensure_ascii=False, indent=1)

# summaries
from collections import Counter
bc = Counter(b['prev_cat'] for b in baseline)
print("jmp_lines_total =", jmp_lines_total)
print("baseline prev categories:", dict(bc))
print("census (noinit->JMP) count =", len(census))
print("pure noinit stubs (no JMP within 3 lines) =", len(pure_stubs))
# addr uniqueness
addrs = [c['addr'] for c in census]
print("census unique addrs =", len(set(addrs)), "dupes=", [hex(a) for a,n in Counter(addrs).items() if n>1])
print("wrote census_detailed.json")
