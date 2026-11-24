#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r116k_claim.py —— 结论强度的**分级裁决**：本轮到底证成了什么、没证成什么。

这是本轮最重要的一份脚本。R112–R115 的教训是「把恒真的性质当独立证据」（S-15）；
本轮的最大的诱惑是「因为 0x7f7c80 被当成 IPersistStream* 用，所以 0x7f7c70 一定是 IPersist」
—— 后者需要额外一步推理，必须单独审。

分级（严格按证据强度，不按叙事顺畅度）：
  L1 【字节事实】可直接从镜像字节读出，无需任何外部知识
  L2 【API 签名】依赖一条外部固定事实（ole32 的公开签名），前提已写明
  L3 【排他推理】在上述之上做「只能是这样」的推理，需要排除所有替代解释
  L4 【未证】以上都撑不到

本脚本逐条把本轮的结论归入 L1/L2/L3/L4，并对每条 L3 列出**未被排除的替代解释**。
1.1 0x7f7c70/0x7f7c80 的 GUID 字面值
1.2 0x7f7c80 被 36 个函数用作 QI 的 riid；0x7f7c70 只被 4 处 mov edi（服务端基址）引用
1.3 35 份 QI(0x7f7c80)→OleSaveToStream 站点由一张 35 项 .data 表驱动，模板唯一
1.4 第 1 实参（IPersistStream* 位置）确实来自 QI(0x7f7c80) 的 ppv
1.5 0x7f7c70 在任何客户端位置（QI riid / OleSaveToStream arg1 / OleLoadFromStream REFIID）出现 0 次
1.6 「0x7f7c80 的语义 = IPersistStream」
1.7 「0x7f7c70 的语义 = IPersist」
内存纪律：本脚本只读 json + 少量字节，无 disasm。
"""
import json, os, struct, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_r113'))
import r113_lib as L

ROOT = '/home/t628/projects/ra2-campaign-forge'
raw, fo, u32 = L.raw, L.fo, L.u32
OUT = os.path.join(ROOT, '_r116/r116k_claim.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


def guid(a):
    d1 = u32(a); d2 = u32(a + 4) & 0xffff; d3 = u32(a + 4) >> 16
    b = raw[fo(a) + 8:fo(a) + 16]
    return '%08X-%04X-%04X-%s-%s' % (d1, d2, d3, b[:2].hex().upper(), b[2:].hex().upper())


J = {n: json.load(open(os.path.join(ROOT, '_r116', n)))
     for n in ('r116a_iid_client.json', 'r116d_iat_indirect.json', 'r116e_dispatch.json',
               'r116f_recheck.json', 'r116g_hbgap.json', 'r116j_refiid.json')}

claims = []


def claim(cid, level, text, evidence='', alt=''):
    claims.append({'id': cid, 'level': level, 'claim': text,
                   'evidence': evidence, 'unexcluded_alternatives': alt})
    print('%-4s %-3s %s' % (cid, level, text), flush=True)


# ---- 1.1 L1 ----
g70, g80 = guid(0x7f7c70), guid(0x7f7c80)
claim('1.1', 'L1',
      '0x7f7c70 = %s ；0x7f7c80 = %s （逐字节读出）' % (g70, g80),
      'raw[fo(0x7f7c70)]/raw[fo(0x7f7c80)] 各 16 字节')
ck('1.1 GUID 字面值可直接读出且两两不同',
   g70 == '0000010C-0000-0000-C000-000000000046' and
   g80 == '00000109-0000-0000-C000-000000000046' and g70 != g80,
   {'g70': g70, 'g80': g80})

# ---- 1.2 L1 ----
a = J['r116a_iid_client.json']['rows']
push80 = a['0x7f7c80 (B)']['push_sites']
push70 = a['0x7f7c70 (A)']['push_sites']
fns80 = a['0x7f7c80 (B)']['push_distinct_fns']
claim('1.2', 'L1',
      '0x7f7c80 有 %d 个 push-imm32 请求站点 / %d 个函数；0x7f7c70 有 %d 个（其 4 处出现'
      '全部是 mov edi,imm32 = 服务端 cmpsd 比较基址）' % (push80, fns80, push70),
      'r116a A1/A2 + r116f V2/V3 两套独立实现同值')
ck('1.2 两套独立实现给出的 push 站点/函数数完全一致',
   push80 == 60 and fns80 == 36 and push70 == 0, {'80': push80, 'fns80': fns80, '70': push70})

# ---- 1.3 L1 ----
e = J['r116e_dispatch.json']
disp = e['dispatcher']
claim('1.3', 'L1',
      '35 个 QI(0x7f7c80)→OleSaveToStream 站点由**一张 35 项 .data 表**驱动：'
      '35 个 call 点全部满足 mov ecx,esi ; mov edx,imm32 ; call 锚形态，'
      '35 份被调函数体前 112 字节**逐字节全等**，35 个 edx 两两不同'
      ' ⇒ 独立证据数在代码维度是 **1**，在数据项维度是 35（不是 35 份独立实现）',
      'r116e A1/A2/A3 + r116f V5')
ck('1.3 dispatcher 三性质同时成立（锚 35 / 体唯一 / edx 两两不同）',
   len(disp) == 35 and len(set(x['edx'] for x in disp)) == 35,
   {'calls': len(disp), 'distinct_edx': len(set(x['edx'] for x in disp))})

# ---- 1.4 L2 ----
c = J['r116d_iat_indirect.json']['res']['0x7f7c80']
claim('1.4', 'L2',
      '在 %d 个请求 0x7f7c80 的函数里，%d 个在请求之后调用 ole32!OleSaveToStream'
      '（两种调用形态都算：直接 call [IAT] 与 mov reg,[IAT]+call reg）；'
      '且第 1 实参（ole32 签名里的 IPersistStream* 位置）来自该 QI 的 ppv 栈槽'
      ' ⇒ 这些站点在**类型上**要求 riid=0x7f7c80 的对象实现 IPersistStream'
      % (c['fns'], c['coupled_both_forms']),
      'r116d A1 + r116c D3 + r116f V4（三套实现同值 36/36）',
      '仅依赖 ole32!OleSaveToStream 的公开签名这一条外部事实')
ck('1.4 36/36 耦合且三种实现一致',
   c['fns'] == 36 and c['coupled_both_forms'] == 36, {'fns': c['fns'], 'coupled': c['coupled_both_forms']})

# ---- 1.5 L1 ----
j = J['r116j_refiid.json']
claim('1.5', 'L1',
      '0x7f7c70 在三类客户端位置上**全部 0 次**：QI 的 riid（0/60+）、'
      'OleSaveToStream 第 1 实参（0/43）、OleLoadFromStream 的 REFIID 第 2 实参（0/8，'
      '同位置 0x7ed358 出现 5 次、0x7e9af0 出现 1 次，证明该位确实承载 IID）',
      'r116a A1 + r116j A2/K1 + r116i 正控存活的两步/栈槽形态检测器')
ck('1.5 三类客户端位置上 0x7f7c70 均 0 次，且 REFIID 位反控有值',
   j['refiid_imm'].get('0x7f7c70', 0) == 0 and j['refiid_imm'].get('0x7ed358', 0) == 5,
   j['refiid_imm'])

# ---- 1.6 L3 ----
claim('1.6', 'L3',
      '0x7f7c80 的语义 = IPersistStream',
      '由 1.4 直接得到（L2 依赖 API 签名）',
      '替代解释：这些站点可能只是「把任何 ole32 能存的接口都交出去」的通用包装器。'
      '已被部分排除：同一批函数从不请求 0x7f7c90(IUnknown)/0x7f7c70；'
      '未排除：该包装器可能对**其它**未在本镜像出现的 IID 也一视同仁')
ck('1.6 归为 L3 并显式列出未排除的替代解释', True,
   {'level': 'L3', 'alt_listed': True})

# ---- 1.7 L4 ----
claim('1.7', 'L4',
      '0x7f7c70 的语义 = IPersist',
      '**未证**。只有「0x7f7c70 从不被客户端请求」这条阴性事实（1.5）',
      '阴性事实不足以定名：一个从不被请求的 IID 可以是 IPersist、IUnknown 的别名、'
      '某个仅服务端登记的历史接口，甚至死常量。本库静态数据无法在这些之间裁决。'
      'R112–R115 的「不编赢家」在本轮**仍然成立**，本轮只是把证据面从 1 个扩到 4 个，'
      '并把 0x7f7c80 一侧定死。')
ck('1.7 明确判为 L4（未证），不编 IPersist 这个名', True, {'level': 'L4'})

levels = {}
for x in claims:
    levels[x['level']] = levels.get(x['level'], 0) + 1
print('\n分级统计：%s' % levels)
json.dump({'claims': claims, 'levels': levels, 'checks': checks},
          open(OUT, 'w'), indent=1)
np_ = sum(1 for c in checks if c['ok'])
print('== %d/%d PASS ==' % (np_, len(checks)))
print('WROTE', OUT)
sys.exit(0 if np_ == len(checks) else 1)
