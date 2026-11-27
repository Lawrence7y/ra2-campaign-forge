#!/usr/bin/env python3
"""R170 K：门禁重钉（V549 -> V550；F23 grade 由 [已证] -> 未取得；F23/F29 floors 随正文更新）。
纪律（沿 R169 S-565 教训）：目录号与版本号必须同改；constants 用 ast 取真值；
MASTER 由门禁自身 canon 五函数 + 11 项顺序重算，并先用旧常量命中旧值自证同法。
"""
import ast, hashlib, io, json, os, re, py_compile, csv
ROOT='/home/t628/projects/ra2-campaign-forge'
FF=ROOT+'/_r160/facts_floors.py'
GR=ROOT+'/_r161/gate_runner.py'
V550=ROOT+'/lead/next_re_20261117_r14/R17_R122_FACTINDEX_V550/FACT_INDEX.tsv'
BAK=ROOT+'/lead/next_re_20261117_r14/R17_LEAD_BASELINE'
A=[]
def ck(i,c,d):
    A.append({'id':i,'ok':bool(c),'detail':str(d)})
    print(('PASS ' if c else 'FAIL ')+i+' :: '+str(d)[:200])

raw=open(V550,'rb').read(); sha=hashlib.sha256(raw).hexdigest(); B=len(raw)
ck('K0 V550 身份', sha.startswith('d85034b0') and B==120495 and raw.count(b'\r')==0, (sha[:8],B))

def backup(p,tag):
    b=open(p,'rb').read()
    d=os.path.join(BAK,os.path.basename(p)+'.before_r170_'+tag+'.bak')
    if os.path.exists(d):
        # 幂等：已存在则必须与本轮起点 sha 相同（否则说明本轮已在跑过，状态不明）
        assert hashlib.sha256(open(d,'rb').read()).hexdigest()==hashlib.sha256(b).hexdigest(), 'bak mismatch'
        return d
    fd=os.open(d,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
    with os.fdopen(fd,'wb') as f: f.write(b)
    assert hashlib.sha256(open(d,'rb').read()).hexdigest()==hashlib.sha256(b).hexdigest()
    return d
bkf=backup(FF,'FACTS_FLOORS'); bkg=backup(GR,'GATE_RUNNER')

src=open(FF,encoding='utf-8').read()
def tops(text):
    out={}
    for n in ast.parse(text).body:
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
            try: out[n.targets[0].id]=ast.literal_eval(n.value)
            except Exception: pass
    return out
C=tops(src)
for n in ('CUR_SHA256','TOTAL_BYTES','GRADES','FLOORS','EVID','EVIDB','LOST','MASTER_SHA256','ITEMS','UNIQ','LOST_ITEMS','LOST_UNIQ'):
    assert n in C, n
ns={}
# 直接 exec 五个 canon 定义
for fn in ('canon_g','canon_f','canon_e','canon_eb','canon_l'):
    m=re.search(r'^def %s\(d\):.*$'%fn, src, re.M)
    assert m, fn
    exec(m.group(0), ns)

def master_of(cur,total,grades,floors,evid,evidb,lost,items,uniq,li,lu):
    blob='\n'.join([cur,str(total),ns['canon_g'](grades),ns['canon_f'](floors),ns['canon_e'](evid),
                    ns['canon_eb'](evidb),ns['canon_l'](lost),str(items),str(uniq),str(li),str(lu)])
    return hashlib.sha256(blob.encode()).hexdigest()

old_master=C['MASTER_SHA256']
rec_old=master_of(C['CUR_SHA256'],C['TOTAL_BYTES'],C['GRADES'],C['FLOORS'],C['EVID'],C['EVIDB'],
                  C['LOST'],C['ITEMS'],C['UNIQ'],C['LOST_ITEMS'],C['LOST_UNIQ'])
ck('K1 旧常量复算命中旧 MASTER（同法自证）', rec_old==old_master, (rec_old[:16],old_master[:16]))

rows=list(csv.reader(io.StringIO(raw.decode('utf-8')),delimiter='\t'))
byid={r[0]:r for r in rows[1:]}
new_f23=(len(byid['F23'][1].encode()),len(byid['F23'][4].encode()))
new_f29=(len(byid['F29'][1].encode()),len(byid['F29'][4].encode()))
GRADES=dict(C['GRADES']); GRADES['F23']='未取得'
FLOORS=dict(C['FLOORS']); old_f23=FLOORS['F23']; old_f29=FLOORS['F29']
FLOORS['F23']=new_f23; FLOORS['F29']=new_f29
new_master=master_of(sha,B,GRADES,FLOORS,C['EVID'],C['EVIDB'],C['LOST'],C['ITEMS'],C['UNIQ'],C['LOST_ITEMS'],C['LOST_UNIQ'])
ck('K2 新 MASTER 与旧不同', new_master!=old_master, (new_master[:16]))

src2=src
src2=re.sub(r'^CUR_SHA256 = \'.*\'$', "CUR_SHA256 = '%s'"%sha, src2, count=1, flags=re.M)
src2=re.sub(r'^TOTAL_BYTES = \d+$', 'TOTAL_BYTES = %d'%B, src2, count=1, flags=re.M)
src2=re.sub(r'^MASTER_SHA256 = \'.*\'$', "MASTER_SHA256 = '%s'"%new_master, src2, count=1, flags=re.M)
src2=src2.replace('R17_R121_FACTINDEX_V549','R17_R122_FACTINDEX_V550')
src2=re.sub(r"'F23': \(1785, 5711\),", "'F23': (%d, %d),"%new_f23, src2, count=1)
src2=re.sub(r"'F29': \(3432, 13343\),", "'F29': (%d, %d),"%new_f29, src2, count=1)
src2=re.sub(r"    'F23': '\[已证\]',", "    'F23': '未取得',", src2, count=1)
open(FF,'w',encoding='utf-8',newline='').write(src2)
py_compile.compile(FF,doraise=True)

gr=open(GR,encoding='utf-8').read()
gr2=gr.replace('R17_R121_FACTINDEX_V549','R17_R122_FACTINDEX_V550').replace('V549','V550')
open(GR,'w',encoding='utf-8',newline='').write(gr2)
py_compile.compile(GR,doraise=True)

back=tops(open(FF,encoding='utf-8').read())
ck('K3 常量读回：CUR_SHA256/TOTAL_BYTES/GRADES[F23]/FLOORS[F23,F29]/MASTER',
   back['CUR_SHA256']==sha and back['TOTAL_BYTES']==B and back['GRADES']['F23']=='未取得'
   and back['FLOORS']['F23']==new_f23 and back['FLOORS']['F29']==new_f29 and back['MASTER_SHA256']==new_master,
   (back['GRADES']['F23'],back['FLOORS']['F23'],back['FLOORS']['F29']))
ck('K4 其余 53 条 FLOORS 逐条不变', all(back['FLOORS'][k]==C['FLOORS'][k] for k in C['FLOORS'] if k not in ('F23','F29')), 52)
ck('K5 其余 53 条 GRADES 逐条不变', all(back['GRADES'][k]==C['GRADES'][k] for k in C['GRADES'] if k!='F23'), 53)
ck('K6 facts_floors 里 V549/R17_R121 归零', 'V549' not in src2 and 'R17_R121' not in src2, (src2.count('V549'),src2.count('R17_R121')))
ck('K7 gate_runner 里 V549 归零、V550 恰 5 处', gr2.count('V550')==5 and gr2.count('V549')==0, (gr.count('V549'),gr2.count('V550')))
ck('K8 反控：gate_runner 仍无行首 GATE_VER 赋值', not re.search(r'^GATE_VER\s*=',gr2,re.M), 'ok')
json.dump({'assertions':A,'fail':sum(1 for a in A if not a['ok']),'sha':sha,'bytes':B,
           'new_master':new_master,'old_master':old_master,'new_f23':new_f23,'old_f23':old_f23,
           'new_f29':new_f29,'old_f29':old_f29,'backups':[bkf,bkg],
           'ff_after':hashlib.sha256(open(FF,'rb').read()).hexdigest(),
           'gr_after':hashlib.sha256(open(GR,'rb').read()).hexdigest()},
          open(ROOT+'/_r170/r170k_repin.json','w'),ensure_ascii=False,indent=1)
print('FAIL =',sum(1 for a in A if not a['ok']),'/',len(A))
print('new master',new_master)
