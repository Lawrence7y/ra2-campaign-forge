"""Lead 抽验：0x55B8F0 派发阶梯的结构化枚举（两条独立通道）。

通道 A：纯字节正则扫描（不反汇编）
   A1 <cnt32> (56)? 8D 70 FF 85 F6 7C ?? 8B 0D <items32> 8B 0C B1 8A 81 98 00 00 00
通道 B：从函数首起线性反汇编，按语义逐块识别，直到 ret

输出块表：起始 VA、Count 地址、Items 地址、skip 偏移、call[vtbl+0x5C] 站点、块长。
"""
import re
import audit_lib as A

NUM = re.compile(r"0x[0-9a-fA-F]+")

# 通道 A 的字节正则：两种块形态（首块多一条 push esi）
PAT = re.compile(
    rb"\xa1(?P<cnt>.{4})(?:\x56)?\x8d\x70\xff\x85\xf6\x7c(?P<jl>.{1})"
    rb"\x8b\x0d(?P<items>.{4})\x8b\x0c\xb1\x8a\x81\x98\x00\x00\x00",
    re.DOTALL,
)


def channel_a(b):
    t = b.text
    buf = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    out = []
    for m in PAT.finditer(buf):
        out.append(dict(
            block_va=t["va"] + m.start(),
            count=int.from_bytes(m.group("cnt"), "little"),
            items=int.from_bytes(m.group("items"), "little"),
            skip=0x98,
            has_push=bool(buf[m.start() + 5] == 0x56),
            byte_len=m.end() - m.start(),
        ))
    return out


def num(text):
    m = NUM.search(text)
    return int(m.group(0), 16) if m else None


def channel_b(b, start=0x55B8F0, max_blocks=40):
    out = []
    cur = start
    for _ in range(max_blocks):
        insns = A.linear_from(b, cur, 0x60)
        if not insns or not insns[0].text if False else not insns:
            break
        if not (insns[0].mnemonic == "mov" and insns[0].op_str.startswith("eax, dword ptr [")):
            break
        cnt = num(insns[0].op_str)
        items = None
        call_va = None
        skip = None
        tail = None
        for insn in insns[1:]:
            txt = "%s %s" % (insn.mnemonic, insn.op_str)
            if items is None and txt.startswith("mov ecx, dword ptr [0x") and insn.address > cur + 10:
                items = num(insn.op_str)
            if insn.mnemonic == "mov" and "+ 0x98]" in txt and skip is None:
                skip = 0x98
            if insn.mnemonic == "call" and "+ 0x5c]" in txt:
                call_va = insn.address
            if insn.mnemonic in ("jns",):
                tail = insn
                break
        if tail is None:
            break
        nxt = tail.address + tail.size
        out.append(dict(block_va=cur, count=cnt, items=items, skip=skip,
                        call_va=call_va, block_len=nxt - cur))
        cur = nxt
    return out, cur


if __name__ == "__main__":
    b = A.Bin()
    rows, _ = A.load_func_atlas()
    atlas = {v for v, _ in rows}

    print("=" * 90)
    print("CHANNEL A : pure byte regex scan")
    print("=" * 90)
    a = channel_a(b)
    print("hits = %d" % len(a))
    for i, h in enumerate(a):
        print("  [%2d] block %08X  Count=%08X  Items=%08X  skip=+0x%02X  push_esi=%s  blockbytes=%d"
              % (i, h["block_va"], h["count"], h["items"], h["skip"], h["has_push"], h["byte_len"]))

    print()
    print("=" * 90)
    print("CHANNEL B : linear disasm from 0x55B8F0")
    print("=" * 90)
    bl, end = channel_b(b)
    print("blocks = %d, ladder ends at %08X" % (len(bl), end))
    for i, h in enumerate(bl):
        print("  [%2d] block %08X  Count=%08X  Items=%08X  call[vtbl+0x5C]@%s  blocklen=0x%02X"
              % (i, h["block_va"], h["count"] or 0, h["items"] or 0,
                 ("%08X" % h["call_va"]) if h["call_va"] else "NONE", h["block_len"]))

    print()
    print("=" * 90)
    print("CROSS-CHECK : A vs B")
    print("=" * 90)
    a_va = [h["block_va"] for h in a if 0x55B000 <= h["block_va"] <= 0x55C000]
    b_va = [h["block_va"] for h in bl]
    print("A blocks in 0x55B000-0x55C000 : %s" % [hex(x) for x in a_va])
    print("B blocks                      : %s" % [hex(x) for x in b_va])
    print("identical sequence            : %s" % (a_va == b_va))

    print()
    print("=" * 90)
    print("FUNCTION EXTENT / ATLAS MEMBERSHIP")
    print("=" * 90)
    first, last_insn = 0x55B8F0, end - 1
    print("ladder span: %08X .. %08X  (%d bytes)" % (first, last_insn, end - first))
    print("is 0x55B8F0 an atlas entry : %s" % (first in atlas))
    e = A.entry_at_or_before(rows, first)
    print("nearest atlas entry <= it  : %08X  size=%s (decimal) -> ends %08X"
          % (e[0], e[1]["size"], e[0] + int(e[1]["size"])))
    ok, insn, why = A.boundary_check(b, e[0], first)
    print("boundary_check from %08X   : is_boundary=%s why=%s" % (e[0], ok, why))
    for insn in A.linear_from(b, end - 8, 16):
        print("  tail %08X  %-8s %s" % (insn.address, insn.mnemonic, insn.op_str))
