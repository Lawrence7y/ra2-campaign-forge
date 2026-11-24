"""S3 · 四条通道（各自独立、互不依赖），全部自写，不依赖 atlas entry+size。

通道 A · 指令边界上的 E8/E9 rel32 目标（来自 S2 的全 .text 线性反汇编索引）
    子通道：A_call = E8 目标；A_jmp = E9 目标（§8.1 ②：jmp32 不得直当真入口，单列）
通道 B · 自写 RTTI 定界后的虚表槽值（.rdata 的 COL → vtable[-1]，§8.1 ⑦ 禁 atlas 反推）
通道 C · .data 段内以该地址为初值的 4 字节项（initterm 表 / 跳表 / 函数指针数组）
通道 D · 结构证据（D1 硬边界 / D2 体自洽），单独统计、不当主判据

本文件同时是**唯一的判据实现**：S4 用 `import s3_channels` 复用同一份 D 通道代码，
保证「池内命中率」与「随机基线命中率」用的是同一套判据（§8.2 技术④ 同质对照）。
"""
import bisect
import json
import os
import pickle
import sys
from array import array

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p0m_common import EVIDENCE, HERE, Image, new_md

img = Image()
md = new_md()

with open(os.path.join(HERE, "index.pkl"), "rb") as _f:
    idx = pickle.load(_f)
starts, sizes, kinds = idx["starts"], idx["sizes"], idx["kinds"]
call_targets, jmp_targets, jcc_targets = idx["call_targets"], idx["jmp_targets"], idx["jcc_targets"]
ends = array("i", (starts[i] + sizes[i] for i in range(len(starts))))

TERM = {"ret", "retf", "int3", "hlt", "ud2"}


def insn_ending_at(va):
    """返回结束地址恰为 va 的线性反汇编指令 (start, size, kind)，不存在返回 None。"""
    i = bisect.bisect_left(ends, va)
    if i < len(ends) and ends[i] == va:
        return starts[i], sizes[i], kinds[i]
    return None


def insn_at(va):
    i = bisect.bisect_left(starts, va)
    if i < len(starts) and starts[i] == va:
        return starts[i], sizes[i], kinds[i]
    return None


def _mnemonic(va, n):
    b = img.read(va, n)
    if b is None:
        return None
    for insn in md.disasm(b, va):
        return insn.mnemonic
    return None


def d1_hard_boundary(va):
    """D1 硬边界：前驱是 ret/retf/int3/hlt/ud2，可隔 1..15 字节 90/CC padding。

    **不含 jmp**：jmp 前驱正是 ENUM 建池条件本身（§8.1 ② + ADJ4 的 3/7 道闸教训）。
    返回 (是否硬边界, padding 字节数, 边界指令地址, 边界指令助记符)。
    """
    pred = insn_ending_at(va)
    if pred is not None:
        mn = _mnemonic(pred[0], pred[1])
        if mn in TERM:
            return True, 0, pred[0], mn
    k = 0
    while k < 15:
        b = img.read(va - k - 1, 1)
        if b is None or b[0] not in (0x90, 0xCC):
            break
        k += 1
    if k >= 1:
        q = va - k
        pr = insn_ending_at(q)
        if pr is not None:
            mn = _mnemonic(pr[0], pr[1])
            if mn in TERM:
                return True, k, q, mn
    return False, k, None, None


def d2_body(va):
    """D2 体自洽：≥2 条指令、≤4096B 内到 ret/retf/int3/hlt、无 jmp-out、无不可解码字节。"""
    buf = img.read(va, 4096)
    if buf is None:
        return False, "unreadable", 0
    n = 0
    for insn in md.disasm(buf, va):
        if insn.id == 0:
            return False, "undecodable", n
        mn = insn.mnemonic
        n += 1
        if mn in ("ret", "retf", "int3", "hlt"):
            return (n >= 2), ("ret" if n >= 2 else "single_insn_ret"), n
        if mn == "jmp" and insn.operands and insn.operands[0].type == 2:
            t = insn.operands[0].imm & 0xFFFFFFFF
            if not (va <= t < va + 4096):
                return False, "jmp_out", n
        if n >= 4000:
            break
    return False, "no_terminator", n


def chan_d(va):
    b_ok, pad, bsrc, bmn = d1_hard_boundary(va)
    body_ok, body_why, body_n = d2_body(va)
    return dict(d1=b_ok, pad=pad, d1_src=bsrc, d1_mn=bmn,
                d2=body_ok, d2_why=body_why, d2_n=body_n, d=b_ok and body_ok)


# ---------------------------------------------------------------- 通道 B：RTTI
def in_sec(sec, va):
    return sec is not None and sec["va"] <= va < sec["va"] + max(sec["vsize"], sec["raw_size"])


def read_cstr(va, maxlen=256):
    b = img.read(va, maxlen)
    if b is None:
        return None
    e = b.find(b"\x00")
    if e < 0:
        return None
    try:
        return b[:e].decode("latin-1")
    except Exception:
        return None


def find_cols():
    """找 CompleteObjectLocator。

    **本镜像实测坑（本卡新增，见 UNKNOWNS U3）**：COL 的 `signature` 字段在本镜像
    **全部 1,214 个 COL 上都是 0**，不是微软文档/惯例的 1 —— 任何「先验 signature==1」的
    过滤得到 **0 个 COL**（首版即如此，通道 B 全灭）。故本实现**不依赖 signature**，
    改用结构性三重约束：COL+0xC 的 TD 指针可读且 `TD+8` 是 '.?A…' 内联名串（技术⑦：
    TD+8 是内联名串不是指针），COL+0x10 的 CHD 指针也可读。且 **TD 落在 `.data`、
    CHD 落在 `.rdata`** —— 段约束必须放宽到两段（首版只认 .rdata，同样 0 命中）。
    """
    rd = img.rdata
    cols = {}
    base, size = rd["va"], rd["raw_size"]
    for off in range(0, size - 0x14, 4):
        p = base + off
        ptd = img.u32(p + 0xC)
        pchd = img.u32(p + 0x10)
        if ptd is None or not (in_sec(rd, ptd) or in_sec(img.data, ptd)):
            continue
        if pchd is None or not (in_sec(rd, pchd) or in_sec(img.data, pchd)):
            continue
        name = read_cstr(ptd + 8, 256)
        if name is None or not name.startswith(".?A"):
            continue
        cols[p] = name
    return cols


def build():
    cols = find_cols()
    colset = set(cols)

    tables = []      # (vt_va, col_va, class_name, [slot values])
    tested = 0
    for sec in (img.rdata, img.data):
        if sec is None:
            continue
        base, size = sec["va"], sec["raw_size"]
        blob = img.read(base, size)
        for off in range(4, size - 4, 4):
            v = int.from_bytes(blob[off:off + 4], "little")
            if not img.in_text(v):
                continue
            tested += 1
            meta = int.from_bytes(blob[off - 4:off], "little")
            if meta not in colset:
                continue
            slots = []
            q = base + off
            while True:
                w = img.u32(q)
                if w is None or not img.in_text(w):
                    break
                slots.append(w)
                q += 4
                if len(slots) > 4000:
                    break
            tables.append((base + off, meta, cols.get(meta, "?"), slots))

    vt_slot_set = set()
    for _, _, _, slots in tables:
        vt_slot_set.update(slots)

    # 通道 C：.data 初值指针
    c_data_ptrs = {}
    d = img.data
    if d is not None:
        base, size = d["va"], d["raw_size"]
        blob = img.read(base, size)
        for off in range(0, size - 4 + 1, 4):
            v = int.from_bytes(blob[off:off + 4], "little")
            if img.in_text(v):
                c_data_ptrs.setdefault(v, []).append(base + off)

    # 参考：.rdata 内非虚表槽的 .text 指针（仅申报，不计入通道 C 主口径）
    c_rdata_extra = {}
    rd = img.rdata
    base, size = rd["va"], rd["raw_size"]
    blob = img.read(base, size)
    for off in range(0, size - 4 + 1, 4):
        v = int.from_bytes(blob[off:off + 4], "little")
        if img.in_text(v) and v not in vt_slot_set:
            c_rdata_extra.setdefault(v, []).append(base + off)

    chan = dict(A_call=call_targets, A_jmp=jmp_targets, jcc=jcc_targets,
                B=vt_slot_set, C=set(c_data_ptrs), C_rdata_extra=set(c_rdata_extra),
                tables=tables, cols=cols, c_data_ptrs=c_data_ptrs, tested=tested)
    return chan


if __name__ == "__main__":
    chan = build()
    with open(os.path.join(HERE, "channels.pkl"), "wb") as f:
        pickle.dump(chan, f)
    tables = chan["tables"]
    stats = dict(
        channel_A=dict(call_targets=len(chan["A_call"]), jmp_targets=len(chan["A_jmp"]),
                       union=len(chan["A_call"] | chan["A_jmp"]),
                       jmp_only=len(chan["A_jmp"] - chan["A_call"])),
        channel_B=dict(cols_found=len(chan["cols"]), tables=len(tables),
                       slots_total=sum(len(s) for _, _, _, s in tables),
                       distinct_slot_values=len(chan["B"]),
                       positions_tested=chan["tested"],
                       sample_tables=[dict(vt=hex(t[0]), col=hex(t[1]), cls=t[2],
                                           n_slots=len(t[3]),
                                           first_slots=[hex(x) for x in t[3][:4]])
                                      for t in tables[:8]]),
        channel_C=dict(distinct_targets=len(chan["C"]),
                       data_slots=sum(len(v) for v in chan["c_data_ptrs"].values()),
                       rdata_nonslot_targets=len(chan["C_rdata_extra"])),
    )
    with open(os.path.join(EVIDENCE, "s3_channels.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
