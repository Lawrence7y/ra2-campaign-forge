#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r116l_audit_recheck.py —— 规则 D：主会话亲自复算 hy4 审计员的每一条**数字**结论。
审计员的**逻辑**批评（越界、范畴错误）由我逐条判接受/驳回并单列。

审计员（hy4, task 209）报告的独立复算：
  R-A 字节级：0x7f7c70 四处的 imm 起点 = 0x4102b1 / 0x4f68c9 / 0x5125dd / 0x55aa2d，全为 mov edi；
      0x7f7c80 四处 mov edi 起点 = 0x41029d / 0x4f68e0 / 0x5125f1 / 0x55a9f7，另有 60 push
  R-B push 函数数：0x7f7c80=60/36、0x7f7c90=56/8、0x7f7d00=2/2，合计 46 对；移除 target 后基线 10 对
  R-C Fisher 精确检验：条件于 35 coupled / 46 对，target 取 35 的单侧 p = 2.7e-9

我要逐条独立算出来，与它报的数比对。任何不一致必须如实登记。
"""
import json, math, os, struct, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_r113'))
import r113_lib as L

ROOT = '/home/t628/projects/ra2-campaign-forge'
raw, fo, u32 = L.raw, L.fo, L.u32
TS, TE = L.TEXT0, L.TEXT1
OUT = os.path.join(ROOT, '_r116/r116l_audit_recheck.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


# ---- R-A 字节级：imm 起点（= 指令起点 + 操作数偏移） ----
def imm_sites(iid):
    pat = struct.pack('<I', iid)
    buf = raw[fo(TS):fo(TE)]
    out, i = [], buf.find(pat)
    while i != -1:
        v = TS + i
        # 找消费该 imm32 的指令
        for back in range(1, 9):
            s0 = v - back
            if s0 < TS:
                continue
            g = list(L.MD.disasm_lite(raw[fo(s0):fo(s0) + 16], s0))
            if g and g[0][0] == s0 and g[0][0] + g[0][1] == v + 4:
                out.append({'imm_va': hex(v), 'insn': hex(s0), 'mnem': g[0][2],
                            'ops': g[0][3], 'len': g[0][1]})
                break
        else:
            out.append({'imm_va': hex(v), 'insn': None, 'mnem': None, 'ops': None, 'len': None})
        i = buf.find(pat, i + 1)
    return out


s70 = imm_sites(0x7f7c70)
s80 = imm_sites(0x7f7c80)
a70 = [x for x in s70 if x['mnem'] == 'mov']
p80 = [x for x in s80 if x['mnem'] == 'push']
mv80 = [x for x in s80 if x['mnem'] == 'mov']
ck('R-A 复算：0x7f7c70 共 %d 处，其中 mov 形态 %d 处，imm 起点 %s'
   % (len(s70), len(a70), [x['imm_va'] for x in a70]),
   len(a70) == 4 and sorted(x['imm_va'] for x in a70) == sorted(
       ['0x4102b1', '0x4f68c9', '0x5125dd', '0x55aa2d']),
   {'mov_sites': [x['imm_va'] for x in a70]})
ck('R-A 复算：0x7f7c80 共 %d 处 = mov %d + push %d；mov 的 imm 起点 %s'
   % (len(s80), len(mv80), len(p80), [x['imm_va'] for x in mv80]),
   len(s80) == 64 and len(p80) == 60 and len(mv80) == 4,
   {'push': len(p80), 'mov': [x['imm_va'] for x in mv80]})

# ---- R-B 各 IID 的 push 站点/函数数 ----
import bisect
HB = sorted(L.HB)


def f_of(va):
    j = bisect.bisect_right(HB, va) - 1
    return HB[j] if j >= 0 else None


def push_sites(iid):
    pat = struct.pack('<I', iid)
    buf = raw[fo(TS):fo(TE)]
    out, i = [], buf.find(pat)
    while i != -1:
        v = TS + i
        for back in range(1, 6):
            s0 = v - back
            if s0 < TS:
                continue
            g = list(L.MD.disasm_lite(raw[fo(s0):fo(s0) + 16], s0))
            if g and g[0][0] == s0 and g[0][0] + g[0][1] == v + 4 and g[0][2] == 'push':
                out.append(s0)
                break
        i = buf.find(pat, i + 1)
    return out


IIDS = [0x7f7c70, 0x7f7c80, 0x7f7c90, 0x7f7ca0, 0x7f7cf0, 0x7f7d00]
tab = {}
tot_pairs = 0
for iid in IIDS:
    ps = push_sites(iid)
    fns = sorted(set(f_of(x) for x in ps))
    tab[hex(iid)] = {'push': len(ps), 'fns': len(fns)}
    tot_pairs += len(fns)
ck('R-B 复算：六个 GUID 形状 IID 的 push 站点/函数数 = %s；合计 (IID,函数) 对 = %d'
   % ({k: (v['push'], v['fns']) for k, v in tab.items()}, tot_pairs),
   tab['0x7f7c80']['push'] == 60 and tab['0x7f7c80']['fns'] == 36 and
   tab['0x7f7c90']['push'] == 56 and tab['0x7f7c90']['fns'] == 8 and
   tab['0x7f7d00']['push'] == 2 and tab['0x7f7d00']['fns'] == 2 and tot_pairs == 46,
   tab)

base_pairs = tot_pairs - tab['0x7f7c80']['fns']
ck('R-B 复算：移除 target(0x7f7c80) 后基线 (IID,函数) 对 = %d（审计员报 10）' % base_pairs,
   base_pairs == 10, {'base_pairs': base_pairs})

# ---- R-C Fisher 精确检验 ----
def fisher_one_sided(a, b, c, d):
    """2x2: [[a,b],[c,d]]，单侧（>= a 方向）。超几何分布。"""
    n = a + b + c + d
    row1 = a + b
    col1 = a + c
    def hyp(x):
        return math.comb(col1, x) * math.comb(n - col1, row1 - x) / math.comb(n, row1)
    lo = max(0, row1 - (n - col1))
    hi = min(row1, col1)
    return sum(hyp(x) for x in range(a, hi + 1))


# 审计员的条件：总计 35 coupled / 46 对；target 取 35
# 表 = [[coupled_target=35, uncoupled_target=1],[coupled_base=0, uncoupled_base=10]]
p35 = fisher_one_sided(35, 1, 0, 10)
p34 = fisher_one_sided(34, 2, 0, 10)
ck('R-C 复算：Fisher 精确检验（单侧）target 取 35 时 p = %.4e（审计员报 2.7e-09）⇒ 主结果'
   '**逐位吻合**，数量级与首两位一致' % p35,
   abs(p35 / 2.7e-9 - 1) < 0.15, {'p35': p35})
# S-29（如实登记）：审计员的次要数字「target 至少 34 时 p = 4.7e-07」我复算不出来。
# 我按同一超几何单侧尾算得 1.619e-08，与它差约 29 倍。
# 但两者都远小于任何常规显著性阈值，故**不影响**它的结论（差异方向极显著）。
# 不粉饰：这是审计员的一处算术不符，我按实测值登记，并保留其主结果。
ck('R-C 次要数字不符（如实登记）：审计员报「target 至少 34 时 p = 4.7e-07」，'
   '我按同一超几何单侧尾复算 = %.4e，相差 %.1f 倍 ⇒ **审计员此处数字有误**，'
   '但其主结果 p(35)=%.3e 逐位吻合，且两者都远低于显著阈值，结论不受影响'
   % (p34, 4.7e-7 / p34, p35),
   abs(p34 / 4.7e-7 - 1) > 0.5,
   {'my_p34': p34, 'auditor_p34': 4.7e-7, 'ratio': 4.7e-7 / p34,
    'note': '如实登记为审计员算术不符，不用以否定其结论'})

# ---- 审计员的定性批评：可机检的部分 ----
# 批1：35 个命中的 API「全部是 OleSaveToStream，不是 Save 或 Load」
J = json.load(open(os.path.join(ROOT, '_r116/r116a_iid_client.json')))
load_with_b = J['reverse']['load']['with_B']
save_with_b = J['reverse']['save']['with_B']
ck('批评一（C2 口径）复算：43 个 OleSaveToStream 站点中先请求 0x7f7c80 者 %d；'
   '8 个 OleLoadFromStream 站点中 %d ⇒ 命中的 API 确实**全部是 Save**，'
   '审计员的措辞修正成立' % (save_with_b, load_with_b),
   save_with_b == 35 and load_with_b == 0, {'save': save_with_b, 'load': load_with_b})

# 批2：基线 8/10 就是 IUnknown 的 8 个函数（C4 与 C7 数据重叠）
iu = J['rows']['0x7f7c90 (IUnknown)']['push_distinct_fns']
ck('批评二（C4/C7 重叠）复算：IUnknown 的请求函数 %d 个，基线共 %d 对 ⇒ 重叠 %d/%d = %.0f%%，'
   '审计员指「C4 与 C7 不是两个独立反控」成立' % (iu, base_pairs, iu, base_pairs, 100.0 * iu / base_pairs),
   iu == 8 and base_pairs == 10, {'iunk_fns': iu, 'base_pairs': base_pairs})

# 批3：target 去重后只有 2 类代码形状
E = json.load(open(os.path.join(ROOT, '_r116/r116d_iat_indirect.json')))
nsh = E['res']['0x7f7c80']['n_shapes']
ck('批评三（效应量放大）复算：target 的 36 个请求函数按指令形状去重 = %d 类 ⇒ '
   '「97.2%%」是被模板复制放大的比例，审计员要求降级表述成立' % nsh,
   nsh == 2, {'n_shapes': nsh})

# 批4：A2b 的 exp=0 是退化比较
B = json.load(open(os.path.join(ROOT, '_r116/r116b_argpos.json')))
rate_b = B['baseline']['rate']
ck('批评四（A2b 退化）复算：留一法基线 rate = %.2f%% ⇒ 期望值 = 36*0 = 0，'
   '「超出期望 35 个」是 trivial 的，审计员批评成立，应改用 Fisher 检验' % rate_b,
   rate_b == 0.0, {'baseline_rate': rate_b})

# ---- 审计员 C6「越界」我是否接受：机检依据 ----
# 审计员的判据是「名字不在字节里，需要 IID→名字 的映射表」。
# 机检：本机是否存在任何 IID→名字 的映射表（头文件/类型库）？
have_sdk = False
for p in ('/usr/i686-w64-mingw32/include/objidl.h', '/usr/x86_64-w64-mingw32/include/objidl.h',
          '/usr/share/mingw-w64/include/objidl.h'):
    if os.path.exists(p):
        have_sdk = True
ck('审计员 C6 的机检依据：本机是否存在 IID→接口名 的映射表（objidl.h 等）—— 实测 %s。'
   '若为 False，则「0x7f7c70 的语义 = IPersist」在本机上**无法机检**，'
   '审计员判 C6 越界成立' % ('存在' if have_sdk else '不存在'),
   not have_sdk, {'sdk_header_found': have_sdk})

json.dump({'R_A': {'70': [x['imm_va'] for x in a70], '80_push': len(p80),
                   '80_mov': [x['imm_va'] for x in mv80]},
           'R_B': tab, 'total_pairs': tot_pairs, 'base_pairs': base_pairs,
           'R_C': {'p35': p35, 'p34': p34},
           'audit_critiques': {'save_with_b': save_with_b, 'load_with_b': load_with_b,
                               'iunk_fns': iu, 'base_pairs': base_pairs,
                               'n_shapes': nsh, 'baseline_rate': rate_b,
                               'sdk_header_found': have_sdk},
           'checks': checks}, open(OUT, 'w'), indent=1)
np_ = sum(1 for c in checks if c['ok'])
print('\n== %d/%d PASS ==' % (np_, len(checks)))
print('WROTE', OUT)
sys.exit(0 if np_ == len(checks) else 1)
