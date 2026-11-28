# -*- coding: utf-8 -*-
"""R206 独立复算：从 gamemd.exe 的 PE 头推导段映射，重新推导 5 项 RTTI 数字。
禁止读取 _r206 目录；只读 ra2bench/gamemd.exe 与 _r185/pe185.py（仅参考思路，不 import）。
"""
import struct, collections, hashlib, os

ROOT='/home/t628/projects/ra2-campaign-forge'
PATH=ROOT+'/ra2bench/gamemd.exe'
RAW=open(PATH,'rb').read()
print('# BINARY | size=%d | sha256=%s' % (len(RAW), hashlib.sha256(RAW).hexdigest()))

# ---------- 1. 自行实现 PE 段映射 ----------
pe_off=struct.unpack_from('<I',RAW,0x3c)[0]
assert RAW[pe_off:pe_off+4]==b'PE\0\0'
nsec=struct.unpack_from('<H',RAW,pe_off+6)[0]
optsz=struct.unpack_from('<H',RAW,pe_off+20)[0]
imagebase=struct.unpack_from('<I',RAW,pe_off+24+28)[0]
secs=[]
for i in range(nsec):
    o=pe_off+24+optsz+40*i
    name=RAW[o:o+8].rstrip(b'\0').decode('latin1')
    vsize,va,rsize,rawoff=struct.unpack_from('<IIII',RAW,o+8)
    secs.append(dict(name=name, lo=imagebase+va, vhi=imagebase+va+vsize,
                     rawptr=rawoff, fhi=imagebase+va+rsize, rsize=rsize))
SECBY={s['name']:s for s in secs}
print('# SECTIONS | ' + ' | '.join('%s va=%08x..%08x raw=%x..%x' %
      (s['name'],s['lo'],s['vhi'],s['rawptr'],s['fhi']) for s in secs))

def sec_of(va):
    for s in secs:
        if s['lo']<=va<s['fhi']: return s
    return None
def r2o(va):
    s=sec_of(va)
    return None if s is None else s['rawptr']+(va-s['lo'])
def dw(va):
    o=r2o(va)
    return None if o is None else struct.unpack_from('<I',RAW,o)[0]
def in_sec(va,name):
    s=SECBY[name]
    return s['lo']<=va<s['fhi']

# ---------- 2. 独立收集 COL 记录，反推 HEAD 集合 ----------
# COL 20B: sig(0..2) mdisp(4) cdOffset(8)=0 pTD(12) pCHD(16)
rdata=SECBY['.rdata']; data=SECBY['.data']
data_range=(data['lo'],data['fhi'])
collected={}  # colva -> (pTD,pCHD)
step=4
for va in range(rdata['lo'], rdata['fhi']-20, step):
    o=r2o(va)
    sig=struct.unpack_from('<I',RAW,o)[0]
    if sig>2: continue
    cd=struct.unpack_from('<I',RAW,o+8)[0]
    if cd!=0: continue
    pTD=struct.unpack_from('<I',RAW,o+12)[0]
    pCHD=struct.unpack_from('<I',RAW,o+16)[0]
    if in_sec(pTD,'.data') and in_sec(pCHD,'.rdata') and pCHD%8==0:
        cstr_off=r2o(pTD+8)
        if cstr_off is not None and RAW[cstr_off:cstr_off+2]==b'.?':
            collected[va]=(pTD,pCHD)
heads=sorted({pCHD for (_,_,pCHD) in [(v,a,b) for v,(a,b) in collected.items()]})
print('# COL candidates=%d | distinct HEAD=%d | all 8-aligned=%s' %
      (len(collected),len(heads),all(h%8==0 for h in heads)))
print('# HEAD first5=%s last5=%s' %
      ([hex(x) for x in heads[:5]],[hex(x) for x in heads[-5:]]))

# 为每块找 24B 项（COL，其 pCHD 指向本块 HEAD 且 colva != HEAD+16）
items_by_head=collections.defaultdict(list)
for colva,(pTD,pCHD) in collected.items():
    if colva!=pCHD+16:
        items_by_head[pCHD].append(colva)
for h in items_by_head: items_by_head[h].sort()

# 逐 HEAD 验证 36B 结构（按背景口径的判据，仅用于筛选 head 合法性）
def head_ok(h):
    return (dw(h)==0 and dw(h+16) in (0,1,2) and
            dw(h+24)==0 and dw(h+32)==h and in_sec(dw(h+12),'.rdata') or
            (dw(h)==0 and dw(h+32)==h))
heads_ok=[h for h in heads if dw(h)==0 and dw(h+32)==h]
heads_sorted=sorted(heads_ok)
print('# HEAD with dw(h)==0 and dw(h+32)==h: %d/%d' % (len(heads_ok),len(heads)))

# ---------- 3. 从 HEAD 的 BCA 反推所有 BCD ----------
bca_by_head={}
bcd_refs=collections.defaultdict(list)   # bcdva -> [referencing HEAD]
for h in heads_ok:
    nb=dw(h+8); pBCA=dw(h+12)
    arr=[]
    if in_sec(pBCA,'.rdata') and nb<10000:
        for i in range(nb):
            b=dw(pBCA+4*i)
            arr.append(b)
            if in_sec(b,'.rdata'):
                bcd_refs[b].append(h)
    bca_by_head[h]=arr
bcds=sorted(bcd_refs)
# BCD 合法性：pdisp at +12 == 0xffffffff, +16==0,+20==0
bcd_ok=[b for b in bcds if dw(b+12)==0xffffffff and dw(b+16)==0 and dw(b+20)==0]
print('# BCD distinct=%d | structurally valid=%d | total refs=%d' %
      (len(bcds),len(bcd_ok),sum(len(v) for v in bcd_refs.values())))

# ---------- 计算每个 HEAD 的块范围（从相邻 HEAD 推导 lo/hi） ----------
# 块 = [lo, HEAD+36)，下一个 HEAD 的 lo 之前属于本块；首块 lo=min(HEAD)-? 由属于它的项推导
block_lo={}
# 首块起点：所有属于首块的项/BCA/BCD 的最小地址
first=heads_sorted[0]
addrs=[]
for it in items_by_head.get(first,[]): addrs.append(it)
for b in bca_by_head[first]:
    if b in bcd_refs: addrs.append(b)
pBCA=dw(first+12); nb=dw(first+8)
addrs.append(pBCA)
block_lo[first]=min(addrs)
for i in range(1,len(heads_sorted)):
    h=heads_sorted[i]; prev=heads_sorted[i-1]
    block_lo[h]=prev+36
# 校验 lo 都是 8 对齐
print('# block_lo 8-aligned=%d/%d' % (sum(1 for h in heads_ok if block_lo[h]%8==0),len(heads_ok)))

# ================= 以下为 5 项实测 =================
print('\n========== ITEM 1 ==========')
for off in (0,8,12,16,32):
    ctr=collections.Counter(dw(h+off) for h in heads_ok)
    top=ctr.most_common(4)
    print('offset +%2d distinct=%d top4=%s' %
          (off,len(ctr),[(hex(v),n) for v,n in top]))
for d in (-8,-4,0,4,8):
    n=sum(1 for h in heads_ok if dw(h+32+d)==h)
    print('dw(a+32%+d)==a : %d/%d' % (d,n,len(heads_ok)))

print('\n========== ITEM 2 ==========')
lo=min(heads_ok); hi=max(heads_ok)+36
print('RTTI interval = [0x%x, 0x%x) size=%d' % (lo,hi,hi-lo))
for tag,base in (('low',lo),('high',hi-16)):
    vals=[dw(base+4*i) for i in range(4)]
    print('%s 4 dwords @0x%x: %s' % (tag,base,' '.join(hex(v) for v in vals)))

print('\n========== ITEM 3 ==========')
# 每条 BCD 的唯一物理持有块（用与 ITEM 4 相同的判据）
def holder_of(b):
    cand=[h for h in heads_sorted if block_lo[h]<=b<h+36]
    return cand[0] if cand else None
bcd_holder={b:holder_of(b) for b in bcd_refs}

owner=collections.defaultdict(list)
def tag(va,cat):
    if lo<=va<hi: owner[va].append(cat)

for h in heads_sorted:
    b_lo=block_lo[h]
    # 24B 项：COL 且 pCHD==h
    for it in items_by_head.get(h,[]):
        for k in range(6): tag(it+4*k,'ITEM24')
    # BCA
    pBCA=dw(h+12); nb=dw(h+8)
    for i in range(nb): tag(pBCA+4*i,'BCA')
    # HEAD 36
    for k in range(9): tag(h+4*k,'HEAD36')
    # pad：块内 [b_lo,h+36) 中尚未归属的 dword
occupied=[]
for it in items_by_head.get(h,[]): occupied.append((it,it+24))
for b,H in bcd_holder.items():
    if H==h: occupied.append((b,b+24))
occupied.append((pBCA,pBCA+4*nb))
occupied.append((h,h+36))
occupied.sort()
pos=b_lo
for a,z in occupied:
    while pos<a:
        tag(pos,'PAD'); pos+=4
    pos=max(pos,z)
# BCD 单独归属
for b,H in bcd_holder.items():
    if H is not None:
        for k in range(6): tag(b+4*k,'BCD')

counts=collections.Counter()
for va,cats in owner.items():
    for c in cats: counts[c]+=1
multi=sum(1 for cats in owner.values() if len(cats)>1)
unowned=sum(1 for va in range(lo,hi,4) if va not in owner)
total_dw=(hi-lo)//4
print('total dwords=%d | assigned unique=%d | multi-assigned=%d | unowned=%d' %
      (total_dw,len(owner),multi,unowned))
print('category dwords=%s' % dict(counts))
for c in ('HEAD36','ITEM24','BCD','BCA','PAD'):
    print('  %-8s dwords=%5d bytes=%6d' % (c,counts[c],counts[c]*4))
print('sum category dwords=%d (expect=%d) | sum bytes=%d' %
      (sum(counts.values()),total_dw,sum(counts.values())*4))
# 列出多归属样本
samples=[(hex(va),cats) for va,cats in owner.items() if len(cats)>1][:5]
print('multi samples=%s' % samples)

print('\n========== ITEM 4 ==========')
# holder_of 已在 ITEM 3 定义
hit_min=hit_max=hit_near=0; total=0
for b,refs in bcd_refs.items():
    holder=holder_of(b)
    if holder is None: continue
    total+=1
    greater=[h for h in refs if h>b]
    less=[h for h in refs if h<b]
    if greater and holder==min(greater): hit_min+=1
    if holder==max(refs): hit_max+=1
    near=min(refs,key=lambda h:abs(h-b))
    if holder==near: hit_near+=1
print('BCD total=%d | min{r>b}=%d | max{refs}=%d | nearest=%d' %
      (total,hit_min,hit_max,hit_near))

print('\n========== ITEM 5 ==========')
shape=collections.Counter()
for h in heads_sorted:
    items=items_by_head.get(h,[])
    s=''.join('C' for _ in items)
    shape[s]+=1
def c_prefix(s):
    return all(x=='C' for x in s[:len(s)-s[::-1].index('B')-1]) if 'B' in s else all(x=='C' for x in s)
# 简化：所有 C 都在 B 之前
all_c_prefix=all(not any(s[i]=='C' for i in range(s.index('B')+1,len(s))) if 'B' in s else True
                 for s in shape for _ in range(shape[s]))
print('top10 shapes=%s' % shape.most_common(10))
print('distinct shapes=%d | C-always-prefix=%s' % (len(shape),all_c_prefix))
print('items total=%d' % sum(len(items_by_head.get(h,[])) for h in heads_sorted))
