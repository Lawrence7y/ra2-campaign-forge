# -*- coding: utf-8 -*-
"""静态定谳：G_FRAME(0xA8ED84) / G_TICK(0xA8ED80) 在 gamemd.exe 里到底是什么。

目的：动态观测进不去对战（全屏不接收合成输入），那就**静态**回答
      「这两个地址是不是帧/节拍计数器」——找谁在写、怎么写（inc / add / mov）。

方法：
  1. 在 .text 里搜这 4 字节地址的**小端字节模式**（覆盖所有绝对地址编码）
  2. 对每个命中位置，用 capstone 从「往前最多 12 字节」逐起点试解码，
     取出**恰好覆盖该地址且指令边界对齐**的那条指令
  3. 按助记符分类：写类（inc/dec/add/sub/mov-to-mem）vs 读类（mov-from-mem/cmp/...）
  4. 统计、并列出所有写点（这才是「谁是计数器」的证据）

★ 零真机：只读磁盘字节，不启动游戏、不 attach。
"""
import ctypes
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(r"D:\Project\ra2-campaign-forge\lead\re_d13_ruling_20261112")
EXE = Path(r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe")
EXPECT_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

TARGETS = {
    "G_TICK": 0x00A8ED80,
    "G_FRAME": 0x00A8ED84,
    "G_EXITSTATE": 0x00A8EDD8,
    "G_SINGLETON": 0x00887368,
}

try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
except ImportError:
    print("!! 需要 capstone: pip install capstone")
    sys.exit(2)


def load_pe():
    d = EXE.read_bytes()
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    nsec = struct.unpack_from("<H", d, pe + 6)[0]
    opt = struct.unpack_from("<H", d, pe + 20)[0]
    imgbase = struct.unpack_from("<I", d, pe + 24 + 28)[0]
    base = pe + 24 + opt
    secs = []
    for i in range(nsec):
        o = base + 40 * i
        name = d[o:o + 8].rstrip(b"\x00").decode("latin1")
        vsz = struct.unpack_from("<I", d, o + 8)[0]
        rva = struct.unpack_from("<I", d, o + 12)[0]
        rawsz = struct.unpack_from("<I", d, o + 16)[0]
        raw = struct.unpack_from("<I", d, o + 20)[0]
        secs.append((name, rva, vsz, raw, rawsz))
    return d, imgbase, secs


def find_hits(text, raw_off, raw_size, addr):
    """在 .text 原始字节里找该地址的小端 4 字节。"""
    pat = struct.pack("<I", addr)
    out = []
    i = 0
    while True:
        j = text.find(pat, i)
        if j < 0:
            break
        out.append(j)                 # 相对 .text 起点的偏移
        i = j + 1
    return out


def decode_covering(md, text, hit, addr):
    """在 hit 附近找「恰好覆盖该地址」的指令。返回 (insn, start_off) 或 None。"""
    pat = struct.pack("<I", addr)
    best = None
    for back in range(0, 13):
        s = hit - back
        if s < 0:
            continue
        chunk = text[s:s + 16]
        for insn in md.disasm(chunk, s):
            cover_start = insn.address
            cover_end = insn.address + insn.size
            if cover_start <= hit and hit + 4 <= cover_end:
                # 优先取「起始离 hit 最近」的
                if best is None or back < best[1]:
                    best = (insn, back)
                break
    return best


WRITE_MNEM = ("inc", "dec", "add", "sub", "mov", "or", "and", "xor", "not", "neg")


def classify(insn):
    m = insn.mnemonic
    ops = insn.op_str
    is_mem_dest = ops.split(",")[0].strip().startswith("dword ptr")
    if m in ("inc", "dec", "not", "neg") and is_mem_dest:
        return "write"
    if m in ("add", "sub", "or", "and", "xor") and is_mem_dest:
        return "write"
    if m == "mov" and is_mem_dest:
        return "write"
    return "read"


def main():
    d, imgbase, secs = load_pe()
    print("=" * 78)
    print("静态定谳：G_TICK / G_FRAME / G_EXITSTATE / G_SINGLETON 的读写点")
    print("=" * 78)
    print("镜像: %s (%d B)" % (EXE.name, len(d)))
    import hashlib
    print("sha256: %s" % hashlib.sha256(d).hexdigest())
    print("ImageBase: %#x" % imgbase)
    for nm, rva, vsz, raw, rawsz in secs:
        print("  %-10s rva=%#010x vsize=%-8d raw=%#010x rawsize=%d"
              % (nm, rva, vsz, raw, rawsz))

    text_sec = [s for s in secs if s[0] == ".text"][0]
    _, t_rva, t_vsz, t_raw, t_rawsz = text_sec
    text = d[t_raw:t_raw + t_rawsz]
    print("\n.text: raw=%#x size=%d" % (t_raw, len(text)))

    md = Cs(CS_ARCH_X86, CS_MODE_32)

    for name, addr in TARGETS.items():
        print("\n" + "=" * 78)
        print("%s  @ %#010x" % (name, addr))
        print("=" * 78)
        hits = find_hits(text, t_raw, t_rawsz, addr)
        print("  4 字节模式命中数 = %d" % len(hits))
        if not hits:
            print("  ⇒ 全 .text 无任何绝对地址引用（该地址可能只在数据区/未使用）")
            continue

        kinds = Counter()
        writes = []
        reads = []
        undecoded = 0
        skipped_fp = [0]
        for h in hits:
            r = decode_covering(md, text, h, addr)
            if r is None:
                undecoded += 1
                continue
            insn, back = r
            k = classify(insn)
            va = imgbase + t_rva + insn.address
            kinds[k] += 1
            # ★ 去假阳性：必须是**真正的内存操作数**（capstone 渲染出 ptr [...]）。
            # 否则 "add eax, 0xa8ed84" 这种 imm32 也含该 4 字节，会把计数灌成上千。
            ops_l = insn.op_str.lower()
            hexs = "0x%x" % addr
            if ("ptr [" + hexs + "]") not in ops_l and ("ptr [" + hexs[:-1]) not in ops_l \
               and (hexs + "]") not in ops_l:
                skipped_fp[0] += 1
                continue
            rec = (va, insn.mnemonic, insn.op_str, insn.bytes.hex(" "), back)
            (writes if k == "write" else reads).append(rec)

        print("  可解码 %d / 未解码 %d / 已剔除假阳性(非内存操作数) %d"
              % (len(writes) + len(reads), undecoded, skipped_fp[0]))
        print("  写类 %d  /  读类 %d" % (kinds.get("write", 0), kinds.get("read", 0)))

        if writes:
            print("\n  ★ 写点（谁是计数器/谁在改它）——按 VA 排序:")
            for va, mn, ops, by, back in sorted(writes)[:40]:
                print("    %#010x  %-6s %-34s  bytes=[%s]" % (va, mn, ops, by))
            if len(writes) > 40:
                print("    ... 共 %d 条写点" % len(writes))
            # 专门找 inc
            incs = [w for w in writes if w[1] == "inc"]
            if incs:
                print("\n  ★★ 递增点（inc dword ptr [%#x]）共 %d 处：" % (addr, len(incs)))
                for va, mn, ops, by, back in sorted(incs):
                    print("    %#010x  %s %s" % (va, mn, ops))
        if reads:
            print("\n  读点（前 20 条）:")
            for va, mn, ops, by, back in sorted(reads)[:20]:
                print("    %#010x  %-6s %-34s" % (va, mn, ops))
            if len(reads) > 20:
                print("    ... 共 %d 条读点" % len(reads))

    print("\n" + "=" * 78)
    print("说明：本脚本只读磁盘字节，未启动游戏、未 attach、未读活进程内存。")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
