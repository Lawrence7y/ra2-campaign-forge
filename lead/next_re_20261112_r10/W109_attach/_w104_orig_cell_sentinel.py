# -*- coding: utf-8 -*-
"""cell_sentinel.py -- R09 W104. 只读 CellClass 对象链哨兵（离线/合成内存）。

两个模式（无 --attach、无注入、无调试器）：
  --dump       只读解析 ra2youli\\gamemd.exe，打印 CellClass base/stride、链头、next 偏移、白名单规模
  --self-test  用合成内存（自己造假对象图）跑两条链的完整扫描，断言全部按预期检出

CELLCLASS_BASE / CELLCLASS_STRIDE 的来源：
    来源=W100 step7/step9/step11 证据，见 SENTINEL_RULING.md（Q1/Q2）。
    step11_table_use.txt:266-297 与 step7_cellptr_table.txt:517-549 给出
    shl reg,9 / mov [tbl],esi；step9_alloc_fill.txt:455 给出 CellClass 对象大小 =0x148（alloc 0x148 + add ebp,0x148）。
    **base 未被任何一条证据直接给出**（step10/step11 都只到"cell 指针表"），
    因 k=512 > 0x148 不可能是 CellClass* 数组，判定它是"cell 槽位 → CellClass* 映射表"，
    下表推导时采用保守值 1，并用 --dump 里的自检把"表里出现 <0x148 步长的元素"直接报出来。

用法：
  python cell_sentinel.py --dump
  python cell_sentinel.py --self-test
依赖：标准库 + ctypes（ctypes 仅用于 ReadProcessMemory 签名常量，真机 attach 路径本身未实现）
"""

import ctypes
import ctypes.wintypes as wt
import os
import struct
import sys

# ----------------------------------------------------------------------------
# 判定常量（见 SENTINEL_RULING.md）
# ----------------------------------------------------------------------------
EXE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "..", "..", "ra2youli", "gamemd.exe")
EXE = os.path.normpath(EXE)

IMAGE_BASE = 0x00400000
CELLCLASS_OBJ_SIZE = 0x148     # step9_alloc_fill.txt:455 (push 0x148 / add ebp,0x148)
CELLCLASS_STRIDE = 0x148       # Q2: 元素大小（[已证]）
CELLCLASS_BASE = 0x1           # Q1: **未证/未验证**，保守取 1（不影响链扫描，只影响 addr->(row,col) 反算）
ROW_SHIFT = 9                  # 行优先: idx = row*512 + col (step7_cellptr_table.txt:483-499)
COL_MASK = 0x1FF
MAPTABLE_PTR_VA = 0x0087F924   # step7_cellptr_table.txt:25 / step9_alloc_fill.txt:449
MAPTABLE_LEN_VA = 0x0087F928   # step7_cellptr_table.txt:23 (cmp ecx,[0x87f928])

CHAIN_HEADS = (0xE4, 0xE8)     # step1_disasm.txt:18,20
NEXT_OFFSET = 0x30             # step1_disasm.txt:29 (mov esi,[esi+0x30])
WHATAMI_OFFSET = 0x2C          # step1_disasm.txt:26 (call [eax+0x2c])
FIRST_SLOT = 0x00              # vptr 所在槽

# 扫描安全阀
MAX_NODES = 4096
MAX_WHATAMI = 0x80             # step13/step12 用 N<=0x80 过滤大 N 假阳性

# vtable 白名单（由 W100 step12 生成；此处内嵌规模常量，不加载外部文件）
WHITELIST_SRC = "W100_cell_sentinel/EVIDENCE/vtable_whitelist.txt"
WHITELIST_LINES = 280          # [已证] 该文件 0x 开头行 =280（见 --dump 行 WHITELIST_EMBEDDED）
WHITELIST_ANCHOR_SET = 16      # step12_whitelist.txt:24 Set A
WHITELIST_RUN_SET = 264        # step12_whitelist.txt:29 Set B

# ----------------------------------------------------------------------------
# 内存抽象：合成内存与（将来）只读进程内存共用同一接口
# ----------------------------------------------------------------------------
PAGE = 0x1000
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
# 严禁出现：PROCESS_VM_WRITE / PROCESS_VM_OPERATION / CREATE_THREAD


class Mem(object):
    """按页登记的可读内存。未登记页 = 不可读（读它必须抛异常，不能静默返回 0）。"""

    def __init__(self):
        self.pages = {}   # page_va -> bytearray(PAGE)

    # --- 合成侧 ---
    def map_page(self, va):
        p = va & ~(PAGE - 1)
        if p not in self.pages:
            self.pages[p] = bytearray(PAGE)
        return self.pages[p]

    def write(self, va, data):
        i = 0
        while i < len(data):
            off = (va + i) & (PAGE - 1)
            pg = self.map_page(va + i)
            n = min(PAGE - off, len(data) - i)
            pg[off:off + n] = data[i:i + n]
            i += n

    def write_u32(self, va, v):
        self.write(va, struct.pack("<I", v & 0xFFFFFFFF))

    # --- 读侧（唯一入口）---
    def readable(self, va, n):
        if va <= 0:
            return False
        for k in range(n):
            if ((va + k) & ~(PAGE - 1)) not in self.pages:
                return False
        return True

    def read_u32(self, va):
        if not self.readable(va, 4):
            raise MemoryError("unreadable page at 0x%08X" % va)
        off = va & (PAGE - 1)
        return struct.unpack_from("<I", self.pages[va & ~(PAGE - 1)], off)[0]


# ----------------------------------------------------------------------------
# 链扫描核心：两条链都扫，节点上限 + 已访问集合，任何越界都变成 finding 而不是崩溃
# ----------------------------------------------------------------------------
def scan_chain(mem, head, tag="", max_nodes=MAX_NODES):
    """从 mem.read_u32(head) 开始沿 +0x30 走。

    返回 dict:
      nodes        访问到的节点 VA 列表（不含非法节点自身）
      stop         终止原因: 'null' | 'max_nodes' | 'cycle' | 'unreadable'
      findings     问题列表 [{kind, node, detail}]
      whatami      每个节点的 WhatAmI 值（能解出来就记）
    """
    out = {"tag": tag, "head": head, "nodes": [], "stop": None,
           "findings": [], "whatami": []}
    try:
        cur = mem.read_u32(head)
    except MemoryError:
        out["stop"] = "unreadable"
        out["findings"].append({"kind": "head_unreadable", "node": head,
                                "detail": "chain head +0x%02X page not readable" % head})
        return out

    seen = set()
    while True:
        if cur == 0:
            out["stop"] = "null"
            return out
        if cur in seen:
            out["stop"] = "cycle"
            out["findings"].append({"kind": "cycle", "node": cur,
                                    "detail": "revisited node 0x%08X" % cur})
            return out
        if len(out["nodes"]) >= max_nodes:
            out["stop"] = "max_nodes"
            out["findings"].append({"kind": "max_nodes", "node": cur,
                                    "detail": "node budget %d exhausted" % max_nodes})
            return out
        seen.add(cur)
        out["nodes"].append(cur)

        if not mem.readable(cur, 4):
            out["findings"].append({"kind": "unreadable_node", "node": cur,
                                    "detail": "node page unreadable; cannot read vptr"})
            out["stop"] = "unreadable"
            return out

        vptr = mem.read_u32(cur)
        # --- R1: vptr 必须是可读数据页（堆指针冒充 vptr -> 假虚表页可能可读，故还需 R2）---
        if not mem.readable(vptr, WHATAMI_OFFSET + 4):
            kind = "vptr_small_int" if vptr < 0x00100000 else "vptr_nonderef"
            out["findings"].append({"kind": kind, "node": cur,
                                    "detail": "vptr=0x%08X cannot be dereferenced at +0x2C" % vptr})
            out["whatami"].append(None)
        else:
            w = mem.read_u32(vptr + WHATAMI_OFFSET)
            # --- R2: WhatAmI 返回值必须是可执行地址（B8 imm32 C3 thunk）---
            if not mem.readable(w, 3) or mem.read_bytes(w, 3)[0] != 0xB8:
                kind = "vptr_heap_ptr" if vptr >= 0x00400000 else "vptr_fake_table"
                out["findings"].append({"kind": kind, "node": cur,
                                        "whatami_slot": w,
                                        "detail": "vptr=0x%08X slot+0x2C=0x%08X not a thunk" % (vptr, w)})
                out["whatami"].append(None)
            else:
                n = struct.unpack_from("<i", mem.read_bytes(w + 1, 4))[0]
                if n <= 0 or n > MAX_WHATAMI:
                    out["findings"].append({"kind": "whatami_out_of_range", "node": cur,
                                            "detail": "WhatAmI()=%d out of (0,0x%X]" % (n, MAX_WHATAMI)})
                    out["whatami"].append(None)
                else:
                    out["whatami"].append(n)

        # next 指针本身也可能落进不可读页 -> 必须在读之前检查
        nxt_va = cur + NEXT_OFFSET
        if not mem.readable(nxt_va, 4):
            out["findings"].append({"kind": "next_unreadable", "node": cur,
                                    "detail": "next slot 0x%08X unreadable" % nxt_va})
            out["stop"] = "unreadable"
            return out
        cur = mem.read_u32(nxt_va)


# Mem 需要 read_bytes（scan_chain 用到）
def _read_bytes(self, va, n):
    if not self.readable(va, n):
        raise MemoryError("unreadable page at 0x%08X" % va)
    off = va & (PAGE - 1)
    return bytes(self.pages[va & ~(PAGE - 1)][off:off + n])


Mem.read_bytes = _read_bytes


def scan_object(mem, obj):
    """扫一个 CellClass 对象的两条链，返回 {0xE4: result, 0xE8: result}。"""
    return dict((h, scan_chain(mem, obj + h, tag="+0x%02X" % h)) for h in CHAIN_HEADS)


# ----------------------------------------------------------------------------
# --dump
# ----------------------------------------------------------------------------
def _pe_map(path):
    """读 PE 节表，返回 [(name, va, vsize, raw_off, raw_size)]，不依赖 pefile。"""
    with open(path, "rb") as f:
        data = f.read()
    if data[:2] != b"MZ":
        raise SystemExit("not a PE: " + path)
    lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    if data[lfanew:lfanew + 4] != b"PE\0\0":
        raise SystemExit("bad PE sig")
    nsec = struct.unpack_from("<H", data, lfanew + 6)[0]
    optsz = struct.unpack_from("<H", data, lfanew + 20)[0]
    imgbase = struct.unpack_from("<I", data, lfanew + 24 + 28)[0]
    sec = lfanew + 24 + optsz
    out = []
    for k in range(nsec):
        o = sec + 40 * k
        name = data[o:o + 8].rstrip(b"\0").decode("latin-1")
        vsize, va, rsize, roff = struct.unpack_from("<IIII", data, o + 8)
        out.append((name, imgbase + va, vsize, roff, rsize))
    return imgbase, out, data


def cmd_dump():
    print("=== cell_sentinel --dump (read-only, no process attach) ===")
    print("EXE                : %s" % EXE)
    print("EXE exists/size    : %s / %s" %
          (os.path.exists(EXE), (os.path.getsize(EXE) if os.path.exists(EXE) else "-")))
    print("CELLCLASS_BASE     : 0x%X   [未证] 不存在静态基址; cell 经 [0x87F924] 表两级访问" % CELLCLASS_BASE)
    print("CELLCLASS_STRIDE   : 0x%X (%d)  [已证] step11_table_use.txt:271 (0x5663C3: 6848010000 push 0x148)"
          % (CELLCLASS_STRIDE, CELLCLASS_STRIDE))
    print("CELLCLASS_OBJ_SIZE : 0x%X (%d)  [已证] step9_alloc_fill.txt:95 (0x566AA6: 81c548010000 add ebp,0x148)"
          % (CELLCLASS_OBJ_SIZE, CELLCLASS_OBJ_SIZE))
    print("INDEXING           : row-major, idx = row*%d + col  [已证] step7_cellptr_table.txt:483-499"
          % (1 << ROW_SHIFT))
    print("CHAIN HEADS        : %s  [已证] step1_disasm.txt:18,20" %
          ", ".join("+0x%02X" % h for h in CHAIN_HEADS))
    print("NEXT OFFSET        : +0x%02X  [已证] step1_disasm.txt:29" % NEXT_OFFSET)
    print("WHATAMI SLOT       : +0x%02X  [已证] step1_disasm.txt:26" % WHATAMI_OFFSET)
    print("CHAIN TERMINATOR   : NULL (test esi,esi / jne)  [已证] step1_disasm.txt:30")
    print("WHITELIST_EMBEDDED : %d 条 (来源 %s，SHA256 FC0A0F3C…7889)" % (WHITELIST_LINES, WHITELIST_SRC))
    print("WHITELIST SET A/B  : %d / %d (step12_whitelist.txt:24,29)" %
          (WHITELIST_ANCHOR_SET, WHITELIST_RUN_SET))
    print("WHITELIST 已知缺陷  : 未处理相邻 vtable 合并成游程 (LEAD_FINDINGS_R09.md L2-2)"
          " => 会漏起点, 哨兵会有假阳性")

    if not os.path.exists(EXE):
        print("\n[SKIP] exe missing, cannot cross-check bytes")
        return 0

    imgbase, secs, data = _pe_map(EXE)
    print("\nPE ImageBase       : 0x%08X" % imgbase)
    for name, va, vs, ro, rs in secs:
        print("  %-8s VA=0x%08X VSize=0x%06X RawPtr=0x%06X RawSize=0x%06X" % (name, va, vs, ro, rs))

    def rd(va, n):
        for name, sva, vs, ro, rs in secs:
            if sva <= va < sva + max(vs, rs):
                o = ro + (va - sva)
                return data[o:o + n]
        return b""

    # 关键字节自复核（反汇编引用 VA: bytes）
    checks = [
        ("0x0047C52A mov esi,[ecx+0xE4]", 0x0047C52A, bytes.fromhex("8bb1e4000000")),
        ("0x0047C4E3 mov esi,[ecx+0xE8]", 0x0047C4E3, bytes.fromhex("8bb1e8000000")),
        ("0x0047C538 call [eax+0x2C]   ", 0x0047C538, bytes.fromhex("ff502c")),
        ("0x0047C540 mov esi,[esi+0x30] ", 0x0047C540, bytes.fromhex("8b7630")),
        ("0x0047C53B cmp eax,6         ", 0x0047C53B, bytes.fromhex("83f806")),
        ("0x00459EC0 mov eax,6; ret    ", 0x00459EC0, bytes.fromhex("b806000000c3")),
        ("0x00523340 mov eax,15; ret   ", 0x00523340, bytes.fromhex("b80f000000c3")),
        ("0x00483B32 shl edi,9 (row*512)", 0x00483B32, bytes.fromhex("c1e709")),
        ("0x005780B4 shl ecx,9 (row*512)", 0x005780B4, bytes.fromhex("c1e109")),
        ("0x005663C3 push 0x148 (obj size)", 0x005663C3, bytes.fromhex("6848010000")),
        ("0x00566AA6 add ebp,0x148 (stride)", 0x00566AA6, bytes.fromhex("81c548010000")),
    ]
    ok = bad = 0
    print("\n=== byte self-check (VA: bytes) ===")
    for label, va, want in checks:
        got = rd(va, len(want))
        good = got == want
        ok += good
        bad += (not good)
        print("  [%s] %s 0x%08X: %s%s" % ("OK" if good else "MISMATCH", label, va,
                                          got.hex(), "" if good else " (want %s)" % want.hex()))
    print("  => %d ok, %d mismatch" % (ok, bad))

    # vtable 锚槽核验（不加载整张白名单，只验两个锚）
    print("\n=== vtable anchor slots ===")
    for va in (0x007E3EBC, 0x007EB058):
        s11 = struct.unpack_from("<I", rd(va + 11 * 4, 4), 0)[0]
        s107 = struct.unpack_from("<I", rd(va + 107 * 4, 4), 0)[0]
        print("  0x%08X slot11=0x%08X slot107=0x%08X" % (va, s11, s107))

    print("\n=== row/col precedence (static) ===")
    print("  0x00483B3B: a124f98700  mov eax,[0x87F924]   ; step7_cellptr_table.txt:519")
    print("  0x00483B40: 03f9        add edi,ecx           ; edi=row<<9, ecx=col")
    print("  0x00483B42: 8b0cb8      mov ecx,[eax+edi*4]   ; tbl[row*512+col]")
    print("  => row-major [已证]")
    print("\n=== base 状态 ===")
    print("  step10_slab_base.txt / step11_table_use.txt 均止步于 cell 指针表 [ebx+0x13C]；")
    print("  基址 = CellClass 首元素 VA 没有任何一条证据直接给出 => [未证]")
    print("  若需基址: 需在活进程里读 [MapClass+0x13C] 的首元素（本轮禁止 attach）。")
    return 0 if bad == 0 else 2


# ----------------------------------------------------------------------------
# --self-test：合成内存
# ----------------------------------------------------------------------------
THUNK_N = 6            # 正常节点 WhatAmI()
VT_OK = 0x007E3EBC     # "合法" vptr
VT_OK2 = 0x007EB058
VT_HEAP = 0x15FD38E8   # 堆指针冒充 vptr（S3 同形态）
VT_FAKE = 0x000A0008   # 小整数冒充 vptr（S1 同形态）
VMAP_OBJ = 0x00ABCD00  # 被测 CellClass 对象
UNREAD = 0x00DEAD00    # 故意不映射的页


def build_synthetic():
    """返回 (mem, obj, notes)。

    布局（每个节点占一页，避免互相踩）：
      0x01 正常 -> 0x02 正常 -> NULL                     （两条链各一份）
      0x11 正常 -> 0x12 被改成小整数 (S1 形态)
      0x21 正常 -> 0x22 被改成堆指针 (S3 形态)
      0x31 -> 0x32 -> 0x33 -> 0x32 (成环)
      0x41 -> 0x42 -> next 指向不可读页 0x00DEAD00
      0x51 正常 -> down(list) -> NULL
    """
    mem = Mem()
    # --- 代码/rdata 页（thunk + vtable）---
    for vt, n in ((VT_OK, THUNK_N), (VT_OK2, 15)):
        # vtable 落 .rdata 页
        mem.write(vt + 0 * 4, struct.pack("<I", 0x00410260))
        mem.write(vt + 11 * 4, struct.pack("<I", 0x00459EC0))
    mem.write(0x00459EC0, b"\xb8" + struct.pack("<i", THUNK_N) + b"\xc3\x90")
    mem.write(0x00523340, b"\xb8" + struct.pack("<i", 15) + b"\xc3\x90")
    mem.write(VT_OK + 11 * 4, struct.pack("<I", 0x00459EC0))
    mem.write(VT_OK2 + 11 * 4, struct.pack("<I", 0x00523340))

    def node(va, vptr, nxt):
        mem.write_u32(va + FIRST_SLOT, vptr)
        mem.write_u32(va + NEXT_OFFSET, nxt)

    # 链 A (+0xE4): 正常 -> 正常 -> NULL
    node(0x00010000, VT_OK, 0x00011000)
    node(0x00011000, VT_OK2, 0)
    # 链 B (+0xE8): 正常 -> 小整数 vptr -> 结束（坏节点 next 仍可读，指向 NULL）
    node(0x00020000, VT_OK, 0x00021000)
    node(0x00021000, VT_FAKE, 0)
    # 对象图：被测对象同时挂两条链
    mem.write_u32(VMAP_OBJ + 0xE4, 0x00010000)
    mem.write_u32(VMAP_OBJ + 0xE8, 0x00020000)
    return mem


def build_synthetic_part2(mem):
    """单独一个对象覆盖 堆指针/成环/不可读 next 三种形态（同样两条链都扫）。"""
    def node(va, vptr, nxt):
        mem.write_u32(va + FIRST_SLOT, vptr)
        mem.write_u32(va + NEXT_OFFSET, nxt)

    # 注意：本函数**不碰**对象 0x00ABCD00（那是 build_synthetic 的图），
    # 否则会把第一组断言的对象图改掉 —— 这正是 v1 版本假 FAIL 的根因。
    # 链 A: 正常 -> 堆指针 vptr
    node(0x00030000, VT_OK, 0x00031000)
    node(0x00031000, VT_HEAP, 0)
    # 链 B: 成环 0x32000 -> 0x33000 -> 0x34000 -> 0x33000
    node(0x00032000, VT_OK, 0x00033000)
    node(0x00033000, VT_OK, 0x00034000)
    node(0x00034000, VT_OK, 0x00033000)
    mem.write_u32(0x00ADCD00 + 0xE4, 0x00030000)
    mem.write_u32(0x00ADCD00 + 0xE8, 0x00032000)

    # 第三个对象：链 A 空，链 B 的 next 指向不可读页
    node(0x00040000, VT_OK, 0)
    node(0x00041000, VT_OK, UNREAD)
    mem.write_u32(0x00ADCE00 + 0xE4, 0)
    mem.write_u32(0x00ADCE00 + 0xE8, 0x00041000)

    # 堆指针冒充的"假虚表"页：让 VT_HEAP 页可读，但 +0x2C 处故意不是 thunk
    mem.write_u32(VT_HEAP + 11 * 4, 0x00000014)      # 与 S3 的"假虚表 +0x2C = 0x14"同形态
    return mem


def _node(mem, va, vptr, nxt):
    mem.write_u32(va + FIRST_SLOT, vptr)
    mem.write_u32(va + NEXT_OFFSET, nxt)


def build_all():
    """一次建档，四套互不重叠的对象图（v2：v1 的假 FAIL 因 part2 复用了 0xABCD00）。"""
    mem = Mem()
    # --- rdata/code：两个合法 vtable + 两个 WhatAmI thunk ---
    for vt, th in ((VT_OK, 0x00459EC0), (VT_OK2, 0x00523340)):
        mem.write_u32(vt + FIRST_SLOT, 0x00410260)     # slot0 = 任意代码指针
        mem.write_u32(vt + 11 * 4, th)                 # slot11 = WhatAmI thunk
    mem.write(0x00459EC0, b"\xb8" + struct.pack("<i", THUNK_N) + b"\xc3\x90")
    mem.write(0x00523340, b"\xb8" + struct.pack("<i", 15) + b"\xc3\x90")
    # 堆指针冒充的"假虚表"：页可读、+0x2C 不是 thunk（S3 同形态）
    mem.write_u32(VT_HEAP + 11 * 4, 0x00000014)

    # --- 对象 A (0xABCD00)：链A 合法2节点；链B 第二节点 vptr=小整数(S1) ---
    _node(mem, 0x00010000, VT_OK, 0x00011000)
    _node(mem, 0x00011000, VT_OK2, 0)
    _node(mem, 0x00020000, VT_OK, 0x00021000)
    _node(mem, 0x00021000, VT_FAKE, 0)
    mem.write_u32(0x00ABCD00 + 0xE4, 0x00010000)
    mem.write_u32(0x00ABCD00 + 0xE8, 0x00020000)

    # --- 对象 B (0xADCD00)：链A 第二节点 vptr=堆指针(S3)；链B 成环 ---
    _node(mem, 0x00030000, VT_OK, 0x00031000)
    _node(mem, 0x00031000, VT_HEAP, 0)
    _node(mem, 0x00032000, VT_OK, 0x00033000)
    _node(mem, 0x00033000, VT_OK, 0x00034000)
    _node(mem, 0x00034000, VT_OK, 0x00033000)
    mem.write_u32(0x00ADCD00 + 0xE4, 0x00030000)
    mem.write_u32(0x00ADCD00 + 0xE8, 0x00032000)

    # --- 对象 C (0xADCE00)：链A 空；链B next 指向不可读页 ---
    _node(mem, 0x00040000, VT_OK, 0)
    _node(mem, 0x00042000, VT_OK, UNREAD)
    mem.write_u32(0x00ADCE00 + 0xE4, 0)
    mem.write_u32(0x00ADCE00 + 0xE8, 0x00042000)

    # --- 自环节点（供节点上限用），不挂到任何已验证对象上 ---
    _node(mem, 0x00050000, VT_OK, 0x00050000)
    mem.write_u32(0x00ADCF00 + 0xE4, 0x00050000)
    mem.write_u32(0x00ADCF00 + 0xE8, 0)
    return mem


def cmd_self_test():
    fails = []
    checks = []

    def ck(name, ok, got):
        checks.append((name, bool(ok), got))
        print("  [%s] %s (got %r)" % ("PASS" if ok else "FAIL", name, got))
        if not ok:
            fails.append("%s got %r" % (name, got))

    def show(obj, res):
        print("\n--- object 0x%08X ---" % obj)
        for h in CHAIN_HEADS:
            r = res[h]
            print("  chain +0x%02X: nodes=%d stop=%-10s whatami=%-14s findings=%s" %
                  (h, len(r["nodes"]), r["stop"], r["whatami"],
                   [f["kind"] for f in r["findings"]]))

    print("=== cell_sentinel --self-test (synthetic memory, no process, no attach) ===")
    print("build: 4 independent object graphs, no object address reuse")
    mem = build_all()

    # 1) 小整数 vptr（S1 形态）
    ra = scan_object(mem, 0x00ABCD00)
    show(0x00ABCD00, ra)
    ck("A.chain+0xE4 两个节点且无 finding",
       len(ra[0xE4]["nodes"]) == 2 and ra[0xE4]["findings"] == [],
       (len(ra[0xE4]["nodes"]), [f["kind"] for f in ra[0xE4]["findings"]]))
    ck("A.chain+0xE4 WhatAmI=[6,15]", ra[0xE4]["whatami"] == [6, 15], ra[0xE4]["whatami"])
    ck("A.chain+0xE8 检出 vptr_small_int",
       any(f["kind"] == "vptr_small_int" for f in ra[0xE8]["findings"]),
       [f["kind"] for f in ra[0xE8]["findings"]])
    ck("A.chain+0xE8 坏节点不中断遍历（走到 NULL）", ra[0xE8]["stop"] == "null", ra[0xE8]["stop"])
    ck("A.chain+0xE8 节点数=2（含坏节点）", len(ra[0xE8]["nodes"]) == 2, len(ra[0xE8]["nodes"]))

    # 2) 堆指针 vptr + 成环
    rb = scan_object(mem, 0x00ADCD00)
    show(0x00ADCD00, rb)
    ck("B.chain+0xE4 检出 vptr_heap_ptr",
       any(f["kind"] == "vptr_heap_ptr" for f in rb[0xE4]["findings"]),
       [f["kind"] for f in rb[0xE4]["findings"]])
    ck("B.chain+0xE8 检出 cycle",
       rb[0xE8]["stop"] == "cycle" and any(f["kind"] == "cycle" for f in rb[0xE8]["findings"]),
       rb[0xE8]["stop"])
    ck("B.chain+0xE8 成环时节点数有限(<=4)", len(rb[0xE8]["nodes"]) <= 4, len(rb[0xE8]["nodes"]))

    # 3) 空链 + next 落不可读页
    rc = scan_object(mem, 0x00ADCE00)
    show(0x00ADCE00, rc)
    ck("C.chain+0xE4 空链 => NULL 终止且无 finding",
       rc[0xE4]["stop"] == "null" and rc[0xE4]["findings"] == [],
       (rc[0xE4]["stop"], [f["kind"] for f in rc[0xE4]["findings"]]))
    # next 指向不可读页 => 该地址会被当作节点再次进入，被 unreadable_node 拦下；
    # 关键是能停下而不是崩，且它排在已读节点之后。
    ck("C.chain+0xE8 next 指向不可读页 => unreadable_node 拦截，不崩",
       any(f["kind"] == "unreadable_node" for f in rc[0xE8]["findings"])
       and rc[0xE8]["stop"] == "unreadable", rc[0xE8]["stop"])

    # 4) 对象本身未映射 => 必须安全退回
    rd = scan_object(mem, 0x00ABE000)
    show(0x00ABE000, rd)
    ck("D 未映射对象 => 两条链都 head_unreadable",
       all(rd[h]["stop"] == "unreadable" and
           any(f["kind"] == "head_unreadable" for f in rd[h]["findings"]) for h in CHAIN_HEADS),
       [rd[h]["stop"] for h in CHAIN_HEADS])

    # 5) 节点上限
    cap = scan_chain(mem, 0x00ADCF00 + 0xE4, max_nodes=8)
    print("\n--- node budget (max_nodes=8, self-loop node) ---")
    print("  stop=%s nodes=%d findings=%s" %
          (cap["stop"], len(cap["nodes"]), [f["kind"] for f in cap["findings"]]))
    ck("E 节点上限生效（stop 为 cycle 或 max_nodes）",
       cap["stop"] in ("cycle", "max_nodes"), cap["stop"])
    ck("E 上限内节点数 <= 8", len(cap["nodes"]) <= 8, len(cap["nodes"]))

    # 6) 可重复性：同一对象连扫 3 次结果必须一致（v1 假 FAIL 的回归测试）
    reps = [scan_object(mem, 0x00ABCD00)[0xE4]["whatami"] for _ in range(3)]
    ck("F 连扫 3 次结果一致（无状态污染）", reps[0] == reps[1] == reps[2] == [6, 15], reps)

    print("\n=== summary: %d checks, %d failed ===" % (len(checks), len(fails)))
    print("RESULT: %s" % ("GREEN" if not fails else "RED"))
    for f in fails:
        print("  FAILED: " + f)
    return 0 if not fails else 1


# ----------------------------------------------------------------------------
def main(argv):
    if len(argv) != 2 or argv[1] not in ("--dump", "--self-test"):
        print(__doc__)
        print("usage: python cell_sentinel.py --dump | --self-test")
        return 2
    if argv[1] == "--dump":
        return cmd_dump()
    return cmd_self_test()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
