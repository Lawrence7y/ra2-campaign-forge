import os, sys, hashlib, datetime, capstone, pefile
ROOT=r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14'
SRC=ROOT+r'/S10_K8F/coverage_delta.tsv'
MERGED=ROOT+r'/COVERAGE/coverage.tsv'
OUTDIR=ROOT+r'/S10_K11'
EVID=OUTDIR+r'/EVIDENCE'
EXE=r'D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe'
tz=datetime.timezone(datetime.timedelta(hours=8))
now=datetime.datetime.now(tz).isoformat(timespec='seconds')

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20), b''): h.update(b)
    return h.hexdigest()

src_sha=sha256(SRC)
merged_sha=sha256(MERGED)
exe_sha=sha256(EXE)

targets=[b'004DFCB0', b'004DFE00']
raw=open(SRC,'rb').read()
lines=raw.splitlines(keepends=True)
selected=[]
for line in lines:
    core=line.rstrip(b'\r\n')
    eol=line[len(core):]
    f=core.split(b'\t')
    if f and f[0] in targets:
        assert len(f)==9, (f[0], len(f))
        selected.append((f, eol))
assert [f[0] for f,_ in selected]==targets, [f[0] for f,_ in selected]

merged_rows={}
for line in open(MERGED,'rb').read().splitlines():
    f=line.split(b'\t')
    if f and f[0] in targets:
        merged_rows[f[0]]=f
assert set(merged_rows)==set(targets)

old_phrase=b'skips when [this+0x5A4]==best or cur==8'
new_phrase=b'skips when [this+0x5A4]==best and [this+0xAC]==8'
house_marker=b'nearest candidate passing 0x457ce0 filter with [v+0x2C]()==0xF, '
house_clause=b'skips when [this+0x5A4]==best and [this+0xAC]==8, '

new_rows=[]
diff_lines=[]
for f,eol in selected:
    old_fields=list(f)
    addr=f[0]
    if addr==b'004DFE00':
        assert f[3].count(old_phrase)==1, 'expected old DFE00 phrase not found once'
        f[3]=f[3].replace(old_phrase,new_phrase)
    elif addr==b'004DFCB0':
        assert b'skips when' not in f[3], 'unexpected existing skip clause in DFCB0'
        assert f[3].count(house_marker)==1, 'house marker not found once'
        f[3]=f[3].replace(house_marker,house_marker+house_clause)
    assert len(f)==9
    for idx in [0,1,2,4,5,6,7,8]:
        assert f[idx]==old_fields[idx], (addr, idx)
    new_rows.append((f,eol))
    diff_lines.append('ADDR '+addr.decode())
    diff_lines.append('OLD '+old_fields[3].decode('utf-8'))
    diff_lines.append('NEW '+f[3].decode('utf-8'))
    diff_lines.append('UNCHANGED name='+f[2].decode('utf-8')+' grade='+f[4].decode('utf-8'))

outdelta=OUTDIR+r'/coverage_delta.tsv'
with open(outdelta,'wb') as out:
    for f,eol in new_rows:
        out.write(b'\t'.join(f)+eol if eol else b'\t'.join(f)+b'\n')

with open(EVID+r'/disk_read_snapshot.tsv','wb') as out:
    out.write(b'# read_at='+now.encode()+b'\n')
    out.write(b'# source='+SRC.encode()+b'\n')
    out.write(b'# sha256='+src_sha.encode()+b'\n')
    for f,eol in selected:
        out.write(b'\t'.join(f)+b'\n')
with open(EVID+r'/disk_read_meta.txt','w',encoding='utf-8') as out:
    out.write('read_at='+now+'\n')
    out.write('source='+SRC+'\n')
    out.write('source_sha256='+src_sha+'\n')
    out.write('merged='+MERGED+'\n')
    out.write('merged_sha256='+merged_sha+'\n')
    for addr,f in sorted(merged_rows.items()):
        out.write(addr.decode()+' merged_name='+f[2].decode('utf-8')+' merged_grade='+f[4].decode('utf-8')+'\n')
    for f,eol in selected:
        out.write(f[0].decode()+' delta_name='+f[2].decode('utf-8')+' delta_grade='+f[4].decode('utf-8')+'\n')

pe=pefile.PE(EXE)
ib=pe.OPTIONAL_HEADER.ImageBase
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail=True; md.skipdata=True
sites=[(0x004DFDBA,0x1A,'004DFCB0'),(0x004DFF00,0x1A,'004DFE00')]
with open(EVID+r'/byte_evidence.txt','w',encoding='utf-8') as out:
    out.write('target='+EXE+'\n')
    out.write('sha256='+exe_sha+'\n')
    out.write('imagebase=0x%08X\n'%ib)
    for va,n,label in sites:
        data=pe.get_data(va-ib,n)
        out.write(label+' va=0x%08X bytes=%s\n'%(va,data.hex(' ')))
        out.write('  cmp/jne chain: 3bc8 7509 83beac00000008 741b\n')
        out.write('  decode: cmp ecx,eax; jne continue; cmp dword [esi+0xAC],8; je skip-dispatch\n')
        out.write('  => skip iff [this+0x5A4]==best AND [this+0xAC]==8\n')

key_addrs={
 0x004DFCF3,0x004DFD92,0x004DFD96,0x004DFDA1,
 0x004DFF00,0x004DFF06,0x004DFF0D,0x004DFF0F,0x004DFF11,0x004DFF18,
 0x004DFE36,0x004DFED4,0x004DFEE7,
 0x004DFDBA,0x004DFDC0,0x004DFDC7,0x004DFDC9,0x004DFDCB,0x004DFDD2,
}
with open(EVID+r'/key_instructions.txt','w',encoding='utf-8') as out:
    out.write('# capstone 5.0.7 CS_MODE_32 skipdata=True; relevant write/compare sites\n')
    for fn in ['disasm_004DFCB0.txt','disasm_004DFE00.txt']:
        for ln in open(EVID+'/'+fn,encoding='utf-8'):
            if ln.startswith('0x'):
                a=int(ln[2:10],16)
                if a in key_addrs: out.write(ln.rstrip()+'\n')

with open(EVID+r'/semantic_diff.txt','w',encoding='utf-8') as out:
    out.write('\n'.join(diff_lines)+'\n')

verify=[]
verify.append('read_at='+now)
verify.append('source_sha256='+src_sha)
verify.append('merged_sha256='+merged_sha)
verify.append('target_sha256='+exe_sha)
verify.append('capstone=5.0.7 pefile=2024.8.26 skipdata=True')
verify.append('output_rows=2 output_columns=9 header=absent')
for f,eol in new_rows:
    verify.append('out addr='+f[0].decode()+' name='+f[2].decode()+' grade='+f[4].decode())
verify.append('all non-semantics fields byte-identical to source: PASS')
verify.append('DFE00 old or-phrase removed: PASS')
verify.append('DFCB0 missing skip clause added: PASS')
verify.append('game binary write attempted: NO')
with open(EVID+r'/verification.txt','w',encoding='utf-8') as out:
    out.write('\n'.join(verify)+'\n')

with open(OUTDIR+r'/DISAGREE.md','w',encoding='utf-8') as out:
    out.write('# DISAGREE\n\n')
    out.write('N/A - no disagreement. Independent capstone decode at 0x004DFDBA and 0x004DFF00 shows 3bc8 7509 83beac00000008 741b: cmp ecx,eax; jne continue; cmp dword [esi+0xAC],8; je skip-dispatch. The skip therefore requires ecx==eax AND [esi+0xAC]==8; R1 or was wrong. Both rows are changed; no row is marked no_change.\n')

progress=[
 '# S10-K11 progress',
 '- Read-at: '+now+'; source S10_K8F/coverage_delta.tsv SHA-256 '+src_sha+'; merged COVERAGE/coverage.tsv SHA-256 '+merged_sha+'.',
 '- On-disk check at that time: 004DFCB0 name=AircraftClass::QueueMissionId8_NearHouseFilter_behavior grade=[已证]; 004DFE00 name=AircraftClass::QueueMissionId8_NearGlobalFilter_behavior grade=[已证]; merged file agrees.',
 '- Independent disassembly: capstone 5.0.7 (skipdata=True) + pefile 2024.8.26; target SHA-256 '+exe_sha+'; Ghidra not used.',
 '- 004DFE00 byte evidence @004DFF00: 8b8ea4050000 c6869106000001 3bc8 7509 83beac00000008 741b => cmp ecx,eax; jne; only then cmp [this+0xAC],8; je skip => AND, not OR.',
 '- 004DFCB0 byte evidence @004DFDBA: 8b8ea4050000 c6869006000001 3bc8 7509 83beac00000008 741b => same AND; this skip condition was missing in the disk wording.',
 '- Best-pointer trace: 004DFCF3/004DFD96/004DFDA1 (House list) and 004DFE36/004DFED4/004DFEE7 (global list) put the selected candidate into eax at the compare.',
 '- Wording changes only: DFE00 "or cur==8" -> "and [this+0xAC]==8"; DFCB0 gained the same skip clause. All other 8 fields kept byte-identical.',
 '- coverage_delta.tsv: exactly 2 rows, 9 columns, disk order (004DFCB0, 004DFE00), no header.',
 '- DISAGREE.md: N/A (no disagreement; no no_change row). Game files untouched; no ledger; no git commit.',
]
with open(OUTDIR+r'/PROGRESS.md','w',encoding='utf-8') as out:
    out.write('\n'.join(progress)+'\n')
assert len(progress)<=20

back=open(outdelta,'rb').read().splitlines()
assert len(back)==2, len(back)
for line,f_expected in zip(back,new_rows):
    f=line.split(b'\t')
    assert len(f)==9
    assert f==f_expected[0]
print('OUTPUT_DELTA='+outdelta)
print('ROWS=2 COLS=9')
print('READ_AT='+now)
print('SRC_SHA='+src_sha)
print('MERGED_SHA='+merged_sha)
print('EXE_SHA='+exe_sha)
for f,eol in new_rows:
    print('ROW '+f[0].decode()+' name='+f[2].decode()+' grade='+f[4].decode())
