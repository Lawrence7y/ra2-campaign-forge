# -*- coding: utf-8 -*-
"""S13-K8RECHK finalize: assemble RECHECK_18.tsv, coverage_delta.tsv and EVIDENCE from verified data.
Writes only under S13_K8RECHK."""
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8')
BASE=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K8RECHK'
WORK=os.path.join(BASE,'work'); EVID=os.path.join(BASE,'EVIDENCE')
os.makedirs(EVID,exist_ok=True)

s1=json.load(open(os.path.join(WORK,'s1_report.json'),encoding='utf-8'))
s3=json.load(open(os.path.join(WORK,'s3_report.json'),encoding='utf-8'))
s6=json.load(open(os.path.join(WORK,'s6_results.json'),encoding='utf-8'))
rep1={r['entry']:r for r in s1['report']}
rep3={r['entry']:r for r in s3['rep']}

# verified per-row: (entry, name, vt, slot, kind, verdict, note)
# verdict from ㉓: DEAD base tables (atexit install, pair contest) = 不可辩护
ROWS=[
 ('0075E510','WarheadTypeClass::scalar_deleting_dtor',0x7F6B30,8,'plain-class','可辩护','实例构造器(0x75cec0等)写堆对象vptr;无atexit;无成对争抢'),
 ('0065BED0','RadSiteClass::scalar_deleting_dtor',0x7F0810,8,'plain-class','可辩护','实例构造器0x65b1e0写堆对象vptr;无atexit;无成对争抢'),
 ('0040BBC0','VectorClass<BombClass*>::scalar_deleting_dtor',0x7E17EC,0,'base','不可辩护','死表:atexit dtor 0x40b5c0@0x40b60a / 0x438590@0x438598;与派生活表0x7e17cc成对争抢'),
 ('0040BC10','DynamicVectorClass<BombClass*>::scalar_deleting_dtor',0x7E17CC,0,'derived','可辩护','活表:initterm ctor 0x40b540@0x40b563 / 0x438550@0x43856d'),
 ('0040F8A0','VectorClass<WarheadTypeClass*>::scalar_deleting_dtor',0x7E1EA4,0,'base','不可辩护','死表:atexit dtor 0x40f4d0@0x40f4d8;与派生活表0x7e1e84成对争抢'),
 ('0040F8F0','DynamicVectorClass<WarheadTypeClass*>::scalar_deleting_dtor',0x7E1E84,0,'derived','可辩护','活表:initterm ctor 0x40f490@0x40f4ad'),
 ('0040FE70','VectorClass<WeaponTypeClass*>::scalar_deleting_dtor',0x7E1EF4,0,'base','不可辩护','死表:atexit dtor 0x40fb70@0x40fb78;与派生活表0x7e1ed4成对争抢'),
 ('0040FEC0','DynamicVectorClass<WeaponTypeClass*>::scalar_deleting_dtor',0x7E1ED4,0,'derived','可辩护','活表:initterm ctor 0x40fb30@0x40fb4d'),
 ('0046B8C0','VectorClass<BulletClass*>::scalar_deleting_dtor',0x7E4698,0,'base','不可辩护','死表:atexit dtor 0x466320@0x46632e / 0x4e68a0@0x4e68a8;与派生活表0x7e4678成对争抢'),
 ('0046B910','DynamicVectorClass<BulletClass*>::scalar_deleting_dtor',0x7E4678,0,'derived','可辩护','活表:initterm ctor 0x4662e0@0x4662fd / 0x4e6860@0x4e687d'),
 ('0048AFD0','VectorClass<DamageGroup*>::scalar_deleting_dtor',0x7E5144,0,'base-noglobal','可辩护','该表仅写栈局部[esp+0x38]/self;无global绝对写、无atexit注册、无成对争抢 ⇒ 未触发㉓'),
 ('0048B020','DynamicVectorClass<DamageGroup*>::scalar_deleting_dtor',0x7E5170,0,'derived-noglobal','可辩护','该表仅写栈局部[esp+0x38];无global绝对写、无atexit注册、无成对争抢 ⇒ 未触发㉓'),
 ('0054EB50','VectorClass<KamikazeControl*>::scalar_deleting_dtor',0x7ECE9C,0,'base','不可辩护','死表:atexit dtor 0x54e2d0@0x54e31d(push@0x54e293,call@0x54e2c7);与派生活表0x7ece7c成对争抢'),
 ('0054EBA0','DynamicVectorClass<KamikazeControl*>::scalar_deleting_dtor',0x7ECE7C,0,'derived','可辩护','活表:initterm ctor 0x54e260@0x54e298'),
 ('0062B330','VectorClass<ParasiteClass*>::scalar_deleting_dtor',0x7EF844,0,'base','不可辩护','死表:atexit dtor 0x6291d0@0x6291d8;与派生活表0x7ef824成对争抢'),
 ('0062B380','DynamicVectorClass<ParasiteClass*>::scalar_deleting_dtor',0x7EF824,0,'derived','可辩护','活表:initterm ctor 0x629190@0x6291ad'),
 ('0065C1B0','VectorClass<RadSiteClass*>::scalar_deleting_dtor',0x7F07C4,0,'base','不可辩护','死表:atexit dtor 0x65b1a0@0x65b1a8;与派生活表0x7f07a4成对争抢'),
 ('0065C200','DynamicVectorClass<RadSiteClass*>::scalar_deleting_dtor',0x7F07A4,0,'derived','可辩护','活表:initterm ctor 0x65b160@0x65b17d'),
]

def writepoints(ea):
    """Return all write points string for the vt of this entry."""
    r1=rep1[ea]
    vt=r1['vt'].lower().replace('0x','')
    ws=rep3[ea]['writes']
    parts=[]
    for w in ws:
        cls=w['cls']; f=w['func']; reg=w['atexit_reg']
        tag='CTOR' if cls=='CTOR' else ('ATEXIT_DTOR' if cls=='ATEXIT_DTOR' else 'OTHER')
        pct=''
        if reg: pct=';atexit_push@%s,call@%s'%(reg[0][0],reg[0][1])
        parts.append('%s(mem=%s,host=%s,%s%s)'%(w['site'],w['mem'],f,tag,pct))
    return ' | '.join(parts) if parts else 'NONE'

def host_summary(ea):
    # KamikazeControl base: write 0x54e31d is inside the atexit dtor 0x54e2d0;
    # capstone jumped to inner loop head 0x54e2e0. Verified in s4_out.txt.
    if ea=='0054EB50':
        return ('ATEXIT_DTOR:0x54e2d0@0x54e31d (push 0x54e2d0@0x54e293, '
                'call 0x7C978A@0x54e2c7; inner loop head 0x54e2e0 misread as start)')
    ws=rep3[ea]['writes']
    globals_=[w for w in ws if w['mem'].startswith('0x')]
    if not globals_:
        return 'NO_GLOBAL_WRITE (stack/self only)'
    ctors=[w for w in globals_ if w['cls']=='CTOR']
    adt=[w for w in globals_ if w['cls']=='ATEXIT_DTOR']
    oth=[w for w in globals_ if w['cls']=='OTHER']
    seg=[]
    if ctors: seg.append('CTOR:'+','.join('%s@%s'%(w['func'],w['site']) for w in ctors))
    if adt: seg.append('ATEXIT_DTOR:'+','.join('%s@%s'%(w['func'],w['site']) for w in adt))
    if oth: seg.append('OTHER:'+','.join('%s@%s'%(w['func'],w['site']) for w in oth))
    return ' | '.join(seg)

# ---------- RECHECK_18.tsv ----------
hdr=['entry','vt','slot','COL','TD','RTTI_name','host_function_ctor_or_dtor','global_all_vptr_writes','verdict','note']
lines=['\t'.join(hdr)]
for ea,name,vt,slot,kind,verdict,note in ROWS:
    r1=rep1[ea]
    lines.append('\t'.join([
        ea, '0x%08X'%vt, str(slot), r1['col'] or 'NA', r1['td'] or 'NA', r1['rtti_name'] or 'NA',
        host_summary(ea), writepoints(ea), verdict, note]))
open(os.path.join(BASE,'RECHECK_18.tsv'),'w',encoding='utf-8').write('\n'.join(lines)+'\n')
print('RECHECK_18.tsv rows',len(ROWS))

# ---------- coverage_delta.tsv (only 可辩护) ----------
d=['entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path']
for ea,name,vt,slot,kind,verdict,note in ROWS:
    if verdict!='可辩护': continue
    if kind=='plain-class':
        why='heap-instance ctor live vt slot%d (no atexit/pair-contest) passed ㉓'%slot
    elif kind.startswith('derived-noglobal') or kind=='base-noglobal':
        why='stack-local vptr, no global/atexit write, no pair-contest -> ㉓ not triggered'
    else:
        why='ctor-installed live vt slot%d passed ㉓'%slot
    sem=('scalar_deleting_dtor: test-flag-gated call 0x7C8B3D(operator delete) + ret 4 '
         '(vptr write optional, base dtor carries it); 无直接调用者，仅虚派发见证; '+why)
    d.append('\t'.join([ea,'S13',name,sem,'[已证]',
        'EVIDENCE/%s.txt;EVIDENCE/RECHECK_EVIDENCE.md'%ea]))
open(os.path.join(BASE,'coverage_delta.tsv'),'w',encoding='utf-8').write('\n'.join(d)+'\n')
print('coverage_delta.tsv rows',len(d)-1)

# ---------- EVIDENCE per-row ----------
ev=['# S13-K8RECHK EVIDENCE — per-row disassembly & write points (untruncated)',
    '',
    'Source: ra2youli\\gamemd.exe SHA-256 73201CC0...F67476, ImageBase 0x400000, read-only.',
    'Tools: system py3.12.10 + capstone 5.0.7(skipdata=True) + pefile; work/s0-s6 scripts.',
    '']
for ea,name,vt,slot,kind,verdict,note in ROWS:
    r1=rep1[ea]; r3=rep3[ea]
    ev.append('## %s  %s'%(ea,name))
    ev.append('')
    ev.append('- vt=0x%08X slot=%d kind=%s'%(vt,slot,kind))
    ev.append('- RTTI: COL=%s TD=%s name=%s (TD+8 inline ASCII, read fail-closed)'%(r1['col'],r1['td'],r1['rtti_name']))
    ev.append('- slot value == entry: %s'%r1['slot_ok'])
    ev.append('- global vptr write points:')
    for w in r3['writes']:
        ev.append('    - site=%s mem=[%s] bytes=%s host=%s cls=%s atexit_reg=%s op_delete_calls=%d atexit_calls=%d'%(
            w['site'],w['mem'],w['bytes'],w['func'],w['cls'],w['atexit_reg'],w['opdel'],w['atexit_calls']))
    ev.append('- ㉓ verdict: **%s** — %s'%(verdict,note))
    ev.append('')
open(os.path.join(EVID,'RECHECK_EVIDENCE.md'),'w',encoding='utf-8').write('\n'.join(ev)+'\n')

# copy full disassembly dumps s2_out/s4_out into EVIDENCE (untruncated)
import shutil
for nm in ('s2_out.txt','s4_out.txt'):
    src=os.path.join(WORK,nm)
    if os.path.exists(src): shutil.copyfile(src,os.path.join(EVID,'DISASM_'+nm))
print('EVIDENCE written')
