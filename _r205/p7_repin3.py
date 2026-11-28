#!/usr/bin/env python3
"""R205 重钉三（收口）：修正 EVID 口径（须经 norm 把 \\ 换成 /）+ FLOORS F01 lim 下限回 15247 + 重算 MASTER。"""
import re,subprocess,os,json,time,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
NEW=ROOT+'/lead/next_re_20261117_r14/R17_R131_FACTINDEX_V588/FACT_INDEX.tsv'
p=ROOT+'/_r160/facts_floors.py'
fails=[]
def ck(n,c,d=''):
    if not c: fails.append(n); print('FAIL '+n+' | '+str(d))
    else: print('PASS '+n)
def strip_note(s):
    s=s.strip()
    if s.endswith(')'):
        d=0
        for i in range(len(s)-1,-1,-1):
            if s[i]==')': d+=1
            elif s[i]=='(':
                d-=1
                if d==0: return s[:i].strip()
    return s
def norm(x): return x.replace('\\','/').strip()

line=[l for l in open(NEW,encoding='utf-8').read().split('\n') if l.startswith('F01\t')][0]
ev=[norm(strip_note(x)) for x in line.split('\t')[3].split(';') if x.strip()]
ck('E1 EVID 30 条且无反斜杠',len(ev)==30 and all('\\' not in x for x in ev),len(ev))

s=open(p,encoding='utf-8').read()
m=re.search(r"    'F01': \[(.*?)\],\n",s,re.S)
s=s[:m.start()]+"    'F01': [%s],\n"%(', '.join("'%s'"%x for x in ev))+s[m.end():]
s=s.replace("    'F01': (6847, 15340),","    'F01': (6847, 15247),")
open(p,'wb').write(s.encode('utf-8'))

def run(ign=False):
    a=['python3',ROOT+'/_r160/facts_floors.py']+(['--ignore-pin'] if ign else [])
    r=subprocess.run(a,capture_output=True,text=True,timeout=300)
    return r.returncode,r.stdout+r.stderr
rc,out=run(True)
mv=re.search(r'D9 master pin: ([0-9a-f]{64})',out)
mm=re.search(r'D7 evidence: items=(\d+) uniq=(\d+) lost_items=(\d+) lost_uniq=(\d+)',out)
ck('E2 拿到 D7/MASTER',mv is not None and mm is not None,out[:150])
items,uniq,lost,lostu=[int(x) for x in mm.groups()]
master=mv.group(1)
s=open(p,encoding='utf-8').read()
s=re.sub(r"ITEMS = \d+","ITEMS = %d"%items,s)
s=re.sub(r"UNIQ = \d+","UNIQ = %d"%uniq,s)
s=re.sub(r"LOST_ITEMS = \d+","LOST_ITEMS = %d"%lost,s)
s=re.sub(r"LOST_UNIQ = \d+","LOST_UNIQ = %d"%lostu,s)
s=re.sub(r"MASTER_SHA256 = '[0-9a-f]{64}'","MASTER_SHA256 = '%s'"%master,s)
open(p,'wb').write(s.encode('utf-8'))

rc2,out2=run(False)
ck('E3 facts_floors exit 0',rc2==0,rc2)
bad=[l for l in out2.split('\n') if 'FAIL' in l]
ck('E4 无 FAIL 行',not bad,bad[:4])
print('   '+'\n   '.join(l for l in out2.split('\n') if l.strip().startswith(('D6','D7','D8','D9','D10'))))
print('\nFAILS:',fails)
json.dump(dict(fails=fails,items=items,uniq=uniq,lost=lost,lostu=lostu,master=master),
          open(ROOT+'/_r205/p7_repin3.json','w'),indent=1)
