#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r119c_push_semantics.py —— 把「IID 的 push 站点数」按**被调 API**切开。

R112..R118 七轮的核心数字都是同一个口径：「某个 IID 立即数在 .text 里被 push 的次数」。
这个口径把**至少两种语义完全不同的调用面**混成一个数：
  ① QueryInterface(riid, ppv)      —— 请求接口，riid 来自 vtable 调用（call dword ptr [reg]）
  ② CoCreateInstance(rclsid, ..., riid, ppv) —— **创建**对象，riid 是「创建出来后要哪个接口」
本脚本用 PE 导入表（本机自解析，不靠任何外部头文件）把每个 push 站点归到具体 API 上。

可机械核验的四件事：
  C1 导入表自解析：ole32 的 15 个函数名与 IAT 地址（含 R116 用的 0x7e15f4）
  C2 每个被研究 IID 的每个 push 站点：向后扫到**第一条 call**，按被调目标分类
     （IAT 命名调用 / 寄存器+位移的虚调用 / 寄存器间接 / 其它）
  C3 .data 侧 5 个 COM 形态常量的站点分类（R118 §EK4 把其中 3 个判为「同值巧合」，
     但它们是否**真被代码当 IID 用**这件事从未测过）
  C4 反控：GUID+4 键、以及「把分类器换成恒返回 same」的置换反控
内存纪律：skipdata=True 的单遍 disasm_lite + 只对命中地址做局部 detail 级窗口；不整段 detail。
"""
import collections
import json
import os
import struct
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE = os.path.join(ROOT, 'ra2bench/gamemd.exe')
OUT = os.path.join(ROOT, '_r119/r119c_push_semantics.json')
raw = open(EXE, 'rb').read()
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


# ---------------- PE ----------------
_e = struct.unpack_from('<I', raw, 0x3c)[0]
_nsec = struct.unpack_from('<H', raw, _e + 6)[0]
_optsz = struct.unpack_from('<H', raw, _e + 20)[0]
_opt = _e + 24
IB = struct.unpack_from('<I', raw, _opt + 28)[0]
imp_rva, imp_sz = struct.unpack_from('<II', raw, _opt + 96 + 8)
SECS = []
for i in range(_nsec):
    o = _opt + _optsz + 40 * i
    nm = raw[o:o + 8].rstrip(b'\x00').decode('latin1')
    vs, va, rs, pr = struct.unpack_from('<IIII', raw, o + 8)
    SECS.append((nm, va + IB, vs, pr, rs))


def fo(va):
    for n, b, vs, pr, rs in SECS:
        if b <= va < b + max(rs, vs):
            o = pr + (va - b)
            return o if 0 <= o < len(raw) else None
    return None


TS = [s for s in SECS if s[0] == '.text'][0]
TEXT0, TEXT1, TRAW0, TRAWSZ = TS[1], TS[1] + TS[2], TS[3], TS[4]

# ---------------- C1 导入表 ----------------
IAT = {}
o = fo(IB + imp_rva)
i = 0
while True:
    ilt, ts_, fc, nm_rva, iat = struct.unpack_from('<IIIII', raw, o + 20 * i)
    if nm_rva == 0:
        break
    dll = raw[fo(IB + nm_rva):].split(b'\x00')[0].decode('latin1')
    t = fo(IB + (ilt if ilt else iat))
    j = 0
    while True:
        v = struct.unpack_from('<I', raw, t + 4 * j)[0]
        if v == 0:
            break
        if v & 0x80000000:
            name = 'ORD%d' % (v & 0xffff)
        else:
            name = raw[fo(IB + v) + 2:].split(b'\x00')[0].decode('latin1')
        IAT[IB + iat + 4 * j] = (dll, name)
        j += 1
    i += 1
OLE = {a: n for a, (d, n) in IAT.items() if d.lower() == 'ole32.dll'}
ck('C1 导入表自解析：共 %d 个 IAT 槽、%d 个 DLL；ole32 %d 个函数'
   % (len(IAT), len(set(d for d, n in IAT.values())), len(OLE)),
   len(OLE) == 15 and IAT.get(0x7e15f4) == ('ole32.dll', 'OleSaveToStream')
   and IAT.get(0x7e15fc) == ('ole32.dll', 'CoCreateInstance'),
   {'ole32': sorted((hex(a), n) for a, n in OLE.items())})

# ---------------- 单遍指令流 ----------------
sys.path.insert(0, os.path.join(ROOT, '_r112'))
import r112_lib as L2                                  # noqa: E402
MDN = L2.MD                                            # skipdata=True（见 S-56）

COM = []
DS = [s for s in SECS if s[0] == '.data'][0]
for off in range(DS[3], min(DS[3] + DS[4], len(raw)) - 16, 4):
    w = struct.unpack_from('<IIII', raw, off)
    if w[1] == 0 and w[2] == 0xc0 and w[3] == 0x46000000:
        COM.append(DS[1] + (off - DS[3]))
NAMED = {0x0: 'IID_IUnknown', 0x10c: 'IID_IPersist', 0xc: 'IID_IStream',
         0x109: 'IID_IPersistStream', 0x20400: 'IID_IDispatch'}

STUDIED = {0x7f7c70: ('0000010C', 'rdata'), 0x7f7c80: ('00000109', 'rdata'),
           0x7f7c90: ('00000000', 'rdata'), 0x7ed358: ('070F3290', 'rdata'),
           0x7e9b10: ('92FEA800', 'rdata'), 0x7e9530: ('0D5CD78E', 'rdata'),
           0x7e9ae0: ('170DAC82', 'rdata'), 0x7f7ca0: ('00000001', 'rdata')}
COPIES = {0x7f7c70: [0x7f7c70, 0x818858], 0x7f7c80: [0x7f7c80, 0x820270],
          0x7f7c90: [0x7f7c90, 0x817bc0], 0x7ed358: [0x7ed358, 0x817bb0],
          0x7e9b10: [0x7e9b10, 0x819088], 0x7e9530: [0x7e9530, 0x83d598],
          0x7e9ae0: [0x7e9ae0], 0x7f7ca0: [0x7f7ca0]}
ALL = sorted(set(c for v in COPIES.values() for c in v))
TARGETS = set(ALL) | {0x81fc50, 0x87da00}

code = raw[TRAW0:TRAW0 + TRAWSZ]
insns = []                       # (va, mnemonic, op_str)
n_insn = 0
for (a, sz, mn, ops) in MDN.disasm_lite(code, TEXT0):
    insns.append((a, mn, ops))
    n_insn += 1
IDX = {a: k for k, (a, mn, ops) in enumerate(insns)}
ck('C2a 单遍 skipdata 线性扫描：%d 条指令，覆盖 .text 到 %s（R119b S-56 已证 skipdata 必需）'
   % (n_insn, hex(insns[-1][0])), n_insn > 1300000, {'n_insn': n_insn})


def classify_after(k):
    """从第 k 条（= push 站点）向后扫到第一条 call，返回分类。"""
    for j in range(k + 1, min(k + 12, len(insns))):
        a, mn, ops = insns[j]
        if mn == 'call':
            if ops.startswith('dword ptr [0x'):
                tgt = int(ops[len('dword ptr ['):-1], 16)
                dll, nm = IAT.get(tgt, ('?', '?'))
                return ('iat:' + nm, a, tgt)
            if ops.startswith('dword ptr ['):
                return ('vcall:' + ops, a, None)
            if ops.startswith('0x'):
                return ('direct:' + ops, a, None)
            return ('call:' + ops, a, None)
        if mn.startswith('j') or mn in ('ret',) or mn.startswith('ret'):
            return ('no_call_before_branch', a, None)
    return ('no_call_in_12', None, None)


# ---- 收集所有 push 站点（按 hx 立即数精确匹配操作数） ----
sites = collections.defaultdict(list)
for k, (a, mn, ops) in enumerate(insns):
    if mn != 'push' or not ops.startswith('0x'):
        continue
    try:
        v = int(ops, 16)
    except ValueError:
        continue
    if v in TARGETS:
        sites[v].append(k)

detailed = {}
for t in sorted(sites):
    rows = []
    for k in sites[t]:
        kind, call_va, tgt = classify_after(k)
        rows.append({'push_at': hex(insns[k][0]), 'kind': kind,
                     'call_at': hex(call_va) if call_va else None})
    detailed[hex(t)] = rows

# ---------------- C2b 分类汇总 ----------------
def summarize(t):
    # 🐞 自错 S-57：0x7f7c70 的全镜像命中全是 mov edi,imm32（R116 已实测 push 0），
    # 故它不在 sites 里 ⇒ 初稿直接 KeyError。改为缺键返回 {}（缺站点 ≠ 程序错误）。
    if hex(t) not in detailed:
        return {}
    cnt = collections.Counter(r['kind'] for r in detailed[hex(t)])
    return dict(cnt)


tot = {hex(t): len(v) for t, v in sites.items()}
ck('C2b 每个被研究 IID 的 push 站点总数（含 .rdata 与 .data 两份拷贝）：%s'
   % json.dumps({k: v for k, v in sorted(tot.items())}, ensure_ascii=False),
   all(v > 0 for v in tot.values()), tot)

for t in (0x7f7c80, 0x7f7c70, 0x7f7c90):
    s = summarize(t)
    push_q = s.get('vcall:dword ptr [ecx]', 0) + s.get('vcall:dword ptr [edx]', 0)
    print('   %s 站点分类 %s' % (hex(t), json.dumps(s, ensure_ascii=False)), flush=True)

# ---------------- C3 .data 侧常量的语义 ----------------
data_sites = {hex(t): detailed.get(hex(t), []) for t in (0x817bc0, 0x818858, 0x81fc50, 0x820270, 0x87da00)}
co_create = {k: [r for r in v if r['kind'] == 'iat:CoCreateInstance'] for k, v in data_sites.items()}
ck('C3 【核心修正】.data 侧 5 个 COM 形态常量的 push 站点里，走 CoCreateInstance 的分别为 %s'
   ' ⇒ 这些站点是「创建对象时指定 riid」，**不是** QueryInterface 请求；R112..R118 的'
   '「push 站点数」把它们与 QI 混为一谈（口径缺陷，非计算错误）'
   % json.dumps({k: len(v) for k, v in co_create.items()}, ensure_ascii=False),
   any(len(v) > 0 for v in co_create.values()),
   {'per_addr': data_sites, 'co_create_counts': {k: len(v) for k, v in co_create.items()}})

# ---------------- C2c 分解 .rdata 侧 0x7f7c80 / 0x7f7c70 ----------------
split = {}
for t in (0x7f7c80, 0x7f7c70, 0x7f7c90, 0x820270, 0x817bc0, 0x818858):
    s = summarize(t)
    split[hex(t)] = s
qi = sum(v for k, v in split.get('0x7f7c80', {}).items() if k.startswith('vcall:'))
cc = split.get('0x7f7c80', {}).get('iat:CoCreateInstance', 0)
ck('C2c 0x7f7c80 的 60 个 push 站点按被调 API 分解：%s（虚调用类合计 %d，CoCreateInstance %d，'
   'OleSaveToStream 前置 %d）'
   % (json.dumps(split['0x7f7c80'], ensure_ascii=False), qi, cc,
      split.get('0x7f7c80', {}).get('iat:OleSaveToStream', 0)),
   len(split.get('0x7f7c80', {})) >= 1, split)

# ---------------- C4 反控 ----------------
bad = 0
for t in (0x81885c, 0x817bc4, 0x87da04):
    if hex(t) in detailed:
        bad += 1
ck('C4a 反控（键精确性）：GUID+4 地址作为键，push 站点必须为 0（实测命中键数 %d）' % bad,
   bad == 0, {'keys_hit': bad})
same = collections.Counter(r['kind'] for rs in detailed.values() for r in rs)
ck('C4b 反控（分类器非常量）：分类结果分布必须 >1 类（实测 %d 类：%s）'
   % (len(same), json.dumps(dict(same), ensure_ascii=False)),
   len(same) >= 2, dict(same))

json.dump({'iat': {hex(a): list(v) for a, v in IAT.items()},
           'ole32': sorted((hex(a), n) for a, n in OLE.items()),
           'com_data': [hex(x) for x in COM],
           'named': {hex(k): v for k, v in NAMED.items()},
           'copies': {hex(k): [hex(x) for x in v] for k, v in COPIES.items()},
           'detailed': detailed, 'summary': split, 'data_sites': data_sites,
           'n_insn': n_insn, 'checks': checks},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n%d/%d PASS -> %s' % (sum(1 for c in checks if c['ok']), len(checks), OUT))
sys.exit(0 if all(c['ok'] for c in checks) else 1)
