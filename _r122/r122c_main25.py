#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r122c: R121 未取得项② —— 主函数 0x67d300 那 25 站的模板展开证据。

R121 的结论只覆盖 35 个孪生站（35 个 edx 是立即数），并明确写了「主函数 25 站与 35 站
不同源，不能外推」。本轮外推之前必须先取证：这 25 站的描述符从哪来。

本脚本回答三件事：
  M1  25 站的描述符来源是哪种指令形态（立即数 / 全局槽读取 / 其他）
  M2  全局槽读取那些，槽里装的是不是同一族的全局 VectorClass 容器（用 c7 05 写入的 vptr
      反解 RTTI 名），还是别的对象
  M3  因此「35 站 = 模板展开」这个结论能不能外推到 25 站（能/不能，给出字节界的边界）

内存纪律：全部单函数/单指令级 disasm，不开整段 detail。
"""
import collections
import hashlib
import json
import struct
import sys

import capstone
import pefile

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r122/r122c_main25.json'
RES = []


def ck(name, cond, detail=''):
    RES.append({'check': name, 'ok': bool(cond), 'detail': str(detail)[:280]})
    return bool(cond)


pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
SECS = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\0').decode()
    SECS.append(dict(name=nm, va=IB + s.VirtualAddress, vs=s.Misc_VirtualSize,
                     pr=s.PointerToRawData, rs=s.SizeOfRawData))
DATA = open(EXE, 'rb').read()
SHA = hashlib.sha256(DATA).hexdigest()


def sec_of(va):
    for x in SECS:
        if x['va'] <= va < x['va'] + x['vs']:
            return x
    return None


def rd(va, n):
    """只返回有文件字节的内容；BSS 一律 None（不越界读别的节）。"""
    x = sec_of(va)
    if x is None:
        return None
    if va - x['va'] + n > x['rs']:
        return None
    off = x['pr'] + (va - x['va'])
    return DATA[off:off + n] if off + n <= len(DATA) else None


def u32(va):
    b = rd(va, 4)
    return None if b is None else struct.unpack('<I', b)[0]


DS = [x for x in SECS if x['name'] == '.data'][0]
BSS_LO, BSS_HI = DS['va'] + DS['rs'], DS['va'] + DS['vs']
TXT = [x for x in SECS if x['name'] == '.text'][0]
TDATA = DATA[TXT['pr']:TXT['pr'] + TXT['rs']]
TBASE = TXT['va']
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True

# ---- 25 站：来自 R121 已落盘的 r121c（60 站 - 35 孪生站），此处用独立方法重算 ----
# 方法：主函数 0x67d300..0x67d434 内，所有 push imm32 == 0x7f7c80 的站点。
# 主函数实际体范围不是 0x67d434（那只是第一个 ret），整函数解码到 0x67e420
# （0x67d300..0x67e3f9 共 1675 条指令，含 45 个 ret 分支）。起点取函数入口。
MAIN_LO, MAIN_HI = 0x67d300, 0x67e420
main_sites = []
code = rd(MAIN_LO, MAIN_HI - MAIN_LO)
# 整函数一次性解码（0x134 字节），保证指令边界对齐；后续按索引在列表里回看，
# 不再对每站单独从 site-40 起解码（那样会因起点不在指令边界而得到垃圾指令）。
MAIN_INSNS = list(md.disasm(code, MAIN_LO))
for ins in MAIN_INSNS:
    if ins.mnemonic == 'push' and ins.op_str == '0x7f7c80':
        main_sites.append(ins.address)
ck('M0 主函数内 push 0x7f7c80 的站点数', len(main_sites) == 25, 'n=%d' % len(main_sites))
ck('M0b 主函数解码得到的指令数（对齐自检）', len(MAIN_INSNS) > 50,
   'insns=%d ; last_addr=0x%08x' % (len(MAIN_INSNS), MAIN_INSNS[-1].address))

# ---- M1：每个站点往前找描述符来源（QI 调用的 this 指针）----
# 形态（实测 0x67d35d 起）：mov eax, dword ptr [global] ; mov [esp+k], edi ;
#                            lea edx,[esp+k] ; mov eax, [eax+ebx*4] ; push edx ; push IID ; push eax
# 所以描述符 = [global] 指向的数组的第 ebx 个元素 = 容器对象的指针
idx_of = {ins.address: k for k, ins in enumerate(MAIN_INSNS)}
rows = []
for site in main_sites:
    k = idx_of[site]
    src = None
    indexed = False
    for j in range(k - 1, max(-1, k - 12), -1):
        ins = MAIN_INSNS[j]
        if ins.mnemonic != 'mov' or len(ins.operands) != 2:
            continue
        o0, o1 = ins.operands
        if o0.type != capstone.x86.X86_OP_REG:
            continue
        if o1.type == capstone.x86.X86_OP_MEM and o1.mem.base == 0 and o1.mem.index == 0 \
           and o1.mem.disp != 0:
            a = o1.mem.disp & 0xffffffff
            s = sec_of(a)
            if s and s['name'] == '.data':
                src = a
                break
        if o1.type == capstone.x86.X86_OP_MEM and o1.mem.index != 0:
            indexed = True
    rows.append(dict(site='0x%08x' % site,
                     desc_global=('0x%08x' % src) if src else None,
                     indexed=indexed))

ck('M1a 每个站点都能往前找到 .data 全局槽作为描述符来源',
   all(r['desc_global'] for r in rows),
   'found=%d/25' % sum(1 for r in rows if r['desc_global']))
GLOBS = sorted({int(r['desc_global'], 16) for r in rows if r['desc_global']})
ck('M1b 25 站各用不同的全局槽（1 站 1 槽，无复用）', len(GLOBS) == 25,
   'n_distinct=%d globals=%s' % (len(GLOBS), ['0x%08x' % g for g in GLOBS]))

# ---- M2：这些全局槽是谁的 +4（Array 成员）？谁写过它的 vptr？ ----
# 扫 .text 全部 c7 05 写 BSS
BSS_WRITES = collections.defaultdict(list)
i = 0
n = len(TDATA)
while i < n - 10:
    if TDATA[i] == 0xc7 and TDATA[i + 1] == 0x05:
        t = struct.unpack_from('<I', TDATA, i + 2)[0]
        if BSS_LO <= t < BSS_HI:
            BSS_WRITES[t].append(TBASE + i)
    i += 1


def vtable_name(vt):
    col = u32(vt - 4)
    if col is None:
        return None
    b = rd(col, 0x18)
    if b is None:
        return None
    sig, off, cd, td, chd, sv = struct.unpack('<IIIIII', b)
    if sig != 0 or td == 0:
        return None
    s = rd(td + 8, 0x100)
    if s is None:
        return None
    nm = s.split(b'\0')[0].decode('ascii', 'replace')
    return nm if nm.startswith('.?AV') else None


def container_of(array_global):
    """VectorClass<T> 布局：+0 vptr, +4 Array, +8 ... 故 Array 地址 - 4 = 对象首址。"""
    return array_global - 4


resolved = []
for g in GLOBS:
    c = container_of(g)
    names = []
    for s in sorted(BSS_WRITES.get(c, [])):
        b = rd(s, 10)
        if b is None:
            continue
        vt = struct.unpack_from('<I', b, 6)[0]
        nm = vtable_name(vt)
        if nm:
            names.append(nm)
    resolved.append(dict(array_global='0x%08x' % g, container='0x%08x' % c,
                         n_vptr_writes=len(BSS_WRITES.get(c, [])),
                         class_names=names))

ck('M2a 每个全局槽 -4 都是被 c7 05 写过 vptr 的 BSS 对象',
   all(r['n_vptr_writes'] > 0 for r in resolved),
   'resolved=%d/%d ; detail=%s'
   % (sum(1 for r in resolved if r['n_vptr_writes'] > 0), len(resolved),
      [(r['container'], r['n_vptr_writes']) for r in resolved]))
ck('M2b 每个这样的容器的 vptr 都能反解出 RTTI 类名',
   all(len(r['class_names']) > 0 for r in resolved),
   'with_names=%d/%d' % (sum(1 for r in resolved if r['class_names']), len(resolved)))
ck('M2c 反解出的类名全属 VectorClass/DynamicVectorClass 族',
   all('VectorClass@' in nm for r in resolved for nm in r['class_names']),
   'names=%s' % ([nm for r in resolved for nm in r['class_names']][:6]))

# ---- M3：边界 —— 25 站与 35 站是同一种描述符吗？ ----
# 35 站：edx = 容器首址（立即数）            -> 描述符 = 容器本身
# 25 站：ecx/this = [ [global+0] + ebx*4 ]   -> 描述符 = 数组元素（容器里的指针）
# M3a 真条件：25 站的描述符来源必须全部是「经 [reg+index*4] 的数组元素」形态，
# 且没有任何一站是「edx=容器首址立即数」形态（后者是 35 站的特征）。
n_direct_imm = 0
for r in rows:
    site = int(r['site'], 16)
    b = rd(site - 7, 7)
    if b and b[0] == 0xba:
        n_direct_imm += 1
ck('M3a 25 站全部是全局槽间接形态，0 站是 edx=立即数形态（故不能把 35 站的结论直接外推）',
   n_direct_imm == 0 and all(r['indexed'] for r in rows),
   'n_direct_imm=%d ; n_indexed=%d/25' % (n_direct_imm, sum(1 for r in rows if r['indexed'])))
# M3b 真条件：25 站的 25 个容器首址必须全部落在同一个 BSS 区，且其 vptr 全在
# VectorClass 族（这才是「同族」，不是「都叫全局容器」这种模糊说法）。
_ctrs = [container_of(g) for g in GLOBS]
ck('M3b 25 站的容器首址全落在 .data BSS 区，且 vptr 全在 VectorClass 族',
   all(BSS_LO <= c < BSS_HI for c in _ctrs) and
   all('VectorClass@' in nm for r in resolved for nm in r['class_names']),
   'n=%d ; in_bss=%d ; low=%08x high=%08x ; BSS=[%08x,%08x)'
   % (len(_ctrs), sum(1 for c in _ctrs if BSS_LO <= c < BSS_HI),
      min(_ctrs), max(_ctrs), BSS_LO, BSS_HI))

# 25 站用的容器是否与 35 个容器重叠？
OBJ35 = set()
calls = {}
for i in range(len(TDATA) - 5):
    if TDATA[i] != 0xe8:
        continue
    rel = struct.unpack_from('<i', TDATA, i + 1)[0]
    va = TBASE + i
    tgt = va + 5 + rel
    if 0x67fdf0 <= tgt <= 0x680f80:
        calls.setdefault(tgt, []).append(va)
for tgt, ss in calls.items():
    for s in ss:
        if s in (0x67d193, 0x67e62b):
            continue
        b = rd(s - 7, 7)
        if b and b[0] == 0xba:
            OBJ35.add(struct.unpack_from('<I', b, 1)[0])
MAIN_CTRS = {container_of(g) for g in GLOBS}
ck('M3c 25 站用的容器与 35 站用的容器不重叠（故不能互相外推，只能各自取证）',
   not (MAIN_CTRS & OBJ35),
   'overlap=%s ; main_n=%d obj35_n=%d'
   % ([hex(x) for x in sorted(MAIN_CTRS & OBJ35)], len(MAIN_CTRS), len(OBJ35)))

# 主函数 25 站各站的描述符元素类型（容器名给出元素类型）
main_elem = []
for r in rows:
    g = int(r['desc_global'], 16)
    ent = [x for x in resolved if x['array_global'] == '0x%08x' % g]
    names = ent[0]['class_names'] if ent else []
    vec = [nm for nm in names if not nm.startswith('.?AV?$Dynamic')]
    elem = vec[0].split('VectorClass@')[1].split('@@@')[0] if len(vec) == 1 else None
    main_elem.append(elem)
ck('M4a 25 站各自的描述符元素类型可解', all(e for e in main_elem),
   'ok=%d/25' % sum(1 for e in main_elem if e))
ck('M4b 25 站的元素类型互不相同（与 35 站同性质，各自独立成立）',
   len(set(e for e in main_elem if e)) == 25,
   'distinct=%d %s' % (len(set(e for e in main_elem if e)),
                       sorted(set(e for e in main_elem if e))))

# 反控：把 container_of 改成 array_global - 0（即当容器首址就是 Array 地址）必须解不出
bad = 0
for g in GLOBS:
    names = []
    for s in sorted(BSS_WRITES.get(g, [])):
        b = rd(s, 10)
        if b is None:
            continue
        vt = struct.unpack_from('<I', b, 6)[0]
        nm = vtable_name(vt)
        if nm:
            names.append(nm)
    if names:
        bad += 1
ck('M5 反控：把 Array 地址直接当容器首址（不减 4）必须解不出 vptr',
   bad == 0, 'resolved_as_container=%d/%d' % (bad, len(GLOBS)))

json.dump(dict(exe_sha256=SHA,
               n_main_sites=len(main_sites),
               desc_globals=['0x%08x' % g for g in GLOBS],
               resolved_containers=resolved,
               rows=rows,
               main_elem_types=main_elem,
               checks=RES, all_ok=all(r['ok'] for r in RES)),
          open(OUT, 'w'), indent=1)

for r in RES:
    print(('  PASS  ' if r['ok'] else '  FAIL  ') + r['check'] + ' :: ' + r['detail'])
print('checks %d ; PASS %d' % (len(RES), sum(1 for r in RES if r['ok'])))
sys.exit(0 if all(r['ok'] for r in RES) else 1)
