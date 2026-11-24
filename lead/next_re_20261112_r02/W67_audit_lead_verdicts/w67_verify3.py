import os, re, struct, subprocess, json

R2 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02"
PROJ = r"D:\Project\ra2-campaign-forge"
OUT = []
def p(s): OUT.append(s)

# ---- PE section map & VA lookup ----
exe = r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe"
data = open(exe, 'rb').read()
e = struct.unpack_from('<I', data, 0x3C)[0]
nsec = struct.unpack_from('<H', data, e + 6)[0]
optsz = struct.unpack_from('<H', data, e + 20)[0]
opt = e + 24
imagebase = struct.unpack_from('<I', data, opt + 28)[0]
secoff = opt + optsz
secs = []
for i in range(nsec):
    b = secoff + i * 40
    name = data[b:b+8].rstrip(b'\x00').decode(errors='replace')
    vsz, va, rsz, praw = struct.unpack_from('<IIII', data, b + 8)
    secs.append((name, va, vsz, praw, rsz))
p("ImageBase=0x%X sections=%s" % (imagebase, [(n, hex(a), hex(v)) for n, a, v, _, _ in secs]))
def va2off(vaddr):
    for n, va, vsz, praw, rsz in secs:
        if va <= vaddr < va + max(vsz, rsz):
            return n, praw + (vaddr - va)
    return None, None
for va in (0x6041FD, 0x4261A8, 0x426198):
    sec, off = va2off(va)
    p("VA 0x%X -> section=%s off=%s bytes=%r" % (va, sec, hex(off) if off else '-', data[off:off+40] if off else b''))
for s in [b'STT:CampaignAnimTutorial', b'DESC:TUT1', b'GUI:TutorialCampaign', b'BootCampSelect']:
    p("exe count %s = %d" % (s.decode(), data.count(s)))

# ---- CSF greps (W61 work) ----
w61work = os.path.join(R2, "W61_third_badge_route", "work")
for fn in ['language.mix_7F6FBCDF.csf', 'langmd.mix_BD835079.csf']:
    fp = os.path.join(w61work, fn)
    if os.path.isfile(fp):
        b = open(fp, 'rb').read()
        p("%s size=%d DESC:TUT1=%d CampaignAnimTutorial=%d TutorialCampaign=%d" % (
            fn, len(b), b.count(b'DESC:TUT1'), b.count(b'CampaignAnimTutorial'), b.count(b'TutorialCampaign')))

# ---- W55b root ----
p("W55b root: %s" % sorted(os.listdir(os.path.join(R2, "W55b_equivalence_rerun"))))

# ---- CFB None contexts ----
cfb = os.path.join(R2, "W55b_equivalence_rerun", "out", "CFB_COMPARE_TABLE.md")
t = open(cfb, encoding='utf-8', errors='replace').read()
for m in re.findall(r'.{0,50}None.{0,50}', t):
    p("CFB None ctx: " + m.replace('\n', ' '))

# ---- W58 EVIDENCE groups ----
ev = os.path.join(R2, "W58_menu_review", "EVIDENCE")
names = sorted(os.listdir(ev))
groups = set()
for n in names:
    m = re.match(r'(\d+[^_.]*)', n)
    groups.add(m.group(1) if m else n)
p("W58 EVIDENCE files=%d groups~%d: %s" % (len(names), len(groups), sorted(groups)))

# ---- RUNLOG current text (re-read after 00:31:31 write) ----
run = open(os.path.join(R2, "RUNLOG.md"), encoding='utf-8').read()
p("RUNLOG total lines now=%d" % run.count('\n'))
for pat in [r'.{0,40}33\s*B.{0,60}', r'.{0,40}21/21.{0,60}', r'.{0,30}byte_identical.{0,60}', r'.{0,20}21 个沙箱.{0,60}',
            r'.{0,30}插 3[23] B.{0,60}']:
    for m in re.findall(pat, run):
        p("RUNLOG now: %r" % m)

# ---- W64b evidence & maplike & MB ----
w64 = os.path.join(R2, "W64_bootcamp_inventory")
p("W64 dir: %s" % sorted(os.listdir(w64)))
evd = os.path.join(w64, 'EVIDENCE')
if os.path.isdir(evd):
    p("W64 EVIDENCE: %s" % sorted(os.listdir(evd)))
bi = open(os.path.join(w64, 'BOOTCAMP_INVENTORY.md'), encoding='utf-8', errors='replace').read()
for pat in [r'.{0,60}map-like.{0,80}', r'.{0,60}maplike.{0,80}', r'.{0,40}MB.{0,60}', r'.{0,50}LOCAL\.MIX.{0,120}']:
    for m in re.findall(pat, bi)[:6]:
        p("BI: %r" % m)
s2 = os.path.join(evd, 'S2_q2_stdout.txt')
if os.path.isfile(s2):
    t2 = open(s2, encoding='utf-8', errors='replace').read()
    p("S2_q2_stdout head: %r" % t2[:600])
    for kw in ['635', '198', 'map']:
        p("S2 contains %s: %d" % (kw, t2.count(kw)))

# ---- git status PENDING_DECISIONS ----
try:
    r = subprocess.run(['git', '-C', PROJ, 'status', '--porcelain', '--', 'lead/PENDING_DECISIONS.md'],
                       capture_output=True, text=True, timeout=30)
    p("git status PENDING_DECISIONS: rc=%d out=%r err=%r" % (r.returncode, r.stdout.strip(), r.stderr.strip()[:100]))
except Exception as ex:
    p("git status err: %s" % ex)

# ---- W63 REAL_DIR_PROOF / probe / robocopy ----
rdp = open(os.path.join(R2, "W63_route_a_e2e", "REAL_DIR_PROOF.txt"), encoding='utf-8', errors='replace').read()
for kw in ['IDENTICAL_TREE', '647', '1,989,215,270', '1989215270']:
    p("REAL_DIR_PROOF %s: %d" % (kw, rdp.count(kw)))
dp = open(os.path.join(R2, "W63_route_a_e2e", "out", "desktop_probe.ndjson"), encoding='utf-8', errors='replace').read()
p("desktop_probe: %r" % dp[:400])
rb = open(os.path.join(R2, "W63_route_a_e2e", "out", "cmd_robocopy_sandbox.log"), encoding='utf-8', errors='replace').read()
p("robocopy log: %r" % rb[:300])

# ---- W61 insert size wording ----
tb = open(os.path.join(R2, "W61_third_badge_route", "THIRD_BADGE_ROUTE.md"), encoding='utf-8', errors='replace').read()
for pat in [r'.{0,60}插.{0,80}', r'.{0,50}32 字节.{0,60}', r'.{0,50}33 字节.{0,60}', r'.{0,60}cDlgItems.{0,80}']:
    for m in re.findall(pat, tb)[:6]:
        p("TBR: %r" % m)
pd = open(os.path.join(w61work, 'patch_dlg148.py'), encoding='utf-8', errors='replace').read()
for m in re.findall(r'.{0,60}(?:32|33).{0,60}', pd)[:10]:
    p("patch_dlg148.py: %r" % m)
rb14 = open(os.path.join(w61work, 'readback_14.txt'), encoding='utf-8', errors='replace').read()
p("readback_14 head: %r" % rb14[:400])

# ---- lock file locate ----
for root, dirs, files in os.walk(R2):
    dirs[:] = [d for d in dirs if d not in ('sandbox_game', 'baseline_clean', 'sandbox_base', 'pristine')]
    for f in files:
        if 'game_instance.lock' in f:
            p("lock found: %s" % os.path.join(root, f))

with open(os.path.join(R2, "W67_audit_lead_verdicts", "_w67_verify3_out.txt"), 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT))
print('\n'.join(OUT))
