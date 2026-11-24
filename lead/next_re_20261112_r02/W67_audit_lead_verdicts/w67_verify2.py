import os, re, json, datetime

R2 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02"
PROJ = r"D:\Project\ra2-campaign-forge"
OUT = []
def p(s): OUT.append(s)
def mtime(path):
    try: return datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e: return 'ERR'

# ---- FINALIZE config_restore count ----
fj = os.path.join(R2, "W63_route_a_e2e", "out", "FINALIZE.json")
obj = json.load(open(fj, encoding='utf-8'))
cr = obj['config_restore']
n_all = len(cr)
n_bi = sum(1 for e in cr if e.get('byte_identical') is True)
others = [e['file'] + ':' + ','.join(k for k in e if k not in ('file',)) for e in cr if e.get('byte_identical') is not True]
p("FINALIZE.config_restore: entries=%d byte_identical_true=%d non-bi=%s" % (n_all, n_bi, others))

# ---- refined frozen samples ----
fp = os.path.join(R2, "W63_route_a_e2e", "out", "run.ndjson")
ts = []
for line in open(fp, encoding='utf-8', errors='replace'):
    if 'RA2F_M3.MAP' not in line: continue
    try: objl = json.loads(line)
    except Exception: continue
    def walk(o):
        if isinstance(o, dict):
            if o.get('fn') == 'RA2F_M3.MAP' and 't' in o:
                ts.append((o.get('t'), o.get('frame'), o.get('stage'), o.get('eog')))
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(objl)
frozen = [x for x in ts if x[1] == 210 and x[2] == 9 and x[3] == 1]
p("M3 samples: all=%d frozen(frame210,stage9,eog1)=%d tspan_frozen=%s..%s (claim 47 samples / 71 s)" % (
    len(ts), len(frozen), frozen[0][0] if frozen else None, frozen[-1][0] if frozen else None))

# ---- W61 THIRD_BADGE_ROUTE.md ----
tb = os.path.join(R2, "W61_third_badge_route", "THIRD_BADGE_ROUTE.md")
p("THIRD_BADGE_ROUTE.md exists=%s size=%s" % (os.path.isfile(tb), os.path.getsize(tb) if os.path.isfile(tb) else '-'))
if os.path.isfile(tb):
    txt = open(tb, encoding='utf-8', errors='replace').read()
    for pat in [r'.{60}\b3[23]\s*B\b.{60}', r'.{50}664.{50}', r'.{50}696.{50}', r'.{60}61/113.{60}',
                r'.{50}0x18128.{50}', r'.{50}b9021544.{60}', r'.{60}310\s*,\s*34.{60}', r'.{50}110\s*[x×]\s*87.{50}',
                r'.{60}0x6041FD.{60}', r'.{60}#534.{40}', r'.{40}BootCampSelect.{40}']:
        ms = re.findall(pat, txt)
        p("PAT %s -> %d hit(s)" % (pat[:28], len(ms)))
        for m in ms[:4]: p("   > " + m.replace('\n', ' '))
w61dir = os.path.join(R2, "W61_third_badge_route")
p("W61 dir: %s" % sorted(os.listdir(w61dir))[:30])
work = os.path.join(w61dir, 'work')
if os.path.isdir(work):
    p("W61 work: %s" % sorted(os.listdir(work))[:30])

# ---- W64b BOOTCAMP_INVENTORY.md ----
bi = os.path.join(R2, "W64_bootcamp_inventory", "BOOTCAMP_INVENTORY.md")
p("BOOTCAMP_INVENTORY.md exists=%s" % os.path.isfile(bi))
if os.path.isfile(bi):
    txt = open(bi, encoding='utf-8', errors='replace').read()
    for pat in [r'.{40}LOCAL\.MIX.{80}', r'.{30}A8548FD9.{60}', r'.{30}33\.18.{50}', r'.{30}4,054.{50}',
                r'.{30}a5752a8d.{50}', r'.{30}1,003.{60}', r'.{30}13,007.{60}', r'.{30}2,125.{50}',
                r'.{30}635.{60}', r'.{30}198.{50}', r'.{40}21 个.{60}', r'.{30}17 组.{50}', r'.{30}5,573.{60}',
                r'.{30}074ccccd.{50}', r'.{30}20 段.{50}', r'.{30}14 个阶段.{40}']:
        ms = re.findall(pat, txt)
        p("PAT %s -> %d hit(s)" % (pat[:24], len(ms)))
        for m in ms[:3]: p("   > " + m.replace('\n', ' '))

# ---- W60 evidence for SHA 369592f0 / 2730 ----
w60out = os.path.join(R2, "W60_battlemd_inplace", "out")
hits = []
if os.path.isdir(w60out):
    names = sorted(os.listdir(w60out))
    p("W60 out file count=%d" % len(names))
    for fn in names:
        fp2 = os.path.join(w60out, fn)
        if not os.path.isfile(fp2): continue
        if fn.endswith(('.log', '.txt', '.json', '.md')):
            try: t = open(fp2, encoding='utf-8', errors='replace').read()
            except Exception: continue
            if '369592f0' in t: hits.append(fn + ':369592f0')
            if '2730' in t: hits.append(fn + ':2730')
            if 'ECH01.MAP' in t and 'inplace' in t.lower() and fn.endswith('.json'): hits.append(fn + ':inplace+ECH01')
    p("W60 evidence hits: %s" % hits[:20])

# ---- W57 dir ----
w57 = os.path.join(R2, "W57_gate_writer_adjudication")
if os.path.isdir(w57):
    entries = sorted(os.listdir(w57))
    p("W57 dir n=%d: W57B-copies=%s COLLISION=%s" % (len(entries),
        [e for e in entries if 'W57B' in e.upper()], [e for e in entries if 'COLLISION' in e.upper()]))

# ---- W58 dir ----
w58 = os.path.join(R2, "W58_menu_review")
if os.path.isdir(w58):
    p("W58 dir: %s" % sorted(os.listdir(w58)))
    ev = os.path.join(w58, 'EVIDENCE')
    if os.path.isdir(ev):
        p("W58 EVIDENCE count=%d (claim 14 组)" % len(os.listdir(ev)))

# ---- W55b CFB_COMPARE_TABLE None ----
cfb = os.path.join(R2, "W55b_equivalence_rerun", "out", "CFB_COMPARE_TABLE.md")
if os.path.isfile(cfb):
    t = open(cfb, encoding='utf-8', errors='replace').read()
    p("CFB_COMPARE_TABLE.md: None-count=%d ; SAVE5802 rows mention=%d" % (t.count('None'), t.count('SAVE5802')))
    for m in re.findall(r'.{0,60}SAVE5802.{0,80}', t)[:3]:
        p("   > " + m.replace('\n', ' '))

# ---- EQUIVALENCE_RESULT_V2 head ----
ev2 = os.path.join(R2, "W55b_equivalence_rerun", "EQUIVALENCE_RESULT_V2.md")
if os.path.isfile(ev2):
    head = open(ev2, encoding='utf-8', errors='replace').read()[:400]
    p("EQUIVALENCE_RESULT_V2.md mtime=%s HEAD: %r" % (mtime(ev2), head[:200]))

# ---- HANDOFF / PENDING ----
p("HANDOFF.md mtime=%s" % mtime(os.path.join(R2, "HANDOFF.md")))
p("RUNLOG.md mtime=%s" % mtime(os.path.join(R2, "RUNLOG.md")))
pend = os.path.join(PROJ, "lead", "PENDING_DECISIONS.md")
p("lead\\PENDING_DECISIONS.md exists=%s mtime=%s" % (os.path.isfile(pend), mtime(pend) if os.path.isfile(pend) else '-'))

# ---- W44 baseline 647/1989215270 ----
w44root = os.path.join(R2, "W44_c_line_e2e")
found = []
for root, dirs, files in os.walk(w44root):
    if 'sandbox_game' in root or 'baseline_clean' in root: continue
    for fn in files:
        if fn.endswith(('.md', '.json', '.txt')):
            fp3 = os.path.join(root, fn)
            try: t = open(fp3, encoding='utf-8', errors='replace').read()
            except Exception: continue
            if '1989215270' in t or '1,989,215,270' in t:
                found.append(os.path.relpath(fp3, w44root))
p("W44 files mentioning 1,989,215,270: %s" % found[:10])

with open(os.path.join(R2, "W67_audit_lead_verdicts", "_w67_verify2_out.txt"), 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT))
print('\n'.join(OUT))
