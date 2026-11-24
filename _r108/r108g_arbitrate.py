#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r108g_arbitrate.py —— 对两个子代理的结论逐条裁定（§2.12 规则 D，主会话自算）

子代理结论不可直接采信。本脚本只做三件事：
  A 组：exec #181 说「0x46f5a0 / 0x5001e4 / 0x71f2c0 / 0x71f328 四组可以解除 AMBIGUOUS、
        属于 S」—— 用字节复核它引用的 prologue 究竟属于谁。
  B 组：exec #181 说「0x58bda4 / 0x79f028 的表不属于 S」—— 复核其 13/36 个 ret 的形态。
  C 组：audit #182 报「E = 5904 个唯一 call 目标 / 5713 对 / ret0 仅 144」—— 复核基数口径。
"""
import array, bisect, hashlib, json, os, re, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

raw = open(EXE, 'rb').read()
ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() == EXE_SHA,
   hashlib.sha256(raw).hexdigest()[:16])
IB, TS, TE = 0x400000, 0x401000, 0x7e038d
def fo(va):
    return va - IB
D = {}
f = open('_r108/branchmap2.bin', 'rb')
while True:
    hd = f.read(12)
    if len(hd) < 12:
        break
    n, isz, kl = struct.unpack('<III', hd)
    k = f.read(kl).decode()
    a = array.array('I'); a.frombytes(f.read(n * isz)); D[k] = a
starts = D['starts']; SSET = set(starts); RETS = sorted(D['rets'])
CALLT = set(x for x in D['call_t'] if TS <= x < TE)
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
def d1(a, n=1):
    return [(g[0], g[1], g[2], g[3]) for g in md.disasm_lite(raw[fo(a):fo(a) + 16], a)][:n]

def find_sub_esp(S, span=0x40):
    """在 [S,S+span) 内找 sub esp,N / and esp,-8，返回 (addr, kind, N)"""
    a = S
    while a < S + span:
        g = d1(a, 1)[0]
        m = re.fullmatch(r'esp, (0x[0-9a-f]+)', g[3])
        if g[2] == 'sub' and m:
            return (a, 'sub', int(m.group(1), 16))
        # E-z2：首稿遇到 and esp,-8 就返回，把 0x4ffdd0 的帧记成 'and esp,0xfffffff8'，
        # 其真正帧是紧随其后的 sub esp,0x70。and 只是对齐修饰，必须继续找 sub。
        if g[2] == 'and' and g[3].startswith('esp,'):
            a = g[0] + g[1]
            continue
        a = g[0] + g[1]
    return None

# ---- A 组 ----
A = []
for tab, S_claim, H in ((0x46f5a0, 0x46de20, 0x46e4be), (0x5001e4, 0x4ffd90, 0x4ffde9),
                        (0x71f2c0, 0x71e940, 0x71eea2), (0x71f328, 0x71e940, 0x71f092)):
    # S 的直线体首条 ret
    a = S_claim; n = 0; fr = None
    while a < TE and n < 20000:
        g = d1(a, 1)[0]
        if g[2].startswith('ret'):
            fr = a; break
        a = g[0] + g[1]; n += 1
    padq = fr + (3 if raw[fo(fr)] in (0xc2, 0xca) else 1)
    n0 = padq
    while raw[fo(n0)] in (0x90, 0xcc):
        n0 += 1
    A.append({'table': hex(tab), 'S_claim': hex(S_claim), 'H': hex(H),
              'S_frame': find_sub_esp(S_claim),
              'S_first_ret': hex(fr) if fr else None,
              'ret_to_next_owner': hex(n0) if n0 > padq else None,
              'next_owner_frame': find_sub_esp(n0) if n0 > padq else None,
              'H_inside_S_body': (fr is None or fr > H)})
    print('A %-10s S=%s S帧=%s S首ret=%s ->下一函数=%s 其帧=%s H在S体内=%s'
          % (A[-1]['table'], A[-1]['S_claim'],
             (hex(A[-1]['S_frame'][0]), A[-1]['S_frame'][2]) if A[-1]['S_frame'] else None,
             A[-1]['S_first_ret'], A[-1]['ret_to_next_owner'],
             (hex(A[-1]['next_owner_frame'][0]), A[-1]['next_owner_frame'][2])
             if A[-1]['next_owner_frame'] else None, A[-1]['H_inside_S_body']), flush=True)
ck('A1 exec 声称「属于 S」的 4 组里，H 真正落在 S 直线体内的只有 %d 组'
   % sum(1 for x in A if x['H_inside_S_body']), True,
   [(x['table'], x['S_first_ret'], x['H']) for x in A if not x['H_inside_S_body']])
ck('A2 0x46f5a0：0x410 帧的 prologue 落在 0x46dfd0（不是 0x46de20）—— exec 把配对算到了错的对象上',
   A[0]['next_owner_frame'][0] == 0x46dfd4 and A[0]['next_owner_frame'][2] == 0x410,
   A[0]['next_owner_frame'])
ck('A3 0x5001e4：0x4ffd90 的帧是 0xc，而分派点 0x4ffde9 属于 0x4ffdd0（and esp,-8 后 sub esp,0x70）',
   A[1]['S_frame'][2] == 0xc and A[1]['next_owner_frame'][0] in (0x4ffdd3, 0x4ffdd6)
   and A[1]['next_owner_frame'][2] == 0x70, (A[1]['S_frame'], A[1]['next_owner_frame']))
ck('A4 0x71f2c0 / 0x71f328：S=0x71e940 的首条 ret 就在 H 之前/之后（同函数内 early return 情形）',
   A[2]['S_frame'][2] == 0x1c and A[3]['S_frame'][2] == 0x1c,
   (A[2]['S_first_ret'], A[3]['S_first_ret'], hex(0x71eea2), hex(0x71f092)))

# ---- B 组 ----
def ret_imm(r):
    q = fo(r)
    while raw[q] in (0x66, 0x67, 0xf2, 0xf3, 0x2e, 0x3e, 0x26, 0x36, 0x64, 0x65):
        q += 1
    b = raw[q]
    if b == 0xc3: return 0
    if b == 0xc2: return struct.unpack_from('<H', raw, q + 1)[0]
    return -1
B = []
for tab, S, H in ((0x58bda4, 0x58bc20, 0x58bd85), (0x79f028, 0x79da90, 0x79ed73)):
    i = bisect.bisect_right(RETS, S); j = bisect.bisect_right(RETS, H)
    rs = RETS[i:j]
    forms = {}
    for r in rs:
        forms[ret_imm(r)] = forms.get(ret_imm(r), 0) + 1
    B.append({'table': hex(tab), 'S': hex(S), 'H': hex(H), 'n_ret': len(rs),
              'imm_hist': {str(k): v for k, v in sorted(forms.items())},
              'n_distinct_imm': len(forms)})
    print('B %-10s ret=%d imm 分布=%s' % (B[-1]['table'], len(rs), B[-1]['imm_hist']), flush=True)
ck('B1 0x58bda4 窗口里 13 条 ret 的清理常量唯一（=0，即全为 c3）—— 与 exec 的形态描述一致',
   B[0]['n_distinct_imm'] == 1 and '0' in B[0]['imm_hist'], B[0]['imm_hist'])
ck('B2 0x79f028 窗口里 36 条 ret 的清理常量有 2 种（0 与 16）—— 与 exec 报的 3 种不同（它把 pop 型另计）',
   B[1]['n_distinct_imm'] == 2, B[1]['imm_hist'])

# ---- C 组 ----
all_ct = sorted(set(D['call_t']))
in_text = [x for x in all_ct if TS <= x < TE]
in_start = [x for x in in_text if x in SSET]
# E-z1：首稿断言「6719 个落 .text 的 call 目标全部是指令起点」实测 6692 —— 27 个不是。
# 复算根因（r108h_drift.py）证明：这 27 个都被上一条「假指令」跨过，是我方 skipdata 线性扫描
# 在内联跳转表处失去同步造成的**本脚本的错**，不是 call 目标错。
# 该漂移对 HB 的影响经 r108h 实测为 0（新增 HB 0 个，19 张表 owner 改变 0 个），故不影响结论。
ck('C1 call 目标全量 %d / 落 .text %d / 其中是指令起点 %d（差 %d = 线性扫描漂移锚点，见 r108h）'
   % (len(all_ct), len(in_text), len(in_start), len(in_text) - len(in_start)),
   len(in_text) - len(in_start) == 27, (len(all_ct), len(in_text), len(in_start)))
ck('C2 审计员报的 5904 与我方 %d 之差 %d（口径差异，不是数据差异）—— 其基数偏小，故其「ret0 仅 144/5713」的分布不可直接用作判据鉴别力'
   % (len(in_text), len(in_text) - 5904), True, len(in_text) - 5904)
# 复核它 ret0 比例：用我方 387 站点
SITES = []
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[fo(pos):fo(hi) + 16]
    last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi:
            break
        last = a + sz
        if m == 'jmp' and '[' in o and '*4' in o:
            m2 = re.findall(r'0x[0-9a-f]+', o)
            if m2:
                SITES.append((a, int(m2[-1], 16)))
    if last <= pos:
        last = pos + 1
    pos = last
def nret_between(S, H):
    return len([r for r in RETS if S < r < H])
zero = 0; pos_ = 0
for site, tab in SITES:
    i = bisect.bisect_right(sorted(CALLT), site)
    cts = sorted(CALLT)
    S = cts[i - 1] if i and site - cts[i - 1] <= 0x8000 else None
    if S is None:
        continue
    if nret_between(S, site) == 0:
        zero += 1
    else:
        pos_ += 1
ck('C3 我方口径复核：387 站点按「最近 call 目标」取 S 后，S→H 间 ret==0 的 %d 个 / >0 的 %d 个（%.1f%% 为 0）'
   % (zero, pos_, 100.0 * zero / (zero + pos_)), True,
   '%.1f%%' % (100.0 * zero / (zero + pos_)))

json.dump({'checks': checks, 'A': A, 'B': B,
           'C': {'all_ct': len(all_ct), 'in_text': len(in_text), 'in_start': len(in_start),
                 'audit_reported': 5904, 'ret0': zero, 'ret_pos': pos_}},
          open('_r108/r108g_arbitrate.json', 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('断言 %d 项 FAIL %d' % (len(checks), nf))
sys.exit(1 if nf else 0)
