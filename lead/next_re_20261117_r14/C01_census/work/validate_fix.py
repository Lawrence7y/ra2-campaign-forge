"""C01 FIX-round final validation. Reads only, writes EVIDENCE/validation_fix.txt."""
import os, re, json, collections
HERE=os.path.dirname(os.path.abspath(__file__))
BASE=os.path.abspath(os.path.join(HERE,'..')); EVID=os.path.join(BASE,'EVIDENCE')
PROJECT=os.path.abspath(os.path.join(HERE,'..','..','..','..'))
ATLAS=os.path.join(PROJECT,'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv')
TAB=chr(9); checks=[]
def ck(n,ok,d=''): checks.append((n,bool(ok),d))

al=open(ATLAS,encoding='utf-8',errors='replace').read().splitlines()[1:1293]
ck('atlas slice 1292',len(al)==1292,str(len(al)))
cl=open(os.path.join(BASE,'coverage_delta.tsv'),encoding='utf-8').read().splitlines()
rows=cl[1:]
ck('coverage rows 1292',len(rows)==1292,str(len(rows)))
ck('coverage 6 cols',all(len(r.split(TAB))==6 for r in rows))
ents=[r.split(TAB)[0] for r in rows]
ck('unique entries',len(set(ents))==1292)
ck('entries==atlas slice',set(ents)==set(r.split(TAB)[0] for r in al))
grades=[r.split(TAB)[4] for r in rows]
ck('high==96',grades.count('[已证]')==96,str(grades.count('[已证]')))
ck('med==703',grades.count('[静态推断]')==703,str(grades.count('[静态推断]')))
ck('low==493',grades.count('[未证]')==493,str(grades.count('[未证]')))
# 24 name fixes
d={r.split(TAB)[0].lower():r.split(TAB)[2] for r in rows}
exp={'004011c0':'AudioIDXData::Create','00405c00':'AudioController::~AudioController',
 '00407b60':'AudioStream::PlayWAV','00408610':'Audio::ReadWAVFile','0040e320':'GenericNode::GenericNode',
 '0042e6f0':'BaseClass::BaseClass','00438bf0':'BombListClass::Update','004397e0':'BounceClass::Initialize',
 '004385d0':'BombClass::BombClass'}
ck('name fixes sample',all(d.get(a)==n for a,n in exp.items()))
# 6 downgrades
for a in ['004060f0','00406130','00406170','004061d0','00406270','00406310']:
    r=[x for x in rows if x.split(TAB)[0].lower()==a][0]
    ck('downgrade '+a,r.split(TAB)[4]=='[静态推断]')
# atlas gaps
gl=open(os.path.join(BASE,'atlas_gaps.tsv'),encoding='utf-8').read().splitlines()
gaps=[g.split(TAB) for g in gl[1:]]
ck('gaps 9 rows',len(gaps)==9,str(len(gaps)))
ck('gaps chan col',all(len(g)>=9 for g in gaps))
chans=collections.Counter(g[1] for g in gaps)
ck('chan call-jmp=2',chans.get('call-jmp')==0+2,str(dict(chans)))
ck('chan orphan=6',chans.get('orphan')==6,str(dict(chans)))
ck('lower=7',sum(1 for g in gaps if g[1] in ('call-jmp','orphan') and g[7]=='high')==7)
ck('upper=9',len(gaps)==9)
# docs
pl=open(os.path.join(BASE,'PROGRESS.md'),encoding='utf-8').read().splitlines()
ck('PROGRESS<=60',len(pl)<=60,str(len(pl)))
pt='\n'.join(pl)
ck('PROGRESS high96', '96' in pt and '7.43%' in pt)
ck('PROGRESS gap bound','7' in pt and '9' in pt and '下界' in pt and '上界' in pt)
ck('PROGRESS no-C02','C02' in pt and '1214' in pt)
ul=open(os.path.join(BASE,'UNKNOWNS.md'),encoding='utf-8').read()
ck('UNKNOWNS U3 fixed','仅 1 个' in ul and '0x00410B90 WriteINI' in ul)
fl=open(os.path.join(BASE,'FIX_REPORT.md'),encoding='utf-8').read().splitlines()
ck('FIX_REPORT<=40',len(fl)<=40,str(len(fl)))
# evidence
for fn in ('orphan_forward_stdout.txt','orphan_forward_verification.json','verify_name_fixes.txt',
           'verify_coverage_fix.txt','classify_fix_stdout.txt','gap_bound_counts.txt'):
    ck('evidence '+fn,os.path.exists(os.path.join(EVID,fn)))
out=[('PASS' if ok else 'FAIL')+'  '+n+('  ['+ds+']' if ds else '') for n,ok,ds in checks]
nf=sum(1 for _,ok,_ in checks if not ok)
out.append('TOTAL=%d FAIL=%d'%(len(checks),nf))
open(os.path.join(EVID,'validation_fix.txt'),'w',encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
