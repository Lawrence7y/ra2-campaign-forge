#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""c″（泵等待环 hwnd==0 逃生门）补丁规格生成器 — 设计工件，未部署。

§432 定稿：E9@0x6BE0E1（覆盖 cmp 前 5B）+ 90@0x6BE0E6；cave=
  mov eax,[0xB73550] / test / je exit / cmp [0xA8EDD8],1 / jne exit / jmp 0x6BE0DC
  exit: jmp 0x6BE0E9
语义=B 兄弟（0x6BEC94..9B）自带的 bail 原样嫁接；原 je@0x6BE0E7 变死代码。

产出 lead/qc161_u0400_trip/d09a_c2_patchspec.json：
  - 快照锚（sha16 + 站点原窗字节断言）
  - E9 rel32 模板（cave 基址运行期由守卫分配器给；离线验证用测试基址）
  - cave 36B 模板（4 个 rel32 占位，位置无关长度）
  - 断言清单（门禁判据表，verify 脚本独立重查）
负控由 _verify_c2_cave.py --selfcheck 承担（每个变异必须被抓）。
"""
import io, json, struct, hashlib, subprocess, sys
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

SNAP = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020") / "gamemd.exe"
EXPECT_SHA16 = "73201cc021497c95"
SITE = 0x6BE0E1
ORIG_WIN = bytes.fromhex("393dd8eda80074f3")   # cmp dword[0xA8EDD8],edi + je 0x6BE0DC
LOOP_HEAD = 0x6BE0DC
EXIT_IP = 0x6BE0E9
TEST_CAVE = 0x10001000        # 离线测试基址（运行期实际由守卫分配器给，姊妹 cave 不共用）

DATA = SNAP.read_bytes()
assert hashlib.sha256(DATA).hexdigest()[:16] == EXPECT_SHA16, "snapshot drifted"
f = lambda v: v - 0x400000


def cave_bytes(base):
    """编码 cave；base=运行期 cave VA。返回 (bytes, [断言描述])"""
    out = bytearray()
    out += b"\xA1\x50\x35\xB7\x00"                      # mov eax,[0x00B73550]
    out += b"\x85\xC0"                                  # test eax,eax
    out += b"\x0F\x84" + struct.pack("<i", EXIT_IP - (base + len(out) + 6))   # je exit
    out += b"\x83\x3D\xD8\xED\xA8\x00\x01"              # cmp dword[0x00A8EDD8],1
    out += b"\x0F\x85" + struct.pack("<i", EXIT_IP - (base + len(out) + 6))   # jne exit
    out += b"\xE9" + struct.pack("<i", LOOP_HEAD - (base + len(out) + 5))     # jmp loop_head
    exit_ip = base + len(out)
    out += b"\xE9" + struct.pack("<i", EXIT_IP - (exit_ip + 5))               # exit: jmp 0x6BE0E9
    return bytes(out)


def site_patch_bytes(base):
    """站点补丁：E9 rel32（覆盖 cmp 前 5B）+ 90（cmp 第 6B）；原 je 变死代码。"""
    rel = base - (SITE + 5)
    return b"\xE9" + struct.pack("<i", rel) + b"\x90"


def main():
    win = DATA[f(SITE):f(SITE) + len(ORIG_WIN)]
    assert win == ORIG_WIN, "site window mismatch: %s" % win.hex()

    cave = cave_bytes(TEST_CAVE)
    site = site_patch_bytes(TEST_CAVE)

    # 自检 1：站点 E9 解回 cave 基址
    got = struct.unpack_from("<i", site, 1)[0]
    assert SITE + 5 + got == TEST_CAVE, "site E9 target mismatch"

    # 自检 2：capstone 逐条解码 cave，断言语义序列
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    seq = [(i.mnemonic, i.op_str) for i in md.disasm(cave, TEST_CAVE)]
    expect_seq = [
        ("mov", "eax, dword ptr [0xb73550]"),
        ("test", "eax, eax"),
        ("je", "0x6be0e9"),
        ("cmp", "dword ptr [0xa8edd8], 1"),
        ("jne", "0x6be0e9"),
        ("jmp", "0x6be0dc"),
        ("jmp", "0x6be0e9"),
    ]
    assert len(seq) == len(expect_seq), "cave instr count %d != %d" % (len(seq), len(expect_seq))
    for i, ((m, o), (em, eo)) in enumerate(zip(seq, expect_seq)):
        assert m == em and o == eo, "cave[%d] %s %s != %s %s" % (i, m, o, em, eo)

    # 自检 3：第二个 je/jne 的 rel32 目标=EXIT_IP（je 分支的本体跳转）
    je_off = 5 + 2                      # je 指令起点
    je_target = TEST_CAVE + je_off + 6 + struct.unpack_from("<i", cave, je_off + 2)[0]
    assert je_target == EXIT_IP
    jne_off = je_off + 6 + 7            # jne 指令起点
    jne_target = TEST_CAVE + jne_off + 6 + struct.unpack_from("<i", cave, jne_off + 2)[0]
    assert jne_target == EXIT_IP

    spec = {
        "name": "d09a_c2_exitbail",
        "gated_by": "[Logic] EnableRC4Guard（复用守卫总闸）或独立 EnableRC4ExitBail（Lead 裁决）",
        "sibling_cave_rule": "新专用 cave，不与 v5 8 头 cave 共用（RC4-SPEC-V2 姊妹 cave 规则）",
        "snapshot_sha16": EXPECT_SHA16,
        "site": {"va": SITE, "orig_win_hex": ORIG_WIN.hex(), "len": 8,
                 "patch_hex_at_test_base": site.hex(),
                 "patch_hex_template": "e9{rel32}90",
                 "dead_after": "je@0x6BE0E7 74F3 不可达（E9 不落回）"},
        "cave": {"va_template": "runtime-allocated (v5 分配器同域, 参考基址 0x10000000 区)",
                 "len": len(cave), "test_base_hex": hex(TEST_CAVE),
                 "bytes_at_test_base_hex": cave.hex()},
        "targets": {"loop_head": hex(LOOP_HEAD), "exit": hex(EXIT_IP)},
        "semantics": "hwnd==0 ⇒ 放弃等待出环（=B@0x6BEC94..9B 原生 bail）；"
                     "exitstate!=1 ⇒ 出环（原 cmp/je 语义）；否则回 0x6BE0DC 继续泵等",
        "regs": "cave 仅动 eax（call 泵后 eax 本就死值）；不碰栈；E9 不经 ret",
        "verify_recipe": "_verify_c2_cave.py --selfcheck（独立重查 + 每个变异必被抓）",
    }
    out_p = Path(__file__).parent / "d09a_c2_patchspec.json"
    io.open(out_p, "w", encoding="utf-8").write(json.dumps(spec, ensure_ascii=False, indent=1))
    print("OK spec written:", out_p.name)
    print("  site patch @%08X (test base): %s" % (SITE, site.hex(" ")))
    print("  cave %dB @%08X: %s" % (len(cave), TEST_CAVE, cave.hex(" ")))
    print("  decoded seq:")
    for (m, o) in seq:
        print("    %s %s" % (m, o))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
