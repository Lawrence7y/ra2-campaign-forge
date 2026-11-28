import hashlib, re, os
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
fails=[]
def ck(n,c,d=''):
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
# 1 四件套
for name,path,cr in (('R14',TIER+'/R14_COMMON.md',1081),('GOAL',ROOT+'/lead/GOAL_THREE_TARGETS_20261018.md',337),
                     ('LOCK',ROOT+'/lead/LEAD_LOCK',137),('BOARD',TIER+'/STATUS_BOARD.md',0),
                     ('ARCH',TIER+'/BOARD_ARCHIVE.md',2952)):
    b=open(path,'rb').read()
    ck('S1 %s CR=%d'%(name,cr),b.count(b'\r')==cr,b.count(b'\r'))
ck('S2 BOARD 行数 <= 300',open(TIER+'/STATUS_BOARD.md','rb').read().count(b'\n')<=300)
# 2 LEDGER 指针三方一致
pt=open(TIER+'/FACT_INDEX_CURRENT.md',encoding='utf-8').read()
d=re.search(r'\| 版本目录 \| (R17_R131_FACTINDEX_V\d+) \|',pt).group(1)
sha=re.search(r'\| sha256 \| ([0-9a-f]{64}) \|',pt).group(1)
nb=int(re.search(r'\| 字节数 \| (\d+) \|',pt).group(1))
p=TIER+'/'+d+'/FACT_INDEX.tsv'
b=open(p,'rb').read()
ck('S3 指针目录 = V605',d=='R17_R131_FACTINDEX_V605',d)
ck('S4 sha 与现盘一致',hashlib.sha256(b).hexdigest()==sha,(hashlib.sha256(b).hexdigest()[:16],sha[:16]))
ck('S5 字节数一致',len(b)==nb,(len(b),nb))
ck('S6 LEDGER CR=0',b.count(b'\r')==0)
ff=open(ROOT+'/_r160/facts_floors.py',encoding='utf-8').read()
ck('S7 facts_floors EXPECT_CUR -> V605',"R17_R131_FACTINDEX_V605" in ff)
ck('S8 facts_floors CUR_SHA256 == 现盘',sha in ff)
ck('S9 facts_floors TOTAL_BYTES == %d'%nb,('TOTAL_BYTES = %d'%nb) in ff)
gr=open(ROOT+'/_r161/gate_runner.py',encoding='utf-8').read()
ck('S10 gate_runner LEDGER -> V605',"R17_R131_FACTINDEX_V605" in gr)
# 3 C16 floors
cd=open(TIER+'/check_disc.py',encoding='utf-8').read()
m=re.search(r'C16_FLOORS = \{(.*?)\n\}',cd,re.S)
tbl={}
for ln in m.group(1).split('\n'):
    ln=ln.strip()
    if not ln: continue
    k,v=ln.split(':'); tbl[int(k)]=int(v.strip().rstrip(','))
sh=hashlib.sha256('\n'.join('%d:%d'%(k,tbl[k]) for k in sorted(tbl)).encode()).hexdigest()
pin=re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'",cd).group(1)
ck('S11 C16_FLOORS 223 节且 231 已钉',len(tbl)==223 and 231 in tbl,(len(tbl),231 in tbl))
ck('S12 C16_FLOORS_SHA256 自洽',sh==pin,(sh[:16],pin[:16]))
# 4 vs actual R14 section sizes
rc=open(TIER+'/R14_COMMON.md','rb').read().decode('utf-8')
secs=[];cur=None;buf=[]
for l in rc.split('\n'):
    mm=re.match(r'^## (2\.(\d+))\b',l)
    if mm:
        if cur is not None: secs.append((cur,len('\n'.join(buf).encode())))
        cur=int(mm.group(2)); buf=[l]
    elif cur is not None: buf.append(l)
if cur is not None: secs.append((cur,len('\n'.join(buf).encode())))
dd=dict(secs)
ck('S13 C16 钉的 231 大小 == 实测',tbl[231]==dd[231],(tbl[231],dd[231]))
ck('S14 R14 末节 = 231',secs[-1][0]==231,secs[-1])
print('[SUCCESS]' if not fails else '[FAILS] %s'%fails)
