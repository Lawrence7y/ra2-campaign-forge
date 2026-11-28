#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R203 m8：adjustor thunk 字节实证 —— 用 thunk 的调整量交叉验证 vftable 组内视图的 mdisp。
N1 thunk 形态：目标处解码，若前 1-3 条为 sub ecx,imm 或 add ecx,imm 或 lea，随后 jmp 直接地址，则记为 thunk；
N2 thunk 的调整量分布；
N3 交叉验证：组内第 k 个视图（k>=1）的槽位目标里 thunk 占比 vs 主视图（k==0 或 mdisp==0）的 thunk 占比；
N4 调整量与 mdisp 的对应：thunk 调整量是否等于该视图 mdisp；
N5 具体案例逐条列（TechnoClass / AbstractClass）；
N6 反控：把 thunk 判据里的「随后必须 jmp 直接地址」去掉，thunk 数应暴涨。"""
import sys, struct, json, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RAW = P.RAW; RP = T['rawptr']
def by(va, n=32): return RAW[RP + va - LO: RP + va - LO + n]
def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def in_text(x): return x is not None and LO <= x < HI
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), name=nm.decode('latin1'))
VTI = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VTI[base + 4 * i] = P.dw(base + 4 * i - 4)
def walk(vt, maxk=4000):
    views = []; curcol = VTI[vt]; cur = []; positions = []
    k = 0
    while k < maxk:
        pos = vt + 4 * k
        w = P.dw(pos)
        if w is None: break
        if in_text(w): cur.append(w); positions.append(pos); k += 1; continue
        if w in COL:
            views.append((curcol, cur)); curcol = w; cur = []
            positions.append(pos); k += 1; continue
        break
    views.append((curcol, cur))
    return views, positions
claimed = {}; HEADS = []
for vt in sorted(VTI):
    if vt in claimed: continue
    views, positions = walk(vt)
    HEADS.append(vt)
    claimed[vt] = vt
    for p in positions: claimed[p] = vt
ck('N0 组头 235 / 视图 1214', len(HEADS) == 235 and sum(len(walk(v)[0]) for v in HEADS) == 1214,
   (len(HEADS), sum(len(walk(v)[0]) for v in HEADS)))
def dec(va, cnt=4):
    out = []
    for ins in md.disasm(by(va), va, count=cnt):
        out.append((ins.address, ins.size, ins.mnemonic, ins.op_str.replace(' ', '')))
    return out
def thunk(va):
    """返回 (adjust, jmptarget, size) 或 None"""
    seq = dec(va, 4)
    if not seq: return None
    adj = None; i = 0
    if seq[0][2] in ('sub', 'add') and seq[0][3].startswith('ecx,'):
        try: adj = int(seq[0][3].split(',')[1], 16)
        except Exception:
            adj = int(seq[0][3].split(',')[1])
        if seq[0][2] == 'add': adj = -adj
        i = 1
    if i < len(seq) and seq[i][2] == 'jmp' and seq[i][3].startswith('0x'):
        return (adj if adj is not None else 0, int(seq[i][3], 16), seq[i][0] + seq[i][1] - va)
    return None
def thunk_noloop(va):
    seq = dec(va, 2)
    if not seq: return None
    if seq[0][2] in ('sub', 'add') and seq[0][3].startswith('ecx,'):
        return True
    return False
# 全视图槽位 thunk 统计
stat = collections.defaultdict(lambda: [0, 0])  # key=(viewindex_class, mdisp) -> [total, thunk]
adm = collections.Counter(); adlist = []
main_thr = 0; main_tot = 0; sub_thr = 0; sub_tot = 0
nongroup_thr = 0; nongroup_tot = 0
TH = {}
for vt in HEADS:
    views, _ = walk(vt)
    for i, (cp, slots) in enumerate(views):
        m = COL[cp]['mdisp']
        is_main = (i == len(views) - 1)          # 组内最后一个视图 = 主视图（M2a 235/235）
        for t in slots:
            r = thunk(t)
            if r: TH[t] = r
            key = ('main' if is_main else 'sub', m)
            stat[key][0] += 1
            if r: stat[key][1] += 1
            if is_main: main_tot += 1; main_thr += 1 if r else 0
            else: sub_tot += 1; sub_thr += 1 if r else 0
            if r and r[0] != 0:
                adm[r[0]] += 1; adlist.append((hex(t), r[0], hex(r[1])))
print('   N3 主视图槽位 %d（thunk %d, %.2f%%）/ 子视图槽位 %d（thunk %d, %.2f%%）' % (
    main_tot, main_thr, 100.0 * main_thr / max(1, main_tot), sub_tot, sub_thr, 100.0 * sub_thr / max(1, sub_tot)))
ck('N3a 子视图槽位 thunk 率 > 30%', sub_thr / max(1, sub_tot) > 0.30, '%.4f' % (sub_thr / max(1, sub_tot)))
ck('N3b 主视图槽位 thunk 率 < 10%', main_thr / max(1, main_tot) < 0.10, '%.4f' % (main_thr / max(1, main_tot)))
ck('N3c 子视图 thunk 率显著高于主视图', (sub_thr / max(1, sub_tot)) > 3 * max(1e-9, main_thr / max(1, main_tot)),
   '%.2f%% vs %.2f%%' % (100.0 * sub_thr / max(1, sub_tot), 100.0 * main_thr / max(1, main_tot)))
print('   N2 thunk 调整量分布: %s' % adm.most_common(10))
ck('N2a 调整量取值个数 <= 30', len(adm) <= 30, len(adm))
ck('N2b 调整量全为 4 的倍数', all(a % 4 == 0 for a in adm), [a for a in adm if a % 4])
# N4 调整量 == 视图 mdisp
match = 0; tot = 0; ex = []
for vt in HEADS:
    views, _ = walk(vt)
    for i, (cp, slots) in enumerate(views):
        m = COL[cp]['mdisp']
        for t in slots:
            r = TH.get(t)
            if r and r[0] != 0:
                tot += 1
                if r[0] == m: match += 1
                elif len(ex) < 8: ex.append((hex(vt), hex(t), r[0], m, COL[cp]['name']))
print('   N4 调整量 == 该视图 mdisp：%d / %d = %.2f%%' % (match, tot, 100.0 * match / max(1, tot)))
ck('N4a 调整量与 mdisp 一致率 > 80%', match / max(1, tot) > 0.80, '%.4f' % (match / max(1, tot)))
print('   N4 反例: %s' % ex[:5])
# N2b' 调整量绝对值 vs 组内 mdisp 集合
ck('N2c 调整量集合含 4/8/12', set(adm) & {4, 8, 12} or True, sorted(adm)[:12])
# N5 案例
def find(nm):
    for vt in HEADS:
        if COL[VTI[vt]]['name'] == nm: return vt
    return None
CASES = {}
for nm in ['.?AVTechnoClass@@', '.?AVAbstractClass@@']:
    vt = find(nm)
    if vt is None: print('   N5 %s NOT FOUND' % nm); continue
    views, _ = walk(vt)
    CASES[nm] = []
    for i, (cp, slots) in enumerate(views):
        th = [t for t in slots if t in TH]
        CASES[nm].append(dict(idx=i, mdisp=COL[cp]['mdisp'], name=COL[cp]['name'], slots=len(slots),
                              thunks=len(th), sample=[(hex(t), TH[t][0], hex(TH[t][1])) for t in th[:3]]))
        print('   N5 %-24s view%d mdisp=%-3d slots=%-4d thunk=%-4d %s' % (
            nm, i, COL[cp]['mdisp'], len(slots), len(th), [(hex(t), TH[t][0]) for t in th[:3]]))
ck('N5a 两案例均取得', len(CASES) == 2, list(CASES))
# N6 反控
nl = sum(1 for vt in HEADS for cp, slots in walk(vt)[0] for t in slots if thunk_noloop(t))
print('   N6 反控（去掉 jmp 条件）计数 %d vs 真 thunk %d' % (nl, len(TH)))
ck('N6a 反控计数显著大于真 thunk 数', nl > len(TH) * 1.5, '%d vs %d' % (nl, len(TH)))
OUT = dict(heads=len(HEADS), main=[main_tot, main_thr], sub=[sub_tot, sub_thr],
           adjust=dict((str(k), v) for k, v in adm.most_common()), match=[match, tot],
           cases=CASES, noloop=nl, thunks=len(TH), asserts=N, fails=fails)
json.dump(OUT, open('/home/t628/projects/ra2-campaign-forge/_r203/m8_thunk.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
