"""PC-2 for Q5: use a2_sites' 00407780 call record, find the call byte in
D41_SUBST/EVIDENCE/disasm_00407780.txt, and check the same 5 bytes in gamemd.exe."""
import json, struct, re
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
LOG = []
def P(*a):
    line = ' '.join(str(x) for x in a); LOG.append(line); print(line, flush=True)

d = json.loads(open(BASE + r'\D41_SUBST\_audit\EVIDENCE\a2_sites.json', 'rb').read().decode('utf-8'))
calls = d['calls']
P('a2_sites["00407780"] =', calls.get('00407780'))
sites = calls['00407780']

txt = open(BASE + r'\D41_SUBST\EVIDENCE\disasm_00407780.txt', 'rb').read().decode('utf-8')
P('')
P('--- disasm text line for site 004077EA ---')
for ln in txt.splitlines():
    if ln.upper().startswith('004077EA'):
        P('  ', ln)
        m = re.search(r'\b([0-9a-fA-F]{4,20})\s+(call|jmp)\b', ln[10:])
        P('   hex column:', m.group(1) if m else 'NONE')
        site_hex = m.group(1) if m else None

blob = open(EXE, 'rb').read()
TEXT_RAW, TEXT_VA = 4096, 0x00401000
so = TEXT_RAW + (0x004077EA - TEXT_VA)
raw5 = blob[so:so+5]
P('  gamemd.exe bytes @file_off %d : %s' % (so, raw5.hex().upper()))
P('  disasm hex column               : %s' % (site_hex or '').upper())
P('  MATCH (disasm text == exe bytes):', site_hex is not None and site_hex.upper() == raw5.hex().upper())
rel = struct.unpack_from('<i', blob, so + 1)[0]
P('  rel32 = %d -> target %08X ; a2_sites says %s ; equal=%s'
  % (rel, (0x004077EA + 5 + rel) & 0xFFFFFFFF, sites, '%08X' % ((0x004077EA + 5 + rel) & 0xFFFFFFFF) == '00407780'))
P('')
P('--- search the same value pair in other EVIDENCE files ---')
targets = [
    ('S16_N1/_audit/callmap.json', 'dict hex->[sites]'),
    ('S09_KPROVED7/_audit/EVIDENCE/e8_sites_audit.json', '[[site,target],...]'),
    ('S21_DIRECT/_audit/EVIDENCE/scan_mine.json', '{"calls": [[site,target],...]}'),
]
for rel_p, fmt in targets:
    p = BASE + '\\' + rel_p.replace('/', '\\')
    o = json.load(open(p, encoding='utf-8'))
    if rel_p.startswith('S16_N1'):
        hit = o.get('00407780')
    elif rel_p.startswith('S09'):
        hit = [x for x in o if x[1] == 0x00407780]
    else:
        hit = [x for x in o['calls'] if x[1] == 0x00407780]
    P('  %-50s -> %s' % (rel_p, hit))
# also: does the disasm .txt for 004073c0 exist? (the callee)
P('')
P('does a disasm file for the callee 004073C0 exist?',
  __import__('os').path.exists(BASE + r'\D41_SUBST\EVIDENCE\disasm_004073C0.txt'))
import glob
P('D41_SUBST disasm files:', sorted(x.split('\\')[-1] for x in glob.glob(BASE + r'\D41_SUBST\EVIDENCE\disasm_*.txt')))
open(BASE + r'\R17_R95_T1_A2SITES\q5_pc2.out','w',encoding='utf-8').write('\n'.join(LOG))
