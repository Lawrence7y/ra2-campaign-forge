from pathlib import Path
import hashlib
import struct
import sys

ROOT = Path('D:/Project/ra2-campaign-forge')
BASELINES = '''lead/n9_erratum_20261108/N9_SPEC_ERRATUM.md 61446db581a273725010e9b09cf3ebeba0d1412fc8666c0c6b8c660e4f7d22b4 20630
lead/d_o1o4_necessity_20261108/O1_O4_NECESSITY.md d4ac0f28c108986b7037b2315a796766d7ed5d8212bce6f3c08af815310b1661 35637
lead/r2_final_grade_20261108/R2_FINAL_GRADE.md 7ce09812f7bd905a95114a2cc2cea56b3dc3dbaef3d8e0d14c58685762ecab24 30140
lead/a_dim_reduced_20261108/A_REDUCED_FORM.md 18c3e80120a758ed66adcaf6e7e7cf5efdab8a99e5feab932dcf92ff00a3169d 24000
lead/matrix_binding_20261108/MATRIX_BINDING_FACTS.md dbe00c859bb2627a4be930cdc4f9065ed371faa42eea7c92a015cf4495805f8b 19663
lead/d13d14_cards_20261108/DECISION_QUESTIONS.md 0a709f2da12e0234cd94ff0baf521652e7d1aed6cfd04929b9728adbfd85bf5f 27172
lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md 7a617a43b32fc2e38c7e46ff9d436f903810ad9cae919fc0eb891a0f9f5796e0 29619
lead/p11_stations_20261108/P11_STATION_NAMING.md d328e4f99d428daf86047ca420d0c84668d4827865ec62296904f467f9ee4b9e 24636
lead/spec_static_closure_20261108/STATIC_GAP_CLOSURE.md e0c00683fb23b0b3777d71639f3d7d265208057969073e53fd2b7195d0c3e1f7 28648
lead/n8_residual_20261108/N8_RESIDUAL_CLOSURE.md ce440d53388443a8c10dfa1f9fc5d105cb3c60b5592c5281db8987659fad4252 18116
lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c 27225
lead/PENDING_DECISIONS.md 7f68fc6c6ed1ab6ba16210b611906c6189ad0af90a84b46b263a19379fbfcd48 50194
lead/GOAL_THREE_TARGETS_20261018.md 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede 759518'''
EXTRA = '''lead/slowframe_r3_20261108/S604_GAP_RECHECK.md
lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md
lead/b2_preaudit_20261106/B2_PREAUDIT.md
lead/b2b_preaudit_20261106/B2B_PREAUDIT.md
lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md
lead/d26_ruling_20261106/RULING_D26.md
lead/d14_dual_20261107/D14_DUAL_RECHECK.md
lead/r2_unclosed_cd_20261108/CD_BREAKPOINTS.md
lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md'''
rows=[]
all_ok=True
for line in BASELINES.splitlines():
    name, expected, size = line.split()
    b=(ROOT/name).read_bytes()
    h=hashlib.sha256(b).hexdigest()
    ok=h==expected and len(b)==int(size)
    all_ok &= ok
    rows.append(f'{name}: 被核对象 SHA256 = {h}，字节数 = {len(b)}；基准 {"MATCH" if ok else "MISMATCH"}')
rows.append(f'BASELINES: {"13/13 MATCH" if all_ok else "FAIL"}')
for name in EXTRA.splitlines():
    b=(ROOT/name).read_bytes()
    rows.append(f'{name}: 被核对象 SHA256 = {hashlib.sha256(b).hexdigest()}，字节数 = {len(b)}；补充件本轮绑定，无编排方基准')
# Disk-only PE mapping: no execution, process or memory APIs.
b=(ROOT/'ra2youli/gamemd.exe').read_bytes()
pe=struct.unpack_from('<I',b,0x3c)[0]
assert b[pe:pe+4]==b'PE\0\0'
nsec=struct.unpack_from('<H',b,pe+6)[0]
optlen=struct.unpack_from('<H',b,pe+20)[0]
opt=pe+24
assert struct.unpack_from('<H',b,opt)[0]==0x10b
imagebase=struct.unpack_from('<I',b,opt+28)[0]
rows.append(f'PE imagebase={imagebase:#x}; sha256={hashlib.sha256(b).hexdigest()}; bytes={len(b)}')
for va in [0xB0CD48,0xB0CD78,0xB0CD88,0xB0CD8C,0x7E1728,0x7E1738,0x7E27F8]:
    rva=va-imagebase
    hits=[]
    for i in range(nsec):
        p=opt+optlen+i*40
        name=b[p:p+8].rstrip(b'\0').decode('ascii')
        vs,sva,rawsz,rawptr=struct.unpack_from('<IIII',b,p+8)
        if sva<=rva<sva+max(vs,rawsz):
            d=rva-sva
            value=struct.unpack_from('<d',b,rawptr+d)[0] if d+8<=rawsz else 'NO_FILE_BYTES'
            hits.append(f'{name}: d={d:#x}, RAWSZ={rawsz:#x}, double={value}')
    rows.append(f'VA {va:#x}: '+ '; '.join(hits))
    assert len(hits)==1
rows.append('ARITHMETIC: 1/50=2.0%; 2/50=4.0%; 2/20=10.0%')
report=ROOT/'lead/direction_ruling_20261108/_dr_RULING.md'
if report.exists():
    b=report.read_bytes()
    rows.append(f'裁决书: 被核对象 SHA256 = {hashlib.sha256(b).hexdigest()}，字节数 = {len(b)}')
text='\n'.join(rows)+'\n'
(ROOT/'lead/direction_ruling_20261108/_dr_verify_out.txt').write_text(text,encoding='utf-8')
print(text,end='')
sys.exit(0 if all_ok else 1)
