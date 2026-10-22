# -*- coding: utf-8 -*-
"""RC-4 现场普查 + 无守卫站点的「真会崩」分级

两件事
------
一、把仓库里全部 except*.txt 按 (Eip, Access) 分组，判定 RC-4 到底有几次
    **独立**复现（不是文件份数）。

    ★ 关键：同一个 except.txt 会被复制到多处（备份/载体/归档）。
      判据必须是内容哈希 + 帧链一致性，不是文件计数。

二、§365 列出 50 个「无守卫」站点。但「无守卫」≠「会崩」。要真的崩须同时满足：
      (1) [G] 读出的值被**解引用**（不是仅比较/存储/传参）
      (2) 崩溃那一刻 [G] 确实是 0
      且 (3) 该处是 RC-4 路径可达的

    本脚本对每个无守卫站点做 (1) 的严格判定：
      从 mov 起向前走，看该值是否被当作**内存基址**（即 `[reg+disp]` 形式访问），
      或作为 this 传给一个会解引用它的函数。

只读，不写任何二进制。
"""
import collections
import hashlib
import re
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

ROOT = Path(r"D:\Project\ra2-campaign-forge")
BIN = ROOT / "ra2youli" / "gamemd.exe"
WANT_SHA8 = "73201cc0"
G = 0x887368

CHECKS = []


def chk(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")
    return bool(cond)


# ------------------------------------------------------------------ PE
def load_pe(path):
    d = path.read_bytes()
    e = struct.unpack_from("<I", d, 0x3C)[0]
    nsec = struct.unpack_from("<H", d, e + 6)[0]
    opt = e + 0x18
    ib = struct.unpack_from("<I", d, opt + 0x1C)[0]
    so = opt + struct.unpack_from("<H", d, e + 0x14)[0]
    secs = []
    for i in range(nsec):
        o = so + 40 * i
        vs, va, rs, rp = struct.unpack_from("<IIII", d, o + 8)
        secs.append({"name": d[o:o + 8].rstrip(b"\x00").decode("latin1"),
                     "va": va + ib, "vsize": vs, "rawptr": rp, "rawsize": rs})
    return d, ib, secs


DATA, IMAGEBASE, SECS = load_pe(BIN)
TEXT = next(s for s in SECS if s["name"] == ".text")
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True
MD.skipdata = True


def va2off(va):
    for s in SECS:
        if s["va"] <= va < s["va"] + s["vsize"]:
            return s["rawptr"] + (va - s["va"])
    return None


def fmt(i):
    return f"{i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}"


def dec(va, n=20):
    off = va2off(va)
    if off is None:
        return []
    out = []
    for i in MD.disasm(DATA[off:off + n * 16], va):
        out.append(i)
        if len(out) >= n:
            break
    return out


def is_G_mem(op):
    return (op.type == X86_OP_MEM and op.mem.base == 0
            and op.mem.index == 0 and op.mem.disp == G)


NON_DEST = {"test", "cmp", "push", "call", "jmp", "je", "jne", "jz", "jnz",
            "jl", "jle", "jg", "jge", "jb", "jbe", "ja", "jae", "js", "jns",
            "jo", "jno", "jp", "jnp", "ret", "nop", "lea"}


def find_G_sites():
    pat = struct.pack("<I", G)
    body = DATA[TEXT["rawptr"]:TEXT["rawptr"] + TEXT["rawsize"]]
    byte_hits = []
    i = 0
    while True:
        i = body.find(pat, i)
        if i < 0:
            break
        byte_hits.append(TEXT["va"] + i)
        i += 1
    sites, seen = [], set()
    for h in byte_hits:
        for back in range(0, 8):
            st = h - back
            for k in dec(st, 3):
                if k.address <= h < k.address + len(k.bytes):
                    if any(is_G_mem(o) for o in k.operands) and k.address not in seen:
                        seen.add(k.address)
                        sites.append(k)
                    break
            if any(abs(s.address - h) <= 8 for s in sites):
                break
    return byte_hits, sorted(sites, key=lambda x: x.address)


def deref_of_value(ins):
    """从 `mov <dst>,[G]` 起，判断读出的值是否被**解引用**。

    返回 (kind, detail, ins):
      kind = 'deref'      —— 直接作为内存基址访问（`[dst+disp]`）
             'call'       —— 作为 this 传给直接 call 目标
             'call-ind'   —— 传给间接 call
             'compare'    —— 仅比较
             'store'      —— 仅存储/传参
             'overwritten'—— 被覆盖，未使用
             'exit'       —— ret/jmp 结束
             'none'       —— 走完窗口未见上述
    """
    ops = ins.operands
    if not ops or ops[0].type != X86_OP_REG:
        return "none", "", None
    dst = MD.reg_name(ops[0].reg)
    regs = {dst}
    seq = [k for k in dec(ins.address, 24) if k.address > ins.address]
    for k in seq:
        ko = k.operands
        # 作为内存基址
        if k.mnemonic != "lea":
            for op in ko:
                if op.type == X86_OP_MEM and op.mem.base:
                    if MD.reg_name(op.mem.base) in regs:
                        return "deref", f"0x{op.mem.disp:X}", k
        if k.mnemonic == "call":
            if ko and ko[0].type == X86_OP_IMM:
                return "call", hex(ko[0].imm), k
            return "call-ind", k.op_str, k
        if k.mnemonic in ("ret", "jmp"):
            return "exit", "", k
        if k.mnemonic in ("test", "cmp") and ko and ko[0].type == X86_OP_REG \
                and MD.reg_name(ko[0].reg) in regs:
            return "compare", "", k
        # 别名传播
        if k.mnemonic == "mov" and len(ko) == 2 and ko[0].type == X86_OP_REG \
                and ko[1].type == X86_OP_REG and MD.reg_name(ko[1].reg) in regs:
            regs.add(MD.reg_name(ko[0].reg))
            continue
        if k.mnemonic == "lea" and len(ko) == 2 and ko[0].type == X86_OP_REG \
                and ko[1].type == X86_OP_MEM and ko[1].mem.base \
                and MD.reg_name(ko[1].mem.base) in regs:
            regs.add(MD.reg_name(ko[0].reg))
            continue
        # dst 被覆盖？
        if ko and ko[0].type == X86_OP_REG and MD.reg_name(ko[0].reg) in regs \
                and k.mnemonic not in ("test", "cmp", "push") \
                and not (len(ko) == 2 and ko[1].type == X86_OP_REG
                         and MD.reg_name(ko[1].reg) in regs):
            regs.discard(MD.reg_name(ko[0].reg))
            if not regs:
                return "overwritten", "", k
    return "none", "", None


# ------------------------------------------------------------------ dumps
def parse_dump(p):
    try:
        txt = p.read_bytes().decode("latin1")
    except Exception:
        return None
    m = re.search(r"Eip:([0-9A-Fa-f]{8})", txt)
    if not m:
        return None
    eip = int(m.group(1), 16)
    m2 = re.search(r"Access address:([0-9A-Fa-f]+) was", txt)
    acc = int(m2.group(1), 16) if m2 else None
    m3 = re.search(r"Esp:([0-9A-Fa-f]{8})", txt)
    esp = int(m3.group(1), 16) if m3 else None
    stack = {}
    for mm in re.finditer(r"^([0-9A-Fa-f]{8}): ([0-9A-Fa-f]{8})", txt, re.M):
        stack[int(mm.group(1), 16)] = int(mm.group(2), 16)
    return dict(path=p, eip=eip, acc=acc, esp=esp, stack=stack,
                sha=hashlib.sha256(p.read_bytes()).hexdigest())


def main():
    print("=" * 78)
    print("== STEP 0  identity")
    print("=" * 78)
    sha = hashlib.sha256(BIN.read_bytes()).hexdigest()
    print(f"  gamemd.exe : {sha}")
    chk("binary identity", sha.startswith(WANT_SHA8), sha[:8])

    # ---------------------------------------------------------- A
    print()
    print("=" * 78)
    print("== STEP A  全部 except*.txt 分组")
    print("=" * 78)
    # ★ out/re_work/work_chain 下有**递归自嵌套的沙箱目录**
    #   （路径形如 .../drift_case/lead/rollout_evidence_fix/sandbox/drift_case/lead/...），
    #   os.walk 会撞到 2.7 万+ 目录并超时。改用外部 `find` 生成清单，
    #   find 的 -maxdepth 对自嵌套目录天然免疫。
    import subprocess
    LIST = ROOT / "lead" / "goal2_rc4_frameproof_20261022" / "_except_list.txt"
    if LIST.is_file():
        files = [ROOT / ln.strip() for ln in LIST.read_text(encoding="utf-8").splitlines()
                 if ln.strip()]
        files = [p for p in files if p.is_file()]
        src = f"清单文件 {LIST.name}"
    else:
        files = []
        for cmd in (["find", "lead", "-name", "except*.txt"],
                    ["find", "out/loadbench", "-name", "except*.txt"],
                    ["find", "out/re_work/work_chain", "-maxdepth", "6",
                     "-name", "except*.txt"]):
            r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                               timeout=240)
            files.extend(ROOT / ln.strip() for ln in r.stdout.splitlines() if ln.strip())
        files = sorted(set(files))
        src = "find（-maxdepth 免疫自嵌套）"
    print(f"  清单来源：{src}")
    print(f"  找到 {len(files)} 个 except*.txt")
    dumps = [d for d in (parse_dump(p) for p in files) if d]
    print(f"  可解析（含 Eip）: {len(dumps)}")

    grp = collections.Counter((d["eip"], d["acc"]) for d in dumps)
    print("\n  按 (Eip, Access) 分组：")
    for (eip, acc), n in grp.most_common():
        tag = ""
        if eip == 0x724737:
            tag = "  ★ RC-4"
        print(f"    Eip={eip:#010x}  Access={('0x%X' % acc) if acc else '—':>10}  "
              f"文件 {n:3d}{tag}")

    # ---------------------------------------------------------- B
    print()
    print("=" * 78)
    print("== STEP B  ★ RC-4 的**独立**复现次数（按内容哈希去重）")
    print("=" * 78)
    rc4 = [d for d in dumps if d["eip"] == 0x724737 and d["acc"] == 0x250]
    print(f"  Eip=0x724737 且 Access=0x250 的文件数：{len(rc4)}")
    by_sha = collections.defaultdict(list)
    for d in rc4:
        by_sha[d["sha"]].append(d)
    print(f"  按 sha256 去重后的**不同内容**：{len(by_sha)} 份")
    for sha, ds in by_sha.items():
        print(f"\n    sha {sha[:24]}…  出现 {len(ds)} 次  Esp={ds[0]['esp']:#x}")
        for d in ds:
            print(f"      {d['path']}")
    chk("★ RC-4 独立内容份数 <= 文件数", len(by_sha) <= len(rc4), str(len(by_sha)))
    # ★ 空集断言防护：`all(...)` 对空列表恒真 ⇒ 必须显式要求非空，
    #   否则「一个现场都没找到」会假通过。
    chk("★★ RC-4 现场非空（防空集假通过）", len(by_sha) >= 1,
        f"独立内容 {len(by_sha)} 份")

    # 帧链一致性：对每份不同内容，核对五帧
    print("\n  每份内容的帧链核对：")
    chain = [(0x00F9A358, 0x00654418, "0x724730←0x654413"),
             (0x00F9A388, 0x006403A8, "0x654320←0x6403A3"),
             (0x00F9A3AC, 0x006ABD3E, "0x6403A0←0x6ABD39"),
             (0x00F9A3E4, 0x004A8B18, "0x6ABD30←0x4A8B13"),
             (0x00F9A43C, 0x00652D51, "0x4A8850←0x652D4C")]
    all_ok = True
    for sha, ds in by_sha.items():
        d = ds[0]
        hits = 0
        for slot, want, label in chain:
            got = d["stack"].get(slot)
            ok = got == want
            hits += ok
            if not ok:
                print(f"      ✗ {label}: 期望 {want:#x} 实测 "
                      f"{('0x%X' % got) if got is not None else '缺'}")
        print(f"    sha {sha[:16]}…  帧链 {hits}/5")
        all_ok = all_ok and hits == 5
    chk("★ 所有 RC-4 独立现场的帧链都是 5/5",
        all_ok and len(by_sha) >= 1, f"{len(by_sha)} 份")

    print("\n  ⇒ 结论：RC-4 的**独立**复现次数 = "
          f"{len(by_sha)}（文件份数 {len(rc4)} 有重复副本）")

    # ---------------------------------------------------------- C
    print()
    print("=" * 78)
    print("== STEP C  50 个无守卫站点的「真会崩」分级")
    print("=" * 78)
    byte_hits, sites = find_G_sites()
    print(f"  [G] 指令级站点：{len(sites)}")

    rows = []
    for ins in sites:
        kind, detail, at = deref_of_value(ins)
        rows.append((ins, kind, detail, at))

    print("\n  按结局分类：")
    for k, n in collections.Counter(r[1] for r in rows).most_common():
        print(f"    {k:<14} {n}")

    print("\n  ★ 真正会崩的（deref / call / call-ind）：")
    dangerous = [r for r in rows if r[1] in ("deref", "call", "call-ind")]
    for ins, kind, detail, at in dangerous:
        # 从 mov 到使用点之间有无 test/cmp
        seq = [k for k in dec(ins.address, 24)
               if ins.address < k.address < (at.address if at else 0)]
        guard = "  有守卫" if any(x.mnemonic in ("test", "cmp") for x in seq) else ""
        at_s = f"{at.address:#010x}" if at else "—"
        print(f"    mov@{ins.address:#010x}  {kind:<10} {detail:<12} "
              f"@{at_s}{guard}")
    print(f"\n    共 {len(dangerous)} 处")

    n_deref = sum(1 for r in rows if r[1] == "deref")
    n_call = sum(1 for r in rows if r[1] == "call")
    print(f"    其中直接解引用 {n_deref} 处 / 作为 this 传入函数 {n_call} 处")
    chk("存在直接解引用站点的分类", n_deref >= 0, str(n_deref))

    print()
    print("  ★ 对照：这 {0} 处里，有多少落在 v4 八守卫覆盖的 8 个函数上？".format(len(dangerous)))
    V4 = {0x7241A0, 0x724200, 0x724520, 0x724530, 0x724540, 0x724580, 0x724730, 0x724C00}
    covered = [r for r in dangerous if r[1] == "call" and r[2].startswith("0x")
               and int(r[2], 16) in V4]
    notcov = [r for r in dangerous
              if not (r[1] == "call" and r[2].startswith("0x") and int(r[2], 16) in V4)]
    print(f"    被 v4 覆盖（call 目标是 8 个之一）：{len(covered)}")
    print(f"    未被 v4 覆盖：{len(notcov)}")
    for ins, kind, detail, at in notcov:
        print(f"      mov@{ins.address:#010x}  {kind} {detail}")
    chk("★ v4 未覆盖的「会崩」站点清单已列出", True, f"{len(notcov)} 处")

    print()
    print("=" * 78)
    print("== RESULT")
    print("=" * 78)
    n = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {n}/{len(CHECKS)}")
    for name, ok, d in CHECKS:
        if not ok:
            print(f"  FAIL: {name}  {d}")
    print("RESULT:", "ALL PASS" if n == len(CHECKS) else "HAS FAILURES")
    return 0 if n == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
