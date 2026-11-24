from pathlib import Path
import hashlib, struct, datetime, sys

ROOT = Path('D:/Project/ra2-campaign-forge')
OUT = ROOT / 'lead/direction_ruling_20261108/_verify_hy4_out.txt'
lines = []
def p(s=''):
    lines.append(str(s))

# --- 1. Baseline hashes taken verbatim from the ask (编排方指纹), NOT from _dr_verify.py ---
BASE = {
'lead/n9_erratum_20261108/N9_SPEC_ERRATUM.md':('61446db581a273725010e9b09cf3ebeba0d1412fc8666c0c6b8c660e4f7d22b4',20630),
'lead/d_o1o4_necessity_20261108/O1_O4_NECESSITY.md':('d4ac0f28c108986b7037b2315a796766d7ed5d8212bce6f3c08af815310b1661',35637),
'lead/r2_final_grade_20261108/R2_FINAL_GRADE.md':('7ce09812f7bd905a95114a2cc2cea56b3dc3dbaef3d8e0d14c58685762ecab24',30140),
'lead/a_dim_reduced_20261108/A_REDUCED_FORM.md':('18c3e80120a758ed66adcaf6e7e7cf5efdab8a99e5feab932dcf92ff00a3169d',24000),
'lead/matrix_binding_20261108/MATRIX_BINDING_FACTS.md':('dbe00c859bb2627a4be930cdc4f9065ed371faa42eea7c92a015cf4495805f8b',19663),
'lead/d13d14_cards_20261108/DECISION_QUESTIONS.md':('0a709f2da12e0234cd94ff0baf521652e7d1aed6cfd04929b9728adbfd85bf5f',27172),
'lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md':('7a617a43b32fc2e38c7e46ff9d436f903810ad9cae919fc0eb891a0f9f5796e0',29619),
'lead/p11_stations_20261108/P11_STATION_NAMING.md':('d328e4f99d428daf86047ca420d0c84668d4827865ec62296904f467f9ee4b9e',24636),
'lead/spec_static_closure_20261108/STATIC_GAP_CLOSURE.md':('e0c00683fb23b0b3777d71639f3d7d265208057969073e53fd2b7195d0c3e1f7',28648),
'lead/n8_residual_20261108/N8_RESIDUAL_CLOSURE.md':('ce440d53388443a8c10dfa1f9fc5d105cb3c60b5592c5281db8987659fad4252',18116),
'lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md':('c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c',27225),
'lead/PENDING_DECISIONS.md':('7f68fc6c6ed1ab6ba16210b611906c6189ad0af90a84b46b263a19379fbfcd48',50194),
'lead/GOAL_THREE_TARGETS_20261018.md':('2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede',759518),
}
p('=== 1. INDEPENDENT FINGERPRINT (baseline = ask 编排方指纹) ===')
all_ok=True
for name,(expect,size) in BASE.items():
    b=(ROOT/name).read_bytes()
    h=hashlib.sha256(b).hexdigest()
    ok=(h==expect and len(b)==size)
    all_ok &= ok
    p(f'{"OK " if ok else "BAD"} {name}: sha={h} bytes={len(b)}')
p(f'BASELINES: {"13/13 MATCH" if all_ok else "FAIL"}')

rp=ROOT/'lead/direction_ruling_20261108/_dr_RULING.md'
rb=rp.read_bytes()
p(f'RULING  sha={hashlib.sha256(rb).hexdigest()} bytes={len(rb)}')

# --- 2. Independent disk-only PE mapping (re-implemented, not importing _dr_verify.py) ---
p()
p('=== 2. INDEPENDENT PE DISK MAPPING ===')
b=(ROOT/'ra2youli/gamemd.exe').read_bytes()
pe=struct.unpack_from('<I',b,0x3c)[0]
nsec=struct.unpack_from('<H',b,pe+6)[0]
optlen=struct.unpack_from('<H',b,pe+20)[0]
opt=pe+24
imagebase=struct.unpack_from('<I',b,opt+28)[0]
p(f'gamemd.exe sha={hashlib.sha256(b).hexdigest()} bytes={len(b)} imagebase={imagebase:#x} nsec={nsec}')
for va in [0xB0CD48,0xB0CD78,0xB0CD88,0xB0CD8C,0x7E1728,0x7E1738,0x7E27F8]:
    rva=va-imagebase
    hit=[]
    for i in range(nsec):
        q=opt+optlen+i*40
        sname=b[q:q+8].rstrip(b'\0').decode('ascii','replace')
        vs,sva,rawsz,rawptr=struct.unpack_from('<IIII',b,q+8)
        if sva<=rva<sva+max(vs,rawsz):
            d=rva-sva
            val=struct.unpack_from('<d',b,rawptr+d)[0] if d+8<=rawsz else 'NO_FILE_BYTES'
            hit.append(f'{sname} d={d:#x} RAWSZ={rawsz:#x} -> {val}')
    p(f'VA {va:#x}: ' + ('; '.join(hit) if hit else 'NO_SECTION'))
p('ARITHMETIC: 1/50=%.1f%% 2/50=%.1f%% 2/20=%.1f%%' % (2.0,4.0,10.0))

# --- 3. Cited file:line existence + verbatim lines ---
CITES = {
'lead/n9_erratum_20261108/N9_SPEC_ERRATUM.md':[34,35,37,50,51,52,53,70,81,89,118,120,145],
'lead/d_o1o4_necessity_20261108/O1_O4_NECESSITY.md':[133,155,168,177,184,185,186,206,207,218,235,237,265,271,276,277,278,279],
'lead/slowframe_r3_20261108/S604_GAP_RECHECK.md':[32,35,36,37,41,49,70,73,81,82,85,86,87,88,91,98,101,147,153],
'lead/GOAL_THREE_TARGETS_20261018.md':[9706,9720,9723,9724,9725,9729,9739,9745,9751],
'lead/b2_preaudit_20261106/B2_PREAUDIT.md':[17,20,21],
'lead/b2b_preaudit_20261106/B2B_PREAUDIT.md':[13,16],
'lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md':[21,23,32,33,34],
'lead/matrix_binding_20261108/MATRIX_BINDING_FACTS.md':[48,69,70,78,81,102,104,105],
'lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md':[47,48,49,56,58,81,89,103,105,111,113,114],
'lead/r2_final_grade_20261108/R2_FINAL_GRADE.md':[25,35,77,137,142],
'lead/a_dim_reduced_20261108/A_REDUCED_FORM.md':[49,50,52,57,59,63,64,65,78,80,125,136],
'lead/r2_unclosed_b_20261108/B_BREAKPOINTS_2_6.md':[91,95,97,104,105],
'lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md':[146],
'lead/r2_unclosed_cd_20261108/CD_BREAKPOINTS.md':[74,80,87,88,89,90],
'lead/dtrigger_round2_20261107/_dD_PHYSICAL_S_ALIGNMENT.md':[120,127,130,132],
'lead/PENDING_DECISIONS.md':[10,12,47,64,68,75,78,105,126,130,131,132,133,138,141,144,147],
'lead/d26_ruling_20261106/RULING_D26.md':[7,9,27,28,29,41],
'lead/d13d14_cards_20261108/DECISION_QUESTIONS.md':[69,70,71,88,96,102,114,116,120,167,168,169,170,172],
'lead/spec_static_closure_20261108/STATIC_GAP_CLOSURE.md':[169,173,176,183,188,189],
'lead/d14_dual_20261107/D14_DUAL_RECHECK.md':[67,68],
'lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md':[137,138],
'lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md':[63,69,72,75,91,99,103,104],
'lead/p11_stations_20261108/P11_STATION_NAMING.md':[143,144,149,150,151,154],
'lead/n8_residual_20261108/N8_RESIDUAL_CLOSURE.md':[114],
}
p()
p('=== 3. CITED file:line VERBATIM ===')
for name,nums in CITES.items():
    fp=ROOT/name
    if not fp.exists():
        p(f'!! MISSING FILE {name}'); continue
    txt=fp.read_text(encoding='utf-8',errors='replace').splitlines()
    p(f'--- {name}  (total {len(txt)} lines) ---')
    for n in nums:
        if 1<=n<=len(txt):
            p(f'{n}: {txt[n-1]}')
        else:
            p(f'{n}: !! OUT_OF_RANGE (file has {len(txt)} lines)')

# --- 4. mtime containment for write domain & protected files ---
p()
p('=== 4. MTIMES (write-domain containment) ===')
for name in ['lead/direction_ruling_20261108/_dr_RULING.md',
             'lead/direction_ruling_20261108/_dr_verify.py',
             'lead/direction_ruling_20261108/_dr_verify_out.txt',
             'lead/PENDING_DECISIONS.md','lead/GOAL_THREE_TARGETS_20261018.md',
             'lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md']:
    st=(ROOT/name).stat()
    p(f'{datetime.datetime.fromtimestamp(st.st_mtime).isoformat()}  {name}')

OUT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
sys.exit(0 if all_ok else 1)
