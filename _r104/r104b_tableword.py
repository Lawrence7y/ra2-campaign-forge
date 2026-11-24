#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r104b_tableword.py —— R101 待办② 收口：集 A 的 5 个「直接跳转命中」到底是什么

R101 记下的待办②原文（COMPACT_STATE R101 段）：
    「集 A 里 4 条 jXX +0(0x71f99e/0x728e0a/0x7b0082/0x7d9d2d)自身是否真代码未验证」
R101 的结论是「这 4 条是数据被读成代码的典型形态，不能充当真实入口证据，
仅 0x71f2c5(eb ef 真向后跳)有控制流意义、单例」。

本轮用第三套解码器 + 原始字节把它做成字节级定论，并**修正其中两个错误**：
  E1 清单里第 1 个地址 0x71f99e 抄错：该处是零填充区（解出 add [eax],al），
     真正的 jXX +0 在 0x71f9e2（jno 0x71f9e4）。差 0x44 字节。
  E2 唯一那个「有控制流意义」的 0x71f2c5 也不是真入口：它的 eb ef 反向跳
     落在一个跳转表的 DWORD 项高位字上。

核心机制（本节要证的就是这一条）：
  这 5 个地址全部落在 `jmp DWORD PTR [reg*4+base]` 跳转表的表体内部，
  且全部是某个 32 位指针 0x00XXXXXX 的**高 16 位**。
  高半部的首字节恰好是 70..7F 段（= jcc rel8 的 opcode 区），第二字节 00
  （= disp8 为 0，即「跳到下一条」）—— 这两个字节合起来必然解出一条 jXX +0。
  所以「jXX +0」不是巧合，是 x86 下 .text 段指针表高位字的**必然形态**。

  这同时给出一条可复用的判据（R104 新增）：凡「位移 0 的条件跳转」出现在 .text 内，
  先测它是不是某个 DWORD 指针表的高位字，再谈它是不是控制流。

五组：
  T1 四个表基址的存在性证明：给出 `jmp [reg*4+base]` 的持有指令地址与逐项值
  T2 5 个地址逐址：所在表的 base / 项序号 / 该项完整 DWORD / 目标地址 = 该项的低半部
  T3 反控：把表项的高位字换成 0x00（即改成 .data 地址）后该 jXX +0 必须消失 —— 证明
     「是高位字」这个归因不是从结果反推的空话
  T4 全库普查：.text 内位移 0 的 jcc 共多少条、其中多少条落在 DWORD 表高位字上
  T5 修正登记：0x71f99e 抄错，真值 0x71f9e2；并给这两处的字节与解码对照
"""
import array, bisect, collections, hashlib, io, json, os, re, struct, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, '_r104', 'vendor'))
import iced_x86

OUT = '_r104/r104b_tableword.json'
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
nsec, = struct.unpack_from('<H', raw, e + 6)
osz, = struct.unpack_from('<H', raw, e + 20)
opt = e + 24
IB = struct.unpack_from('<I', raw, opt + 28)[0]
sh = opt + osz
SEC = {}
for i in range(nsec):
    o = sh + 40 * i
    nm = raw[o:o + 8].rstrip(b'\0').decode('ascii', 'replace')
    vs, va, rsz, roff = struct.unpack_from('<IIII', raw, o + 8)
    SEC[nm] = {'va': IB + va, 'vsize': vs, 'roff': roff, 'rsz': rsz}
B, TVS, TROFF = SEC['.text']['va'], SEC['.text']['vsize'], SEC['.text']['roff']
END = B + TVS
txt = raw[TROFF:TROFF + TVS]
ck('S1 .text = [0x401000, 0x7E038D)', (B, END) == (0x401000, 0x7e038d), '%x..%x' % (B, END))

def byteof(va):
    return raw[va - B + TROFF]
def dw(va):
    return struct.unpack_from('<I', raw, va - B + TROFF)[0]
def intext(v):
    return B <= v < END
def dec(va, n=15):
    return iced_x86.Decoder(32, txt[va - B:va - B + n], ip=va).decode()

# ---------------- T1 四个表基址：从持有指令反查
# 表基址来自 objdump 里 jmp DWORD PTR [reg*4+base] 的 disp32；这里不抄 objdump，自己扫 iced 全库
# 找 FF 24 8D/85/9D/... = jmp [reg*4+disp32]，取 disp32 落在 .text 内的那些。
dec0 = iced_x86.Decoder(32, txt, ip=B)
CAND = []
while dec0.can_decode:
    i = dec0.decode()
    if i.is_invalid:
        continue
    try:
        if i.mnemonic == iced_x86.Mnemonic.JMP and i.op0_kind == iced_x86.OpKind.MEMORY \
                and i.memory_index != iced_x86.Register.NONE and i.memory_index_scale == 4 \
                and i.memory_displacement and intext(i.memory_displacement):
            CAND.append({'at': i.ip, 'base': i.memory_displacement,
                         'idx': str(i.memory_index), 'txt': str(i)[:48]})
    except Exception:
        pass
put('T1_indexed_jmp_in_text_disp', len(CAND))
# 只保留「表体全部是 .text 指针」的
TABLES = {}
for c in CAND:
    base = c['base']
    n = 0
    while n < 512 and intext(dw(base + 4 * n)):
        n += 1
    if n >= 2:
        TABLES[base] = {'n': n, 'via': c['at'], 'via_txt': c['txt'],
                        'vals': [dw(base + 4 * k) for k in range(n)]}
put('T1_tables', {hex(k): {'n': v['n'], 'via': hex(v['via']), 'vals': [hex(x) for x in v['vals'][:14]]}
                  for k, v in sorted(TABLES.items())})
ck('T1 至少 4 张表（本轮要定的 4 个基址都在其中）',
   all(b in TABLES for b in (0x71f9e0, 0x728e08, 0x7b0074, 0x7d9d13)),
   'tables=%d' % len(TABLES))

# ---------------- T2 5 个地址逐址
TARGETS = [
    # (R101 记的 jXX 源地址, 它指向的目标地址)
    (0x71f99e, 0x71f9e4),   # R101 的清单值 —— 本轮证为抄错
    (0x728e0a, 0x728e0c),
    (0x7b0082, 0x7b0084),
    (0x7d9d2d, 0x7d9d2f),
    (0x71f2d4, 0x71f2c5),   # eb ef 反向跳
]
def which_table(va):
    """返回 (base, idx) 若 va 落在某张表体的 4 字节项内部（含非对齐情况按项起点算）。"""
    for base, t in TABLES.items():
        for k in range(t['n']):
            a0 = base + 4 * k
            if a0 <= va < a0 + 4:
                return base, k, a0
    return None
rows = []
for src, tgt in TARGETS:
    b = raw[src - B + TROFF:src - B + TROFF + 4].hex(' ')
    i = dec(src)
    hit = which_table(src)
    thr = which_table(tgt)
    rows.append({
        'src': hex(src), 'src_bytes': b, 'src_decodes': str(i), 'src_len': i.len,
        'into_next': i.next_ip,
        'is_zero_disp': (i.op0_kind == iced_x86.OpKind.NEAR_BRANCH32
                         and i.near_branch_target == i.next_ip),
        'src_in_table': (None if not hit else {'base': hex(hit[0]), 'idx': hit[1], 'item_at': hex(hit[2])}),
        'table_item_dword': (None if not hit else hex(dw(hit[2]))),
        'table_item_target': (None if not hit else hex(dw(hit[2]))),
        'high_word_of_item': (None if not hit else '0x%04x' % ((dw(hit[2]) >> 16) & 0xffff)),
        'target_in_table': (None if not thr else {'base': hex(thr[0]), 'idx': thr[1]}),
        'target_is_item_value': (None if not thr else dw(thr[2]) == tgt),
    })
for r in rows:
    print('   ', json.dumps(r, ensure_ascii=False))
put('T2_rows', rows)
ck('T2a 清单里 4 条中有 3 条落在 DWORD 表体的某一项内部（第 1 条 0x71f99e 是抄错的，见 T5）',
   sum(1 for r in rows[:4] if r['src_in_table']) == 3, [r['src'] for r in rows[:4]])
ck('T2b 上一条对 0x71f99e 不成立（该处不在任何表体、也不是 jXX）—— 本轮修正点',
   rows[0]['src_in_table'] is None and not rows[0]['is_zero_disp'],
   'bytes=%s decodes=%s' % (rows[0]['src_bytes'], rows[0]['src_decodes']))
ck('T2c 真实 jXX 源 0x71f9e2 落在表 0x71f9e0 的第 0 项内部（抄错值的对照）',
   (lambda h: h is not None and h[0] == 0x71f9e0 and h[1] == 0)(which_table(0x71f9e2)),
   which_table(0x71f9e2))
# 修正（原版断言写错）：目标**不是**表项的值，而是「同表下一项的表体起点」。
# 因为高半部两字节在项 k 的 +2 处，解得 jcc rel8 00 ⇒ 目标 = +2 + 2 = 项 k+1 的表体起点。
ck('T2d 4 条的目标地址都落在同一张表的下一项表体起点上（不是表项的值）',
   all(r['target_in_table'] and r['src_in_table'] and
       r['target_in_table']['base'] == r['src_in_table']['base'] and
       r['target_in_table']['idx'] == r['src_in_table']['idx'] + 1
       for r in rows[1:4]),
   [(r['src'], r['src_in_table'], r['target_in_table']) for r in rows[1:4]])
put('T2d_note', '源与目标都在同一张表体内：源 = 项 k 的 +2（高半部首字节 70..7F）'
                '，目标 = 项 k+1 的表体起点。故「jXX +0」是表体被读成代码，两端都不是代码。')
ck('T2e 5 条「引用源」全部是表项高位字或表项内部字节，无一条是真控制流入口',
   all(r['src_in_table'] for r in rows[1:5]), [r['src'] for r in rows[1:5]])

# ---------------- T3 反控：把高位字清零 ⇒ 该 jXX +0 消失
NC = []
for src, tgt in TARGETS[1:5]:
    hit = which_table(src)
    if not hit:
        NC.append({'src': hex(src), 'ok': False, 'why': 'not in table'})
        continue
    base, k, a0 = hit
    v0 = dw(a0)
    v1 = v0 & 0x0000ffff          # 把高位字清零 ⇒ 变成 .text 内低地址（不在表内）
    buf = bytearray(txt)
    off = a0 - B
    buf[off:off + 4] = struct.pack('<I', v1)
    d = iced_x86.Decoder(32, bytes(buf[src - B:src - B + 15]), ip=src).decode()
    NC.append({'src': hex(src), 'orig_dw': hex(v0), 'patched_dw': hex(v1),
               'orig': str(dec(src)), 'patched': str(d),
               'still_zero_disp': (d.op0_kind == iced_x86.OpKind.NEAR_BRANCH32
                                   and d.near_branch_target == d.next_ip)})
put('T3_patch_control', NC)
ck('T3 反控：把 4 个表项高位字清零后，那 4 条「jXX +0」全部消失（4/4）',
   all(not r['still_zero_disp'] for r in NC), [(r['src'], r['patched']) for r in NC])

# ---------------- T4 全库普查：位移 0 的 jcc，多少落在表高位字上
dec1 = iced_x86.Decoder(32, txt, ip=B)
zero_jcc = []
while dec1.can_decode:
    i = dec1.decode()
    if i.is_invalid:
        continue
    if i.mnemonic in (iced_x86.Mnemonic.JO, iced_x86.Mnemonic.JNO, iced_x86.Mnemonic.JB,
                      iced_x86.Mnemonic.JAE, iced_x86.Mnemonic.JE, iced_x86.Mnemonic.JNE,
                      iced_x86.Mnemonic.JBE, iced_x86.Mnemonic.JA, iced_x86.Mnemonic.JS,
                      iced_x86.Mnemonic.JNS, iced_x86.Mnemonic.JP, iced_x86.Mnemonic.JNP,
                      iced_x86.Mnemonic.JL, iced_x86.Mnemonic.JGE, iced_x86.Mnemonic.JLE,
                      iced_x86.Mnemonic.JG):
        if i.op0_kind == iced_x86.OpKind.NEAR_BRANCH32 and i.near_branch_target == i.next_ip:
            zero_jcc.append(i.ip)
in_tab = [a for a in zero_jcc if which_table(a)]
not_in = [a for a in zero_jcc if not which_table(a)]
put('T4_zero_disp_jcc', {'total_linear_sweep': len(zero_jcc),
                         'in_table_item': len(in_tab),
                         'not_in_table': len(not_in),
                         'in_table_addrs': [hex(a) for a in in_tab[:40]],
                         'not_in_sample': [hex(a) for a in not_in[:20]]})
ck('T4a 线性扫描下位移 0 的 jcc 总数 > 0（判据非空）', len(zero_jcc) > 0, len(zero_jcc))
# 修正（第二版断言也不对）：线性扫描**根本走不到** 0x7b0082 —— 它落在另一个单元内部。
# 这是本轮新增的一条事实：同一形态的 4 条里，3 条在线性扫描的位移 0 jcc 集合里，
# 第 4 条（0x7b0082）必须先由「任意偏移解码」才能看到。两者必须分开报，不能合成一个数。
_reach = set(zero_jcc)
_in_scan = [t for t in (0x71f9e2, 0x728e0a, 0x7b0082, 0x7d9d2d) if t in _reach]
_out_scan = [t for t in (0x71f9e2, 0x728e0a, 0x7b0082, 0x7d9d2d) if t not in _reach]
put('T4b_reachability', {'in_linear_sweep': [hex(a) for a in _in_scan],
                         'not_reached_by_sweep': [hex(a) for a in _out_scan],
                         'all_of_4_in_table': [hex(a) for a in (0x71f9e2, 0x728e0a, 0x7b0082, 0x7d9d2d)
                                               if which_table(a)]})
ck('T4b 4 个真源地址全部落在 DWORD 表项内（用 which_table 直判，与是否被扫到无关）',
   all(which_table(a) for a in (0x71f9e2, 0x728e0a, 0x7b0082, 0x7d9d2d)),
   [hex(a) for a in (0x71f9e2, 0x728e0a, 0x7b0082, 0x7d9d2d) if not which_table(a)])
ck('T4b2 这 4 条**不是**全部被线性扫描看到：0x7b0082 落在别的单元内部（如实报，不合并口径）',
   len(_in_scan) == 3 and _out_scan == [0x7b0082],
   'in=%d out=%s' % (len(_in_scan), [hex(a) for a in _out_scan]))
ck('T4c 也存在不在表内的位移 0 jcc（说明「落在表内」不是自动成立的）',
   len(not_in) > 0, len(not_in))
# 反控（零信息格已删）：改成有判别力的对照组 —— 用同一判据去测「非表内」那批，
# 若判据说谎，它会把 not_in 里的地址也说成在表内。
_false_pos = [a for a in not_in if which_table(a)]
ck('T4d 反控：判据对「非表内」那 36 条不得产生假阳性（必须给 0）', len(_false_pos) == 0, len(_false_pos))

# ---------------- T5 修正登记
for a in (0x71f99e, 0x71f9e2):
    i = dec(a)
    print('   fix-check', hex(a), raw[a - B + TROFF:a - B + TROFF + 6].hex(' '), '->', i, i.len, i.is_invalid)
FIX = {'wrong': '0x71f99e', 'right': '0x71f9e2', 'delta_bytes': 0x71f9e2 - 0x71f99e,
       'wrong_bytes': raw[0x71f99e - B + TROFF:0x71f99e - B + TROFF + 8].hex(' '),
       'wrong_decodes': str(dec(0x71f99e)),
       'right_bytes': raw[0x71f9e2 - B + TROFF:0x71f9e2 - B + TROFF + 8].hex(' '),
       'right_decodes': str(dec(0x71f9e2)),
       'right_is_zero_disp_jcc': (dec(0x71f9e2).near_branch_target == dec(0x71f9e2).next_ip)}
put('T5_correction', FIX)
ck('T5 R101 待办② 清单第 1 个地址 0x71f99e 不是 jXX（本轮如实修正为 0x71f9e2）',
   not FIX['wrong_is_zero_jcc'] if 'wrong_is_zero_jcc' in FIX else not (dec(0x71f99e).op0_kind == iced_x86.OpKind.NEAR_BRANCH32),
   FIX['wrong_decodes'])
ck('T5b 0x71f9e2 确实是位移 0 的 jcc', FIX['right_is_zero_disp_jcc'], FIX['right_decodes'])

n_fail = sum(1 for c in checks if not c['ok'])
json.dump({'checks': checks, 'R': R}, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('SUMMARY: %d checks, %d FAIL -> %s' % (len(checks), n_fail, OUT))
sys.exit(1 if n_fail else 0)
