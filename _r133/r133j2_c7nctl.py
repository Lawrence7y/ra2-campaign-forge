#!/usr/bin/env python3
# R133 r133j2: positive/negative controls for the new C7b census pin, fast version.
#
# WHY THIS FILE EXISTS (replaces r133j):
#   r133j staged controls with shutil.copytree(R14) -- but R14 is 811 MB, of which
#   R17_LEAD_BASELINE alone is 766 MB, and the gate never opens a single byte of it.
#   Six copytrees therefore wrote ~4.8 GB into tmpfs and the suite died on its own
#   600 s timeout (exit 143) with no verdict. That is a harness defect in the control,
#   not a verdict about the gate -- so the control is re-run, not reinterpreted.
#   Measured file set (io.open spy over one real gate run) = 31 files, all small.
#   Staging now copies exactly those, so a control costs milliseconds and the whole
#   suite finishes well inside one timeout.
#
# Discipline honoured here: each control mutates exactly ONE thing in its own staged
# copy; the real tree is never written; the real files are hash-checked afterwards.
import hashlib, io, json, os, shutil, subprocess, sys, tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead/next_re_20261117_r14')
OUT  = os.path.join(ROOT, '_r133/r133j2_c7nctl.json')
TAB  = 'DISC_RECHECK.tsv'

# The file set is DERIVED, not hand-listed. A hand-list was tried first and was wrong:
# it omitted place_r87.py (imported at gate line 74), so every staged copy failed at
# import and all 13 controls reported FAIL for a reason that had nothing to do with C7b.
# Deriving it by spying io.open/builtins.open over one real gate run means an added
# dependency can never silently fall out of the staging set.
def derive_needed():
    import builtins, collections, runpy
    seen = collections.Counter()
    real_io, real_open = io.open, builtins.open
    def spy(p, *a, **k):
        try:
            ap = os.path.abspath(str(p))
            # module bodies pulled in by the import machinery count too
            seen[ap] += 1
        except Exception:
            pass
        return real_io(p, *a, **k)
    def spy2(p, *a, **k):
        try: seen[os.path.abspath(str(p))] += 1
        except Exception: pass
        return real_open(p, *a, **k)
    cwd = os.getcwd()
    os.chdir(os.path.join(R14))
    sys.path.insert(0, os.path.join(R14))      # the gate imports place_r87 from its own dir
    io.open, builtins.open = spy, spy2
    argv = sys.argv
    sys.argv = ['check_disc.py']
    try:
        runpy.run_path('check_disc.py', run_name='__main__')
    except SystemExit:
        pass
    finally:
        io.open, builtins.open = real_io, real_open
        sys.argv = argv
        os.chdir(cwd)
    rels = []
    for ap in seen:
        if not ap.startswith(ROOT + os.sep):
            continue
        rel = os.path.relpath(ap, ROOT)
        if rel.startswith('lead/next_re_20261117_r14/R17_LEAD_BASELINE'):
            continue                      # 766 MB, never opened by the gate
        if rel.endswith('.pyc'):
            continue
        rels.append(rel)
    # importlib loads module bodies through _io.open_code, which bypasses both spies, so
    # any module the gate imports is invisible above. Stage every top-level .py in R14
    # as well -- they are small, and this is what makes place_r87.py (gate line 74) present.
    for fn in sorted(os.listdir(R14)):
        if fn.endswith('.py'):
            rels.append(os.path.relpath(os.path.join(R14, fn), ROOT))
    return sorted(set(rels))

NEEDED = derive_needed()

R, ASSERT = {}, []
def chk(name, cond, detail=''):
    ASSERT.append({'assert': name, 'pass': bool(cond), 'detail': str(detail)})
    print(('  PASS ' if cond else '  FAIL ') + name + (('  [' + str(detail) + ']') if detail != '' else ''))
    return bool(cond)

def stage():
    td = tempfile.mkdtemp(prefix='r133j2_')
    for rel in NEEDED:
        src = os.path.join(ROOT, rel)
        dst = os.path.join(td, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    return td

def gate_path(td):
    return os.path.join(td, 'lead/next_re_20261117_r14/check_disc.py')

def run_gate(td):
    p = subprocess.run([sys.executable, gate_path(td)],
                       capture_output=True, text=True, timeout=120,
                       cwd=os.path.dirname(gate_path(td)))
    return p.returncode, p.stdout + p.stderr

def rewrite_row(td, old_head, new_head):
    """Change the col-6 shape head of the FIRST data row that uses old_head."""
    t = os.path.join(td, 'lead/next_re_20261117_r14', TAB)
    lines = io.open(t, encoding='utf-8', newline='').read().split('\n')
    for i, l in enumerate(lines):
        if l.count('\t') == 6 and ('\t' + old_head) in l:
            c = l.split('\t')
            c[5] = new_head
            lines[i] = '\t'.join(c)
            io.open(t, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
            return True
    return False

# ---- baseline hash of the real files (must be unchanged at the end) ----
def real_hashes():
    h = {}
    for rel in ('lead/next_re_20261117_r14/check_disc.py', 'lead/next_re_20261117_r14/DISC_RECHECK.tsv'):
        h[rel] = hashlib.sha256(open(os.path.join(ROOT, rel), 'rb').read()).hexdigest()
    return h
H0 = real_hashes()

print('=== PC: positive controls ===')
td = stage()
rc, out = run_gate(td)
R['pc_exit'] = rc
chk('PC1 unmodified staged copy exits 0', rc == 0, rc)
chk('PC2 the C7b census is printed with the three zero-count shapes',
    all(s in out for s in ('C7b shape census', 'exists=0', 'bytes==0', 'none=0')),
    [l.strip() for l in out.splitlines() if 'C7b' in l][:1])
chk('PC3 the C7 result line also carries the census (edit 2 landed)',
    any(l.startswith('C7 live-checks') and 'shape census' in l for l in out.splitlines()),
    [l.strip() for l in out.splitlines() if l.startswith('C7 live-checks')][:1])
shutil.rmtree(td, ignore_errors=True)

print('\n=== NC: negative controls (each mutates exactly one thing) ===')
for head, newh, key in (('\tgrep=', 'exists (1 B)', 'exists'),
                        ('\tgrep=', 'bytes=999', 'bytes='),
                        ('\tgrep=', 'none', 'none')):
    td = stage()
    ok = rewrite_row(td, 'grep=', newh)
    rc, out = run_gate(td)
    R['nc_%s_exit' % key.replace('=', '')] = rc
    chk('NC[%s] turning a grep row into %r flips exit 0 -> non-0 and names the drift'
        % (key, newh),
        ok and rc != 0 and 'drifted' in out,
        'row_rewritten=%s rc=%s' % (ok, rc))
    shutil.rmtree(td, ignore_errors=True)

# NC4: remove the zero-seeding -> zero-count shapes are ABSENT from the dict -> "vanished"
td = stage()
g = gate_path(td)
src = io.open(g, encoding='utf-8').read()
seed = 'c7_shape = dict((_k, 0) for _k in C7_SHAPE_PIN)'
chk('NC4a the seeding line under test is present exactly once', src.count(seed) == 1, src.count(seed))
io.open(g, 'w', encoding='utf-8', newline='\n').write(src.replace(seed, 'c7_shape = {}'))
rc, out = run_gate(td)
R['nc4_exit'] = rc
chk('NC4 removing the zero-seeding makes zero-count shapes FAIL as vanished',
    rc != 0 and 'vanished from the table entirely' in out, rc)
shutil.rmtree(td, ignore_errors=True)

# NC5: prove C7b specifically is REPINNABLE (catchable but not unpassable).
# The first attempt at this asserted the whole gate exits 0 after a deliberate repin, and
# that was wrong: rewriting a row's shape also changes what that row's own C7 live-check
# does, and the C13/C14 fingerprints, so the gate fails for reasons that have nothing to
# do with C7b. The claim worth testing is narrower -- with the table mutated AND the pin
# updated to match, C7b's own drift message must disappear. That isolates the check under
# test from every other check in the file.
td = stage()
rewrite_row(td, 'grep=', 'exists (1 B)')
g = gate_path(td)
src = io.open(g, encoding='utf-8').read()
src = src.replace("'exists': 0", "'exists': 1").replace("'grep=': 24", "'grep=': 23")
io.open(g, 'w', encoding='utf-8', newline='\n').write(src)
rc5, out5 = run_gate(td)
R['nc5_exit'] = rc5
chk('NC5 with table and pin moved together, C7b reports no drift (the pin is repinnable)',
    'C7b shape census drifted' not in out5 and 'vanished from the table entirely' not in out5,
    'gate_exit=%s (other checks may still fail, by design)' % rc5)
shutil.rmtree(td, ignore_errors=True)

print('\n=== integrity: the real tree was never written ===')
H1 = real_hashes()
for rel in H0:
    chk('REAL %s unchanged by the control suite' % os.path.basename(rel), H0[rel] == H1[rel], H1[rel][:16])

# ---- resolution control: the scanner can SEE each shape when it is genuinely there ----
print('\n=== resolution: each of the three dead shapes is distinguishable when present ===')
td = stage()
base_rc, base_out = run_gate(td)
def census_of(out):
    # line shape: '... shape census bytes==0, exists=0, grep==24, ...'
    # the key 'bytes=' itself ends in '=', so split on the LAST '=' of each item.
    for l in out.splitlines():
        if 'C7b shape census' in l:
            seg = l.split('shape census:', 1)[1].split(';')[0]
            d = {}
            for kv in seg.split(','):
                kv = kv.strip()
                if '=' not in kv:
                    continue
                k, v = kv.rsplit('=', 1)
                d[k.strip()] = int(v.strip())
            return d
    return None
c0 = census_of(base_out)
chk('RES1 baseline census parses and shows the three shapes at zero',
    c0 is not None and c0.get('exists') == 0 and c0.get('bytes=') == 0 and c0.get('none') == 0, c0)
shutil.rmtree(td, ignore_errors=True)
td = stage()
rewrite_row(td, 'grep=', 'none')
rc, out = run_gate(td)
c1 = census_of(out)
chk('RES2 injecting one "none" row moves that census count 0 -> 1 (pin has resolution)',
    c1 is not None and c1.get('none') == 1 and c1.get('grep=') == 23, c1)
shutil.rmtree(td, ignore_errors=True)

R['assertions'] = ASSERT
R['summary'] = {'pass': sum(1 for a in ASSERT if a['pass']), 'total': len(ASSERT)}
print('\nSUMMARY %d/%d PASS' % (R['summary']['pass'], R['summary']['total']))
json.dump(R, io.open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
