import hashlib, os, re, struct, json, datetime

R2 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02"
OUT = []

def p(s):
    OUT.append(s)

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def mtime(path):
    try:
        return datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        return 'ERR ' + str(e)

# ---------- locate exe ----------
exe = None
for c in [r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe",
          os.path.join(R2, "W63_route_a_e2e", "out", "pristine", "gamemd.exe")]:
    if os.path.isfile(c):
        exe = c
        break
p("=== EXE ===")
p("exe=%s" % exe)
if exe:
    data = open(exe, 'rb').read()
    p("size=%d (claim 4,825,360)" % len(data))
    p("sha256=%s (claim 73201cc0...67476)" % sha256(exe))

    # gate byte LE32 scans
    pat_ad = b'\xad\xf7\xa8\x00'
    off_ad = []
    i = data.find(pat_ad)
    while i != -1:
        off_ad.append(i)
        i = data.find(pat_ad, i + 1)
    p("LE32 0xA8F7AD count=%d offsets=%s (claim 1 @0x12F00C)" % (len(off_ad), [hex(o) for o in off_ad]))

    pat_a0ad = b'\xa0\xad\xf7\xa8\x00'
    off_a0ad = []
    i = data.find(pat_a0ad)
    while i != -1:
        off_a0ad.append(i)
        i = data.find(pat_a0ad, i + 1)
    p("A0 AD F7 A8 00 count=%d offsets=%s (claim 1 @0x12F00B -> VA 0x52F00B)" % (len(off_a0ad), [hex(o) for o in off_a0ad]))

    pat_ac = b'\xac\xf7\xa8\x00'
    off_ac = []
    i = data.find(pat_ac)
    while i != -1:
        off_ac.append(i)
        i = data.find(pat_ac, i + 1)
    p("LE32 0xA8F7AC count=%d offsets=%s (claim 1 @0x2BE030)" % (len(off_ac), [hex(o) for o in off_ac]))

    # neighborhood scan: every byte offset, LE32 in [0xA8F7A0, 0xA8F7B4]
    lo, hi = 0xA8F7A0, 0xA8F7B4
    hits = {}
    n = len(data)
    for i in range(0, n - 3):
        v = struct.unpack_from('<I', data, i)[0]
        if lo <= v <= hi:
            hits.setdefault(hex(v), []).append(hex(i))
    total_hits = sum(len(v) for v in hits.values())
    p("neighborhood full-offset scan: total=%d (claim 36) detail=%s" % (total_hits, {k: v[:8] for k, v in hits.items()}))

    # battle name strings
    for name in [b'all1', b'sov1', b'tut1', b'all2', b'sov2', b'tut2', b'all3', b'sov3']:
        cnt = data.count(name)
        locs = []
        i = data.find(name)
        while i != -1 and len(locs) < 6:
            locs.append(hex(i))
            i = data.find(name, i + 1)
        p("ascii %s count=%d at=%s" % (name.decode(), cnt, locs))

    p("BATTLE.INI (exact) count=%d (W64b claim 0)" % data.count(b'BATTLE.INI'))
    i1 = data.find(b'BATTLEMD*.INI')
    i2 = data.find(b'BATTLEMD.INI\x00')
    p("BATTLEMD*.INI @%s (W64b claim VA 0x4261A8) ; BATTLEMD.INI\\x00 @%s (claim VA 0x426198)" % (hex(i1) if i1 != -1 else 'NOT FOUND', hex(i2) if i2 != -1 else 'NOT FOUND'))

    # W59 bytes
    checks = [
        (0x1CF04F, b'\x83\xff\x64\x7f\x1d\x33', 'cmp edi,0x64 loopA @VA 0x5CF04F'),
        (0x1CF367, b'\x83\xfd\x64\x7f\x71\xe9', 'cmp ebp,0x64 loopB @VA 0x5CF367'),
        (0x1AE0B8, b'\x66\x89\x83\xa0\x35\x00\x00', 'mov word [ebx+0x35a0],ax @VA 0x5AE0B8'),
        (0x1AE1FA, b'\x66\x89\x83\xa0\x35\x00\x00', 'same interactive @VA 0x5AE1FA'),
        (0x2859BF, b'\x8a\x81\xac\x34', 'mov al,[ecx+0x34ac] @VA 0x6859BF'),
        (0x2859C7, b'\x74\x47', 'je +0x47 @VA 0x6859C7 -> 0x685A10'),
        (0x28594B, b'\x8a\x81\xae\x34\x00\x00', 'SkipScore @VA 0x68594B'),
        (0x28A11F, b'\x88\x86\xac\x34\x00\x00', '[Basic]EndOfGame->Scen+0x34AC @VA 0x68A11F'),
        (0x285C4E, b'\x8d\x88\x5c', 'lea ecx,[eax+0x125c] @VA 0x685C4E'),
        (0x285C54, b'\xe8\x57\xde\xff\xff', 'call rel32 @VA 0x685C54 -> 0x683AB0'),
        (0x12F00B, b'\xa0\xad\xf7\xa8\x00', 'A0 read gate @VA 0x52F00B'),
        (0x2BE02F, b'\xa0\xac\xf7\xa8\x00', 'A0 read 0xA8F7AC @VA 0x6BE02F'),
    ]
    p("=== W59/W57 byte claims ===")
    for off, want, label in checks:
        got = data[off:off + len(want)]
        p("%s: %s %s" % (label, 'MATCH' if got == want else 'MISMATCH got=' + got.hex(),
                         hex(off)))
    # string at 0x6041FD (RULING_C: tooltip)
    s = data[0x2041FD:0x2041FD + 40]
    p("bytes@FOFF 0x2041FD (VA 0x6041FD) = %r" % s)

# ---------- hashes ----------
p("=== HASHES ===")
pristine = os.path.join(R2, "W63_route_a_e2e", "out", "pristine", "BATTLEMD.INI")
if os.path.isfile(pristine):
    p("pristine BATTLEMD.INI size=%d (claim 2733) sha=%s" % (os.path.getsize(pristine), sha256(pristine)))
bak = os.path.join(R2, "W63_route_a_e2e", "out", "pristine", "BATTLEMD.INI.ra2forge.bak")
if os.path.isfile(bak):
    p("pristine .bak size=%d (claim 241) sha=%s (claim 9f804531...)" % (os.path.getsize(bak), sha256(bak)))

# ---------- W44 ----------
p("=== W44_c_line_e2e/out ===")
w44 = os.path.join(R2, "W44_c_line_e2e", "out")
if os.path.isdir(w44):
    pfx = []
    s256 = []
    for fn in sorted(os.listdir(w44)):
        fp = os.path.join(w44, fn)
        if not os.path.isfile(fp):
            continue
        h = sha256(fp)
        pfx.append((fn, h[:8]))
        if os.path.getsize(fp) == 2562915:
            s256.append((fn, h, os.path.getmtime(fp)))
    for fn, h, mt in s256:
        p("size 2,562,915: %s sha=%s mtime=%s (TRIAGE claim SHA 0C7FB5FB...)" % (fn, h, mtime(fp)))
    p("files with sha prefix 0bdcfd8c: %s (TRIAGE claim: none)" % [fn for fn, h in pfx if h.startswith('0bdcfd8c')])
else:
    p("W44 out missing")

# ---------- W45 saves ----------
p("=== W45_b_line_equivalence/out save_*.SAV ===")
w45 = os.path.join(R2, "W45_b_line_equivalence", "out")
claim_sizes = {
    'A1_SAVE2147': 1405384, 'A1_SAVE31D9': 1397199, 'A1test2_SAVE3CD8': 1395201,
    'A2_SAVE2EB9': 1382212, 'A2_SAVE6C99': 1399419, 'B1_SAVE161E': 1398096,
    'B1_SAVE7DBC': 1382156, 'B2_SAVE27BB': 1366595,
}
if os.path.isdir(w45):
    for fn in sorted(os.listdir(w45)):
        if fn.lower().endswith('.sav'):
            fp = os.path.join(w45, fn)
            hdr = open(fp, 'rb').read(80)
            magic = hdr[0:8].hex()
            minor, major = struct.unpack_from('<H', hdr, 0x18)[0], struct.unpack_from('<H', hdr, 0x1A)[0]
            sshift, mshift = struct.unpack_from('<H', hdr, 0x1E)[0], struct.unpack_from('<H', hdr, 0x20)[0]
            nfat = struct.unpack_from('<I', hdr, 0x2C)[0]
            cutoff = struct.unpack_from('<I', hdr, 0x38)[0]
            key = fn.replace('save_', '').replace('.SAV', '').replace('.sav', '')
            cl = claim_sizes.get(key)
            p("%s size=%d (claim %s) magic=%s ver=%s.%02X ss=%d ms=%d nFAT=%d cutoff=%d" % (
                fn, os.path.getsize(fp), cl, magic, major, minor, sshift, mshift, nfat, cutoff))
else:
    p("W45 out missing")

# ---------- mtimes ----------
p("=== MTIMES (REVIEW) ===")
rev = os.path.join(R2, "REVIEW")
for fn in ["LEAD_CHECK_gate_byte.md", "LEAD_RULING_D5_2_INPLACE_UNFREEZE.md", "LEAD_CHECK_menu_3slot.md",
           "LEAD_VERIFY_W55B.md", "LEAD_VERIFY_W57.md", "LEAD_VERIFY_W58.md", "LEAD_VERIFY_W59.md",
           "LEAD_VERIFY_W63.md", "LEAD_VERIFY_W64B.md", "LEAD_VERIFY_W54_INDEPENDENT.md",
           "LEAD_CHECK_W54_CFB.md", "LEAD_TRIAGE_W52.md", "LEAD_RULING_C_line_route_a_first.md",
           "LEAD_VERIFY_W60.md", "LEAD_VERIFY_W61.md", "LEAD_VERIFY_W60_ANY.md"]:
    fp = os.path.join(rev, fn)
    p("%s -> %s" % (fn, mtime(fp) if os.path.isfile(fp) else 'ABSENT'))

p("=== MTIMES (W55b) ===")
w55b_out = os.path.join(R2, "W55b_equivalence_rerun", "out")
if os.path.isdir(w55b_out):
    for fn in sorted(os.listdir(w55b_out)):
        fp = os.path.join(w55b_out, fn)
        if os.path.isfile(fp):
            p("out/%s size=%d mtime=%s" % (fn, os.path.getsize(fp), mtime(fp)))
w55b_root = os.path.join(R2, "W55b_equivalence_rerun")
for fn in ["story.md", "REPORT.md", "EQUIVALENCE_RESULT_V2.md"]:
    fp = os.path.join(w55b_root, fn)
    if os.path.isfile(fp):
        p("root/%s mtime=%s" % (fn, mtime(fp)))
    else:
        p("root/%s ABSENT" % fn)

# ---------- MAPSELMD variant ----------
p("=== W63 MAPSELMD.INI.variant_from1 ===")
vm = os.path.join(R2, "W63_route_a_e2e", "out", "MAPSELMD.INI.variant_from1")
if os.path.isfile(vm):
    lines = open(vm, 'r', encoding='utf-8', errors='replace').read().splitlines()
    p("lines=%d (claim 296)" % len(lines))
    innod = False
    nod = []
    for ln in lines:
        if ln.strip().lower().startswith('[nod]'):
            innod = True
            continue
        if innod and ln.strip().startswith('['):
            break
        if innod and '=' in ln:
            nod.append(ln.strip())
    p("[Nod] entries (%d): %s" % (len(nod), nod))

# ---------- run.ndjson / finalize.ndjson ----------
p("=== W63 ndjson scans ===")
for nm in ["run.ndjson", "finalize.ndjson", "offline.ndjson"]:
    fp = os.path.join(R2, "W63_route_a_e2e", "out", nm)
    if os.path.isfile(fp):
        txt = open(fp, 'r', encoding='utf-8', errors='replace').read()
        p("%s: UnableMapSelect=%d ; RA2F_M3.MAP-mentions=%d" % (
            nm, txt.count('UnableMapSelect'), txt.count('RA2F_M3.MAP')))

# frozen sampling: parse run.ndjson for RA2F_M3 poll samples
fp = os.path.join(R2, "W63_route_a_e2e", "out", "run.ndjson")
if os.path.isfile(fp):
    ts = []
    for line in open(fp, 'r', encoding='utf-8', errors='replace'):
        if 'RA2F_M3.MAP' not in line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        def walk(o):
            if isinstance(o, dict):
                if o.get('fn') == 'RA2F_M3.MAP' and 't' in o:
                    ts.append((o.get('t'), o.get('frame'), o.get('stage'), o.get('eog')))
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(obj)
    p("RA2F_M3 poll samples with t: n=%d t_min=%s t_max=%s (claim 47 samples / 71 s)" % (
        len(ts), min([t for t, _, _, _ in ts], default=None), max([t for t, _, _, _ in ts], default=None)))
    if ts:
        p("last 3: %s" % ts[-3:])

with open(os.path.join(R2, "W67_audit_lead_verdicts", "_w67_verify1_out.txt"), 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT))
print('\n'.join(OUT))
