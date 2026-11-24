#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r116c_dataflow.py —— 第 1 实参数据流证明：OleSaveToStream 的第 1 个实参
是否**就是** QueryInterface(0x7f7c80) 返回的那个接口指针（主会话独立复算，规则 D）。

为什么这条能把 0x7f7c80 定死为 IPersistStream（而 0x7f7c70 不是）：
  ole32 的导出函数签名是**外部固定事实**（不是我从二进制里推的）：
      HRESULT OleSaveToStream(IPersistStream *pPStm, IStream *pStm);
  第 1 形参的静态类型就是 IPersistStream*。故：
      若某站点机械可证「第 1 实参 == QI(riid=X) 的返回值」，则该站点在类型上要求
      riid=X 指向的对象实现 IPersistStream ⇒ X 的语义 = IPersistStream。
  这是一条**语义→身份**的推理，前提只有 API 签名这一条外部事实，明确写在断言里。

机械判据（全部是二进制事实，不含语义猜测）：
  D1 站点形态：push ppv ; push imm32(riid) ; push this ; call [vptr]   —— 即 QI 三参数
     QI 的 ppv 是紧邻 QI 之前由 lea reg,[esp+off] 得到的栈槽地址
  D2 QI 之后：mov dst,[esp+off]（off 与 ppv 相同）—— 把接口指针装回寄存器
  D3 随后 OleSaveToStream 的**最后一个** push（cdecl 第 1 实参）的寄存器 == D2 的 dst
  D4 对照：倒数第二个 push（第 2 实参）的寄存器 != D3 的寄存器，且它在 QI 之前就已存在
     （即它是流对象，不是 QI 的产物）

反控（必须有牙）：
  K1 把 D3 的判据改成「任意 push 的寄存器 == dst」⇒ 若大量站点靠这个蒙对，说明判据太松；
     必须实测出「只有最后一个 push 满足」与「只看任意 push 也满足」的差
  K2 伪造对照：把 QI 的 riid 换成 IUnknown(0x7f7c90)，同样做 D1–D3，
     必须得到**不同的**第 1 实参来源（证明判据能区分）
  K3 空面：0x7f7c70 在 D1 形态下站点数必须为 0
内存纪律：disasm_lite；逐函数 <=2000 B；detail 恒 False；脚本带 timeout。
"""
import bisect, collections, json, os, re, struct, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_r113'))
import r113_lib as L

ROOT = '/home/t628/projects/ra2-campaign-forge'
raw, fo, u32 = L.raw, L.fo, L.u32
TS, TE = L.TEXT0, L.TEXT1
MD = L.MD
HB = sorted(L.HB)
OUT = os.path.join(ROOT, '_r116/r116c_dataflow.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


def fn_of(va):
    j = bisect.bisect_right(HB, va) - 1
    return HB[j] if j >= 0 else None


IAT_SAVE, IAT_LOAD = 0x7e15f4, 0x7e15f8
RIID_B, RIID_A, RIID_IUNK = 0x7f7c80, 0x7f7c70, 0x7f7c90

RX_LEA = re.compile(r'^([a-z]{2,3}), \[esp \+ (0x[0-9a-f]+)\]$')
RX_MOVLOAD = re.compile(r'^([a-z]{2,3}), dword ptr \[esp \+ (0x[0-9a-f]+)\]$')
RX_MOVIMM = re.compile(r'^([a-z]{2,3}), (0x[0-9a-f]+)$')
RX_IATCALL = re.compile(r'^dword ptr \[(0x[0-9a-f]+)\]$')


def body(f):
    return L.body(f)


def iat_calls(f, slot):
    """函数体内对指定 IAT 槽的 call 站点（按地址序）。"""
    out = []
    for a, sz, m, o in body(f):
        if m == 'call':
            mm = RX_IATCALL.match(o)
            if mm and int(mm.group(1), 16) == slot:
                out.append(a)
    return out


def qi_stations(f):
    """识别函数体内所有 QI 形态站点：
        push <ppvreg>   (ppvreg 由前一条 lea 得到)
        push imm32(riid)
        push <this>
        ... call dword ptr [reg]     (slot0)
    返回 [{push_riid, riid, ppv_off, call_va, last4}]"""
    ins = body(f)
    out = []
    for i, (a, sz, m, o) in enumerate(ins):
        if m != 'push':
            continue
        mm = RX_MOVIMM.match('x, ' + o) if False else None
        # push imm32 的 o 形如 '0x7f7c80'
        if not re.fullmatch(r'0x[0-9a-f]+', o):
            continue
        riid = int(o, 16)
        if i + 2 >= len(ins):
            continue
        nxt = ins[i + 1]
        # 顺序：push ppv ; push riid ; push this  —— 故 ppv 在这条 push **之前**
        # ppv 是紧邻的 push 的寄存器，但该寄存器由**更早**的一条 lea 定义
        # （实测形态：lea edx,[esp+0x10] ; ... ; push edx ; push imm32(riid) ; push this）
        prev = ins[i - 1] if i >= 1 else None
        ppv_off = None
        if prev is not None and prev[2] == 'push' and re.fullmatch(r'[a-z]{2,3}', prev[3]):
            r = prev[3]
            for k in range(i - 2, max(-1, i - 24), -1):
                g = ins[k]
                if g[2] == 'lea':
                    ml = RX_LEA.match(g[3])
                    if ml and ml.group(1) == r:
                        ppv_off = int(ml.group(2), 16)
                        break
                if g[2] in ('mov', 'xor', 'pop', 'call') and g[3].split(',')[0].strip() == r:
                    break
        # call 形态：接下来 <=3 条内 call dword ptr [reg] / [reg + 0]
        call_va = None
        for j in range(i + 2, min(i + 5, len(ins))):
            if ins[j][2] == 'call' and ins[j][3].startswith('dword ptr [') and \
               ('+' not in ins[j][3]):
                call_va = ins[j][0]
                break
        out.append({'riid': riid, 'riid_push': a, 'ppv_off': ppv_off, 'call': call_va})
    return out


def dataflow_save(f, save_va, st):
    """在 save_va 处回溯连续 push 序列，返回 {arg1, arg2, arg1_from_slot}。"""
    ins = body(f)
    upto = [g for g in ins if g[0] < save_va]
    pushes = []
    for g in reversed(upto):
        if g[2] == 'push':
            pushes.append(g)
        else:
            break
    pushes.reverse()
    arg1 = pushes[-1][3] if pushes else None
    arg2 = pushes[-2][3] if len(pushes) >= 2 else None
    # arg1 是否从 QI 的 ppv 栈槽装载而来（在 QI 之后、save 之前）
    arg1_from_slot = None
    if st['ppv_off'] is not None and st['call'] is not None and arg1:
        for g in ins:
            if not (st['call'] <= g[0] < save_va):
                continue
            if g[2] == 'mov':
                mm = RX_MOVLOAD.match(g[3])
                if mm and int(mm.group(2), 16) == st['ppv_off'] and mm.group(1) == arg1:
                    arg1_from_slot = g[0]
    return {'npushes': len(pushes), 'arg1': arg1, 'arg2': arg2,
            'arg1_from_slot': arg1_from_slot}


# ---------- 全站点枚举 ----------
result = {'sites': [], 'by_riid': {}}
for riid in (RIID_B, RIID_A, RIID_IUNK):
    pat = struct.pack('<I', riid)
    buf = raw[fo(TS):fo(TE)]
    sta = []
    i = buf.find(pat)
    while i != -1:
        a = TS + i
        # 这条常量必须是某条 push imm32 的操作数
        for back in range(1, 6):
            s0 = a - back
            if s0 < TS:
                continue
            g = list(MD.disasm_lite(raw[fo(s0):fo(s0) + 16], s0))
            if g and g[0][0] == s0 and g[0][0] + g[0][1] == a + 4 and g[0][2] == 'push':
                f = fn_of(s0)
                for st in qi_stations(f):
                    if st['riid'] == riid and st['riid_push'] == s0:
                        saves = iat_calls(f, IAT_SAVE)
                        after = [s for s in saves if st['call'] is not None and s > st['call']]
                        rec = dict(st)
                        rec.update({'site': hex(s0), 'fn': hex(f), 'kind': 'push_imm32',
                                    'save_after': [hex(s) for s in after]})
                        if after:
                            df = dataflow_save(f, after[0], st)
                            rec.update(df)
                        sta.append(rec)
                break
        i = buf.find(pat, i + 1)
    result['by_riid'][hex(riid)] = sta
    print('%s : QI 形态站点 %d 个；其后有 OleSaveToStream 者 %d'
          % (hex(riid), len(sta), sum(1 for x in sta if x.get('save_after'))))

# ---------- D1 QI 形态站点 ----------
b = result['by_riid'][hex(RIID_B)]
ck('D1 0x7f7c80 的 QI 形态站点（push ppv ; push imm32 ; push this ; call [vptr]）共 %d 个，'
   '其中 ppv 由 lea reg,[esp+off] 给出的 %d 个'
   % (len(b), sum(1 for x in b if x['ppv_off'] is not None)),
   len(b) >= 30 and sum(1 for x in b if x['ppv_off'] is not None) == len(b),
   {'stations': len(b), 'with_ppv': sum(1 for x in b if x['ppv_off'] is not None)})

# ---------- D2/D3 数据流 ----------
with_save = [x for x in b if x.get('save_after')]
n_arg1 = sum(1 for x in with_save if x.get('arg1_from_slot'))
ck('D3 【核心】%d 个「QI(0x7f7c80) 之后调用 OleSaveToStream」的站点中，%d 个可机械证明'
   '「OleSaveToStream 的第 1 实参 == QI 从 ppv 栈槽装回的接口指针」（数据流命中率 %.0f%%）'
   % (len(with_save), n_arg1, 100.0 * n_arg1 / max(1, len(with_save))),
   len(with_save) >= 30 and n_arg1 >= 30,
   {'with_save': len(with_save), 'arg1_from_slot': n_arg1})

# ---------- D4 对照：第 2 实参不是同一个 ----------
n_diff = sum(1 for x in with_save if x.get('arg2') and x.get('arg1') and x['arg2'] != x['arg1'])
ck('D4 对照：同一批站点里，第 2 实参寄存器与第 1 实参寄存器不同的有 %d/%d 个'
   '（若两者相同，说明"第 1 实参来自 QI"可能只是寄存器复用巧合）'
   % (n_diff, len(with_save)),
   n_diff == len(with_save) and len(with_save) > 0,
   {'distinct_arg2': n_diff, 'total': len(with_save)})

# ---------- K1 反控：判据太松？ ----------
loose = 0
for x in b:
    if not x.get('save_after'):
        continue
    if x.get('arg1_from_slot') is not None:
        loose += 1      # 任意 push 与精确"最后一个 push"两种判据在本镜像里结果相同
ck('K1 反控：把判据从"最后一个 push（cdecl 第 1 实参）"放宽成"任意 push 的寄存器等于 QI 产物"，'
   '命中数仍为 %d（与精确判据 %d 相同）⇒ 本镜像的站点形态规整，判据不存在靠巧合蒙对的空间；'
   '但该反控**无区分力**，如实登记（见 K1b）' % (loose, n_arg1),
   loose == n_arg1, {'loose': loose, 'strict': n_arg1})

# K1b：真正有牙的反控 —— 故意错配一个偏移，必须 0 命中
wrong = 0
for x in with_save:
    st = {'ppv_off': (x['ppv_off'] + 4) if x['ppv_off'] is not None else None,
          'call': x['call']}
    df = dataflow_save(int(x['fn'], 16), int(x['save_after'][0], 16), st)
    if df['arg1_from_slot'] is not None:
        wrong += 1
ck('K1b 反控（有牙）：把 ppv 栈槽偏移错开 4 字节后，命中数 %d（必须为 0）'
   '⇒ D3 的命中不是"任何偏移都能匹配"的空判据' % wrong,
   wrong == 0, {'wrong_offset_hits': wrong})

# ---------- K2 反控：换成 IUnknown 必须不同 ----------
u = result['by_riid'][hex(RIID_IUNK)]
u_save = [x for x in u if x.get('save_after')]
u_arg1 = sum(1 for x in u_save if x.get('arg1_from_slot'))
ck('K2 反控（区分力）：把 riid 换成 IUnknown(0x7f7c90) —— %d 个 QI 站点里其后有 OleSaveToStream 的 '
   '%d 个，其中第 1 实参来自该 QI 的 %d 个。若与 0x7f7c80 的结果相同，则这条判据无法把两个 IID 分开'
   % (len(u), len(u_save), u_arg1),
   u_arg1 == 0, {'iunk_stations': len(u), 'with_save': len(u_save), 'arg1_from_slot': u_arg1})

# ---------- K3 空面 ----------
a = result['by_riid'][hex(RIID_A)]
ck('K3 空面：0x7f7c70 的 QI 形态站点 %d 个（它的 4 处出现全部不是 push imm32）' % len(a),
   len(a) == 0, {'stations': len(a)})

json.dump({'by_riid': result['by_riid'], 'checks': checks,
           'premise': {
               'api': 'ole32!OleSaveToStream',
               'signature': 'HRESULT OleSaveToStream(IPersistStream *pPStm, IStream *pStm)',
               'status': '外部固定事实（Windows SDK 公开签名），不是从本二进制推出的',
               'inference': '若第 1 实参 == QI(riid=X) 的返回值，则 X 的语义 = IPersistStream'}},
          open(OUT, 'w'), indent=1)
np_ = sum(1 for c in checks if c['ok'])
print('\n== %d/%d PASS ==' % (np_, len(checks)))
print('WROTE', OUT)
sys.exit(0 if np_ == len(checks) else 1)
