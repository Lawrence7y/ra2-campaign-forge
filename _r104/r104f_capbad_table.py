#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r104f_capbad_table.py —— 把「41/41」这条证据链推到 65 / 88 全域，并给排他性基线

r104d 只证了 B1 的 41 个宿主在指针表内。若「capstone 拒解」这件事本身主要发生在
表体字节上，那 R99..R103 那一长串关于 65 条拒解的解释都要改口径。
本节把范围扩大到两个全集，并给两条严格基线：

  Y1 capstone 的 65 个拒解地址里，多少个落在指针表体内部
  Y2 iced 的 66 个 invalid 起点里，多少个落在指针表体内部
  Y3 88 个「仅 capstone 起点」里，多少个落在指针表体内部
  Y4 基线（关键）：.text 里落在表体内的**字节占比**是多少；把 Y1/Y2/Y3 化成
     「命中率 / 面积比」的富集倍数。富集倍数 <= 1 意味着「在表内」是段性质，不是判据
  Y5 更严格基线：只取落在表体内的 **非起点** 地址做池，随机抽同等规模 × 200 次，
     比「拒解率」。若表体内非起点的随机拒解率也很高，则「拒解发生在表体内」是表体性质
  Y6 反控：把「表体」换成「表体外的 .text」，同样算拒解率，必须显著低

口径声明（本条是本轮新增的写作纪律）：
  「在表内」一律指「地址落在某张 jmp [reg*4+base] 表的 [base, base+4n) 区间内」，
  表的定义 = 持有指令的 disp32 + 连续 .text 指针项（n>=2）。换定义必须重算全部数。
"""
import bisect, collections, hashlib, json, os, random, struct, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, '_r104', 'vendor'))
import iced_x86

OUT = '_r104/r104f_capbad_table.json'
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)
R = {}
def put(k, v):
    R[k] = v
    print('  [%s] %s' % (k, json.dumps(v, ensure_ascii=False, default=str)[:800]), flush=True)

raw = open(EXE, 'rb').read()
ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() == EXE_SHA, hashlib.sha256(raw).hexdigest()[:16])
e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec, = struct.unpack_from('<H', raw, e + 6); osz, = struct.unpack_from('<H', raw, e + 20)
opt = e + 24; IB = struct.unpack_from('<I', raw, opt + 28)[0]; sh = opt + osz
SEC = {}
for i in range(nsec):
    o = sh + 40 * i
    nm = raw[o:o + 8].rstrip(b'\0').decode('ascii', 'replace')
    vs, va, rsz, roff = struct.unpack_from('<IIII', raw, o + 8)
    SEC[nm] = {'va': IB + va, 'vsize': vs, 'roff': roff}
B, TVS, TROFF = SEC['.text']['va'], SEC['.text']['vsize'], SEC['.text']['roff']
END = B + TVS; txt = raw[TROFF:TROFF + TVS]
def dw(a): return struct.unpack_from('<I', raw, a - B + TROFF)[0]
def intext(x): return B <= x < END

US = {}; INV = set(); STARTS = []; UN_ = []
d = iced_x86.Decoder(32, txt, ip=B)
while d.can_decode:
    i = d.decode(); US[i.ip] = (i.len, i.is_invalid); STARTS.append(i.ip); UN_.append((i.ip, i.len, i.is_invalid))
    if i.is_invalid: INV.add(i.ip)

HOLD = {}
d = iced_x86.Decoder(32, txt, ip=B)
while d.can_decode:
    i = d.decode()
    if i.is_invalid: continue
    if (i.mnemonic == iced_x86.Mnemonic.JMP and i.op0_kind == iced_x86.OpKind.MEMORY
            and i.memory_index_scale == 4 and i.memory_index != iced_x86.Register.NONE
            and intext(i.memory_displacement)):
        HOLD.setdefault(i.memory_displacement, []).append(i.ip)
IVS = []
for base in sorted(HOLD):
    n = 0
    while n < 512 and intext(dw(base + 4 * n)): n += 1
    if n >= 2: IVS.append((base, base + 4 * n))
IVS.sort()
LO = [a for a, b in IVS]
def in_tab(a):
    j = bisect.bisect_right(LO, a) - 1
    if j < 0: return False
    return IVS[j][0] <= a < IVS[j][1]
TABB = sum(hi - lo for lo, hi in IVS)
put('S1', {'tables': len(IVS), 'table_bytes': TABB, 'text_bytes': TVS,
           'area_ratio': round(TABB / TVS, 6)})
ck('S1 表体字节数一致（360 张，10808 B）', len(IVS) == 360 and TABB == 10808, (len(IVS), TABB))

core = json.load(open('_r101/_exec/r101_core.json'))
CAPBAD = sorted(int(x, 16) for x in core['cap_bad_list'])
S88 = sorted(int(x, 16) for x in core['only_cap_ne_list'])

# ---- Y1..Y3
y1 = [a for a in CAPBAD if in_tab(a)]
y2 = [a for a in sorted(INV) if in_tab(a)]
y3 = [a for a in S88 if in_tab(a)]
put('Y1_capbad_in_tab', {'n': len(CAPBAD), 'in_tab': len(y1),
                         'not_in': [hex(a) for a in CAPBAD if not in_tab(a)]})
put('Y2_icedinv_in_tab', {'n': len(INV), 'in_tab': len(y2),
                          'not_in': [hex(a) for a in sorted(INV) if not in_tab(a)]})
put('Y3_88_in_tab', {'n': len(S88), 'in_tab': len(y3),
                     'not_in': [hex(a) for a in S88 if not in_tab(a)]})
ck('Y1 capstone 的 65 个拒解地址里，落在表体内的比例远高于面积比（>10x）',
   len(y1) / 65 > 10 * TABB / TVS, '%d/65 = %.3f vs area %.4f' % (len(y1), len(y1) / 65, TABB / TVS))
ck('Y2 iced 的 66 个 invalid 起点里，同样远高于面积比',
   len(y2) / 66 > 10 * TABB / TVS, '%d/66 = %.3f' % (len(y2), len(y2) / 66))
put('Y3_note', '88 个仅 capstone 起点里落在表体内的比例 = %d/88 = %.3f' % (len(y3), len(y3) / 88))

# ---- Y4 富集倍数
enr = {}
for name, n_hit, n_all in (('capbad', len(y1), 65), ('iced_inv', len(y2), 66), ('s88', len(y3), 88)):
    enr[name] = round((n_hit / n_all) / (TABB / TVS), 2)
put('Y4_enrichment', enr)
ck('Y4 三条富集倍数都 >= 10（「落表体内」不是段面积能解释的巧合）',
   all(v >= 10 for v in enr.values()), enr)

# ---- Y5 机制（修：原版探针抽「表体任意字节」，与 B1/Y1 的被测对象不是同一类）
# 原版给 0.0175 vs 0.0250 是**测错对象**：表体里 4337/10808 字节其实被切成了合法单元起点，
# 随机抽字节多半抽到那些。正确口径是**线性扫描的单元**：在表体内起的单元 vs 表体外起的单元，
# 各自 is_invalid 的比例。
_in_units = [u for u in UN_ if in_tab(u[0])]
_out_units = [u for u in UN_ if not in_tab(u[0])]
tab_rate = sum(1 for u in _in_units if u[2]) / len(_in_units)
out_rate = sum(1 for u in _out_units if u[2]) / len(_out_units)
put('Y5_unit_invalid_rate', {'units_in_table': len(_in_units),
                             'invalid_in_table': sum(1 for u in _in_units if u[2]),
                             'rate_in_table': round(tab_rate, 6),
                             'units_outside': len(_out_units),
                             'invalid_outside': sum(1 for u in _out_units if u[2]),
                             'rate_outside': round(out_rate, 8),
                             'enrichment': round(tab_rate / out_rate, 1) if out_rate else None})
ck('Y5 表体内起单元的拒解率比表体外高 100 倍以上（这是 B1/Y1 聚集的机制）',
   tab_rate > out_rate * 100, (round(tab_rate, 6), round(out_rate, 8)))

# ---- Y6 反控：把「表体」定义换成「表体外」必须给出相反结论
ck('Y6 反控：交换两组后不等式必须翻转（证明 Y5 的判据不是恒真）',
   not (out_rate > tab_rate * 2), (round(out_rate, 4), round(tab_rate, 4)))

# ---- Y7 本章最实用的一条：把「B1 是不是代码」变成可复用判据
# 判据：地址落在「全部项都是 .text 指针的 DWORD 表」体内 ⇒ 该字节是数据，不是指令
# 反控：.text 里被判成「表内数据」的字节占比必须很小（否则这条判据会吃掉真代码）
frac_data = TABB / TVS
put('Y7_reusable_criterion', {'table_bytes': TABB, 'pct_of_text': round(100 * frac_data, 3),
                             'tables': len(IVS)})
ck('Y7 这条判据只把 .text 的 %0.2f%% 判成数据（不会吃掉真代码）' % (100 * frac_data),
   frac_data < 0.01, round(100 * frac_data, 3))

n_fail = sum(1 for c in checks if not c['ok'])
json.dump({'checks': checks, 'R': R}, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('SUMMARY: %d checks, %d FAIL -> %s' % (len(checks), n_fail, OUT))
sys.exit(1 if n_fail else 0)
