# -*- coding: utf-8 -*-
"""R221 p7：FACT_INDEX 指针与门禁重钉（V602 -> V603）。先写版本目录（p6 已完成）、后改指针。"""
import hashlib, os, ast, json
ROOT='/home/t628/projects/ra2-campaign-forge'; TIER=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/R17_LEAD_BASELINE'; FF=ROOT+'/_r160/facts_floors.py'; GR=ROOT+'/_r161/gate_runner.py'
PT=TIER+'/FACT_INDEX_CURRENT.md'
NEWD='R17_R131_FACTINDEX_V603'; OLDD='R17_R131_FACTINDEX_V602'
TSV=TIER+'/'+NEWD+'/FACT_INDEX.tsv'
raw=open(TSV,'rb').read(); newsha=hashlib.sha256(raw).hexdigest()
fails=[]
def ck(n,c,d=''):
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
def bak(path,tag):
    b=open(path,'rb').read()
    base='%s/%s.before_r221_%s'%(BASE,os.path.basename(path),tag)
    for i in range(10):
        dst=base+(('_%d'%i) if i else '')+'_20261128.bak'
        if os.path.exists(dst):
            if open(dst,'rb').read()==b: return b
            continue
        fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
        with os.fdopen(fd,'wb') as f: f.write(b)
        return b
    raise SystemExit('bak exhausted')
print('新 V603 sha=%s bytes=%d'%(newsha,len(raw)))
ck('P1 V603 CR=0 且字节增长', raw.count(b'\r')==0 and len(raw)>290024)
ck('P1b sha != V602 87ed9228', not newsha.startswith('87ed9228'))
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
m_old=master_of('87ed922851b156ed8487c5f2fa27c90403bc83168ea5ad584cae5f23e569aa5d',290024)
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
open(GR,'wb').write(s.encode()); print('[GR] LEDGER -> V603')
b=bak(PT,'PT'); s=b.decode()
old_sha='87ed922851b156ed8487c5f2fa27c90403bc83168ea5ad584cae5f23e569aa5d'
for old,new in [(OLDD,NEWD),(old_sha,newsha),('| 字节数 | 290024 |','| 字节数 | %d |'%len(raw)),
                ('| 声明轮次 | R220（V602） |','| 声明轮次 | R221（V603） |')]:
    ck('P7 指针替换 %r'%old[:26], s.count(old)>=1, s.count(old)); s=s.replace(old,new)
s=s.replace('| 声明依据 |','| 声明依据 | **R221 再升 V603**（ADPCM 编解码常量区全解：两块 9056 B 镜像逐字节同一、双解码器差 = 纯表地址重定位 25 段 + 1 段尾声、律 D 与律 S 双双 1424/1424 闭合而 R220「余 22 块」= floor 口径错），区间改为 **530..603**；',1)
open(PT,'wb').write(s.encode()); print('[PT] 指针 -> V603')
json.dump(dict(newsha=newsha,bytes=len(raw),master=m_new,old_master=G['MASTER_SHA256']),
          open(ROOT+'/_r221/p7.json','w'),indent=1)
print('[OK] 重钉完成')
