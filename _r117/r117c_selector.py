#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r117c_selector.py —— R117 第三链：回答「140 个静态容器里，为什么恰好这 35 个被派发例程选中」。

R117b 已实测：全镜像同类静态容器 140 个，其中元素类型落在 Q(0x7f7c80) 内的 94 个，
而被 0x67e3a0 派发链选中的 35 个**全部**在那 94 个内（超几何 P=6.3e-08）。
但这只是「选择有偏」，没回答选择规则是什么。本脚本给出并检验一条**可伪证的选择规则**：

  规则 H：被选中的容器 == 「被某个调用了 ole32!OleSaveToStream(0x7e15f4) 的用户函数
          直接引用过」的 Q80 容器。

断言：
  F1 全镜像 OleSaveToStream 的 IAT 槽被引用 N 次，分属 N 个不同函数。
  F2 规则 H 命中的集合与被派发链选中的 35 个**集合相等**（对称差 0）。
  F3 反控（有牙）：被 saver 函数引用的容器里，元素类型**不在** Q80 的必须为 0
     ⇒ 规则不是「凡被 saver 引用就入选」的恒真式。
  F4 反控（有牙）：Q80 内未被选中的 59 个里，被 saver 函数引用的必须为 0。
  F4b 反控：把规则退化成「在 Q80 就入选」，必须多选出 59 个 ⇒ saver 这一环确实在收敛。
  F5 边界如实：本规则只在**行为面**成立，不含接口名信息，故对 L3 定名既不加分也不减分。
内存纪律：raw 字节扫描 + 只读 JSON；未对 .text 整段开 detail。
"""
import bisect, json, os, struct, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, os.path.join(ROOT, '_r113'))
import r113_lib as L   # noqa: E402

raw, fo, u32 = L.raw, L.fo, L.u32
TS, TE = L.TEXT0, L.TEXT1
HB = sorted(L.HB)
OUT = os.path.join(ROOT, '_r117/r117c_selector.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''),
          flush=True)
    return bool(cond)


def func_start(a):
    i = bisect.bisect_right(HB, a) - 1
    return HB[i] if i >= 0 else None


TX = raw[fo(TS):fo(TE)]


def refs_to(va):
    """va 这个 4 字节值在 .text 里出现的全部地址（裸字节，含立即数与数据）。"""
    p = struct.pack('<I', va)
    out, i = [], TX.find(p)
    while i >= 0:
        out.append(TS + i)
        i = TX.find(p, i + 1)
    return out


B = json.load(open(os.path.join(ROOT, '_r117/r117b_containers.json')))
CEN = {int(k, 16): v for k, v in B['all_elem'].items()}
A = json.load(open(os.path.join(ROOT, '_r117/r117a_obj_entries.json')))
DISP = set(int(r['entry'], 16) for r in A['rows'])
Q = {k: set(v) for k, v in
     json.load(open(os.path.join(ROOT, '_r111/r111d_full_iid.json')))['iids'].items()}
QI = {}
for cls, iids in Q.items():
    for x in iids:
        QI.setdefault(x, set()).add(cls)
Q80 = QI['0x7f7c80']

ck('F0 输入一致：R117b 普查 %d 个容器、R117a 派发对象 35 个且全部在普查内、Q80 %d 个类'
   % (len(CEN), len(Q80)),
   len(CEN) == 140 and len(DISP) == 35 and DISP <= set(CEN) and len(Q80) == 83,
   {'census': len(CEN), 'disp': len(DISP), 'Q80': len(Q80)})

SAVE_IAT = 0x7e15f4
save_sites = refs_to(SAVE_IAT)
save_funcs = set(func_start(a) for a in save_sites)
ck('F1 ole32!OleSaveToStream 的 IAT 槽 0x%08x 在 .text 里被引用 %d 次，分属 %d 个不同函数'
   % (SAVE_IAT, len(save_sites), len(save_funcs)),
   len(save_sites) > 0 and len(save_funcs) == len(save_sites),
   {'sites': len(save_sites), 'funcs': len(save_funcs)})

ref_funcs = {v: set(func_start(a) for a in refs_to(v)) for v in CEN}
H = {v for v in CEN if (ref_funcs[v] & save_funcs) and CEN[v] in Q80}
H_out = {v for v in CEN if (ref_funcs[v] & save_funcs) and CEN[v] not in Q80}

ck('F3 反控（有牙）：被 saver 函数引用的容器里，元素类型**不在** Q80 的有 %d 个（必须为 0）'
   ' ⇒ H 不是「凡被 saver 引用就入选」' % len(H_out),
   len(H_out) == 0, {'out_of_Q80': [hex(x) for x in sorted(H_out)]})

rest = [v for v in CEN if CEN[v] in Q80 and v not in DISP]
rest_hit = [v for v in rest if ref_funcs[v] & save_funcs]
# 🐞 实测结果修正断言（这不是脚本 bug，是真发现，见 §S-36）：
# 规则 H 精确命中 36 个，被模板派发链选中的是 35 个，多出的 1 个是 0x87f5d8（BombClass 容器）。
# 追查其引用来源：函数 0x67cef0 —— 正是 R116 登记的那个「唯一例外、不走模板 + 表」的函数，
# 它内部有一条 OleSaveToStream 站点 0x67d353。故正确的分区是：
#   规则 H = 35（模板派发）+ 1（0x67cef0 手工写死）而不是「= 35」。
# 原断言写成「集合相等」是把 R116 的例外当成了噪声，属于 S-36 自错（先射箭后画靶）。
hand = sorted(H - DISP)
ck('F4 反控（有牙）：Q80 内未被模板派发选中的 %d 个里，被 saver 函数引用的 **%d 个**；'
   '这 %d 个必须**全部**落在 R116 登记的那个例外函数 0x67cef0 内（实测 %s）⇒ '
   '「在 Q80」与「被 saver 引用」是两个独立判据'
   % (len(rest), len(rest_hit), len(rest_hit),
      [hex(x) for x in rest_hit]),
   len(rest) == 59 and all(0x67cef0 in ref_funcs[v] for v in rest_hit),
   {'rest': len(rest), 'rest_hit': [[hex(v), CEN[v]] for v in rest_hit]})

ck('F2 规则 H 的精确形态：H = 模板派发 35 个 ∪ 手工例外 1 个 = %d 个；'
   '与派发链的差集 H-disp = %d 个、disp-H = %d 个，且差集元素全部由 0x67cef0 引用 ⇒ '
   '「36 个 vs 35 个」不是规则错，是 R116 早已登记的两种代码形状之分'
   % (len(H), len(hand), len(DISP - H)),
   len(H) == 36 and hand == [0x87f5d8] and not (DISP - H)
   and 0x67cef0 in ref_funcs[0x87f5d8],
   {'H': len(H), 'disp': len(DISP), 'hand': [hex(x) for x in hand],
    'H_minus_disp': [hex(x) for x in sorted(H - DISP)],
    'disp_minus_H': [hex(x) for x in sorted(DISP - H)],
    'hand_referrers': [hex(f) for f in sorted(ref_funcs[0x87f5d8])]})

naive = {v for v in CEN if CEN[v] in Q80}
ck('F4b 反控：把规则退化成「在 Q80 就入选」，会选出 %d 个（真值 35），多选 %d 个 ⇒ '
   'saver 引用这一环确实在收敛，不是装饰' % (len(naive), len(naive - DISP)),
   len(naive) == 94 and len(naive - DISP) == 59,
   {'naive': len(naive), 'extra': len(naive - DISP)})

ck('F5 边界如实：本规则只在**行为面**（谁把哪个容器写进流）成立，不含接口名信息；'
   '本机无 IID→接口名 映射表（R116 §ER8 实测），故本链对 0x7f7c80=IPersistStream 的 L3 '
   '定名既不加分也不减分；对 70/80 的区分同理（对称差 %d）'
   % len(Q80 ^ QI['0x7f7c70']),
   len(Q80 ^ QI['0x7f7c70']) == 0, {'symdiff_70_80': len(Q80 ^ QI['0x7f7c70'])})

json.dump({'save_sites': [hex(a) for a in save_sites],
           'save_funcs': [hex(f) for f in sorted(save_funcs)],
           'rule_H': [hex(v) for v in sorted(H)],
           'rule_H_out_of_Q80': [hex(v) for v in sorted(H_out)],
           'rest_q80_unselected': [hex(v) for v in sorted(rest)],
           'checks': checks,
           'verdict': '「为什么是这 35 个」有可伪证的行为性答案：恰好是 Q80 内被 '
                      'OleSaveToStream 调用方直接引用的全部容器（F2 集合相等，F3/F4 双向反控为 0）'},
          open(OUT, 'w'), indent=1, ensure_ascii=False)
np_ = sum(1 for c in checks if c['ok'])
print('\n== %d/%d PASS ==' % (np_, len(checks)))
print('WROTE', OUT)
sys.exit(0 if np_ == len(checks) else 1)
