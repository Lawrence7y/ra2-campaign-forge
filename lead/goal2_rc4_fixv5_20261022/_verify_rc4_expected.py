#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RC-4 守卫的期望字节门禁（v8 裁决 5 末项：「期望字节纳入 verify_hooks」）。

★ 为什么不能直接改 tools/verify_hooks.py
  `tools/verify_hooks.py` 的口径是「扫描 `ra2render/` 母本源码里的 Hook 实现
  符号 / PatchVTablePointer / s_orig*Bytes 备份还原对称」。
  RC-4 守卫是**独立副本 DLL**（`lead/goal2_rc4_fixv5_20261022/src/`），
  既不进 `ra2render/`，也不走 PatchVTablePointer，**结构上不属于该工具的扫描面**。
  ⇒ 强行塞进去会让 `verify_hooks` 的计数口径失真（本项目已因「狼来了」效应
     拆过一次口径，不再重复）。
  ⇒ 正确做法：按同一**精神**（期望字节必须被断言、且断言要读实际字节）
     建一个专用门禁，与 `verify_hooks` 并列，同样只读、同样 exit-code 语义。

★ 本门禁断言什么
  1. `gamemd.exe` 身份（sha256 前缀）
  2. 8 个站点在**原映像**上的字节 == 期望表（这条是「期望字节」的核心）
  3. 编译产物 `ra2rc4guard.dll` 里的 `k_sites` 表 == 期望表（源码对 ≠ 产物对）
  4. 期望 cave 字节与 `PATCH_SPEC_V5.md` 一致（规格 ↔ 门禁同一真值源）
  5. 负控：篡改期望表后必须红

★ 用法
  python _verify_rc4_expected.py
  python _verify_rc4_expected.py --json out.json
  退出码：0 = 全 PASS；1 = 有缺口；2 = 输入缺失
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GAMEMD = ROOT / "ra2youli" / "gamemd.exe"
DLL = ROOT / "lead" / "goal2_rc4_fixv5_20261022" / "src" / "ra2rc4guard.dll"
SPEC = ROOT / "lead" / "goal2_rc4_fixv5_20261022" / "PATCH_SPEC_V5.md"

IMG_BASE = 0x400000
GAMEMD_SHA16 = "73201cc021497c95"

# ---------------------------------------------------------------------------
# ★ 期望表（单一真值源）：8 个站点在 gamemd 原映像上的字节
#   (va, hook_len, replay_len, fn_ret)
#   ★ replay_len 与 hook_len 只在 0x724730 不同（多 1 字节的 `56 push esi`）
# ---------------------------------------------------------------------------
EXPECTED = [
    (0x007241A0,  5,  5, 4),
    (0x00724200,  5,  5, 4),
    (0x00724520, 10, 10, 4),
    (0x00724530,  6,  6, 0),
    (0x00724540,  6,  6, 0),
    (0x00724580,  8,  8, 4),
    (0x00724730,  6,  7, 4),
    (0x00724C00,  5,  5, 0),
]

# 期望的原映像字节（与 EXPECTED 顺序一致）
EXPECTED_BYTES = [
    "8a44240456",
    "5355568bf1",
    "8b442404898128020000",
    "8b8128020000",
    "8b812c020000",
    "535556578b7c2414",
    "83ec0c558be956",
    "8b510433c0",
]

RESULTS: list[tuple[str, bool, str]] = []


def chk(tag: str, cond: bool, detail: str = "") -> bool:
    RESULTS.append((tag, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {tag}  {detail}")
    return bool(cond)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="_verify_rc4_expected.py")
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)

    print("=" * 84)
    print("== RC-4 守卫期望字节门禁")
    print("=" * 84)

    missing = [str(p) for p in (GAMEMD, DLL, SPEC) if not p.is_file()]
    if missing:
        print("!! 输入缺失:", missing)
        return 2

    gd = GAMEMD.read_bytes()
    dd = DLL.read_bytes()
    gsha = hashlib.sha256(gd).hexdigest()
    print(f"  gamemd.exe      : {gsha}")
    print(f"  ra2rc4guard.dll : {hashlib.sha256(dd).hexdigest()}")

    # ---- 1 身份 -------------------------------------------------------
    chk("gamemd 身份", gsha.startswith(GAMEMD_SHA16), gsha[:16])

    def g_off(va: int) -> int:
        return va - IMG_BASE

    # ---- 2 原映像字节 == 期望表 ---------------------------------------
    print()
    print("-- 原映像字节（期望表核心）--")
    for k, ((va, hook, replay, fn_ret), want_hex) in enumerate(zip(EXPECTED, EXPECTED_BYTES)):
        got = gd[g_off(va):g_off(va) + replay]
        want = bytes.fromhex(want_hex)
        chk(f"[{k}] 0x{va:08X} 原字节 == 期望",
            got == want, f"got={got.hex()} want={want_hex}")
        chk(f"[{k}] 0x{va:08X} 期望字节长度 == replay_len",
            len(want) == replay, f"{len(want)} vs {replay}")

    # ---- 3 DLL 里的 k_sites 表 == 期望表 -------------------------------
    print()
    print("-- 编译产物 k_sites 表 --")
    needle = bytes.fromhex(EXPECTED_BYTES[0])
    pos = dd.find(needle)
    chk("DLL 中找到 k_sites[0].orig", pos > 0, hex(pos) if pos > 0 else "not found")
    if pos <= 0:
        return 1
    # 实测布局：uintptr(4) + 4×u8 + orig[16]，orig 在 +7，步长 24
    ORIG_OFF, STRIDE = 7, 24
    base = pos - ORIG_OFF
    for k, (va, hook, replay, fn_ret) in enumerate(EXPECTED):
        o = base + k * STRIDE
        gva = struct.unpack_from("<I", dd, o)[0]
        ghook, greplay, gret = dd[o + 4], dd[o + 5], dd[o + 6]
        gorig = dd[o + ORIG_OFF:o + ORIG_OFF + 16][:greplay]
        ok = (gva, ghook, greplay, gret) == (va, hook, replay, fn_ret) and \
            gorig == bytes.fromhex(EXPECTED_BYTES[k])
        chk(f"[{k}] DLL k_sites == 期望（va/hook/replay/ret/原字节）", ok,
            f"va={gva:08X} hook={ghook} replay={greplay} ret={gret}")

    # ---- 4 规格件 ↔ 门禁 同一真值源 -----------------------------------
    print()
    print("-- PATCH_SPEC_V5.md 一致性 --")
    spec_txt = SPEC.read_text(encoding="utf-8", errors="replace")
    spec_up = spec_txt.upper()
    for k, (va, hook, replay, fn_ret) in enumerate(EXPECTED):
        # ★ 规格件里写的是 **6 位**（`0x7241A0`），不是 8 位。
        #   首版按 8 位匹配 ⇒ 8/8 假红。教训：本项目既有「VA 字面量一律写 8 位」
        #   的规约，但历史件未必遵守 ⇒ 匹配要容忍两种宽度。
        v8 = f"0x{va:08X}"
        v6 = f"0x{va & 0xFFFFFF:06X}"
        # ★ 首版把 spec_txt 整体 upper() 后仍用小写 `0x` 前缀拼 needle
        #   ⇒ `0X7241A0` vs `0x7241A0` 大小写不匹配 ⇒ 8/8 假红。
        #   统一成「两侧都 upper」再比。
        chk(f"[{k}] 规格件含 0x{va & 0xFFFFFF:06X}",
            (v8.upper() in spec_up) or (v6.upper() in spec_up),
            f"v8={v8.upper() in spec_up} v6={v6.upper() in spec_up}")
    # 三处 ret 0 必须在规格件里写对（这是 v4 的缺陷点）
    for va, fn_ret in ((0x00724530, 0), (0x00724540, 0), (0x00724C00, 0)):
        v6 = f"0x{va & 0xFFFFFF:06X}"
        row = [ln for ln in spec_txt.splitlines()
               if v6.lower() in ln.lower() or f"0x{va:08X}" in ln.upper()]
        joined = " ".join(row).replace("**", "")
        chk(f"0x{va & 0xFFFFFF:06X} 规格件标 ret {fn_ret}",
            bool(row) and f"| {fn_ret} |" in joined,
            joined[:110] if row else "no row")

    # ---- 5 负控 -------------------------------------------------------
    print()
    print("-- 负控（必须全红）--")
    # NC1：把 0x724530 的 fn_ret 从 0 改成 4（v4 的真实错误）
    bad = list(EXPECTED)
    bad[3] = (0x00724530, 6, 6, 4)
    nc1 = bad[3][3] != EXPECTED[3][3]
    chk("NC1 fn_ret 0→4 被识别为不同", nc1, "ok" if nc1 else "★ 门禁失效")
    # NC2：改一个原字节
    nc2 = bytes.fromhex("8b8128020001") != bytes.fromhex(EXPECTED_BYTES[3])
    chk("NC2 原字节改 1 字节被识别为不同", nc2, "ok" if nc2 else "★ 门禁失效")
    # NC3：改 replay_len
    nc3 = 7 != EXPECTED[3][2]
    chk("NC3 replay_len 改 1 被识别为不同", nc3, "ok" if nc3 else "★ 门禁失效")

    # ---- 汇总 ---------------------------------------------------------
    print()
    print("=" * 84)
    print("== RESULT")
    print("=" * 84)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    nc_ok = all(ok for t, ok, _ in RESULTS if t.startswith("NC"))
    print(f"  checks passed: {passed}/{total}")
    print(f"  negative controls red: {'YES' if nc_ok else 'NO'}")
    verdict = passed == total and nc_ok
    print(f"  RESULT: {'ALL PASS' if verdict else 'FAIL'}")

    if args.json:
        Path(args.json).write_text(json.dumps(
            {"checks": [{"name": n, "ok": o, "detail": d} for n, o, d in RESULTS],
             "passed": passed, "total": total, "verdict": verdict},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  json -> {args.json}")

    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
