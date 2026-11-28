# -*- coding: utf-8 -*-
"""R220 p7：FACT_INDEX 指针与门禁重钉（V601 -> V602）。先写版本目录（p6 已完成）、后改指针。"""
import hashlib, os, ast, json
ROOT='/home/t628/projects/ra2-campaign-forge'; TIER=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/R17_LEAD_BASELINE'; FF=ROOT+'/_r160/facts_floors.py'; GR=ROOT+'/_r161/gate_runner.py'
PT=TIER+'/FACT_INDEX_CURRENT.md'
NEWD='R17_R131_FACTINDEX_V602'; OLDD='R17_R131_FACTINDEX_V601'
TSV=TIER+'/'+NEWD+'/FACT_INDEX.tsv'
raw=open(TSV,'rb').read(); newsha=hashlib.sha256(raw).hexdigest()
fails=[]
def ck(n,c,d=''):
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
def bak(path,tag):
    b=open(path,'rb').read()
    base='%s/%s.before_r220_%s'%(BASE,os.path.basename(path),tag)
    for i in range(10):
        dst=base+(('_%d'%i) if i else '')+'_20261128.bak'
        if os.path.exists(dst):
            if open(dst,'rb').read()==b: return b
            continue
        fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
        with os.fdopen(fd,'wb') as f: f.write(b)
        return b
    raise SystemExit('bak exhausted')
print('新 V602 sha=%s bytes=%d'%(newsha,len(raw)))
ck('P1 V602 CR=0 且字节增长', raw.count(b'\r')==0 and len(raw)>284839)
ck('P1b sha != V601 54ff0419', not newsha.startswith('54ff0419'))
src=open(FF,encoding='utf-8').read(); tree=ast.parse(src); G={}
for node in tree.body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
        nm=node.targets[0].id
        if nm in ('GRADES','FLOORS','EVID','EVIDB','LOST','ITEMS','UNIQ','LOST_ITEMS','LOST_UNIQ',
                  'CUR_SHA256','TOTAL_BYTES','MASTER_SHA256'):
            try: G[nm]=ast.literal_eval(node.value)
            except Exception as e: print('  skip',nm,e)
ck('P2 AST 取到 12 个常量', len(G)==12, sorted(G))
def canon_g(d):  return '\n'.join("    '%s': '%s',"%(k,d[k]) for k in sorted(d))
def canon_f(d):  return '\n'.join("    '%s': (%d, %d),"%(k,d[k][0],d[k][1]) for k in sorted(d))
def canon_e(d):  return '\n'.join("    '%s': [%s],"%(k,', '.join("'%s'"%x for x in d[k])) for k in sorted(d))
def canon_l(d):  return '\n'.join("    '%s': %d,"%(k,d[k]) for k in sorted(d))
def master_of(cur,tot):
    return hashlib.sha256(('\n'.join([cur,str(tot),canon_g(G['GRADES']),canon_f(G['FLOORS']),
        canon_e(G['EVID']),canon_l(G['EVIDB']),canon_l(G['LOST']),str(G['ITEMS']),
        str(G['UNIQ']),str(G['LOST_ITEMS']),str(G['LOST_UNIQ'])])).encode()).hexdigest()
m_new=master_of(newsha,len(raw))
m_old=master_of('54ff04190b015ca13847191e194a47c1263241f5fa8eedd20db00b89b5f83111',284839)
ck('P3 正控 用旧 CUR/TOTAL 复算 == 旧 MASTER', m_old==G['MASTER_SHA256'], (m_old[:16],G['MASTER_SHA256'][:16]))
ck('P4 新 MASTER != 旧 MASTER', m_new!=G['MASTER_SHA256'])
if fails: print('[ABORT-before-write] %r'%fails); raise SystemExit(1)
b=bak(FF,'FF'); s=b.decode()
reps=[("EXPECT_CUR = os.path.join(TIER, '%s', 'FACT_INDEX.tsv')"%OLDD,
       "EXPECT_CUR = os.path.join(TIER, '%s', 'FACT_INDEX.tsv')"%NEWD),
      ("CUR_SHA256 = '%s'"%G['CUR_SHA256'], "CUR_SHA256 = '%s'"%newsha),
      ('TOTAL_BYTES = %d'%G['TOTAL_BYTES'], 'TOTAL_BYTES = %d'%len(raw)),
      ("MASTER_SHA256 = '%s'"%G['MASTER_SHA256'], "MASTER_SHA256 = '%s'"%m_new)]
for old,new in reps:
    ck('P5 facts_floors 旧值命中 1 次 : %s…'%old[:40], s.count(old)==1, s.count(old)); s=s.replace(old,new)
open(FF,'wb').write(s.encode())
chk=open(FF,'rb').read().decode()
assert newsha in chk and ('TOTAL_BYTES = %d'%len(raw)) in chk and NEWD in chk and m_new in chk
print('[FF] EXPECT_CUR / CUR_SHA256 / TOTAL_BYTES / MASTER_SHA256 已重钉')
b=bak(GR,'GR'); s=b.decode()
old="LEDGER = os.path.join(TIER, '%s', 'FACT_INDEX.tsv')"%OLDD
ck('P6 gate_runner 旧 LEDGER 命中 1 次', s.count(old)==1, s.count(old))
s=s.replace(old,"LEDGER = os.path.join(TIER, '%s', 'FACT_INDEX.tsv')"%NEWD)
open(GR,'wb').write(s.encode()); print('[GR] LEDGER -> V602')
b=bak(PT,'PT'); s=b.decode()
old_sha='54ff04190b015ca13847191e194a47c1263241f5fa8eedd20db00b89b5f83111'
for old,new in [(OLDD,NEWD),(old_sha,newsha),('| 字节数 | 284839 |','| 字节数 | %d |'%len(raw)),
                ('| 声明轮次 | R219（V601） |','| 声明轮次 | R220（V602） |')]:
    ck('P7 指针替换 %r'%old[:26], s.count(old)>=1, s.count(old)); s=s.replace(old,new)
s=s.replace('| 声明依据 |','| 声明依据 | **R220 再升 V602**（`0x87c484` 定性为 CRT locale 类别表 6 条；162 记录表真实跨度 2592 B；'
            'IMA ADPCM 三表互锁：89 项 step table / 89 块 diff 表 5696 B 与 0x87b170 零间隙 / 16×16 dither 表；'
            '`.text` 段界 rawsize 1,394,186 vs vsize 1,392,592 差 1594 条填充伪指令），区间改为 **530..602**；',1)
open(PT,'wb').write(s.encode()); print('[PT] 指针 -> V602')
json.dump(dict(newsha=newsha,bytes=len(raw),master=m_new,old_master=G['MASTER_SHA256']),
          open(ROOT+'/_r220/p7.json','w'),indent=1)
print('[OK] 重钉完成')
