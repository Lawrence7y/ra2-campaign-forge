#!/usr/bin/env python
"""裁决 3 第 1 条 · 3 处「间接 call」站点的真实语义（本轮更正）。

★★ 先更正 §365 的分类错误
  §365 把 `0x4F4562 / 0x6A707F / 0x7777F3` 记成「间接 `call [mem]` 目标未解」。
  **这是分类错误。** 三处在磁盘字节上完全一样：

      8b 0d 68 73 88 00     mov ecx, [0x887368]

  即它们是 `[0x887368]` 的**读取点**，不是 `call [mem]` 站点。
  真正的间接调用在**同一基本块的下一条**，且目标是**虚表槽**：

      0x4F456E  push 0
      0x4F4570  ff 50 0c        call [eax+0x0C]   ; slot 3
      0x6A708B  push 1
      0x6A708D  ff 52 0c        call [edx+0x0C]   ; slot 3
      0x7777FF  push 1
      0x777801  ff 10           call [eax]        ; slot 0（删构）

★ 三处都**有 null 守卫**（`test ecx,ecx` 或 `cmp ecx,ebx` 紧跟 `je`）
  ⇒ 它们**不是**「无守卫站点」，也不构成 v4 的覆盖缺口。

★ 判据
  C1 三处站点字节都是 `8B 0D`（mov ecx,[abs]），不是 FF 15
  C2 读取的绝对地址都是 `0x887368`
  C3 每处读取之后、`call [reg+disp]` 之前，存在 `test`/`cmp` + `je` 守卫
  C4 三处的虚表槽号已读出（slot 3 / slot 3 / slot 0）
  C5 三处都**不需要** v4 守卫（已有 null 检查）⇒ 更正 §365 的「未解 3 处」

★ 用法
  python _indirect_call_resolve.py
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
GAMEMD = ROOT / "ra2youli/gamemd.exe"

SITES = [0x004F4562, 0x006A707F, 0x007777F3]
SINGLETON = 0x00887368

CHECKS = []


def chk(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print("  [%s] %-56s %s" % ("PASS" if ok else "FAIL", name, detail))


def load_text():
    b = GAMEMD.read_bytes()
    e = struct.unpack("<I", b[0x3C:0x40])[0]
    n = struct.unpack("<H", b[e + 6:e + 8])[0]
    optsz = struct.unpack("<H", b[e + 0x14:e + 0x16])[0]
    opt = e + 0x18
    image_base = struct.unpack("<I", b[opt + 0x1C:opt + 0x20])[0]
    sec = opt + optsz
    for i in range(n):
        p = sec + i * 40
        if b[p:p + 8].rstrip(b"\0") != b".text":
            continue
        vs = struct.unpack("<I", b[p + 8:p + 12])[0]
        va = struct.unpack("<I", b[p + 12:p + 16])[0]
        rs = struct.unpack("<I", b[p + 16:p + 20])[0]
        rp = struct.unpack("<I", b[p + 20:p + 24])[0]
        return b[rp:rp + min(vs, rs)], image_base + va
    raise RuntimeError(".text not found")


def main() -> int:
    print("=" * 78)
    print("裁决 3 第 1 条 · 三处站点的真实语义（更正 §365 分类）")
    print("=" * 78)

    td, tva = load_text()
    print(".text VA=%08X size=%X" % (tva, len(td)))
    print()

    results = []
    for site in SITES:
        off = site - tva
        raw = td[off:off + 32]
        print("--- 站点 %08X ---" % site)
        print("      前 12 字节: %s" % raw[:12].hex())

        # C1：8B 0D
        is_mov_ecx = (raw[0] == 0x8B and raw[1] == 0x0D)
        chk("C1 %08X 是 8B 0D（mov ecx,[abs]）而非 FF 15" % site,
            is_mov_ecx, raw[:2].hex())

        abs_addr = struct.unpack("<I", raw[2:6])[0]
        # C2
        chk("C2 %08X 读的绝对地址 == 0x887368" % site,
            abs_addr == SINGLETON, "got %08X" % abs_addr)

        # C3：扫描后续 0x20 字节，找 test/cmp + je，再找 call [reg+disp]
        guard = None
        callop = None
        i = 6
        while i < min(len(raw), 0x20):
            # test ecx,ecx = 85 C9 ; cmp ecx,ebx = 3B CB
            if raw[i] == 0x85 and raw[i + 1] == 0xC9:
                if raw[i + 2] in (0x74, 0x75):      # je/jne rel8
                    guard = (tva + site + i, "test ecx,ecx / %s"
                             % ("je" if raw[i + 2] == 0x74 else "jne"))
                i += 3
                continue
            if raw[i] == 0x3B and raw[i + 1] == 0xCB:
                if raw[i + 2] in (0x74, 0x75):
                    guard = (tva + site + i, "cmp ecx,ebx / %s"
                             % ("je" if raw[i + 2] == 0x74 else "jne"))
                i += 3
                continue
            # mov eax,[ecx] = 8B 01 ; mov edx,[ecx] = 8B 11
            if raw[i] == 0x8B and raw[i + 1] in (0x01, 0x11):
                i += 2
                continue
            # push imm8 = 6A xx
            if raw[i] == 0x6A:
                i += 2
                continue
            # call [reg+disp8] = FF 50/52/10
            if raw[i] == 0xFF and raw[i + 1] in (0x50, 0x52, 0x10):
                modrm = raw[i + 1]
                reg = {0x50: "eax", 0x52: "edx", 0x10: "eax"}[modrm]
                if modrm == 0x10:
                    slot = 0
                else:
                    slot = raw[i + 2] // 4
                callop = (tva + site + i, "call [%s+0x%X] → slot %d"
                          % (reg, slot * 4, slot))
                break
            i += 1

        chk("C3 %08X 有 null 守卫（test/cmp + je）" % site,
            guard is not None,
            ("%s @%08X" % (guard[1], guard[0])) if guard else "未找到")
        chk("C4 %08X 虚表槽已读出" % site, callop is not None,
            ("%s @%08X" % (callop[1], callop[0])) if callop else "未找到")

        results.append({"site": site, "is_mov_ecx": is_mov_ecx,
                        "abs": abs_addr, "guard": guard, "call": callop})
        print()

    # ---- C5：三处都有守卫 ⇒ 不是 v4 的缺口 ----
    all_guarded = all(r["guard"] is not None for r in results)
    chk("C5 三处都有 null 守卫 ⇒ 不构成 v4 覆盖缺口", all_guarded,
        "guarded=%d/%d" % (sum(1 for r in results if r["guard"]),
                           len(results)))

    print()
    print("=" * 78)
    print("结论（更正 §365）：")
    print("  这三处**不是**「间接 call 目标未解」，而是 [0x887368] 的读取点，")
    print("  真正的调用在下一句、且都是**虚表槽**（slot 3 / slot 3 / slot 0）。")
    print("  三处**全部带 null 守卫** ⇒ 既不需要 v4 守卫，也不构成覆盖缺口。")
    print("  ⇒ v4 的「66/66 站点」不需要把这 3 处算进去，")
    print("     §365 的「3 处间接 call 未解」应改写为「3 处已解：均为带守卫的虚表调用」。")

    print()
    n = len(CHECKS)
    ok = sum(1 for _, v, _ in CHECKS if v)
    print("-" * 78)
    print("结果：%d/%d PASS" % (ok, n))
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(main())
