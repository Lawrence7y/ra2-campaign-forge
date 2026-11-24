import os, re, struct

R2 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02"
OUT = []
def p(s): OUT.append(s)

# ---- RUNLOG current line numbers ----
lines = open(os.path.join(R2, "RUNLOG.md"), encoding='utf-8').read().splitlines()
p("RUNLOG lines=%d" % len(lines))
targets = ['33 B', '插 32 B', '21/21', '21 个沙箱配置', '47 samples', '96–97', 'D ≤ N', '六卡收官', 'FULL_CHAIN', 'W65', 'W64b']
for t in targets:
    for i, ln in enumerate(lines, 1):
        if t in ln:
            p("L%d: %s" % (i, ln.strip()[:150]))
p('--- RUNLOG tail 640-667 ---')
for i in range(639, len(lines)):
    p("L%d: %s" % (i + 1, lines[i][:160]))

# ---- exe: locate STT string & section mapping ----
exe = r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe"
data = open(exe, 'rb').read()
e = struct.unpack_from('<I', data, 0x3C)[0]
nsec = struct.unpack_from('<H', data, e + 6)[0]
optsz = struct.unpack_from('<H', data, e + 20)[0]
secoff = e + 24 + optsz
secs = []
for i in range(nsec):
    b = secoff + i * 40
    name = data[b:b+8].rstrip(b'\x00').decode(errors='replace')
    vsz, rva, rsz, praw = struct.unpack_from('<IIII', data, b + 8)
    secs.append((name, rva, vsz, praw, rsz))
    p("SEC %-8s RVA=0x%06X VSZ=0x%06X RAW=0x%06X RSZ=0x%06X" % (name, rva, vsz, praw, rsz))
for s in [b'STT:CampaignAnimTutorial', b'BootCampSelect', b'SovietCampaignSelect']:
    i = data.find(s)
    if i == -1:
        p("%s NOT IN FILE" % s.decode()); continue
    sec = None
    for n, rva, vsz, praw, rsz in secs:
        if praw <= i < praw + rsz:
            sec = (n, rva, praw)
    if sec:
        n, rva, praw = sec
        va = 0x400000 + rva + (i - praw)
        p("%s @FOFF 0x%X -> section=%s VA=0x%X" % (s.decode(), i, n, va))
    else:
        p("%s @FOFF 0x%X -> section=? (beyond raw)" % (s.decode(), i))

# extra gate patterns (RVA / page-relative forms claimed 0)
for label, pat in [('RVA 0x68F7AD', b'\xad\xf7\x68\x00'), ('RVA 0x68F7AC', b'\xac\xf7\x68\x00'),
                   ('page-rel 0x27D7AD', b'\xad\xd7\x27\x00'), ('page-rel 0x27D7AC', b'\xac\xd7\x27\x00')]:
    cnt = data.count(pat)
    locs = []
    j = data.find(pat)
    while j != -1 and len(locs) < 5:
        locs.append(hex(j)); j = data.find(pat, j + 1)
    p("%s count=%d %s" % (label, cnt, locs))

# ---- W58 EVIDENCE mtimes ----
import datetime
ev = os.path.join(R2, "W58_menu_review", "EVIDENCE")
st = []
for n in os.listdir(ev):
    fp = os.path.join(ev, n)
    if os.path.isfile(fp):
        st.append((datetime.datetime.fromtimestamp(os.path.getmtime(fp)), n))
st.sort()
p("W58 EVIDENCE earliest=%s latest=%s ; files with mtime > 23:03:00 = %d" % (
    st[0][0].strftime('%H:%M:%S'), st[-1][0].strftime('%H:%M:%S'),
    sum(1 for t, _ in st if t > datetime.datetime(2026, 11, 13, 23, 3))))
for t, n in st[-6:]:
    p("  late: %s %s" % (t.strftime('%H:%M:%S'), n))

# ---- W59 report: mov ebp,1 ----
w59 = os.path.join(R2, "W59_endofgame_chain")
found = []
for root, dirs, files in os.walk(w59):
    for f in files:
        if f.endswith(('.md', '.txt', '.json')):
            fp = os.path.join(root, f)
            try: t = open(fp, encoding='utf-8', errors='replace').read()
            except Exception: continue
            if re.search(r'mov\s+ebp,\s*1\b|mov ebp,1', t):
                found.append(os.path.relpath(fp, w59))
p("W59 files mentioning 'mov ebp,1': %s" % found[:8])

# ---- W63 pid 34668 in run.ndjson ----
run = open(os.path.join(R2, "W63_route_a_e2e", "out", "run.ndjson"), encoding='utf-8', errors='replace').read()
p("run.ndjson mentions 34668: %d" % run.count('34668'))
fin = open(os.path.join(R2, "W63_route_a_e2e", "out", "finalize.ndjson"), encoding='utf-8', errors='replace').read()
p("finalize.ndjson mentions 34668: %d ; residual_own_pid mentions: %d" % (fin.count('34668'), fin.count('residual')))

with open(os.path.join(R2, "W67_audit_lead_verdicts", "_w67_verify4_out.txt"), 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT))
print('ok')
