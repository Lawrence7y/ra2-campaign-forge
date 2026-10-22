# -*- coding: utf-8 -*-
"""待办 9 第二段：5 个 RadarClass 构造宿主的调用链与时机判定。

已定案前提（§352，本轮不复证）
------------------------------
- 表 B `0x7F0344` = RadarClass，slot5 = `0x652CF0` = One_Time
- 唯一装表 B 的函数 `0x652C00` 有 6 个调用者：
  `0x40D1F7`（退出期 atexit 回调内，作用在 MouseClass 单例上）
  `0x40D2D4` / `0x5BEA0A` / `0x6404B3` / `0x69391A` / `0x6AC81A`（运行期，作用在参数对象上）
- One_Time 只经表 B slot5 可达（.rdata 唯一 dword + 0 处 E8）

本脚本要答
----------
对这 5 个运行期宿主，各自求 **E8 调用闭包**（向上），并给每个闭包成员打**时机标签**：
  启动初始化 / 每局开局 / 载图 / 每帧 / 显示模式切换 / 退出 / 其它

判定依据（按强度降序）：
  1. **字符串证据**（最硬）：宿主闭包内 push 的可读串含 Scenario/Load/Map/Start 等；
  2. 是否在 `0x6930A0`（WndProc 分派目标）闭包内；
  3. 是否在消息泵 `0x5D4D50` 闭包内；
  4. 是否在静态构造表（`.data` 指针表）内。

输出：每个宿主的「闭包规模 / 时机标签 / 关键字符串 / 判定」。
"""
import hashlib
import struct
import sys
from collections import deque
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"

HOSTS = {
    0x40D2D4: "caller_40D2D4",
    0x5BEA0A: "caller_5BEA0A",
    0x6404B3: "caller_6404B3",
    0x69391A: "caller_69391A",
    0x6AC81A: "caller_6AC81A",
}
PUMP = 0x5D4D50          # 消息泵（§346 定案）
WNDPROC_DISPATCH = 0x6930A0
REINIT = 0x652C00

# 时机关键词 → 标签
TIMING_KW = [
    ("Scenario", "场景/战役"),
    ("scenario", "场景/战役"),
    ("Load", "载入"),
    ("load", "载入"),
    ("Map", "地图"),
    ("map", "地图"),
    ("Start", "开局"),
    ("Init", "初始化"),
    ("Initializ", "初始化"),
    ("New Game", "开局"),
    ("Resume", "读档"),
    ("Save", "存档"),
    ("Mode", "显示模式"),
    ("Surface", "显示模式"),
    ("Exit", "退出"),
    ("Quit", "退出"),
    ("Shutdown", "退出"),
]

CHECKS = []


def chk(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")
    return bool(cond)


class PE:
    def __init__(self, data):
        self.data = data
        e = struct.unpack_from("<I", data, 0x3C)[0]
        self.imagebase = struct.unpack_from("<I", data, e + 0x18 + 0x1C)[0]
        nsec = struct.unpack_from("<H", data, e + 0x06)[0]
        optsz = struct.unpack_from("<H", data, e + 0x14)[0]
        off = e + 0x18 + optsz
        self.sections = []
        for i in range(nsec):
            o = off + i * 40
            nm = data[o:o + 8].rstrip(b"\x00").decode("ascii", "ignore")
            vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, o + 8)
            self.sections.append({"name": nm, "vsize": vsize, "va": vaddr,
                                  "rawsize": rawsize, "rawptr": rawptr})

    def va2off(self, va):
        rva = va - self.imagebase
        for s in self.sections:
            if s["va"] <= rva < s["va"] + max(s["vsize"], s["rawsize"]):
                d = rva - s["va"]
                return s["rawptr"] + d if d < s["rawsize"] else None
        return None

    def read(self, va, n):
        o = self.va2off(va)
        return None if o is None or o + n > len(self.data) else self.data[o:o + n]

    def cstr(self, va, n=100):
        b = self.read(va, n)
        if not b:
            return None
        z = b.split(b"\x00")[0]
        try:
            s = z.decode("ascii")
        except Exception:
            return None
        return s if 4 <= len(s) and all(32 <= ord(c) < 127 or c in "\t\n" for c in s) else None


def main():
    print("=" * 78)
    print("== STEP 0  identity + decode")
    print("=" * 78)
    data = BIN.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    print(f"sha256 : {sha}")
    if not chk("sha256[:8] == " + WANT_SHA8, sha[:8] == WANT_SHA8, sha[:8]):
        return 1
    pe = PE(data)
    text = next(s for s in pe.sections if s["name"] == ".text")
    text_va = text["va"] + pe.imagebase
    end = text_va + text["rawsize"]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    insns = []
    cur = text_va
    while cur < end:
        off = pe.va2off(cur)
        if off is None:
            break
        chunk = data[off:off + (end - cur)]
        got = 0
        last = cur
        for i in md.disasm(chunk, cur):
            insns.append(i)
            got += 1
            last = i.address + i.size
        cur = last if got else cur + 1
    print(f"decoded {len(insns)}")
    if not chk("decoded > 500000", len(insns) > 500000, str(len(insns))):
        return 1

    # 建 E8 图：caller -> set(callee)
    callees = {}
    callers = {}
    idx_of = {i.address: k for k, i in enumerate(insns)}
    for i in insns:
        if i.mnemonic == "call" and i.operands and i.operands[0].type == X86_OP_IMM:
            t = i.operands[0].imm & 0xFFFFFFFF
            if text_va <= t < end:
                callees.setdefault(i.address, set()).add(t)
                callers.setdefault(t, set()).add(i.address)

    # 预建函数头集合：所有「前一条是 ret/int3」的指令地址 + 段首
    # ★ 必须预先算好，否则在 func_range 里边扫边算会退化成 O(n^2)。
    HEADS = []
    prev_term = True
    for i in insns:
        if prev_term:
            HEADS.append(i.address)
        prev_term = i.mnemonic in ("ret", "retn", "int3", "hlt")
    HEADS_SET = set(HEADS)
    HEADS_SORTED = sorted(HEADS_SET)

    def func_head_of(va):
        """向上找函数头：小于等于 va 的最大 HEADS 成员。"""
        import bisect
        k = bisect.bisect_right(HEADS_SORTED, va) - 1
        return HEADS_SORTED[k] if k >= 0 else insns[0].address

    def func_range(head):
        """函数体范围：head 到下一个函数头（用预建表，O(log n)）。"""
        import bisect
        k = bisect.bisect_right(HEADS_SORTED, head)
        nxt = HEADS_SORTED[k] if k < len(HEADS_SORTED) else (end)
        return head, min(nxt, head + 0x4000)

    def upward_closure(start_va, max_nodes=400, max_depth=6):
        """从 start_va 向上求 E8 闭包（谁调它）。

        ★ 关键：`callers` 是按**被调目标地址**索引的，而一个函数体内部可能有多处
          `call 目标`。所以必须对「当前函数体范围内的所有 call 目标」求 callers，
          不能只查函数头那一个地址（本轮首版就错在这里，闭包恒为 1）。
        """
        seen = set()
        q = deque([(start_va, 0)])
        while q:
            head, d = q.popleft()
            if head in seen or len(seen) >= max_nodes:
                continue
            seen.add(head)
            if d >= max_depth:
                continue
            # 收集该函数体内所有 call 目标
            lo, hi = func_range(head)
            k = idx_of.get(head)
            targets = set()
            if k is not None:
                while k < len(insns) and insns[k].address < hi:
                    p = insns[k]
                    if p.mnemonic == "call" and p.operands \
                            and p.operands[0].type == X86_OP_IMM:
                        targets.add(p.operands[0].imm & 0xFFFFFFFF)
                    k += 1
            # 对本函数自身 + 所有被调目标，找谁调用
            for t in targets | {head}:
                for c in callers.get(t, ()):
                    ch = func_head_of(c)
                    if ch is not None and ch not in seen:
                        q.append((ch, d + 1))
        return seen

    def strings_in(head):
        lo, hi = func_range(head)
        out = []
        k = idx_of.get(head)
        if k is None:
            return out
        while k < len(insns) and insns[k].address < hi:
            p = insns[k]
            if p.mnemonic == "push" and p.operands and p.operands[0].type == X86_OP_IMM:
                v = p.operands[0].imm & 0xFFFFFFFF
                if 0x7E1000 <= v < 0xB96000:
                    s = pe.cstr(v)
                    if s:
                        out.append((p.address, v, s))
            k += 1
        return out

    print()
    print("=" * 78)
    print("== STEP 1  per-host upward closure + timing tags")
    print("=" * 78)

    summary = []
    for site, label in sorted(HOSTS.items()):
        print(f"\n{'-'*74}")
        print(f"-- {label}  site 0x{site:08X}")
        head = func_head_of(site)
        if head is None:
            print("   !! site not at a boundary")
            continue
        print(f"   host head 0x{head:08X}")
        clo = upward_closure(head)
        print(f"   upward E8 closure: {len(clo)} functions")

        in_pump = PUMP in clo
        in_wnd = WNDPROC_DISPATCH in clo
        print(f"   in pump 0x{PUMP:X} closure : {in_pump}")
        print(f"   in WndProc dispatch closure: {in_wnd}")

        # 收集闭包内所有函数的时机串
        tags = {}
        key_strs = []
        for f in clo:
            for a, v, s in strings_in(f):
                for kw, tag in TIMING_KW:
                    if kw in s:
                        tags.setdefault(tag, []).append((f, s))
                        if len(key_strs) < 12:
                            key_strs.append((f, s))
                        break
        print(f"   timing tags: {sorted(tags.keys())}")
        for f, s in key_strs[:8]:
            print(f"      0x{f:08X}  {s[:70]!r}")

        summary.append({"site": site, "label": label, "head": head,
                        "closure": len(clo), "in_pump": in_pump,
                        "in_wnd": in_wnd, "tags": sorted(tags.keys()),
                        "strs": key_strs[:6]})

    print()
    print("=" * 78)
    print("== STEP 2  verdict per host")
    print("=" * 78)
    for s in summary:
        tags = s["tags"]
        if any(t in ("场景/战役", "载入", "地图", "开局") for t in tags):
            v = "B（换图/载入路径）强候选"
        elif s["in_pump"] or s["in_wnd"]:
            v = "A'（消息/退出期路径）"
        elif any(t in ("显示模式",) for t in tags):
            v = "显示模式切换"
        elif not tags:
            v = "未定（闭包内无时机串）"
        else:
            v = f"其它 {tags}"
        print(f"  0x{s['site']:08X} ({s['label']:<18}) closure={s['closure']:>3} "
              f"pump={s['in_pump']!s:<5} wnd={s['in_wnd']!s:<5} => {v}")

    print()
    print("=" * 78)
    print("== STEP 3  aggregate judgement on branch A/B/A'")
    print("=" * 78)
    b_hosts = [s for s in summary
               if any(t in ("场景/战役", "载入", "地图", "开局") for t in s["tags"])]
    a_hosts = [s for s in summary if s["in_pump"] or s["in_wnd"]]
    print(f"  B-supporting hosts (load/map/scenario strings): {len(b_hosts)}")
    for s in b_hosts:
        print(f"     0x{s['site']:08X}  tags={s['tags']}")
    print(f"  A'-supporting hosts (in pump/WndProc closure): {len(a_hosts)}")
    for s in a_hosts:
        print(f"     0x{s['site']:08X}  tags={s['tags']}")

    if b_hosts and not a_hosts:
        print("  [强推断] 分岔 B：RadarClass 在载图/换图路径上构造 ⇒ One_Time 每次载图重跑")
        verdict = "B_SUPPORTED"
    elif b_hosts and a_hosts:
        print("  [部分] 两类宿主并存 ⇒ B 与 A' 都可能，需看哪个在崩溃现场")
        verdict = "B_AND_APRIME"
    elif a_hosts:
        print("  [强推断] 分岔 A'：宿主在消息/退出路径上")
        verdict = "APRIME_SUPPORTED"
    else:
        print("  [未定] 闭包内无时机串 ⇒ 需真机断点")
        verdict = "UNDETERMINED"

    chk("closure computation produced >=1 host", len(summary) >= 1, str(len(summary)))
    chk("every host has a resolved function head",
        all(s["head"] for s in summary), str(len(summary)))

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print(f"verdict: {verdict}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
