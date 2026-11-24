"""Lead 独立抽验工具库（R12）。刻意不复用任何子代理代码。

用途：
  - 从已知函数入口线性反汇编到目标地址，判定"该地址是否指令边界"（R12_FACTS §3-2 的纪律）
  - 全 .text 线性扫描建立 call/jmp 目标表（字节通道的引用模型）
  - 带边界校验的字节模式扫描

设计取舍：
  - 一律按 VA 寻址（ImageBase 0x400000），与台账口径一致。
  - 线性反汇编**不**跟随跳转，只做"从 A 到 B 中间有没有一条指令恰好落在 B"这种判定。
  - `sweep` 只依赖线性反汇编，与 Ghidra 的函数边界模型相互独立 ⇒ 双通道对账用。
"""
import struct
import pefile
import capstone

IMAGE_BASE = 0x400000
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"


class Bin:
    def __init__(self, path=EXE):
        self.pe = pefile.PE(path, fast_load=True)
        self.image_base = self.pe.OPTIONAL_HEADER.ImageBase
        self.sections = []
        for s in self.pe.sections:
            name = s.Name.decode(errors="replace").rstrip("\x00")
            va = self.image_base + s.VirtualAddress
            self.sections.append(
                dict(name=name, va=va, vsize=s.Misc_VirtualSize,
                     raw=s.PointerToRawData, rawsize=s.SizeOfRawData)
            )
        self.text = self.sec(".text")

    def sec(self, name):
        for s in self.sections:
            if s["name"] == name:
                return s
        raise KeyError(name)

    def read(self, va, n):
        """读 VA 处 n 字节（跨节时不处理，直接报错，宁可失败也不给错字节）。"""
        for s in self.sections:
            if s["va"] <= va and va + n <= s["va"] + s["rawsize"]:
                off = s["raw"] + (va - s["va"])
                return self.pe.__data__[off:off + n]
        raise ValueError("VA %08X+%d 不在任何节的 raw 范围内" % (va, n))

    def u32(self, va):
        return struct.unpack("<I", self.read(va, 4))[0]

    def u16(self, va):
        return struct.unpack("<H", self.read(va, 2))[0]

    def u8(self, va):
        return self.read(va, 1)[0]


def md32(skipdata=False):
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    m.skipdata = skipdata
    return m


def linear_from(bin_, start_va, max_bytes, stop_at=None):
    """从 start_va 线性反汇编 max_bytes 字节。不跟随跳转。"""
    m = md32()
    data = bin_.read(start_va, max_bytes)
    out = []
    for insn in m.disasm(data, start_va):
        out.append(insn)
        if stop_at is not None and insn.address >= stop_at:
            break
    return out


def boundary_check(bin_, entry_va, target_va, max_bytes=0x20000):
    """返回 (is_boundary, insn_or_None, reason)。

    从 entry_va 线性反汇编，看是否有指令恰好起于 target_va。

    ⚠️ 两个历史 bug（都会被误读成"不是指令边界"）：
      1. capstone 默认 skipdata=False ⇒ 遇不可解码字节**静默停止**，走不到 target。
         这里改用 skipdata=True 的 disassembler。
      2. 早期 max_bytes 默认 0x2000(8192)：当 |target-entry| 超过它时本函数直接 bail 返回 False，
         被调用方当成"不是边界"。R12 第 2 轮就因此把 0x617641 / 0x61CC5C 两个**真实**的
         `call [reg+0x5C]` 误判为假阳性。现把默认放宽到 0x20000 并在超限时给出明确 reason。
    """
    if target_va < entry_va:
        return (False, None, "target < entry")
    span = target_va - entry_va
    if span >= max_bytes:
        return (False, None, "span %d >= max_bytes %d (未判定，不是'非边界')" % (span, max_bytes))
    m = md32(skipdata=True)
    data = bin_.read(entry_va, span + 16)
    for insn in m.disasm(data, entry_va):
        if insn.id == 0:          # skipdata 产生的 .byte，不是真指令
            continue
        if insn.address == target_va:
            return (True, insn, "ok")
        if insn.address > target_va:
            break
    # 找覆盖 target 的那条指令
    for insn in m.disasm(data, entry_va):
        if insn.id == 0:
            continue
        if insn.address < target_va < insn.address + insn.size:
            return (False, insn, "inside insn at %08X size %d (%s %s)"
                    % (insn.address, insn.size, insn.mnemonic, insn.op_str))
        if insn.address > target_va:
            break
    return (False, None, "linear disasm did not reach target")


def load_func_atlas(path=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"):
    """读 function_atlas.tsv。⚠️ size 列是十进制（§863）。返回 (entries sorted, dict)。"""
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t")
            rec = dict(zip(header, parts))
            try:
                va = int(rec.get("entry") or rec.get("address") or rec.get("va"), 16)
            except Exception:
                continue
            rows.append((va, rec))
    rows.sort(key=lambda t: t[0])
    return rows, header


def entry_at_or_before(rows, va):
    """线性找 <= va 的最大 entry（不假设 va 一定在函数内）。"""
    lo, hi = 0, len(rows) - 1
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        if rows[mid][0] <= va:
            best = rows[mid]
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def bytescan(bin_, pattern, sec_name=None, boundary_entries=None):
    """在指定节里找字节模式。若给 boundary_entries（已排序 entry 列表），
    对每个命中用 boundary_check 判定是否指令边界。"""
    secs = [bin_.sec(sec_name)] if sec_name else bin_.sections
    hits = []
    for s in secs:
        buf = bin_.pe.__data__[s["raw"]:s["raw"] + s["rawsize"]]
        start = 0
        while True:
            i = buf.find(pattern, start)
            if i < 0:
                break
            va = s["va"] + i
            rec = dict(va=va, section=s["name"])
            if boundary_entries is not None:
                e = entry_at_or_before(boundary_entries, va)
                if e is None:
                    rec["boundary"] = None
                else:
                    ok, insn, why = boundary_check(bin_, e[0], va)
                    rec["from_entry"] = e[0]
                    rec["boundary"] = ok
                    rec["why"] = why
                    if ok:
                        rec["insn"] = "%s %s" % (insn.mnemonic, insn.op_str)
            hits.append(rec)
            start = i + 1
    return hits


def sweep_calls(bin_):
    """全 .text 线性反汇编，收集 (call_target -> [site_va...]) 与 (jmp_target -> [...]).
    这是字节通道的"引用模型"，与 Ghidra 的函数引用模型独立。

    ⚠️ 必须 skipdata=True：capstone 默认遇到不可解码字节就**静默停止**，
    在 4 MB .text 上只会解出约 15 万条（真值约 80 万条），造成大面积漏报。"""
    m = md32(skipdata=True)
    t = bin_.text
    data = bin_.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    calls, jmps = {}, {}
    n = 0
    n_skip = 0
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0:  # skipdata 产生的 .byte
            n_skip += insn.size
            continue
        n += 1
        if insn.mnemonic == "call" and insn.op_str.startswith("0x"):
            tgt = int(insn.op_str, 16)
            calls.setdefault(tgt, []).append(insn.address)
        elif insn.mnemonic == "jmp" and insn.op_str.startswith("0x"):
            tgt = int(insn.op_str, 16)
            jmps.setdefault(tgt, []).append(insn.address)
    return calls, jmps, dict(insns=n, skipped_bytes=n_skip, text_bytes=len(data))


def sweep_disps(bin_, target_va, disp_size=4):
    """找所有以 [reg+disp] / [abs] 形式引用 target_va 的指令。
    32 位模式下 base==0 && index==0 时 disp32 就是绝对地址。也必须 skipdata。"""
    m = md32(skipdata=True)
    t = bin_.text
    data = bin_.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    found = []
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0:
            continue
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_MEM:
                mem = op.mem
                if mem.base == 0 and mem.index == 0 and (mem.disp & 0xFFFFFFFF) == target_va:
                    found.append(dict(va=insn.address, insn="%s %s" % (insn.mnemonic, insn.op_str),
                                      kind="abs"))
                elif mem.base != 0 and mem.disp == target_va:
                    found.append(dict(va=insn.address, insn="%s %s" % (insn.mnemonic, insn.op_str),
                                      kind="reg+disp"))
    return found


if __name__ == "__main__":
    b = Bin()
    print("ImageBase", hex(b.image_base))
    for s in b.sections:
        print("  %-8s va=%08X vsize=%08X raw=%08X rawsize=%08X"
              % (s["name"], s["va"], s["vsize"], s["raw"], s["rawsize"]))
