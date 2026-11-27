#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R186 D：复算审计 #448 的三条关键主张（§2.12 规则 D：审计结论必须由主会话亲自复算）。

审计 #448（deepseek / 20 回合 / 16.2 分 / **OVERTIME：16.2 分 vs 预算 2.0 分**）对本轮提出的
三条实质指控，逐条用本脚本复算：

  A1「分块 disasm_lite 只覆盖 .text 的 82.70%（62 块中 53 块提前终止），故 4720/4564/3216 是
      覆盖不足下的数字；全覆盖口径应为 5894/5729/4051」
      → 复算：块内线性扫描的消费字节率；以及**不依赖解码**的 C7 /0 字节模式全量命中数。
  A2「全覆盖口径下 disp==COL.mdisp 为 3735/4051 = 92.20%，残差 265，其中模板/容器 262、
      真个例恒为 3 个（004A8660 LayerClass /−8、004F73CA BaseClass /22272、00632CE0 BlowPipe /20）」
      → 复算：字节模式对象 store 的 (a) 口径计数、残差按类名分组、3 个个例逐字节核对。
  A3「COL+16 恰等于其配对 vtable 基址的个数 == 0/1214（COL 与 vtable 不是相邻布局）；
      只算 .?AV 时为 1212 / 952 组」
      → 复算：两个数。

反控：
  N1 字节模式关掉 SIB ⇒ 命中数下降（证明 SIB 分支真的在跑）
  N2 位移 +1 判相等 ⇒ 0 命中
  N3 把块扫描的 resync 关掉 / 打开，消费字节率必须变化（证明 A1 的机制真实存在）
"""
import sys, os, json, struct, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_r185'))
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
mdl = Cs(CS_ARCH_X86, CS_MODE_32); mdl.detail = False
fails = []; nchk = [0]
def ck(nm, cond, detail=''):
    nchk[0] += 1
    if not cond: fails.append(nm)
    print(('PASS ' if cond else 'FAIL ') + nm + ((' | ' + str(detail)) if detail != '' else ''))

TEXT = P.B['.text']; OFF = TEXT['rawptr']; SIZE = TEXT['rawsize']; TLO = TEXT['lo']; THI = TEXT['hi_file']
BLOB = P.RAW[OFF:OFF + SIZE]
REG32 = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']

# ---------- 0. COL / vtable ----------
def enum(av_only=False):
    cols = {}
    for sec in ('.rdata', '.data'):
        s = P.B[sec]; blob = P.RAW[s['rawptr']:s['rawptr'] + s['rawsize']]
        nd = len(blob) // 4
        vals = struct.unpack_from('<%dI' % nd, blob, 0)
        for i in range(nd - 4):
            base = s['lo'] + 4 * i; d = vals[i:i + 5]
            if d[0] not in (0, 1) or d[2] != 0: continue
            if P.where(d[3]) != '.data' or P.where(d[4]) != '.rdata': continue
            nm = P.cstr(d[3] + 8, 200)
            if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
            if av_only and not nm.startswith(b'.?AV'): continue
            cols[base] = dict(mdisp=d[1], ptd=d[3], pchd=d[4], name=nm.decode('latin1'))
    vts = {}
    for sec in ('.rdata', '.data'):
        s = P.B[sec]; nd = s['rawsize'] // 4
        vals = struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr'])
        for i, v in enumerate(vals):
            if not (TLO <= v < THI): continue
            base = s['lo'] + 4 * i; c = P.dw(base - 4)
            if c in cols: vts[base] = cols[c]
    return cols, vts

COLS, VTS = enum(False)
COLS_AV, VTS_AV = enum(True)
ck('D0a 严格口径 COL 1214 / vtable 1214', len(COLS) == 1214 and len(VTS) == 1214, (len(COLS), len(VTS)))
ck('D0b 只算 .?AV 口径 COL 1212 / vtable 1212 / 组数 952（复算审计 A3 后半）',
   len(COLS_AV) == 1212 and len(VTS_AV) == 1212 and len({c['ptd'] for c in VTS_AV.values()}) == 952,
   (len(COLS_AV), len(VTS_AV), len({c['ptd'] for c in VTS_AV.values()})))
def clsname(vt):
    n = VTS[vt]['name']
    return n[4:-2] if n.startswith('.?A') and n.endswith('@@') else n

# ---------- A3：COL+16 == vtable ? ----------
same = sum(1 for vt in VTS if P.dw(vt - 4) is not None and (P.dw(vt - 4) + 16) == vt)
gaps = [vt - P.dw(vt - 4) for vt in VTS]
ck('D1a COL+16 恰等于配对 vtable 基址的个数 == 0/1214（复算审计 A3 前半）', same == 0, same)
ck('D1b gap == vtable − COL 全为负、非固定值',
   all(g < 0 for g in gaps) and len(set(gaps)) > 100, (min(gaps), max(gaps), len(set(gaps))))

# ---------- A1：分块线性扫描的覆盖字节率 ----------
covered = 0; stops = []
for st in range(0, SIZE, 65536):
    seg = BLOB[st:st + 65536]
    last = st
    for a, sz, mn, op in mdl.disasm_lite(seg, TLO + st):
        last = (a - TLO) + sz
    covered += last - st
    if last - st < len(seg): stops.append((hex(TLO + st), last - st, len(seg)))
    # resync 版本：从断点继续
ck('D2a 分块线性扫描的消费字节率 < 100%（复算审计 A1 的机制）',
   covered < SIZE, '%.2f%% (%d/%d)' % (100.0 * covered / SIZE, covered, SIZE))
ck('D2b 提前终止的块数 > 0，逐块列出', len(stops) > 0, len(stops))
print('   前 5 个提前终止块：', stops[:5])

covered2 = 0; resync = 0
for st in range(0, SIZE, 65536):
    seg = BLOB[st:st + 65536]; p = 0
    while p < len(seg):
        last = p
        for a, sz, mn, op in mdl.disasm_lite(seg[p:], TLO + st + p):
            last = (a - TLO - st) + sz
        if last == p:
            p += 1; resync += 1
        else:
            p = last
    covered2 += p
ck('D2c 逐字节重同步后消费字节率 == 100%（resync 次数 > 0）',
   covered2 >= SIZE and resync > 0, ('%.4f%%' % (100.0 * covered2 / SIZE), resync))

# ---------- A1/A2：字节模式的 C7 /0 全量扫描 ----------
def scan_pattern(with_sib=True):
    hits = []
    n = len(BLOB)
    for i in range(n - 8):
        if BLOB[i] != 0xC7: continue
        m = BLOB[i + 1]; mod = m >> 6; reg = (m >> 3) & 7; rm = m & 7
        if reg != 0: continue
        base = None; index = None; d = 0; o = None
        if rm == 4:
            if not with_sib: continue
            sib = BLOB[i + 2]; sc = sib >> 6; ix = (sib >> 3) & 7; bs = sib & 7
            index = None if ix == 4 else REG32[ix]
            if bs == 5 and mod == 0:
                d = struct.unpack_from('<i', BLOB, i + 3)[0]; o = i + 7
            elif bs == 5:
                base = 'ebp'
                if mod == 1: d = struct.unpack_from('<b', BLOB, i + 3)[0]; o = i + 4
                else: d = struct.unpack_from('<i', BLOB, i + 3)[0]; o = i + 7
            else:
                base = REG32[bs]
                if mod == 0: o = i + 3
                elif mod == 1: d = struct.unpack_from('<b', BLOB, i + 3)[0]; o = i + 4
                else: d = struct.unpack_from('<i', BLOB, i + 3)[0]; o = i + 7
        elif mod == 0:
            if rm == 5: d = struct.unpack_from('<i', BLOB, i + 2)[0]; o = i + 6
            else: base = REG32[rm]; o = i + 2
        elif mod == 1:
            base = REG32[rm]; d = struct.unpack_from('<b', BLOB, i + 2)[0]; o = i + 3
        elif mod == 2:
            base = REG32[rm]; d = struct.unpack_from('<i', BLOB, i + 2)[0]; o = i + 6
        else:
            continue
        if o is None or o + 4 > n: continue
        w = struct.unpack_from('<I', BLOB, o)[0]
        if w in VTS: hits.append((TLO + i, base, index, d, w))
    return hits

H = scan_pattern(True); HNS = scan_pattern(False)
ck('D3a 字节模式（含 SIB）命中 vtable 的 store 条数', len(H) > 5000, len(H))
ck('N1 反控：关掉 SIB 后命中数下降', len(HNS) < len(H), (len(HNS), len(H), len(H) - len(HNS)))
STACK = {'esp', 'ebp'}
obj = [h for h in H if h[1] not in STACK and h[2] is None and h[1] is not None]
ck('D3b 对象寄存器 store（基址非 esp/ebp、无索引）条数（复算审计的 4051 量级）',
   3800 < len(obj) < 4300, len(obj))
eq = [h for h in obj if h[3] == VTS[h[4]]['mdisp']]
ck('D3c 口径(a) disp == COL.mdisp 条数与比例（复算审计 A2「3735/4051 = 92.20%」）',
   3600 < len(eq) < 3900, '%d/%d = %.2f%%' % (len(eq), len(obj), 100.0 * len(eq) / len(obj)))
ck('N2 反控：位移 +1 判相等 ⇒ 0 命中', len([h for h in obj if h[3] + 1 == VTS[h[4]]['mdisp']]) == 0)

# ---------- A2：残差分组 + 3 个个例 ----------
own = collections.defaultdict(set)
for vt, c in VTS.items(): own[c['ptd']].add(c['mdisp'])
wide = collections.defaultdict(set)
for ptd, ms in own.items(): wide[ptd] |= ms
for vt, c in VTS.items():
    ch = [P.dw(c['pchd'] + 4 * k) for k in range(4)]
    if None in ch or not (1 <= ch[2] <= 64) or P.where(ch[3]) != '.rdata': continue
    for i in range(ch[2]):
        bo = P.dw(ch[3] + 4 * i)
        if bo is None: continue
        f = [P.dw(bo + 4 * j) for j in range(6)]
        if None in f: continue
        wide[f[0]].add(f[2])
res = [h for h in obj if h[3] not in wide[VTS[h[4]]['ptd']]]
rc = collections.Counter(clsname(h[4]) for h in res)
tm = sum(n for c, n in rc.items() if '$' in c or 'List' in c)
non = {c: n for c, n in rc.items() if not ('$' in c or 'List' in c)}
ck('D4a 口径(c) 残差条数（复算审计 A2「265」量级）', 150 < len(res) < 400, len(res))
ck('D4b 残差里模板/容器类占绝大多数、非模板类逐个列出', len(res) - tm < len(res) // 2,
   ('模板 %d / 非模板 %d' % (tm, len(res) - tm), non))
for addr, exp_cls, exp_disp in ((0x004A8660, 'LayerClass', -8), (0x004F73CA, 'BaseClass', 22272), (0x00632CE0, 'BlowPipe', 20)):
    hit = [h for h in obj if h[0] == addr]
    ok = bool(hit) and clsname(hit[0][4]) == exp_cls and hit[0][3] == exp_disp
    ck('D4c 个例 %08X 复算：%s / disp=%d（审计 A2 称恒为 3 个）' % (addr, exp_cls, exp_disp), ok,
       ([(hex(h[0]), clsname(h[4]), h[3]) for h in hit], ))

resj = {'cols': len(COLS), 'cols_av': len(COLS_AV), 'vt_av': len(VTS_AV),
        'groups_av': len({c['ptd'] for c in VTS_AV.values()}),
        'col_plus16_eq_vt': same, 'gap_min': min(gaps), 'gap_max': max(gaps), 'gap_distinct': len(set(gaps)),
        'covered_block': covered, 'covered_block_pct': round(100.0 * covered / SIZE, 2),
        'early_stop_blocks': len(stops), 'covered_resync_pct': round(100.0 * covered2 / SIZE, 4),
        'resync': resync,
        'hits': len(H), 'hits_nosib': len(HNS), 'obj': len(obj), 'eq': len(eq),
        'eq_pct': round(100.0 * len(eq) / len(obj), 2),
        'residual': len(res), 'residual_tmpl': tm, 'residual_non_tmpl': non,
        'residual_cls_top': rc.most_common(12),
        'checks': nchk[0], 'fails': fails}
json.dump(resj, open(os.path.join(HERE, 'r186d.json'), 'w'), indent=1, sort_keys=True, ensure_ascii=False)
print('\nchecks=%d fails=%d' % (nchk[0], len(fails)))
if fails: print('FAILS:', fails); sys.exit(1)
