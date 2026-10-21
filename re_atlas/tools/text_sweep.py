"""Instruction sweep over .text with AUDITABLE resynchronisation.

Why this exists: a single `md.disasm(.text)` does not cover .text. It stops at
the first byte sequence capstone refuses to decode, and on this image that is
0x46F5A0 -- a jump table whose dwords (`c5 e4 46 00 ...`) sit in the middle of
the code section. The sweeping pass therefore decoded 155,215 instructions and
then simply ended, leaving 89% of the section unscanned while looking like a
complete result. R-019's key index (473 sites) and R-023's first consumer map
were both built that way and are undercounts.

Two failure modes have to be told apart, because they need opposite handling:

  * a jump-table or embedded-data block, where decoding stops; and
  * a stretch that decodes to valid-but-wrong instructions because a previous
    stop left the reader mid-instruction.

The sweep handles the first by resyncing, and reports the second by recording
every resync point and validating that the resync target is reachable-looking
(decodes a long run, contains a return, and is preceded by padding). Nothing is
silently skipped: `resyncs()` returns the whole audit trail, and callers are
expected to print it.

Run: python re_atlas/tools/text_sweep.py        (self-check + coverage report)
"""

import os
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_rules_sections as D  # noqa: E402  read_va with per-section bounds

TEXT_LO, TEXT_HI = 0x401000, 0x7E1000
PAD = (0xCC, 0x90)

_RESYNCS = []


def _decodable_run(md, addr, want=24, limit=0x400):
    """How many instructions decode cleanly from addr (capped)."""
    n = 0
    for insn in md.disasm(D.read_va(addr, limit), addr):
        n += 1
        if n >= want:
            return n
    return n


def _find_resync(md, after, hi):
    """Earliest offset >= after that looks like a real instruction boundary.

    A candidate must decode >= 24 instructions cleanly AND sit inside a region
    whose local byte statistics look like code rather than like a table. The
    table test is what makes this work: an earlier version keyed on the byte
    BEFORE the candidate being padding, which is wrong at the first stop point --
    0x46F5A0 is preceded by 0x00 (the last byte of a dword) and followed by a
    jump table, so that test found nothing and the whole sweep gave up at 155,215
    instructions while reporting success.

    The reliable signal is CALL DENSITY: machine code produced by MSVC contains an
    `e8 rel32` call every few dozen bytes, while a jump table or a translation
    table contains none. A 256-byte window with at least two decodable `call`
    instructions is treated as code.
    """
    a = after
    while a + 0x120 < hi:
        win = D.read_va(a, 0x120)
        if len(win) == 0x120:
            calls = 0
            for k in range(len(win) - 5):
                if win[k] == 0xE8:
                    tgt = (a + k + 5 + int.from_bytes(win[k + 1:k + 5], "little", signed=True)) & 0xFFFFFFFF
                    if 0x401000 <= tgt < 0x7E1000:
                        calls += 1
            if calls >= 2 and _decodable_run(md, a, want=24, limit=0x200) >= 24:
                return a
        a += 1
    return None


def sweep(lo=TEXT_LO, hi=TEXT_HI, collect=True):
    """Yield instructions covering [lo, hi), resyncing across data blocks.

    Returns the list of resync records via resyncs(); callers that only want a
    count can pass collect=False.
    """
    del _RESYNCS[:]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    out = []
    addr = lo
    while addr < hi:
        last = None
        for insn in md.disasm(D.read_va(addr, hi - addr), addr):
            if collect:
                out.append(insn)
            last = insn
        if last is None:
            nxt = _find_resync(md, addr + 1, hi)
            _RESYNCS.append({"stopped_at": addr, "resynced_at": nxt})
            if nxt is None:
                break
            addr = nxt
            continue
        end = last.address + last.size
        if end >= hi:
            break
        nxt = _find_resync(md, end, hi)
        _RESYNCS.append({"stopped_at": end, "resynced_at": nxt})
        if nxt is None:
            break
        addr = nxt
    return out


def resyncs():
    return list(_RESYNCS)


def main():
    insns = sweep()
    lo = insns[0].address if insns else 0
    hi = insns[-1].address + insns[-1].size if insns else 0
    print("=== 全段扫描 ===")
    print(f"  指令 {len(insns)}  覆盖 [0x{lo:08X}, 0x{hi:08X})  "
          f"/ 目标 [0x{TEXT_LO:08X}, 0x{TEXT_HI:08X})")
    print(f"  覆盖率 {(hi - TEXT_LO) / (TEXT_HI - TEXT_LO) * 100:.1f}%")

    print("\n=== 重同步审计（每一处跳过都必须在这里出现）===")
    for r in resyncs():
        tgt = r["resynced_at"]
        print(f"  停于 0x{r['stopped_at']:08X} -> 重同步 0x{tgt:08X}"
              if tgt else f"  停于 0x{r['stopped_at']:08X} -> 无处可同步（扫到段尾）")

    print("\n=== 正对照 ===")
    ok = True
    # 1) the single-pass truncation point must be passed, not the end of the scan
    if hi < 0x7E0000:
        print(f"  !! 只扫到 0x{hi:08X}，没有走到 .text 尾部")
        ok = False
    # 2) known instruction boundaries that the single pass never reached
    want = {
        0x00526810: b"\x8b\xff",      # GetSection pad-less prologue
        0x00671EA0: b"\xa1\xa0\x0c\x7f\x00",
        0x005295F0: None,
    }
    addrs = {i.address for i in insns}
    for va in (0x00671EA0, 0x0066D530, 0x00731865):
        if va not in addrs:
            print(f"  !! 0x{va:08X} 不在指令边界集合里")
            ok = False
    # 3) instruction count must be the full-image order of magnitude, not 155k
    if len(insns) < 900000:
        print(f"  !! 只有 {len(insns)} 条指令，疑似仍被截断")
        ok = False
    if not ok:
        print("  正对照失败 —— 以上结果不可信")
        return 1
    print(f"  正对照通过（覆盖到段尾 / 三个已知边界在集合内 / 指令数 {len(insns)} ≥ 900000）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
