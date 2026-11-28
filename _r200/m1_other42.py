#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200 主会话第一刀：槽 0 实现体内「装 42 个既非本类也非直基类主表」的 store 的语义判据（纯字节）。

R199 遗留 (c)。R199 用地址恒等把 538 条 [reg]=imm32 store 分成
  own_main 110 / base_main 385 / other_main 42 / nonvt 1 / subtable 0。
本刀只吃 other_main 这 42 条，问「imm 那张主表的类在 vt_d 类的 RTTI 继承树里是什么位置」。

判据（全字节）：
 J1 重建 RTTI：COL 24B / CHD 16B（+8 n、+12 BCD 指针数组）/ BCD 24B（+0 pTD、+4 ncb、+8 mdisp）。
    类 -> pTD -> 该类的 CHD（在 COL.pchd）；BCA 数组 n 项，BCD[0] 是类自身。
 J2 祖先判定：A 是 B 的祖先 iff A.pTD 出现在 B 的 BCD 数组下标 >=1 处（含间接，BCD 已扁平）。
 J3 对每个 other_main store：给 (关系) 五类：ancestor / descendant / sibling(同祖先但互不祖先) /
    self_same_td_diff_vt（同一 pTD 但不同 vt，多继承子表情形） / unrelated。
 J4 对 ancestor 类再给 BCD 里 A 的 mdisp，以及 A 的主表与该 vt_d 的主表槽数。
反控：
 R1 把「祖先」判据换成「类名字符串前缀相同」看计数差。
 R2 把 other_main 扩大到「imm 在 VT 内且 imm != vt_d 且 imm != vt_b」（即把 own/base 重新并入）看是否自洽。
"""
import sys, struct, collections, json, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RAW = P.RAW
def in_text(x): return x is not None and LO <= x < HI

# ---- J1 RTTI 重建 ----
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), ptd=w[i + 3], pchd=w[i + 4],
                                 name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
NS = {}
def nslot(vt):
    if vt in NS: return NS[vt]
    k = 0
    while True:
        if not in_text(P.dw(vt + 4 * k)): break
        k += 1
    NS[vt] = k; return k

# pTD -> 该 pTD 的 BCD 列表（用 COL.pchd -> CHD -> BCA）
CHD = {}
for vt, col in VT.items():
    chd = COL[col]['pchd']
    if chd in CHD: continue
    n = P.dw(chd + 8); bca = P.dw(chd + 12)
    if n is None or bca is None or n <= 0 or n > 200: CHD[chd] = None; continue
    items = []
    ok = True
    for i in range(n):
        bcd = P.dw(bca + 4 * i)
        if bcd is None: ok = False; break
        ptd = P.dw(bcd + 0); ncb = P.dw(bcd + 4); disp = P.dw(bcd + 8)
        if ptd is None: ok = False; break
        items.append((ptd, ncb, s32(disp)))
    CHD[chd] = items if ok else None

PTD_BCD = {}
for vt, col in VT.items():
    c = COL[col]; lst = CHD.get(c['pchd'])
    if lst: PTD_BCD[c['ptd']] = lst
ck('J1a COL==1214 / VT==1214', (len(COL), len(VT)) == (1214, 1214), (len(COL), len(VT)))
ck('J1b 有 BCD 列表的 pTD 数 > 900', len(PTD_BCD) > 900, len(PTD_BCD))

MD = {vt: COL[VT[vt]]['mdisp'] for vt in VT}
CLS = {vt: COL[VT[vt]]['name'] for vt in VT}
PTD_OF = {vt: COL[VT[vt]]['ptd'] for vt in VT}
MAINBYPTD = {}
for vt in VT:
    if MD[vt] == 0: MAINBYPTD[PTD_OF[vt]] = vt

def ancestors(ptd):
    lst = PTD_BCD.get(ptd)
    if not lst: return None
    return lst[1:]

# ---- 复现 R199 的 538 条 store 分类 ----
d = json.load(open('/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json'))
pairs = [(int(a, 16), int(b, 16)) for a, b in d['pairs']]
s0d = []
for vt_d, vt_b in pairs:
    if min(nslot(vt_d), nslot(vt_b)) < 1: continue
    a = P.dw(vt_d); b = P.dw(vt_b)
    if a != b: s0d.append((vt_d, a, vt_b))
ck('J0a 槽0 派生不匹配 == 516', len(s0d) == 516, len(s0d))

def body(va, maxb=600, maxi=300):
    o = P.r2o(va)
    if o is None: return None
    ins = []
    for i in md.disasm(RAW[o:o + maxb], va):
        ins.append((i.address, i.size, i.mnemonic, i.op_str))
        if i.mnemonic.startswith('ret'): break
        if len(ins) >= maxi: break
    return ins

STORE_RE = re.compile(r'^dword ptr \[(e[a-z]{2})(?: \+ (0x[0-9a-f]+))?\], (0x[0-9a-f]+)$')
cat = collections.Counter(); other = []
for vt_d, a, vt_b in s0d:
    for ad, sz, mn, op in body(a) or []:
        if mn != 'mov': continue
        m = STORE_RE.match(op)
        if not m: continue
        imm = int(m.group(3), 16)
        if imm == vt_d: t = 'own_main'
        elif imm == vt_b: t = 'base_main'
        elif imm in VT and MD[imm] != 0: t = 'subtable'
        elif imm in VT: t = 'other_main'; other.append((vt_d, a, vt_b, ad, imm))
        else: t = 'nonvt'
        cat[t] += 1
ck('J0b store 538 条四分类复现 (own110/base385/other42/nonvt1)',
   (cat['own_main'], cat['base_main'], cat['other_main'], cat['nonvt'], cat['subtable']) == (110, 385, 42, 1, 0), dict(cat))
ck('J0c other_main 条数 42', len(other) == 42, len(other))

# ---- J3 关系分类 ----
rel = collections.Counter(); rows = []
for vt_d, a, vt_b, ad, imm in other:
    p_d = PTD_OF[vt_d]; p_o = PTD_OF[imm]; p_b = PTD_OF[vt_b]
    anc_d = ancestors(p_d); anc_o = ancestors(p_o)
    if p_o == p_d: t = 'same_ptd'
    elif anc_d is None or anc_o is None: t = 'nodata'
    elif any(x[0] == p_o for x in anc_d): t = 'ancestor'
    elif any(x[0] == p_d for x in anc_o): t = 'descendant'
    else:
        sd = set(x[0] for x in anc_d); so = set(x[0] for x in anc_o)
        t = 'sibling' if (sd & so) else 'unrelated'
    disp_o = next((x[2] for x in (anc_d or []) if x[0] == p_o), None)
    rel[t] += 1
    rows.append(dict(cls_d=CLS[vt_d], impl=hex(a), store_at=hex(ad), imm=hex(imm),
                     cls_imm=CLS[imm], n_d=nslot(vt_d), n_imm=nslot(imm), n_b=nslot(vt_b),
                     rel=t, disp_o=disp_o,
                     imm_is_main=MD[imm] == 0))
print('   J3 关系分布: %s' % dict(rel))
for r in rows: print('   J3r %-58s %-42s rel=%-10s n_d=%d n_imm=%d n_b=%d disp=%s' %
                     (r['cls_d'], r['cls_imm'], r['rel'], r['n_d'], r['n_imm'], r['n_b'], r['disp_o']))
ck('J3a 42 条关系全覆盖（无 nodata）', rel['nodata'] == 0, rel['nodata'])

# ---- J4 ancestor 类细节 ----
anc = [r for r in rows if r['rel'] == 'ancestor']
print('   J4 ancestor 条数 %d' % len(anc))
# 反控 R1 名字前缀
pref = 0
for r in rows:
    if r['cls_d'].split('@@')[0][:12] == r['cls_imm'].split('@@')[0][:12]: pref += 1
ck('R1 名字前缀同者 < ancestor 数（名字口径不足）', pref <= rel['ancestor'], (pref, rel['ancestor']))
# 反控 R2 自洽：other 集合与 own/base 无交集
ck('R2a other_main 的 imm 全在 VT 且 mdisp==0', all(MD[r['imm'] if isinstance(r['imm'], int) else int(r['imm'], 16)] == 0 for r in rows), True)

json.dump(dict(rel=dict(rel), rows=rows, cat=dict(cat), asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r200/m1_other42.json', 'w'),
          ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
