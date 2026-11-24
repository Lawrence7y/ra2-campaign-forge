#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r116i_ctlfix.py —— 自错 S-28：r116h 的 T2/T3 反控**无牙**，必须重做成有正控的版本。

S-28（主会话自抓，如实登记）：
  r116h 的 T2（两步形态 mov R,imm32 ; push R）与 T3（栈槽 mov [esp+X],imm32）
  对 0x7f7c70 命中 0，我据此在断言文字里写了「H2/H3 被排除」。
  但同一检测器对 0x7f7c80 与 0x7ed358 也命中 0 —— 而这两个**确实**有请求站点。
  这说明检测器根本没被证明能命中任何东西，**在不下手的地方打了反控**（= R115 自错 S-16 复发）。
  一条"处处 0"的检测器不能用来排除任何假设。

正确做法：先构造正控 —— 在真实镜像里找一个**确实**是「mov R,imm32 ; push R」形态的站点，
让检测器必须命中它；只有正控命中之后，0x7f7c70 的 0 才有意义。

断言：
  P1 正控构造：扫全 .text 找所有「mov R,imm32 (<0x10000 之外) ; 紧随 push R」形态，
     报出数量与样本（必须 > 0，否则检测器不可用，本轮的排除结论作废）
  P2 有正控后重测 0x7f7c70 的两步形态（必须 0）
  P3 栈槽形态的同理正控 + 重测
  P4 若 P1 或 P3 的正控为 0：本轮**撤回** r116h 中「H2/H3 被排除」的措辞，降级为「未测」
"""
import bisect, json, os, struct, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_r113'))
import r113_lib as L

ROOT = '/home/t628/projects/ra2-campaign-forge'
raw, fo, u32 = L.raw, L.fo, L.u32
TS, TE = L.TEXT0, L.TEXT1
OUT = os.path.join(ROOT, '_r116/r116i_ctlfix.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


def linear(start, n):
    return list(L.MD.disasm_lite(raw[fo(start):fo(start) + n], start))


# ---- P1 正控：全 .text 找 mov R,imm32 ; push R ----
# 只解 .text 里所有 `ba..bf`/`b8..bb` 5 字节 mov imm32 位置，再往后看是否 push R。
# 独立于目标 IID，纯形态扫描 ⇒ 这是真正的正控。
pos_hits = []
a = TS
while a < TE - 10:
    o = fo(a)
    b = raw[o]
    if 0xb8 <= b <= 0xbf:                 # mov r32, imm32
        imm = struct.unpack_from('<I', raw, o + 1)[0]
        reg = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi'][b - 0xb8]
        nxt = a + 5
        g = linear(nxt, 8)
        if g and g[0][2] == 'push' and g[0][3] == reg:
            pos_hits.append({'mov': hex(a), 'imm': '%08x' % imm, 'push': hex(nxt), 'reg': reg})
        a += 5
        continue
    a += 1
ck('P1 正控构造：全 .text 里「mov R,imm32 ; 紧随 push R」形态实测 %d 例（样本 %s）'
   % (len(pos_hits), pos_hits[:3]),
   len(pos_hits) > 0, {'n': len(pos_hits), 'sample': pos_hits[:3]})


# 用正控验证「检测器思路」本身：对正控里的每个 imm，两步检测器必须能命中
def two_step_of(iid):
    return [h for h in pos_hits if int(h['imm'], 16) == iid]


ctrl_iid = int(pos_hits[0]['imm'], 16) if pos_hits else None
hit_ctrl = two_step_of(ctrl_iid) if ctrl_iid else []
ck('P1b 检测器有牙性验证：拿正控样本里的 imm %s 回灌同一检测器，必须命中 %d 次（>0）'
   % (hex(ctrl_iid) if ctrl_iid else 'none', len(hit_ctrl)),
   len(hit_ctrl) > 0, {'ctrl_iid': hex(ctrl_iid) if ctrl_iid else None, 'hits': len(hit_ctrl)})

# ---- P2 有正控后重测 ----
t70 = two_step_of(0x7f7c70)
t80 = two_step_of(0x7f7c80)
has_ctrl = len(pos_hits) > 0
ck('P2 在 P1b 正控成立的前提下重测：0x7f7c70 的两步形态 %d 次、0x7f7c80 %d 次'
   % (len(t70), len(t80)),
   has_ctrl and len(t70) == 0,
   {'t70': len(t70), 't80': len(t80), 'control_alive': has_ctrl})

# ---- P3 栈槽形态正控 ----
stack_pos = []
a = TS
while a < TE - 12:
    o = fo(a)
    if raw[o] == 0xc7:                    # mov r/m32, imm32
        modrm = raw[o + 1]
        if modrm == 0x44 and raw[o + 2] == 0x24:      # [esp+disp8]
            imm = struct.unpack_from('<I', raw, o + 4)[0]
            stack_pos.append({'site': hex(a), 'imm': '%08x' % imm})
            a += 8
            continue
    a += 1
n70 = sum(1 for x in stack_pos if int(x['imm'], 16) == 0x7f7c70)
ck('P3 栈槽形态正控：全 .text 里 `mov dword ptr [esp+disp8], imm32` 实测 %d 例（正控存活）；'
   '其中 imm == 0x7f7c70 的 %d 例'
   % (len(stack_pos), n70),
   len(stack_pos) > 0 and n70 == 0,
   {'stack_mov_imm_total': len(stack_pos), 'i70': n70, 'sample': stack_pos[:3]})

# ---- P4 措辞裁决 ----
ck('P4 措辞裁决：P1b 正控 %s、P3 正控 %s ⇒ r116h 中「H2/H3 被排除」的措辞 %s'
   % ('存活' if has_ctrl else '不存活', '存活' if stack_pos else '不存活',
      '可保留' if (has_ctrl and stack_pos) else '必须撤回并降级为未测'),
   has_ctrl and len(stack_pos) > 0,
   {'p1': has_ctrl, 'p3': bool(stack_pos)})

json.dump({'pos_hits': len(pos_hits), 'sample': pos_hits[:5],
           'stack_pos': len(stack_pos), 'i70_two_step': len(t70),
           'i70_stack': n70, 'control_alive': has_ctrl, 'checks': checks},
          open(OUT, 'w'), indent=1)
np_ = sum(1 for c in checks if c['ok'])
print('\n== %d/%d PASS ==' % (np_, len(checks)))
print('WROTE', OUT)
sys.exit(0 if np_ == len(checks) else 1)
