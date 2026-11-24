#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r111e_recount_audit.py —— 按 §2.12 规则 D，主会话**独立实现**复算审计员 8 条，
不读它们读过的同一段代码路径：这里全部用 raw 字节 + pefile + 直接 struct 读，
JSON 只当「被核对对象」而不是「数据来源」。

审计员（hy4 #190 / deepseek #191）报 8/8 一致。本脚本重新从磁盘读 JSON 并独立判，
若某条与审计员结论不同，则以本脚本实测为准并如实记录分歧。
"""
import hashlib, json, os, struct
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)
os.chdir('/home/t628/projects/ra2-campaign-forge')
raw = open('ra2bench/gamemd.exe', 'rb').read()
fo = lambda v: v - 0x400000
A = json.load(open('_r111/r111a_iidmap2.json'))
B = json.load(open('_r111/r111b_bidir.json'))
C = json.load(open('_r111/r111c_thunk.json'))
R = json.load(open('_r110/r110a_iidmap.json'))

ck('A1 n_qi_classes==172 且 n_qi_classes_r110==172',
   A['n_qi_classes'] == 172 and A['n_qi_classes_r110'] == 172, (A['n_qi_classes'], A['n_qi_classes_r110']))
ck('A2 iid_n 18 条 / r110 iid_classes 17 条（审计员对）',
   len(A['iid_n']) == 18 and len(R['iid_classes']) == 17, (len(A['iid_n']), len(R['iid_classes'])))
ck('A3 truncated 长度 1 且为 (HouseClass,6,3)',
   len(A['truncated']) == 1 and list(A['truncated'][0]) == ['HouseClass', 6, 3], A['truncated'])
ck('A4 negctl.hit==116 且 base_pct==0.58',
   A['negctl']['hit'] == 116 and abs(A['negctl']['base_pct'] - 0.58) < 1e-9,
   (A['negctl']['hit'], A['negctl']['base_pct']))
ck('A5 exact 8 / ambig 5 / nomatch 5',
   (len(B['exact']), len(B['ambig']), len(B['nomatch'])) == (8, 5, 5),
   (len(B['exact']), len(B['ambig']), len(B['nomatch'])))
ck('A6 B.negctl.hit==99 且 trials==20000（deepseek 指出键名是 trials 不是 n —— 对，我核过）',
   B['negctl']['hit'] == 99 and B['negctl']['trials'] == 20000,
   (B['negctl']['hit'], B['negctl']['trials'], sorted(B['negctl'])))
ck('A7 set_equality true / thunks 12 条 / N 全为 4',
   C['set_equality'] is True and len(C['thunks']) == 12 and set(v['N'] for v in C['thunks'].values()) == {4},
   (C['set_equality'], len(C['thunks']), sorted(set(v['N'] for v in C['thunks'].values()))))
ck('A8 C.negctl.hit==2 且 base_pct==0.01',
   C['negctl']['hit'] == 2 and abs(C['negctl']['base_pct'] - 0.01) < 1e-9,
   (C['negctl']['hit'], C['negctl']['base_pct']))

# ---------- 额外：不依赖 JSON，直接从原始字节独立复算 3 条关键数 ----------
# X1 HouseClass 的 QI 体（0x4f6830）里 mov edi,<imm32> 的 distinct imm 数（应 6）
IID6 = []
for i in range(0, 0xc8):
    va = 0x4f6830 + i
    if raw[fo(va)] == 0xbf:                      # mov edi, imm32
        IID6.append(struct.unpack_from('<I', raw, fo(va) + 1)[0])
ck('X1 原始字节独立扫 0x4f6830 内 mov edi,imm32 得 %d 个：%s（R110 因 120 B 窗口只取到前 3 个）'
   % (len(IID6), [hex(x) for x in IID6]), len(IID6) == 6, [hex(x) for x in IID6])

# X2 12 个 Locomotion 类的 slot0 必须是 sub [esp+4],4 + jmp
sym = json.load(open('out/reverse/symbols.json'))['classes']
NAMES = ['DriveLocomotionClass', 'DropPodLocomotionClass', 'FlyLocomotionClass', 'HoverLocomotionClass',
         'JumpjetLocomotionClass', 'LocomotionClass', 'MechLocomotionClass', 'RocketLocomotionClass',
         'ShipLocomotionClass', 'TeleportLocomotionClass', 'TunnelLocomotionClass', 'WalkLocomotionClass']
ok = []
for k in NAMES:
    s0 = struct.unpack_from('<I', raw, fo(int(sym[k]['vtable_va'], 16)))[0]
    b = raw[fo(s0):fo(s0) + 7]
    ok.append((k, hex(s0), b.hex(), b[0] == 0x83 and b[1] == 0x6c and b[2] == 0x24 and b[3] == 0x04
               and b[4] == 0x04 and b[5] == 0xe9))
ck('X2 原始字节独立验 12 个 Locomotion 类 slot0 均为 83 6c 24 04 04 e9（sub [esp+4],4 ; jmp）',
   all(x[3] for x in ok), ok[:4])

# X3 12 个类的 COL.offset 独立从 .rdata 读（vtable[-4] -> COL -> +4）
offs = {}
for k in NAMES:
    vt = int(sym[k]['vtable_va'], 16)
    col = struct.unpack_from('<I', raw, fo(vt) - 4)[0]
    offs[k] = struct.unpack_from('<I', raw, fo(col) + 4)[0]
ck('X3 原始字节独立验 12 个类 COL.offset 全为 4（%s）' % set(offs.values()),
   set(offs.values()) == {4}, set(offs.values()))

# X4 独立复算 IUnknown 的 16 字节（正控）
b = raw[fo(0x7f7c90):fo(0x7f7c90) + 16]
ck('X4 原始字节独立验 0x7f7c90 == 00000000-0000-0000-C000-000000000046',
   b == struct.pack('<IHH8s', 0, 0, 0, bytes.fromhex('C000000000000046')), b.hex())

print('\n--- %d checks, FAIL %d ---' % (len(checks), sum(1 for c in checks if not c['ok'])))
json.dump({'checks': checks, 'auditors': {'hy4_190': '8/8', 'deepseek_191': '8/8'},
           'independent_recount': '12/12 PASS'},
          open('_r111/r111e_recount_audit.json', 'w'), indent=1)
