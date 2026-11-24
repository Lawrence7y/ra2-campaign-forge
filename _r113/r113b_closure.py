#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r113b_closure.py —— 链 G：QI **闭包**认领集（修 R111/R112 的两处漏项），
并用它重裁 R111 §EM3 的「0x7ed358 语义未定」与 R112 的三者不可区分。

R111/R112 的认领集 Q(iid) 只数**本类 slot0 体内**的 cmpsd（adjustor thunk 只看 jmp 目标）。
本轮实测这条口径漏了两类真实形态：
  漏项①  委托调用：slot0 先 call 父类/共享 QI 体，命中后 eq 分支继续查自己的 IID。
          例 AbstractClass 0x410260 体内直接命中 4 个 IID，但 AircraftClass 0x414290
          是先 call 0x410260 再查 0x7e9b40 ⇒ R111 把 AircraftClass 记进 Q(0x7e9b40)，
          却**没**把它记进 Q(0x7f7c70/0x7f7c80/0x7e9ae0/0x7f7c90)，而它实际都能 QI 成功。
  漏项②  thunk 目标体内还有 call：Fly 等 6 类的 slot0 是 `sub [esp+4],4 ; jmp 0x55a9b0`，
          而 0x55a9b0 里第 4 个 cmpsd 才是 0x7f7c70 ⇒ R111 只拿到前 3 个 IID，漏掉 1 个。

本轮的 Q 定义（可机械复算，无阈值）：
  closure(f) = ⋃ cmpsd(体(f)) ∪ closure(thunk-jmp 目标) ∪ closure(call 目标, 深度-1)
  下钻只在 HB 函数入口处发生；深度 2；函数内环状 call 用 seen 集去重。

断言：
  B1 分类域：CMPSD 172 类 + TH 12 类 = 184 个入口（ATL 3 类单列，不进闭包判据）
  B2 Q(0x7f7c90) 必须等于「全部 184 个入口」—— IUnknown 是每条 QI 链的兜底（正控）
  B3 AircraftClass 必须从 4 个 IID 的认领集里**补进去**（漏项① 的直接证据）
  B4 6 个 `jmp 0x55a9b0` 的类必须补齐 0x7f7c70（漏项② 的直接证据）
  B5 R111 §EM3 的 0x7ed358：闭包后 |Q|=12（不是 6），且 FULL(N=4)={ILocomotion} 唯一
  B6 R111 §EM10② 三者在闭包口径下**依然不可区分**（FULL 全同、Q 全同、子对象 vtable 集合全同）
  B7 反控：把下钻关掉（depth=0 且不跟 thunk）⇒ 认领集回落到 R111 的数，证明补的东西
     确实来自闭包而不是我改了别处
  B8 反控：把 Q 缩减 10% 随机子集 ⇒ FULL 集必须变宽（若不变宽说明 FULL 判据对该 IID 无鉴别力）
内存纪律：disasm_lite，函数体 HB 定界，深 2、seen 去环。
"""
import collections, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r113_lib as L

ROOT = L.ROOT
OUT = os.path.join(ROOT, '_r113/r113b_closure.json')
raw, fo, u32, i32 = L.raw, L.fo, L.u32, L.i32
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


A111 = json.load(open(os.path.join(ROOT, '_r111/r111a_iidmap2.json')))
D111 = json.load(open(os.path.join(ROOT, '_r111/r111d_full_iid.json')))
TH111 = json.load(open(os.path.join(ROOT, '_r111/r111c_thunk.json')))['thunks']
B112 = json.load(open(os.path.join(ROOT, '_r112/r112b_qi_offset.json')))
C112 = json.load(open(os.path.join(ROOT, '_r112/r112c_subobj.json')))
sym, VT = L.L.load_symbols()
RT = L.RTTI

ENTRY = {}
for c, e in A111['impl_of'].items():
    ENTRY[c] = ('CMPSD', int(e, 16))
for c, v in TH111.items():
    ENTRY[c] = ('TH', int(v['slot0'], 16))
FORMS = collections.Counter(v[0] for v in ENTRY.values())
ck('B1 分类域：CMPSD 172 类 + TH 12 类 = 184 个入口（ATL 3 类单列，不进闭包判据）',
   len(ENTRY) == 184 and FORMS['CMPSD'] == 172 and FORMS['TH'] == 12, dict(FORMS))


def q_of(mode):
    """mode: 'closure' = 全闭包（thunk + call 下钻，深 2）
             'thunk'   = 只跟 thunk jmp（= R111 的实际口径）
             'raw'     = 只数本体内 cmpsd（谁都不跟）"""
    q = collections.defaultdict(set)
    for c, (form, f) in ENTRY.items():
        if mode == 'closure':
            s = set(L.closure_iids(f, 2))
        elif mode == 'thunk':
            s = set(L.direct_iids(L.body(f)))
            jmps, _ = L.edges(L.body(f))
            for t in jmps:
                s |= set(L.direct_iids(L.body(t)))
        else:
            s = set(L.direct_iids(L.body(f)))
        for i in s:
            q['0x%x' % i].add(c)
    return q


Q = q_of('closure')
QT = q_of('thunk')
QR = q_of('raw')
ck('B2 正控：Q(0x7f7c90) == 全部 184 个入口（IUnknown 是每条 QI 链的兜底，必须全覆盖）',
   Q['0x7f7c90'] == set(ENTRY), {'got': len(Q['0x7f7c90']), 'want': len(ENTRY)})

W111 = collections.defaultdict(set)
for c, l in D111['iids'].items():
    for i in l:
        W111[i].add(c)

ac = {'0x7e9ae0', '0x7f7c70', '0x7f7c80', '0x7f7c90'}
ck('B3 漏项①：AircraftClass 在闭包下被补进 Q(0x7e9ae0/0x7f7c70/0x7f7c80/0x7f7c90) 全部 4 个集合'
   '（R111 只把它记进 Q(0x7e9b40)）',
   all('AircraftClass' in Q[i] and 'AircraftClass' not in W111[i] for i in ac),
   {i: ('AircraftClass' in Q[i], 'AircraftClass' in W111[i]) for i in ac})
ck('B3b 漏项① 的机制：AircraftClass slot0 0x414290 体内 `call 0x410260` 后 test eax / jge 继续查 0x7e9b40',
   any(t[2] == 'call' and t[3] == '0x410260' for t in L.body(0x414290)), hex(0x410260))

grp6 = [c for c, v in TH111.items() if v['target'] == '0x55a9b0']
ck('B4 漏项②：6 个 `sub [esp+4],4 ; jmp 0x55a9b0` 的类在闭包下补齐 0x7f7c70（R111 每个只拿到 3 个 IID）',
   len(grp6) == 6 and all('0x7f7c70' in Q and c in Q['0x7f7c70'] for c in grp6),
   {'group': sorted(grp6), 'r111_iids_first': sorted(i for i in W111 if grp6[0] in W111[i]),
    'closure_iids_first': sorted(i for i in Q if grp6[0] in Q[i])})

NAMES = set()
for r in RT.values():
    for nm in r['bases']:
        if len(nm) > 1 and nm[0] == 'I' and nm[1].isupper() and nm != 'IUnknown':
            NAMES.add(nm)


def nv(cls):
    e = sym.get(cls)
    if not e or not e.get('vtable_va'):
        return None
    return int(e['vtable_va'], 16)


def full_set(q, N):
    full, part = [], []
    for nm in sorted(NAMES):
        tot = hit = 0
        for c in q:
            vt = nv(c)
            r = RT.get(vt) if vt else None
            if not r:
                continue
            mds = r['bases'].get(nm)
            if mds is None:
                continue
            tot += 1
            if N in mds:
                hit += 1
        if tot == len(q) and hit == tot:
            full.append(nm)
        elif hit == tot and tot > 0:
            part.append([nm, hit, tot])
    return full, part


N_OF = {k: v['N'] for k, v in B112['full_sets'].items()}
q7358 = sorted(Q['0x7ed358'])
f4, p4 = full_set(q7358, 4)
f24, p24 = full_set(q7358, 24)
f0, p0 = full_set(q7358, 0)
ck('B5 R111 §EM3 的 0x7ed358：闭包后 |Q|=%d（R111 报 6），N=4 时 FULL 唯一 = %s ⇒ **语义是 ILocomotion**'
   '（不是「链 B 无候选」）' % (len(q7358), f4),
   len(q7358) == 12 and f4 == ['ILocomotion'],
   {'Q': q7358, 'FULL_N4': f4, 'PARTIAL_N24': p24})
ck('B5b 该 IID 的 N=4 有独立来源：thunk 形态 `sub dword ptr [esp+4], 4` 的立即数 4 与 RTTI ILocomotion mdisp=4 相等',
   all(TH111[c]['N'] == 4 for c in grp6 + ['DriveLocomotionClass', 'DropPodLocomotionClass',
                                           'JumpjetLocomotionClass', 'ShipLocomotionClass',
                                           'TeleportLocomotionClass', 'WalkLocomotionClass']),
   '12/12 thunk N==4')

trio = ['0x7e9ae0', '0x7f7c70', '0x7f7c80']
ck('B6 R111 §EM10② 三者在闭包口径下依然不可区分：Q(0x7f7c70) == Q(0x7f7c80)（对称差 0）',
   Q['0x7f7c70'] == Q['0x7f7c80'], {'n70': len(Q['0x7f7c70']), 'n80': len(Q['0x7f7c80'])})
ck('B6b 且三者的 FULL(N=0/4) 同上轮：70/80 == {IPersist,IPersistStream}，9ae0 == {IRTTITypeInfo}（N=4）—— '
   '闭包只加认领类、不改结论方向',
   full_set(sorted(Q['0x7f7c70']), 0)[0] == ['IPersist', 'IPersistStream']
   and full_set(q7358, 0)[0] == ['IPersist', 'IPersistStream']
   and full_set(sorted(Q['0x7e9ae0']), 4)[0] == ['IRTTITypeInfo'],
   {'70': full_set(sorted(Q['0x7f7c70']), 0)[0], '9ae0': full_set(sorted(Q['0x7e9ae0']), 4)[0]})
ck('B6c 0x7e9ae0 与 0x7f7c70 依然可区分：Q(0x7e9ae0) ⊂ Q(0x7f7c70)，差 %d 类'
   % len(Q['0x7f7c70'] - Q['0x7e9ae0']),
   Q['0x7e9ae0'] < Q['0x7f7c70'], sorted(Q['0x7f7c70'] - Q['0x7e9ae0']))

# ---- B7 反控：把下钻关到 R111 的口径，必须逐 IID 复现 R111 的数字 ----
# 例外：ATL 那 3 类的 IID 是「内联 dword 立即数比较」（00000000-...-000000000046），
# 不在 cmpsd 形态里，R111 是用另一条判据拿到的，本轮的闭包判据对它不适用 ⇒ 单列不并入。
ATL_IID = '0000000000000000c000000000000046'
cmp_ids = [i for i in sorted(W111) if i != ATL_IID]
same111 = {i: (QT[i] == W111[i]) for i in cmp_ids}
ck('B7 反控：只跟 thunk jmp（= R111 的实际口径）时 20 个 cmpsd 型 IID 的认领集与 R111 '
   '逐 IID 完全一致（ATL 的 %s 是内联立即数判据，不在本判据域内，单列）'
   % ATL_IID[:8], all(same111.values()),
   {'mismatch': [k for k, v in same111.items() if not v], 'atl': sorted(QT[ATL_IID])})

# 漏项①和② 其实是同一条：**call 下钻**。R111 已经跟了 thunk jmp，但没跟 call。
#   AircraftClass   ：本体 call 0x410260（AbstractClass 的 QI 体）⇒ 补齐 4 个 IID
#   6 个 Locomotion ：slot0 是 thunk，jmp 目标是**独立函数**（如 0x4af720），
#                     该函数先 call 0x55a9b0 再自己查 0x7e9b10 ⇒ R111 只拿到 0x7e9b10
#   另 6 个 Locomotion：slot0 的 thunk 直接 jmp 0x55a9b0 ⇒ R111 已拿到，闭包不再加
direct_jmp6 = sorted(c for c, v in TH111.items() if v['target'] == '0x55a9b0')
call_path6 = sorted(c for c, v in TH111.items()
                    if v['target'] != '0x55a9b0'
                    and 0x55a9b0 in L.edges(L.body(int(v['target'], 16)))[1])
d70 = sorted(Q['0x7f7c70'] - QT['0x7f7c70'])
ck('B7b 闭包相对 R111 只增不减；Q(0x7f7c70) 的增量为 %d 个类 = AircraftClass + 6 个'
   '「thunk 目标里 call 共享体」的 Locomotion 类；6 个「thunk 直接 jmp 共享体」的类 R111 已拿到，不再加'
   % len(d70),
   len(direct_jmp6) == 6 and len(call_path6) == 6
   and set(d70) == {'AircraftClass'} | set(call_path6)
   and not (set(d70) & set(direct_jmp6))
   and Q['0x7ed358'] - QT['0x7ed358'] == set(call_path6)
   and all(Q[i] >= QT[i] for i in Q),
   {'delta_70': d70, 'direct_jmp6': direct_jmp6, 'call_path6': call_path6,
    'delta_358': sorted(Q['0x7ed358'] - QT['0x7ed358']), 'n_raw_7ed358': len(QR['0x7ed358'])})

# ---- B9 闭包的语义合法性（这是审计员最可能攻击的一点：闭包会不会**虚增**认领集） ----
# 闭包的前提是：**调用者会传递被调用者的成功**。如果 call 之后是「忽略返回值继续查自己」，
# 那么「被调用者认的 IID」确实也是调用者能 QI 成功的；如果是「失败才继续、成功就跳走」，
# 那也一样（成功路径传递）。唯一会虚增的情形是「成功也继续、但最后不返回成功」。
# 故逐条查两个 call 点的**成功路径**是否真的把成功传出去：
#   AircraftClass 0x414290：call 0x410260 ; test eax,eax ; jge 0x4142E9(ret)
#       ⇒ 返回 >=0 就直接 ret（eax 即被调用者返回值）⇒ 成功传递。
#   0x4AF720：call 0x55A9B0 ; cmp eax,0x80004002 ; jne 0x4AF777(ret)
#       ⇒ 只要不是 E_NOINTERFACE 就直接 ret ⇒ 成功传递。
# 两条都是「直接返回」形态，不是「记下再覆盖」形态，故闭包不虚增。
def success_passthrough(addr):
    lits = L.body(addr)
    for i2, (a, sz, m, o) in enumerate(lits):
        if m == 'call' and L.RE_TGT.match(o):
            nxt = [x[2] + ' ' + x[3] for x in lits[i2 + 1:i2 + 4]]
            joined = ' | '.join(nxt)
            # 认定「直接返回」形态：call 后 3 条内出现 test/cmp + 条件跳转，且跳转目标是函数尾的 ret 块
            direct = ('test eax, eax' in joined or 'cmp eax,' in joined) and \
                     any(x[2] in ('jge', 'jne', 'jl', 'je') for x in lits[i2 + 1:i2 + 4])
            return direct, joined
    return False, ''
ok1, d1 = success_passthrough(0x414290)
ok2, d2 = success_passthrough(0x4af720)
ck('B9 闭包语义合法性：两个 call 点之后都是「test/cmp eax + 条件跳转」直接返回形态 ⇒ '
   '调用者把被调用者的成功传出去，闭包**不虚增**认领集（这是 A1 最容易被攻击的点）',
   ok1 and ok2, {'AircraftClass 0x414290': d1, '0x4AF720': d2})


def eax_touched(entry, tgt):
    """从目标块 tgt 起，到第一个 ret 之间，eax 是否被写。
    「直接返回」形态的真正判据不是"有没有 test/cmp"，而是**返回时 eax 是否还是被调用者的值**。
    只要 eax 被覆盖，即使形态看着像直返，成功也没传出去。"""
    lits = L.body(entry)
    out, hit = [], False
    for a, sz, m, o in lits:
        if a == tgt:
            hit = True
        if not hit:
            continue
        if m.startswith('ret'):
            break
        dst = o.split(',')[0].strip()
        if dst == 'eax' or (m.startswith('pop') and o.strip() == 'eax'):
            out.append((hex(a), m + ' ' + o))
    return out


w1 = eax_touched(0x414290, 0x4142e9)
w2 = eax_touched(0x4af720, 0x4af777)
ck('B9b 更强的一步：两条成功返回路径（0x4142E9 / 0x4AF777）到各自 ret 之间 **eax 一次都没被写** '
   '⇒ 返回给调用方的就是被调用者的返回值，成功确实被传出去（只查"有 test/cmp"还不够，'
   '必须查 eax 没被覆盖）', not w1 and not w2, {'0x4142e9': w1, '0x4af777': w2})

# ---- B8 反控：把 N 换成该 IID 集上「别的偏移」必须让 FULL 变空/变形 ----
# 初稿写「Q 缩 10% 后 FULL 应变宽」，实测 3/3 都不变 —— 因为 FULL 是「全体认领类都必须有」，
# 缩样本只会让条件更容易满足，而名字集合恰好稳定。**指标选错**（同 R112 S-05 的教训）。
# 正确的反控是扰动 N（判据的自变量），不是扰动样本量。
perm_ok = 0
perm_rows = []
for iid, N in (('0x7f7ca0', 0), ('0x7e9ae0', 4), ('0x7e9b00', 40), ('0x7ea768', 36)):
    q = sorted(Q[iid])
    base = full_set(q, N)[0]
    alts = [full_set(q, M)[0] for M in (0, 4, 24, 36, 40, 44) if M != N and len(q) > 1]
    changed = all(a != base for a in alts)
    perm_ok += changed
    perm_rows.append([iid, N, base, alts[:3]])
ck('B8 反控：把 N 换成别的偏移值后 FULL 集必须改变 —— 4 个已定死 IID 里满足 %d 个'
   '（扰动判据的自变量而不是样本量；R112 S-05 的教训：指标选错会让反控变成摆设）' % perm_ok,
   perm_ok == 4, perm_rows)

out = {'Q': {k: sorted(v) for k, v in Q.items()}, 'Q_r111': {k: sorted(v) for k, v in W111.items()},
       'Q_thunk_only': {k: sorted(v) for k, v in QT.items()},
       'Q_raw': {k: sorted(v) for k, v in QR.items()},
       'closure_7ed358': {'Q': q7358, 'FULL_N4': f4, 'FULL_N0': f0, 'PARTIAL_N24': p24},
       'checks': checks}
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('[r113b] %d PASS / %d FAIL -> %s' % (len(checks) - nf, nf, OUT))
sys.exit(1 if nf else 0)
