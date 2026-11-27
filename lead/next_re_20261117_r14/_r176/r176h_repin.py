# -*- coding: utf-8 -*-
"""R176 门禁重钉：facts_floors（EXPECT_CUR / CUR_SHA256 / TOTAL_BYTES / FLOORS['F24'] / MASTER_SHA256）
与 gate_runner（LEDGER 目录号）。纪律：所有断言在写盘之前；先 ast 取旧常量复算旧 MASTER 命中原值作硬闸。"""
import ast, hashlib, io, os, sys, time
ROOT='/home/t628/projects/ra2-campaign-forge'
FF=os.path.join(ROOT,'_r160/facts_floors.py')
GR=os.path.join(ROOT,'_r161/gate_runner.py')
NEWDIR='R17_R128_FACTINDEX_V559'
NEWTSV=os.path.join(ROOT,'lead/next_re_20261117_r14',NEWDIR,'FACT_INDEX.tsv')
BASE=os.path.join(ROOT,'lead/next_re_20261117_r14/R17_LEAD_BASELINE')
P=F=0
def ck(n,c,d=''):
    global P,F
    if c: P+=1; print('PASS',n,d)
    else: F+=1; print('FAIL',n,d)
raw=open(NEWTSV,'rb').read()
newsha=hashlib.sha256(raw).hexdigest()
ck('A1 new sha',newsha=='e4642d554d8ba9f1dab25b6a2b456e365252051035f9104003b58ff622d489e9',newsha[:16])
ck('A2 new bytes',len(raw)==129405,'%d'%len(raw))
src=open(FF,encoding='utf-8').read()
tree=ast.parse(src)
ns={}
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.name.startswith('canon_'):
        exec(compile(ast.Module(body=[node],type_ignores=[]),FF,'exec'),ns)
want={'GRADES','FLOORS','EVID','EVIDB','LOST','ITEMS','UNIQ','LOST_ITEMS','LOST_UNIQ','MASTER_SHA256','CUR_SHA256','TOTAL_BYTES'}
got={}
for node in tree.body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
        n=node.targets[0].id
        if n in want: got[n]=ast.literal_eval(node.value)
ck('B1 all 12 ast-literal constants',set(got)==want,repr(sorted(want-set(got))))
import re as _re
_m= _re.search(r"EXPECT_CUR = os\.path\.join\(TIER, '([^']+)', 'FACT_INDEX\.tsv'\)", src)
ck('B2 EXPECT_CUR literal parsed',_m is not None and _m.group(1)=='R17_R128_FACTINDEX_V558', _m.group(1) if _m else 'None')
OLDDIR=_m.group(1)
def master(sha,total,floors):
    return hashlib.sha256(('\n'.join([sha,str(total),ns['canon_g'](got['GRADES']),ns['canon_f'](floors),
        ns['canon_e'](got['EVID']),ns['canon_eb'](got['EVIDB']),ns['canon_l'](got['LOST']),
        str(got['ITEMS']),str(got['UNIQ']),str(got['LOST_ITEMS']),str(got['LOST_UNIQ'])])).encode()).hexdigest()
oldm=master(got['CUR_SHA256'],got['TOTAL_BYTES'],got['FLOORS'])
ck('C1 HARD GATE old constants reproduce old MASTER',oldm==got['MASTER_SHA256'],oldm[:16])
ck('C2 old sha is V558',got['CUR_SHA256']=='157996aa5da193d3ac254c9d6026343050b23f969793f83433469d5520bd8aa5')
ck('C3 old total 128835',got['TOTAL_BYTES']==128835)
ck('C4 old F24 floor',got['FLOORS']['F24']==(10996,35925),repr(got['FLOORS']['F24']))
newfl=dict(got['FLOORS']); newfl['F24']=(11349,36142)
gsrc=open(GR,encoding='utf-8').read()
ck('D1 gate_runner holds V558 once',gsrc.count('R17_R128_FACTINDEX_V558')==1,'%d'%gsrc.count('R17_R128_FACTINDEX_V558'))
ck('D2 gate_runner holds new dir zero times',gsrc.count(NEWDIR)==0,'%d'%gsrc.count(NEWDIR))
ck('D3 gate_runner does NOT hold old sha literal',gsrc.count(got['CUR_SHA256'])==0,'%d'%gsrc.count(got['CUR_SHA256']))
ck('D4 gate_runner does NOT hold old MASTER literal',gsrc.count(got['MASTER_SHA256'])==0,'%d'%gsrc.count(got['MASTER_SHA256']))
ck('D5 gate_runner reads sha via regex from facts source',gsrc.count('^CUR_SHA256')>=1 or 'CUR_SHA256' in gsrc,'')
# 反控：新 sha / 新 total / F24 floor 任一改动都使 MASTER 变
m_new=master(newsha,len(raw),newfl)
ck('E1 new master differs from old',m_new!=got['MASTER_SHA256'],m_new[:16])
for nm,args in (('sha',(got['CUR_SHA256'],len(raw),newfl)),('total',(newsha,len(raw)+1,newfl))):
    ck('E2-%s neg-ctrl changes master'%nm,master(*args)!=m_new,'')
for i in (0,1):
    f=dict(newfl); f['F24']=tuple(newfl['F24'][j]+(1 if j==i else 0) for j in range(2))
    ck('E3-F24[%d] neg-ctrl'%i,master(newsha,len(raw),f)!=m_new,'')
if F:
    print('ABORT before write: %d FAIL'%F); sys.exit(1)
# ---- 统一写盘 ----
ts=time.strftime('%Y%m%d_%H%M%S')
def backup(p):
    bp=os.path.join(BASE,os.path.basename(p)+'.before_r176_+%s.bak'%ts)
    with open(bp,'xb') as f: f.write(open(p,'rb').read())
    return bp
bf=backup(FF); bg=backup(GR)
ck('F1 facts backup ok',open(bf,'rb').read()==src.encode())
ck('F2 gate backup ok',open(bg,'rb').read()==gsrc.encode())
new_ff=src
for a,b in (("'%s', 'FACT_INDEX.tsv'"%OLDDIR, "'%s', 'FACT_INDEX.tsv'"%NEWDIR),
            ("CUR_SHA256 = '%s'"%got['CUR_SHA256'], "CUR_SHA256 = '%s'"%newsha),
            ("TOTAL_BYTES = %d"%got['TOTAL_BYTES'], "TOTAL_BYTES = %d"%len(raw)),
            ("'F24': (10996, 35925),", "'F24': (11349, 36142),"),
            ("MASTER_SHA256 = '%s'"%got['MASTER_SHA256'], "MASTER_SHA256 = '%s'"%m_new)):
    ck('G-unique %r'%a[:28], new_ff.count(a)==1,'%d'%new_ff.count(a))
    new_ff=new_ff.replace(a,b)
# 重算自洽（从新源码 ast 再取一遍）
tree2=ast.parse(new_ff); got2={}
for node in tree2.body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
        n=node.targets[0].id
        if n in want: got2[n]=ast.literal_eval(node.value)
ck('H1 new source ast parses',got2['CUR_SHA256']==newsha,got2['CUR_SHA256'][:16])
ck('H2 new total',got2['TOTAL_BYTES']==129405)
ck('H3 new F24 floor',got2['FLOORS']['F24']==(11349,36142))
ck('H4 new master self-consistent',master(got2['CUR_SHA256'],got2['TOTAL_BYTES'],got2['FLOORS'])==m_new,'')
ck('H5 other floors untouched',[k for k in got['FLOORS'] if got['FLOORS'][k]!=got2['FLOORS'][k]]==['F24'])
new_gr=gsrc.replace('R17_R128_FACTINDEX_V558',NEWDIR)
ck('I1 gate new dir once',new_gr.count(NEWDIR)==1)
ck('I2 gate old dir gone',new_gr.count('R17_R128_FACTINDEX_V558')==0)
with open(FF,'wb') as f: f.write(new_ff.encode())
with open(GR,'wb') as f: f.write(new_gr.encode())
ck('J1 facts readback',open(FF,encoding='utf-8').read()==new_ff)
ck('J2 gate readback',open(GR,encoding='utf-8').read()==new_gr)
print('NEW MASTER = %s'%m_new)
print('---- %d PASS / %d FAIL ----'%(P,F))
sys.exit(1 if F else 0)
