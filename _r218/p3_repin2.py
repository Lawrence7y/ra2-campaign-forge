# -*- coding: utf-8 -*-
"""R218 p3：MASTER 重钉 + gate_runner LEDGER + 指针文件。
不 exec facts_floors（其末尾 sys.exit 会打断），改用 AST 文本解析常量，再按同 canon 公式算 MASTER。
fail-closed：全部断言在写盘之前。
"""
import hashlib,os,re,json,ast
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/R17_LEAD_BASELINE'
FF=ROOT+'/_r160/facts_floors.py'; GR=ROOT+'/_r161/gate_runner.py'; PT=TIER+'/FACT_INDEX_CURRENT.md'
NEWD='R17_R131_FACTINDEX_V600'; TSV=TIER+'/'+NEWD+'/FACT_INDEX.tsv'
raw=open(TSV,'rb').read(); newsha=hashlib.sha256(raw).hexdigest()
fails=[]
def ck(n,c,d=''):
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
def bak(path,tag):
    b=open(path,'rb').read()
    base='%s/%s.before_r218_%s'%(BASE,os.path.basename(path),tag)
    for i in range(0,10):
        dst=base+(('_%d'%i) if i else '')+'_20261128.bak'
        if os.path.exists(dst):
            if open(dst,'rb').read()==b: return b
            continue
        fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
        with os.fdopen(fd,'wb') as f: f.write(b)
        print('  [bak] %s'%os.path.basename(dst))
        return b
    raise SystemExit('bak exhausted '+tag)
# --- 用 AST 取常量（不执行模块） ---
src=open(FF,encoding='utf-8').read()
tree=ast.parse(src)
G={}
for node in tree.body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
        nm=node.targets[0].id
        if nm in ('GRADES','FLOORS','EVID','EVIDB','LOST','ITEMS','UNIQ','LOST_ITEMS','LOST_UNIQ',
                  'CUR_SHA256','TOTAL_BYTES','MASTER_SHA256'):
            try: G[nm]=ast.literal_eval(node.value)
            except Exception as e: print('  skip',nm,e)
ck('P5 AST 取到 12 个常量', len(G)==12, sorted(G))
def canon_g(d):  return '\n'.join("    '%s': '%s',"%(k,d[k]) for k in sorted(d))
def canon_f(d):  return '\n'.join("    '%s': (%d, %d),"%(k,d[k][0],d[k][1]) for k in sorted(d))
def canon_e(d):  return '\n'.join("    '%s': [%s],"%(k,', '.join("'%s'"%x for x in d[k])) for k in sorted(d))
def canon_eb(d): return '\n'.join("    '%s': %d,"%(k,d[k]) for k in sorted(d))
def canon_l(d):  return '\n'.join("    '%s': %d,"%(k,d[k]) for k in sorted(d))
master=hashlib.sha256(('\n'.join([G['CUR_SHA256'],str(G['TOTAL_BYTES']),canon_g(G['GRADES']),canon_f(G['FLOORS']),
  canon_e(G['EVID']),canon_eb(G['EVIDB']),canon_l(G['LOST']),str(G['ITEMS']),str(G['UNIQ']),
  str(G['LOST_ITEMS']),str(G['LOST_UNIQ'])])).encode()).hexdigest()
print('  CUR_SHA256=%s TOTAL_BYTES=%d'%(G['CUR_SHA256'][:16],G['TOTAL_BYTES']))
print('  重算 MASTER=%s 旧钉=%s'%(master[:16],G['MASTER_SHA256'][:16]))
ck('P6 重算 MASTER != 旧钉', master!=G['MASTER_SHA256'])
# 自检：用「旧」CUR/TOTAL 复算必须等于旧 MASTER（证明公式与 canon 一致）
old_c='616a86e251fd88e5d4fa7a3c488c15d65ce2c6e1bceb62de6d639ee1dca374e9'; old_t=277566
m_old=hashlib.sha256(('\n'.join([old_c,str(old_t),canon_g(G['GRADES']),canon_f(G['FLOORS']),
  canon_e(G['EVID']),canon_eb(G['EVIDB']),canon_l(G['LOST']),str(G['ITEMS']),str(G['UNIQ']),
  str(G['LOST_ITEMS']),str(G['LOST_UNIQ'])])).encode()).hexdigest()
ck('P7 正控 用旧 CUR/TOTAL 复算 == 旧 MASTER（公式一致）', m_old==G['MASTER_SHA256'], (m_old[:16],G['MASTER_SHA256'][:16]))
if fails: print('[ABORT-before-write] %r'%fails); raise SystemExit(1)
b=bak(FF,'FF'); s=b.decode()
ck('P8 旧 MASTER 字面命中 1 次', s.count("MASTER_SHA256 = '%s'"%G['MASTER_SHA256'])==1)
s=s.replace("MASTER_SHA256 = '%s'"%G['MASTER_SHA256'],"MASTER_SHA256 = '%s'"%master)
open(FF,'wb').write(s.encode()); print('[FF] MASTER 已重钉')
b=bak(GR,'GR'); s=b.decode()
old="LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V599', 'FACT_INDEX.tsv')"
ck('P9 gate_runner 旧 LEDGER 命中 1 次', s.count(old)==1, s.count(old))
s=s.replace(old,"LEDGER = os.path.join(TIER, '%s', 'FACT_INDEX.tsv')"%NEWD)
open(GR,'wb').write(s.encode()); print('[GR] LEDGER -> V600')
b=bak(PT,'PT'); s=b.decode()
reps=[('R17_R131_FACTINDEX_V599',NEWD),
      ('616a86e251fd88e5d4fa7a3c488c15d65ce2c6e1bceb62de6d639ee1dca374e9',newsha),
      ('| 字节数 | 277566 |','| 字节数 | %d |'%len(raw)),
      ('| 声明轮次 | R216（V599） |','| 声明轮次 | R218（V600） |')]
for old,new in reps:
    ck('P10 指针替换 %r'%old[:26], s.count(old)>=1, s.count(old))
    s=s.replace(old,new)
s=s.replace('| 声明依据 |','| 声明依据 | **R218 再升 V600**（虚表口径二分：1214 真虚表 + 4 幻影、BCD 记录 24 B 订正、464 高槽 cov294+diff67+oob103、disp 扫描 18930/931 定稿口径），区间改为 **530..600**；',1)
open(PT,'wb').write(s.encode()); print('[PT] 指针 -> V600')
json.dump(dict(newsha=newsha,bytes=len(raw),master=master,old_master=G['MASTER_SHA256']),open(ROOT+'/_r218/p3.json','w'),indent=1)
print('[OK] 重钉完成')
