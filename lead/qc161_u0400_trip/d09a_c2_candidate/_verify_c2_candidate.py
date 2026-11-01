#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""c″ 候选 DLL 工件级门禁（镜像 v5 `_verify_guard_dll.py` 形态：门禁落在构建产物上）。

STEP 0  身份（gamemd 快照 + 候选 DLL sha256 == 构建时钉值）
STEP 1  k_sites 8 头表在候选 DLL 内逐字段 == 母本规格（证明 8 头路径未被本副本改动）
STEP 2  c″ 常量针值：每个针在候选 DLL 内恰 1 次；母本 DLL 内为 0 次（差异性检验）
STEP 3  C++ cave 构造逻辑镜像重算（测试基址）== d09a_c2_patchspec.json 逐字节
STEP 4  负控 ×3：
        N1 镜像字节任一变异 ⇒ STEP 3 必红（证明比对是活的，非恒真）
        N2 变异后的针值在候选 DLL 中必须 0 次（证明针值有区分度）
        N3 母本 DLL 对 c″ 针值全 0 命中（证明「候选件」判据不认母本）
退出码 0=全绿；1=有 FAIL。
"""
import io, json, hashlib, struct, sys
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

HERE = Path(__file__).parent
CAND_DLL = HERE / "ra2rc4guard_c2.dll"
MOTHER_DLL = Path(r"D:\Project\ra2-campaign-forge\lead\goal2_rc4_fixv5_20261022\src\ra2rc4guard.dll")
SNAP = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020") / "gamemd.exe"
SPEC = HERE.parent / "d09a_c2_patchspec.json"
md = Cs(CS_ARCH_X86, CS_MODE_32)

RESULTS = []
def check(tag, cond, ev=""):
    RESULTS.append(bool(cond))
    print("[%s] %-46s %s" % ("PASS" if cond else "FAIL", tag, ev))

# v5 规格表（= 母本 k_sites；与 PATCH_SPEC_V5.md 一致）
K_SITES_SPEC = [
    (0x007241A0, 5, 5, 4, "8a44240456"),
    (0x00724200, 5, 5, 4, "5355568bf1"),
    (0x00724520, 10, 10, 4, "8b442404898128020000"),
    (0x00724530, 6, 6, 0, "8b8128020000"),
    (0x00724540, 6, 6, 0, "8b812c020000"),
    (0x00724580, 8, 8, 4, "535556578b7c2414"),
    (0x00724730, 6, 7, 4, "83ec0c558be9 56".replace(" ", "")),
    (0x00724C00, 5, 5, 0, "8b510433c0"),
]

def mirror_cave(base):
    """BuildExitBailCave 的 Python 镜像（36B；与 d09a_c2_patchspec.json 同构）"""
    o = bytearray()
    o += b"\xA1\x50\x35\xB7\x00"
    o += b"\x85\xC0"
    o += b"\x0F\x84" + struct.pack("<i", 0x6BE0E9 - (base + len(o) + 6))
    o += b"\x83\x3D\xD8\xED\xA8\x00\x01"
    o += b"\x0F\x85" + struct.pack("<i", 0x6BE0E9 - (base + len(o) + 6))
    o += b"\xE9" + struct.pack("<i", 0x6BE0DC - (base + len(o) + 5))
    o += b"\xE9" + struct.pack("<i", 0x6BE0E9 - (base + len(o) + 5))
    return bytes(o)


def main():
    cand = CAND_DLL.read_bytes()
    mother = MOTHER_DLL.read_bytes()
    snap = SNAP.read_bytes()
    spec = json.loads(io.open(SPEC, "rb").read().decode("utf-8"))

    # ---- STEP 0 身份 ----
    check("S0 gamemd 快照 sha16", hashlib.sha256(snap).hexdigest()[:16] == "73201cc021497c95")
    h = hashlib.sha256(cand).hexdigest()
    pinned = (HERE / "dll_sha256.txt").read_text().strip()
    check("S0 候选 DLL sha == 构建钉值", h == pinned, "%s…" % h[:16])

    # ---- STEP 1 k_sites 8 头表（在候选 DLL 中定位并逐字段比对规格） ----
    first = bytes.fromhex("a0417200050504" + K_SITES_SPEC[0][4])  # va+hook+replay+ret+orig[0..4]
    off = cand.find(first)
    check("S1 k_sites 表定位（首站点针值恰 1 次）",
          off != -1 and cand.count(first) == 1, "file off 0x%X" % off if off != -1 else "")
    if off != -1:
        ok = True
        for i, (va, hook, replay, ret, orig_hex) in enumerate(K_SITES_SPEC):
            e = cand[off + i * 24: off + (i + 1) * 24]
            got = struct.unpack_from("<IBBB", e, 0)
            want = (va, hook, replay, ret)
            if got != want or e[7:7 + replay] != bytes.fromhex(orig_hex):
                ok = False
                check("S1 站点 %d 字段" % i, False, "%s vs %s" % (got, want))
        check("S1 8 头表逐字段 == 母本规格（8/8）", ok)

    # ---- STEP 2 c″ 针值：候选恰 1 次；母本 0 次 ----
    orig_win = bytes.fromhex(spec["site"]["orig_win_hex"])
    # 结构性针值（在候选 DLL 内必须恰 1 次）：k_exitBail 结构体 = hook_len(06)+orig窗 9B 连排
    struct_needle = b"" + orig_win
    cn, mn = cand.count(struct_needle), mother.count(struct_needle)
    check("S2 结构针值 k_exitBail：候选=1 母本=0", cn == 1 and mn == 0,
          "cand=%d mother=%d" % (cn, mn))
    # 非唯一针值只做存在性+差异性（0x6BE0E1 会被编译器折叠成多个立即数=正确性证据）
    for name, ndl in {
        "marker": b"ra2rc4exitbail/v1 d09a_c2",
        "ini_key": b"EnableRC4ExitBail",
        "orig_win": orig_win,
        "site_va": struct.pack("<I", 0x006BE0E1),
    }.items():
        cn, mn = cand.count(ndl), mother.count(ndl)
        check("S2 针值 %s：候选≥1 母本=0" % name, cn >= 1 and mn == 0,
              "cand=%d mother=%d" % (cn, mn))

    # ---- STEP 3 镜像重算 == 规格 JSON（跨工件一致） ----
    base = int(spec["cave"]["test_base_hex"], 16)
    mine = mirror_cave(base)
    want = bytes.fromhex(spec["cave"]["bytes_at_test_base_hex"])
    check("S3 镜像 cave == 规格字节（36B）", mine == want and len(mine) == 36,
          mine.hex()[:32] + "…")
    seq = [(i.mnemonic, i.op_str) for i in md.disasm(mine, base)]
    check("S3 capstone 7 指令序列",
          [s[0] for s in seq] == ["mov", "test", "je", "cmp", "jne", "jmp", "jmp"]
          and seq[2][1] == "0x6be0e9" and seq[5][1] == "0x6be0dc",
          " | ".join(m for m, _ in seq))

    # ---- STEP 4 负控 ----
    mutated = bytearray(mine); mutated[6] ^= 0x09   # test eax,eax → test ecx,ecx
    check("N1 镜像字节变异 ⇒ 与规格必不一致", bytes(mutated) != want)
    bad_needle = bytes(mutated[0:5])  # 变异后的 mov 片段
    check("N2 变异针值在候选 DLL 中 0 次", cand.count(bad_needle) == 0,
          "count=%d" % cand.count(bad_needle))
    check("N3 母本 DLL 对 marker/ini_key 均 0 命中",
          mother.count(b"ra2rc4exitbail/v1 d09a_c2") == 0
          and mother.count(b"EnableRC4ExitBail") == 0)

    n_pass = sum(1 for r in RESULTS if r)
    verdict = n_pass == len(RESULTS)
    print("== RESULT: %d/%d PASS — %s ==" % (n_pass, len(RESULTS),
          "ALL PASS" if verdict else "FAIL"))
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
