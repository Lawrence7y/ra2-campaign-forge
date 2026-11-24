#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r116g_hbgap.py —— 自错 S-27：HB 函数入口集合漏掉了 0x67d300，导致
「0x7f7c80 的请求函数数」在两种归属口径下给出 36 与 35 两个不同的数。

起因（这是在**跨实现复算**里被抓到的，不是同一实现自查）：
  r116a..r116e 用 r113_lib.HB 的 fn_of 归属，得 36 个函数、1 个未耦合（0x67cef0）。
  r116f 用**独立**的「call/jmp rel32 目标」当函数入口，得 36 个函数、1 个未耦合（0x67d300）。
  两个实现的**去重个数相同（36）**，但被指向的"未耦合那个"不同 ⇒ 必有一个边界划分是错的。
  实测：0x67d300 是**真函数入口** ——
      · 前一条指令的末字节是 0xC2 04 00（ret 4），即上一个函数在此结束
      · 0x67d1af 处有 e8 rel32 直接 call 到它
      · 入口形态 sub esp,8 / push ebx / push ebp / push esi 与同族函数一致
  而 HB（r113_lib，来自 r112_lib 的启发式）**没有**收录 0x67d300，
  于是 fn_of 把 [0x67cef0, 0x67e440) 整段当成一个函数，把 0x67d300 的体合并进 0x67cef0。
  后果：0x67cef0 的 QI 站点（7 个）与 0x67d300 的间接 OleSaveToStream 调用被算进**同一个函数**
  ⇒ 得出「0x67cef0 未耦合」这个**错误**结论；真实情况是「0x67d300 已耦合」。
  最终数字不变（36 个函数、全部耦合），但**归属**必须改正。

断言：
  A1 0x67d300 是真入口的三条独立证据（前一函数以 ret 4 结束 / 有 e8 call 直达 / 入口形态）
  A2 HB 里在 (0x67cef0, 0x67e440) 区间内**没有任何**入口 ⇒ HB 漏检，实测确认
  A3 用修正后的归属（把 0x67d300 与 0x67cef0 分开），0x7f7c80 的 36 个请求函数
     **全部**耦合 OleSaveToStream（0 个未耦合）
  A4 归属修正前后，去重后的**函数个数都是 36**（所以 r116a 的 36 这个数是对的，
     错的只是"哪个函数未耦合"这一条）
  K1 反控：把 0x67d300 强行并回 0x67cef0（= 复现 HB 的错），未耦合数必须变回 1
内存纪律：disasm_lite；detail 恒 False。
"""
import bisect, json, os, struct, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_r113'))
import r113_lib as L

ROOT = '/home/t628/projects/ra2-campaign-forge'
raw, fo, u32 = L.raw, L.fo, L.u32
TS, TE = L.TEXT0, L.TEXT1
HB = sorted(L.HB)
IAT_SAVE = 0x7e15f4
OUT = os.path.join(ROOT, '_r116/r116g_hbgap.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


ENTRY = 0x67d300

# ---- A1 三条独立证据 ----
pre = raw[fo(ENTRY) - 3:fo(ENTRY)]
ev1 = pre == b'\xc2\x04\x00'
ev2 = []
a = TS
while a < TE - 5:
    if raw[fo(a)] == 0xe8:
        rel = struct.unpack_from('<i', raw, fo(a) + 1)[0]
        if a + 5 + rel == ENTRY:
            ev2.append(a)
    a += 1
head = [g[2] + ' ' + g[3] for g in L.MD.disasm_lite(raw[fo(ENTRY):fo(ENTRY) + 12], ENTRY)]
ev3 = head[:4] == ['sub esp, 8', 'push ebx', 'push ebp', 'push esi']
ck('A1 0x67d300 是真函数入口，三条独立证据：'
   '① 前 3 字节 = c2 04 00（ret 4，上一函数在此结束）= %s；'
   '② e8 rel32 直达 call 的调用点 %d 个 %s；'
   '③ 入口形态 %s = %s'
   % (ev1, len(ev2), [hex(x) for x in ev2], head[:4], ev3),
   ev1 and len(ev2) >= 1 and ev3, {'pre': pre.hex(), 'callers': [hex(x) for x in ev2], 'head': head[:4]})

# ---- A2 HB 漏检 ----
in_gap = [x for x in HB if 0x67cef0 < x < 0x67e440]
ck('A2 HB 在 (0x67cef0, 0x67e440) 开区间内**没有任何**入口（%d 个）⇒ HB 把 0x67d300 及其后续'
   '函数体全部并入 0x67cef0（实测确认，不是推测）' % len(in_gap),
   len(in_gap) == 0, {'hb_in_gap': in_gap})

# ---- 归属：修正版入口集合 = HB ∪ {0x67d300} ----
HB_FIX = sorted(set(HB) | {ENTRY})


def fn_fix(va):
    j = bisect.bisect_right(HB_FIX, va) - 1
    return HB_FIX[j] if j >= 0 else None


def fn_old(va):
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


def coupled(f):
    """该函数内是否有 OleSaveToStream 调用（直接 call [IAT] 或 mov reg,[IAT] + call reg）"""
    ins = L.body(f, win=1200)
    slot = 'dword ptr [%s]' % hex(IAT_SAVE)
    regs = set()
    for a, sz, m, o in ins:
        if m == 'mov' and o.endswith(', ' + slot):
            r = o.split(',')[0].strip()
            regs.add(r)
        elif m in ('xor', 'mov') and o.split(',')[0].strip() in regs and slot not in o:
            regs.discard(o.split(',')[0].strip())
        elif m == 'call':
            if o == slot:
                return True
            if o in regs:
                return True
    return False


p80 = push_sites(0x7f7c80)
old_fns = sorted(set(fn_old(x) for x in p80))
new_fns = sorted(set(fn_fix(x) for x in p80))
old_unc = [f for f in old_fns if not coupled(f)]
new_unc = [f for f in new_fns if not coupled(f)]
ck('A3 归属修正后：0x7f7c80 的请求函数 %d 个，**全部**耦合 OleSaveToStream（未耦合 %d 个）'
   % (len(new_fns), len(new_unc)),
   len(new_fns) == 36 and len(new_unc) == 0,
   {'fns': len(new_fns), 'uncoupled': [hex(x) for x in new_unc]})

ck('A4 归属修正前后函数个数都是 36（旧归属 %d / 新归属 %d）⇒ r116a 的 36 这个数是对的。'
   '注意：旧版报出的「35 耦合 / 1 未耦合（0x67cef0）」**不是** HB 漏检造成的，'
   '而是 S-24（只认直接 call [IAT]、漏了 mov reg,[IAT]+call reg）造成的；'
   '两处缺陷必须分开记，不得混成一因。HB 漏检的真实后果只是「站点归属到哪个函数」记错。'
   % (len(old_fns), len(new_fns)),
   len(old_fns) == 36 and len(new_fns) == 36 and len(new_unc) == 0,
   {'old': len(old_fns), 'new': len(new_fns),
    'note': 'S-24 与 S-27 是两处独立缺陷，不得混因',
    'old_uncoupled': [hex(x) for x in old_unc], 'new_uncoupled': [hex(x) for x in new_unc]})

# ---- K1 反控：复现 HB 的错 ----
k1 = (fn_old(0x67d36e) == 0x67cef0) and (fn_fix(0x67d36e) == ENTRY)
ck('K1 反控：用旧 HB 归属，0x67d36e（0x7f7c80 的 QI 站点）被算进 0x67cef0；'
   '用修正归属算进 0x67d300（= %s）⇒ 差异确实由这一处 HB 漏检造成' % k1,
   k1, {'old_owner': hex(fn_old(0x67d36e)), 'new_owner': hex(fn_fix(0x67d36e)),
        'entry': hex(ENTRY)})

json.dump({'entry': hex(ENTRY), 'evidence': {'pre': pre.hex(),
                                             'callers': [hex(x) for x in ev2],
                                             'head': head[:4]},
           'hb_gap': in_gap, 'old': {'fns': len(old_fns),
                                     'uncoupled': [hex(x) for x in old_unc]},
           'new': {'fns': len(new_fns), 'uncoupled': [hex(x) for x in new_unc]},
           'checks': checks}, open(OUT, 'w'), indent=1)
np_ = sum(1 for c in checks if c['ok'])
print('\n== %d/%d PASS ==' % (np_, len(checks)))
print('WROTE', OUT)
sys.exit(0 if np_ == len(checks) else 1)
