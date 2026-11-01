#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""c″ 补丁规格独立验证器（不 import 生成器；只吃 JSON 工件+快照+capstone）。

判据（v5 门禁风格）：
  C1 快照锚（sha16 + 站点原窗 8B + 长度钉界）
  C2 站点补丁字节（JSON 里 patch_hex_at_test_base）：E9/rel32→test_base/第6B=90/post窗
  C3 cave 解码=精确 7 条指令序列（mnemonic+op_str 逐条）——把指令布局钉死
  C4 rel32 目标独立重算（布局由 C3 钉死：je@7 jne@20 jmp@26 tail@31）
  C5 cave 长度 36B
变异负控（--selfcheck）：每个变异必须被**其声明的检查**抓住（防多退路假捕获）。
用法：
  python _verify_c2_cave.py                # 净版绿
  python _verify_c2_cave.py --mutate M4    # 单变异必红
  python _verify_c2_cave.py --selfcheck    # 全变异逐个跑+净版绿
"""
import io, json, struct, sys, hashlib, copy
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

HERE = Path(__file__).parent
SPEC = HERE / "d09a_c2_patchspec.json"
SNAP = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020") / "gamemd.exe"
md = Cs(CS_ARCH_X86, CS_MODE_32)


def load_spec():
    return json.loads(io.open(SPEC, "rb").read().decode("utf-8"))


def snapshot():
    return SNAP.read_bytes()


def run_checks(spec, snap):
    fails = []
    site = spec["site"]["va"]
    site = int(site, 16) if isinstance(site, str) else site
    orig = bytes.fromhex(spec["site"]["orig_win_hex"])
    patch = bytes.fromhex(spec["site"]["patch_hex_at_test_base"])
    cave = bytes.fromhex(spec["cave"]["bytes_at_test_base_hex"])
    base = int(spec["cave"]["test_base_hex"], 16)
    loop_head = int(spec["targets"]["loop_head"], 16)
    exit_ip = int(spec["targets"]["exit"], 16)
    f = lambda v: v - 0x400000

    # C1
    if hashlib.sha256(snap).hexdigest()[:16] != spec["snapshot_sha16"]:
        fails.append("C1.sha")
    if snap[f(site):f(site) + len(orig)] != orig:
        fails.append("C1.win")
    if len(orig) != 8:
        fails.append("C1.winlen")

    # C2（断言的是 JSON 里的具体字节，不是现算——防恒真）
    if len(patch) != 6:
        fails.append("C2.len")
    if patch[:1] != b"\xE9":
        fails.append("C2.op")
    if site + 5 + struct.unpack_from("<i", patch, 1)[0] != base:
        fails.append("C2.rel")
    if patch[5:6] != b"\x90":
        fails.append("C2.nop")
    if (patch + orig[6:8])[:1] != b"\xE9":
        fails.append("C2.post")

    # C3
    seq = [(i.mnemonic, i.op_str) for i in md.disasm(cave, base)]
    expect = [
        ("mov", "eax, dword ptr [0xb73550]"),
        ("test", "eax, eax"),
        ("je", hex(exit_ip)),
        ("cmp", "dword ptr [0xa8edd8], 1"),
        ("jne", hex(exit_ip)),
        ("jmp", hex(loop_head)),
        ("jmp", hex(exit_ip)),
    ]
    if len(seq) != len(expect):
        fails.append("C3.count")
    else:
        for i, (got, want) in enumerate(zip(seq, expect)):
            if got != want:
                fails.append("C3.seq[%d]" % i)
                break

    # C4（布局偏移由 C3 钉死：7=je, 20=jne, 26=jmp, 31=tail）
    for off, size, want, name in ((7, 6, exit_ip, "C4.je"),
                                  (20, 6, exit_ip, "C4.jne"),
                                  (26, 5, loop_head, "C4.jmp"),
                                  (31, 5, exit_ip, "C4.tail")):
        got = base + off + size + struct.unpack_from("<i", cave, off + (2 if size == 6 else 1))[0]
        if got != want:
            fails.append(name)

    # C5
    if len(cave) != 36:
        fails.append("C5.len")
    return fails


# 变异表：id → (声明检查, 变异函数 byte 级)
def _mut_orig(s):
    b = bytearray(bytes.fromhex(s["site"]["orig_win_hex"])); b[7] ^= 0x01
    s["site"]["orig_win_hex"] = bytes(b).hex()

def _mut_base(s):
    s["cave"]["test_base_hex"] = hex(int(s["cave"]["test_base_hex"], 16) + 0x10)

def _mut_test_op(s):
    b = bytearray(bytes.fromhex(s["cave"]["bytes_at_test_base_hex"])); b[6] ^= 0x09  # 85C0→85C9
    s["cave"]["bytes_at_test_base_hex"] = bytes(b).hex()

def _mut_je_opcode(s):
    b = bytearray(bytes.fromhex(s["cave"]["bytes_at_test_base_hex"])); b[8] ^= 0x01  # 0F84→0F85
    s["cave"]["bytes_at_test_base_hex"] = bytes(b).hex()

def _mut_je_rel(s):
    b = bytearray(bytes.fromhex(s["cave"]["bytes_at_test_base_hex"])); b[11] ^= 0x10
    s["cave"]["bytes_at_test_base_hex"] = bytes(b).hex()

def _mut_jmp_rel(s):
    b = bytearray(bytes.fromhex(s["cave"]["bytes_at_test_base_hex"])); b[27] ^= 0x10
    s["cave"]["bytes_at_test_base_hex"] = bytes(b).hex()

def _mut_tail_rel(s):
    b = bytearray(bytes.fromhex(s["cave"]["bytes_at_test_base_hex"])); b[32] ^= 0x10
    s["cave"]["bytes_at_test_base_hex"] = bytes(b).hex()

def _mut_site_rel(s):
    b = bytearray(bytes.fromhex(s["site"]["patch_hex_at_test_base"])); b[1] ^= 0x10
    s["site"]["patch_hex_at_test_base"] = bytes(b).hex()

def _mut_cave_len(s):
    s["cave"]["bytes_at_test_base_hex"] += "90"

MUTATIONS = {
    "M1_orig_win":   ("C1.win",  _mut_orig),
    "M2_base":       ("C2.rel",  _mut_base),
    "M3_site_rel":   ("C2.rel",  _mut_site_rel),
    "M4_test_op":    ("C3.seq",  _mut_test_op),
    "M5_je_opcode":  ("C3.seq",  _mut_je_opcode),
    "M6_je_rel":     ("C4.je",   _mut_je_rel),
    "M7_jmp_rel":    ("C4.jmp",  _mut_jmp_rel),
    "M8_tail_rel":   ("C4.tail", _mut_tail_rel),
    "M9_cave_len":   ("C5.len",  _mut_cave_len),
}


def main():
    args = sys.argv[1:]
    spec0 = load_spec()
    snap = snapshot()

    if "--selfcheck" in args:
        for mid, (declared, mut) in MUTATIONS.items():
            s = copy.deepcopy(spec0)
            mut(s)
            fails = run_checks(s, snap)
            if not fails:
                print("逃逸：%s 未被任何检查抓住 ⇒ 门禁恒真" % mid)
                return 2
            hit = [x for x in fails if x == declared or x.startswith(declared + "[") or x.startswith(declared + ".")]
            if not hit:
                print("错抓：%s 被抓于 %s，声明的是 %s" % (mid, fails, declared))
                return 2
            print("  %s → 红 @%s ✓" % (mid, ",".join(hit)))
        fails = run_checks(spec0, snap)
        if fails:
            print("净版红：%s" % fails)
            return 2
        print("selfcheck OK：%d 检查绿（净版），%d 变异全被抓且抓在声明检查上" % (5, len(MUTATIONS)))
        return 0

    if "--mutate" in args:
        mid = args[args.index("--mutate") + 1]
        s = copy.deepcopy(spec0)
        MUTATIONS[mid][1](s)
        fails = run_checks(s, snap)
        if fails:
            print("MUT %s 红（符合预期）: %s" % (mid, fails[:3]))
            return 1
        print("MUT %s 逃逸！" % mid)
        return 2

    fails = run_checks(spec0, snap)
    if fails:
        print("FAIL: %s" % fails)
        return 1
    print("PASS: c″ spec 全绿（C1 锚 / C2 站点 / C3 序列 / C4 rel32 / C5 长度）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
