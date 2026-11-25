# -*- coding: utf-8 -*-
"""R135-DS · F29 D1..D5 最终一轮（只读）：带一致的分节判据与边界裁决，输出即报告引用原文。

分节判据（显式写出，避免上一轮我自己的边界歧义）：
  rva 落在 [section.VirtualAddress, VirtualAddress+max(VirtualSize, SizeOfRawData)) 内即属于该节；
  恰好落在两节边界（= 后一节起点）时，归后一节（即 .rdata 起点 0x7E1000 归 .rdata，不归 .text）。
"""
import re, struct, io, hashlib, collections

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
D = io.open(EXE, 'rb').read()
e = struct.unpack_from('<I', D, 0x3C)[0]
assert D[e:e+4] == b'PE\0\0'
nsec = struct.unpack_from('<H', D, e+6)[0]
soh  = struct.unpack_from('<H', D, e+20)[0]
opt  = e + 24
IMG  = struct.unpack_from('<I', D, opt+28)[0]
S = []
for i in range(nsec):
    o = opt+soh+i*40
    nm = D[o:o+8].rstrip(b'\0').decode()
    vs, va, rs, ro = struct.unpack_from('<IIII', D, o+8)
    S.append(dict(name=nm, va=va, vs=vs, ro=ro, rs=rs))
SEC_RVA = [(s['name'], s['va'], s['va']+max(s['vs'], s['rs'])) for s in S]
SEC_RAW = [(s['name'], s['ro'], s['ro']+s['rs']) for s in S]

def sec_rva(r):
    # 边界归后一节：取所有 s.va <= r < end 中 va 最大者
    cand = [(va, nm) for nm, va, end in SEC_RVA if va <= r < end]
    return max(cand)[1] if cand else '<none>'

def sec_raw(o):
    cand = [(ro, nm) for nm, ro, end in SEC_RAW if ro <= o < end]
    return max(cand)[1] if cand else '<none>'

def off(r):
    for s in S:
        if s['va'] <= r < s['va']+max(s['vs'], s['rs']):
            return s['ro'] + (r - s['va'])

def dw_rva(r): return struct.unpack_from('<I', D, off(r))[0]

print('# R135-DS F29 最终复算输出（原文）')
print('EXE   = %s' % EXE)
print('size  = %d bytes' % len(D))
print('sha256= %s' % hashlib.sha256(D).hexdigest())
print('ImageBase=0x%08X  NumberOfSections=%d' % (IMG, nsec))
for s in S:
    print('  %-8s VA=0x%08X..0x%08X  raw=0x%06X..0x%06X  (VA=%08x vsize=%08x raw=%08x rsize=%08x)'
          % (s['name'], IMG+s['va'], IMG+s['va']+max(s['vs'], s['rs']), s['ro'], s['ro']+s['rs'],
             s['va'], s['vs'], s['ro'], s['rs']))

# ---------------- D1 ----------------
print('\n########## D1 ##########')
print('正则原文 (Python bytes 正则): \\.\\?AV\\?\\$TClassFactory@V([^@]+)@@')
P = re.compile(rb'\.\?AV\?\$TClassFactory@V([^@]+)@@')
hits = [(m.start(), m.group(1), m.group(0)) for m in P.finditer(D)]
Xs = [x for _, x, _ in hits]
print('命中次数            = %d' % len(hits))
print('不同 X 个数         = %d' % len(set(Xs)))
print('每个 X 的出现次数最大值 = %d' % max(collections.Counter(Xs).values()))
print('命中点所在节分布    = %s' % dict(collections.Counter(sec_raw(o) for o, _, _ in hits)))
print('名字串 RVA 区间     = 0x%06X .. 0x%06X (VA 0x%08X..0x%08X)'
      % (hits[0][0], hits[-1][0], IMG+hits[0][0], IMG+hits[-1][0]))
print('77 个串尾部 @ 个数分布 = %s'
      % dict(collections.Counter(len(D[o+len(f):o+len(f)+5]) - len(D[o+len(f):o+len(f)+5].lstrip(b'@')) for o,_,f in hits)))
print('独立交叉核验 1: 子串 b"TClassFactory" 全文件出现 = %d' % D.count(b'TClassFactory'))
print('独立交叉核验 2: 正则 rb"?AV?\\$TClassFactory@V(.+?)@@" 命中 = %d, 不同 = %d'
      % (len(re.findall(rb'\?AV\?\$TClassFactory@V(.+?)@@', D)),
         len(set(re.findall(rb'\?AV\?\$TClassFactory@V(.+?)@@', D)))))
print('不同 X 全表（字典序，%d 项）:' % len(set(Xs)))
for i, x in enumerate(sorted(set(Xs)), 1):
    print('  %2d %s' % (i, x.decode('latin-1')))

# ---------------- D2 ----------------
print('\n########## D2 ##########')
STUB = bytes.fromhex('B801000000C20400')
print('被搜索字节序列 = ' + ' '.join('%02X' % b for b in STUB))
occ = []
p = D.find(STUB)
while p >= 0:
    occ.append(p); p = D.find(STUB, p+1)
print('全文件出现次数 = %d' % len(occ))
cnt = collections.Counter(sec_raw(o) for o in occ)
print('按节分布       = %s' % dict(cnt))
print('数据节合计(.rdata/.data/.rsrc/.detour) = %d'
      % sum(v for k, v in cnt.items() if k != '.text'))
print('40 处 VA 全表:')
for o in occ:
    print('  VA=0x%08X' % (IMG + o - S[0]['ro'] + S[0]['va']))
print('变体 b"B801000000C20400CC" 出现 = %d' % D.count(STUB + b'\xCC'))

# ---------------- D3 ----------------
print('\n########## D3 ##########')
TGT = bytes.fromhex('8B44240483C00450FF15C8117E00C20400')
for va in (0x6C2AC0, 0x6C51C0):
    r = va - IMG
    o = off(r)
    b = D[o:o+17]
    print('VA=0x%08X  RVA=0x%06X  file_off=0x%06X  sec=%s' % (va, r, o, sec_rva(r)))
    print('  bytes  : ' + ' '.join('%02X' % x for x in b))
    print('  hex    : ' + b.hex().upper())
    print('  sha256 : ' + hashlib.sha256(b).hexdigest())
    print('  == 主张序列: %s' % (b == TGT))
a = D[off(0x6C2AC0-IMG):off(0x6C2AC0-IMG)+17]
b = D[off(0x6C51C0-IMG):off(0x6C51C0-IMG)+17]
print('两处 17 字节逐字节相同 = %s（差异下标 %s）'
      % (a == b, [i for i in range(17) if a[i] != b[i]]))
print('主张序列 sha256 = ' + hashlib.sha256(TGT).hexdigest())
print('旁证: 该 17 字节序列全镜像出现 %d 次, 节分布 %s' % (
    len([1 for q in [m.start() for m in re.finditer(re.escape(TGT), D)]]),
    dict(collections.Counter(sec_raw(m.start()) for m in re.finditer(re.escape(TGT), D)))))
lat = []
q = D.find(TGT)
while q >= 0:
    lat.append(q); q = D.find(TGT, q+1)
print('旁证: 出现点 = %s' % ', '.join('0x%08X' % (IMG+x) for x in lat))
print('旁证: 0x6BEEC0+0x180*i 等差数列项数 = %d (i=0..76), 0x6C2AC0 是第 %d 项, 0x6C51C0 是第 %d 项'
      % (len([x for x in range(77) if 0x6BEEC0+0x180*x in [IMG+y for y in lat]]),
         (0x6C2AC0-0x6BEEC0)//0x180, (0x6C51C0-0x6BEEC0)//0x180))

def vtable_of(va):
    bt = struct.pack('<I', va); out = []
    q = D.find(bt)
    while q >= 0:
        out.append(q); q = D.find(bt, q+1)
    return out
for va in (0x6C2AC0, 0x6C51C0):
    for q in vtable_of(va):
        if sec_raw(q) != '.rdata': continue
        vt = IMG + q - 4 - (S[1]['ro'] - S[1]['va']) if sec_raw(q) == '.rdata' else None
        vt_rva = q - 4 - (S[1]['ro'] - S[1]['va'])
        vt_va = IMG + vt_rva
        col = dw_rva(vt_rva - 4); td = dw_rva(col - IMG + 0xC)
        nm = D[off(td - IMG + 8):off(td - IMG + 8)+96].split(b'\0')[0].decode('latin-1')
        print('  该 VA 被 .rdata off=0x%06X 引用 -> 作为 vtable slot1, vtable VA=0x%08X, 名字=%s'
              % (q, vt_va, nm))

# ---------------- 导入遍历 ----------------
imp_rva = struct.unpack_from('<I', D, opt+96+8)[0]
imp_sz  = struct.unpack_from('<I', D, opt+96+8+4)[0]
iat_rva = struct.unpack_from('<I', D, opt+96+12*8)[0]
iat_sz  = struct.unpack_from('<I', D, opt+96+12*8+4)[0]
print('\n########## 导入表手工遍历（D4/D5 共用基础）##########')
print('DataDirectory[1]  Import RVA=0x%06X size=0x%X (VA=0x%08X)  描述符数=17(含终结符)/16(实)'
      % (imp_rva, imp_sz, IMG+imp_rva))
print('DataDirectory[12] IAT    RVA=0x%06X size=0x%X (VA=0x%08X)  = %d dword'
      % (iat_rva, iat_sz, IMG+iat_rva, iat_sz//4))
desc = []
for i in range(64):
    o = off(imp_rva + i*20)
    oft, ts, fc, nr, ft = struct.unpack_from('<5I', D, o)
    if (oft, ts, fc, nr, ft) == (0,)*5: break
    nm = D[off(nr):off(nr)+64].split(b'\0')[0].decode('latin-1')
    desc.append(dict(name=nm, oft=oft, ft=ft, at=imp_rva+i*20, nr=nr))
print('实描述符 %d 条:' % len(desc))
for i, d in enumerate(desc):
    print('  [%2d] AT_RVA=0x%06X OFT(ILT)=0x%06X FirstThunk(IAT)=0x%06X Name=%-14s NameRVA=0x%06X'
          % (i, d['at'], d['oft'], d['ft'], d['name'], d['nr']))
ent = []
for d in desc:
    ilt = d['oft'] or d['ft']; j = 0
    while True:
        iv = struct.unpack_from('<I', D, off(ilt + j*4))[0]
        if iv == 0: break
        item = dict(dll=d['name'], idx=j, ilt=ilt+j*4, iat=d['ft']+j*4, ord=(iv & 0x80000000) != 0)
        if item['ord']:
            item.update(ordnum=iv & 0xFFFF, ibn=None, hint=None, name=None)
        else:
            ho = off(iv)
            item.update(hint=struct.unpack_from('<H', D, ho)[0],
                        name=D[ho+2:ho+2+512].split(b'\0')[0].decode('latin-1'),
                        ibn=iv)
        ent.append(item); j += 1
    d['n'] = j

# ---------------- D5 ----------------
print('\n########## D5 ##########')
tot = len(ent); nb = sum(1 for x in ent if not x['ord']); no = sum(1 for x in ent if x['ord'])
print('① 总条数 = %d ; 按名 = %d ; 按序数 = %d   (372/339/33)' % (tot, nb, no))
print('② ILT 条目节分布 = %s' % dict(collections.Counter(sec_rva(x['ilt']) for x in ent)))
print('   ILT RVA 区间 = 0x%06X..0x%06X' % (min(x['ilt'] for x in ent), max(x['ilt'] for x in ent)))
print('③ IAT 槽节分布   = %s' % dict(collections.Counter(sec_rva(x['iat']) for x in ent)))
for x in ent:
    if sec_rva(x['iat']) != '.rdata':
        print('   非 .rdata 的 IAT 槽: dll=%s idx=%d IAT_RVA=0x%06X kind=%s 序数=%s'
              % (x['dll'], x['idx'], x['iat'], 'ord' if x['ord'] else 'name', x.get('ordnum')))
print('   IAT RVA 区间 = 0x%06X..0x%06X ; .rdata 数组内 0x%06X..0x%06X'
      % (min(x['iat'] for x in ent), max(x['iat'] for x in ent),
         min(x['iat'] for x in ent if sec_rva(x['iat']) == '.rdata'),
         max(x['iat'] for x in ent if sec_rva(x['iat']) == '.rdata')))
print('④ 名字区 IBN 条目 %d 条, 节分布 = %s'
      % (sum(1 for x in ent if x['ibn']), dict(collections.Counter(sec_rva(x['ibn']) for x in ent if x['ibn']))))
print('⑤ IAT 槽磁盘值分类 = %s'
      % dict(collections.Counter(
          ('序数标记 0x8xxxxxxx' if struct.unpack_from('<I', D, off(x['iat']))[0] & 0x80000000
           else sec_rva(struct.unpack_from('<I', D, off(x['iat']))[0] - IMG)) for x in ent)))
print('⑥ 序数导入按 DLL = %s 合计 %d'
      % (dict(collections.Counter(x['dll'] for x in ent if x['ord'])), no))
print('⑦ 每组条数: %s' % {d['name']: d['n'] for d in desc})
print('⑧ 边界裁决验证: ADVAPI32 FirstThunk=0x%06X (RVA) -> VA=0x%08X, 归节 = %s'
      % (desc[4]['ft'], IMG+desc[4]['ft'], sec_rva(desc[4]['ft'])))

# ---------------- D4 ----------------
print('\n########## D4 ##########')
VA = 0x7E11C8; R = VA - IMG
print('目标 VA=0x%08X -> RVA=0x%06X -> file_off=0x%06X -> 所在节 %s' % (VA, R, off(R), sec_rva(R)))
hit = [x for x in ent if x['iat'] == R]
print('作为 IAT 槽被命中 %d 条' % len(hit))
for x in hit:
    grp = [y for y in ent if y['dll'] == x['dll']]
    flat = [k for k, y in enumerate(ent) if y is x][0]
    print('  DLL            = %s' % x['dll'])
    print('  ILT 槽 RVA     = 0x%06X (所在节 %s)' % (x['ilt'], sec_rva(x['ilt'])))
    print('  IBN RVA        = 0x%06X (所在节 %s)' % (x['ibn'], sec_rva(x['ibn'])))
    print('  IBN 原始字节   = ' + ' '.join('%02X' % c for c in D[off(x['ibn']):off(x['ibn'])+18]))
    print('  Hint           = %d (0x%X)' % (x['hint'], x['hint']))
    print('  名字           = %s' % x['name'])
    print('  组内下标       = %d   (0x%06X-0x%06X)/4 = %d ; 组内共 %d 条'
          % (x['idx'], x['iat'], grp[0]['iat'], (x['iat']-grp[0]['iat'])//4, len(grp)))
    print('  整个 IAT 数组全局下标 = (0x%06X-0x%06X)/4 = %d' % (x['iat'], iat_rva, (x['iat']-iat_rva)//4))
    print('  372 条按描述符顺序的 0-based 全表位置 = %d' % flat)
    print('  该槽磁盘值     = 0x%08X' % struct.unpack_from('<I', D, off(R))[0])
print('D4 主张映射: DLL=KERNEL32.dll? %s ; 名字=InterlockedIncrement? %s ; Hint=432? %s ; FirstThunk idx=62? %s'
      % (hit[0]['dll'] == 'KERNEL32.dll', hit[0]['name'] == 'InterlockedIncrement',
         hit[0]['hint'] == 432, hit[0]['idx'] == 62))
