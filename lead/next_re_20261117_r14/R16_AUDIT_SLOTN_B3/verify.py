# -*- coding: utf-8 -*-
"""
R16-AUDIT-SLOTN-B3 · 独立审计复算脚本（只读）
审计员自写；**不**复用执行器的 scan_fields.py / gen_delta.py，也**不**读执行器的
verify_summary.json / scan_raw.json 作为判据。

只读打开：
  - ra2youli\\gamemd.exe
  - COVERAGE\\coverage.tsv
  - R16_SLOTN_B3\\delta.tsv
  - PROBE_802\\slotN43.tsv
写入（仅本卡写域）：bytecheck.tsv / tables.md / verify_out.json

复核项：
  §A 最小改动与原文保全（col4 严格前缀 + 其余 7 列逐字节）
  §B 6 项字节事实（含 capstone 解码装表点）
  §C 行 32/33 表改选四问四答（含全表枚举、全装表点枚举）
  §D 文本与事实一致（含 D-47 披露指针 §12.6 / 禁 §12.4）
  §E 格式合先例（骨架归一后逐字符）
  §F 反抄袭（entry 归一后两两不同）
"""
import hashlib
import json
import os
import re
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

BASE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(BASE)
ROOT = os.path.dirname(os.path.dirname(R14))

EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
DELTA = os.path.join(R14, "R16_SLOTN_B3", "delta.tsv")
SLOTN = os.path.join(R14, "PROBE_802", "slotN43.tsv")

IB_EXPECT = 0x400000
TEXT_LO_EXPECT = 0x401000
TEXT_HI_EXPECT = 0x7E038D
EXPECT_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
EXPECT_SIZE = 4825360


# --------------------------------------------------------------------------
# PE / 镜像
# --------------------------------------------------------------------------
class Sec(object):
    __slots__ = ("name", "va", "vsize", "rawsize", "rawptr")

    def __init__(self, name, va, vsize, rawsize, rawptr):
        self.name = name
        self.va = va
        self.vsize = vsize
        self.rawsize = rawsize
        self.rawptr = rawptr


class Image(object):
    def __init__(self, path):
        self.path = path
        with open(path, "rb") as f:          # 只读
            self.data = f.read()
        self.sha = hashlib.sha256(self.data).hexdigest().upper()
        self.size = len(self.data)
        d = self.data
        if d[:2] != b"MZ":
            raise RuntimeError("not PE")
        e_lfanew = struct.unpack_from("<I", d, 0x3C)[0]
        if d[e_lfanew:e_lfanew + 4] != b"PE\0\0":
            raise RuntimeError("no PE sig")
        coff = e_lfanew + 4
        nsec = struct.unpack_from("<H", d, coff + 2)[0]
        optsize = struct.unpack_from("<H", d, coff + 16)[0]
        opt = coff + 20
        self.magic = struct.unpack_from("<H", d, opt)[0]      # 0x10b = PE32
        self.imagebase = struct.unpack_from("<I", d, opt + 28)[0]
        self.sizeof_image = struct.unpack_from("<I", d, opt + 56)[0]
        self.sizeof_headers = struct.unpack_from("<I", d, opt + 60)[0]
        self.sections = []
        sh = opt + optsize
        for i in range(nsec):
            o = sh + i * 40
            name = d[o:o + 8].rstrip(b"\0").decode("latin-1")
            vsize, va, rawsize, rawptr = struct.unpack_from("<IIII", d, o + 8)
            self.sections.append(Sec(name, va, vsize, rawsize, rawptr))
        t = self.section(".text")
        self.text_lo = self.imagebase + t.va
        self.text_hi = self.imagebase + t.va + t.vsize
        self.text_off = t.rawptr
        self.text_rawsize = t.rawsize

    def section(self, name):
        for s in self.sections:
            if s.name == name:
                return s
        raise KeyError(name)

    def va2off(self, va):
        if va < self.imagebase:
            return None
        rva = va - self.imagebase
        if rva < self.sizeof_headers:
            return rva if rva < self.size else None
        for s in self.sections:
            span = max(s.vsize, s.rawsize)
            if s.va <= rva < s.va + span:
                off = s.rawptr + (rva - s.va)
                return off if off < self.size else None
        return None

    def read(self, va, n):
        off = self.va2off(va)
        if off is None or off + n > self.size:
            return None
        return self.data[off:off + n]

    def u32(self, va):
        b = self.read(va, 4)
        if b is None or len(b) != 4:
            return None
        return struct.unpack("<I", b)[0]

    def cstr(self, va, maxlen=256):
        off = self.va2off(va)
        if off is None:
            return None
        end = self.data.find(b"\0", off, off + maxlen)
        if end < 0:
            return None
        return self.data[off:end].decode("latin-1")

    def in_image(self, va):
        return self.va2off(va) is not None

    def in_text(self, va):
        return self.text_lo <= va < self.text_hi


# --------------------------------------------------------------------------
# RTTI / 虚表
# --------------------------------------------------------------------------
def col_chain(img, vt):
    """vt - 4 -> COL ; COL+4 -> offset ; COL+12 -> TD ; TD+8 -> mangled(内联串)"""
    col = img.u32(vt - 4)
    if col is None or not img.in_image(col):
        return None
    offset = img.u32(col + 4)
    td = img.u32(col + 12)
    rec = {"COL": col, "offset": offset, "TD": td, "mangled": None}
    if td is not None and img.in_image(td):
        rec["mangled"] = img.cstr(td + 8)
    return rec


def table_slots(img, vt, cap=512):
    """从 vt 起连续读出落在 .text 内的槽值（虚表槽必指向代码）。"""
    slots = []
    for i in range(cap):
        v = img.u32(vt + i * 4)
        if v is None or not img.in_text(v):
            break
        slots.append(v)
    return slots


def tables_containing(img, entry, limit=4096):
    """
    全镜像扫 dword == entry，返回每个命中处的**槽地址** VA（候选槽位）。
    「表起点」由调用方 enum_tables_of_entry 回溯确定。
    """
    found = []
    d = img.data
    pat = struct.pack("<I", entry)
    start = 0
    while True:
        idx = d.find(pat, start)
        if idx < 0:
            break
        start = idx + 1
        # 反查该文件偏移所属节的 VA（并校验映射自洽）
        va = None
        for s in img.sections:
            if s.rawptr <= idx < s.rawptr + s.rawsize:
                v = img.imagebase + s.va + (idx - s.rawptr)
                if img.va2off(v) == idx:
                    va = v
                break
        if va is None or va < 4:
            continue
        found.append(va)
        if len(found) > limit:
            break
    return found


def enum_tables_of_entry(img, entry, max_lookback=400):
    """
    独立枚举「哪些表把 entry 放在某一槽」：
    对每个 dword==entry 的地址 S（作槽地址），回溯 k=0..max 使 T=S-4k 满足
      u32(T-4) 为镜像内地址、且 (T-4)+12 可读出 TD、TD+8 为 .?A 开头的装饰名。
    命中的最近 k 即该表的起点（取最小 k）。
    """
    out = []
    for S in tables_containing(img, entry):
        for k in range(0, max_lookback):
            T = S - 4 * k
            if T < img.imagebase:
                break
            col = img.u32(T - 4)
            if col is None or not img.in_image(col):
                continue
            td = img.u32(col + 12)
            if td is None or not img.in_image(td):
                continue
            man = img.cstr(td + 8)
            if not man or not man.startswith(".?A"):
                continue
            off = img.u32(col + 4)
            out.append({"vt": T, "slot": k, "COL": col, "offset": off,
                        "TD": td, "mangled": man})
            break
    # 去重（同一 (vt,slot)）
    seen = set()
    uniq = []
    for r in out:
        key = (r["vt"], r["slot"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
    uniq.sort(key=lambda r: (r["vt"], r["slot"]))
    return uniq


def rtti_class(mangled):
    if not mangled:
        return None
    m = mangled
    if m.startswith(".?AV"):
        m = m[4:]
    elif m.startswith(".?AU"):
        m = m[4:]
    return m.rstrip("@")


# --------------------------------------------------------------------------
# 装表点
# --------------------------------------------------------------------------
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True


def decode_at(img, va, n=16):
    b = img.read(va, n)
    if not b:
        return None
    for insn in MD.disasm(b, va):
        return insn
    return None


def is_mov_mem_imm(insn):
    if insn is None or insn.mnemonic != "mov" or len(insn.operands) != 2:
        return False
    a, b = insn.operands
    return a.type == X86_OP_MEM and b.type == X86_OP_IMM


def site_imm(img, va):
    insn = decode_at(img, va)
    if not is_mov_mem_imm(insn):
        return None, insn
    return insn.operands[1].imm & 0xFFFFFFFF, insn


    # 注：全 .text 线性 sweep 会因 .text 内嵌数据而失步（实测漏掉 0x517D9D 这类真装表点），
    # 故装表点枚举改用「0xC7 字节候选 + capstone 解码确认」——每个候选都真正解码过。
_SITE_CACHE = {}


def find_install_sites(img, vt, max_hits=64):
    """
    枚举 .text 内全部 `mov <mem>, imm32` 且 imm32 == vt 的指令。
    做法：扫 .text 原始字节找所有 0xC7（C7 /0 = mov r/m32, imm32），
    对每个位置用 capstone 解码一条；只保留「首操作数为 mem + 次操作数为 imm32 + 值相等」者。
    """
    if vt in _SITE_CACHE:
        return _SITE_CACHE[vt]
    b = img.data[img.text_off:img.text_off + img.text_rawsize]
    hits = []
    p = b.find(b"\xC7")
    scanned = 0
    while p >= 0:
        scanned += 1
        va = img.text_lo + p
        insn = decode_at(img, va)
        if insn is not None and insn.address == va and is_mov_mem_imm(insn):
            if (insn.operands[1].imm & 0xFFFFFFFF) == vt:
                hits.append(va)
                if len(hits) >= max_hits:
                    break
        p = b.find(b"\xC7", p + 1)
    _SITE_CACHE[vt] = {"hits": hits, "candidates": scanned}
    return _SITE_CACHE[vt]


def is_pad(byte):
    return byte in (0xCC, 0x90)


def decode_reaches(img, start, target, maxlen=0x8000):
    """
    从 start 线性解码到 target，判断 target 是否恰好落在某条指令边界上。
    返回 (hit: bool, insn_count, first_bad_offset or None)
    """
    b = img.read(start, maxlen)
    if not b:
        return False, 0, None
    n = 0
    for insn in MD.disasm(b, start):
        n += 1
        if insn.address == target:
            return True, n, None
        if insn.address > target:
            return False, n, insn.address
    return False, n, None


def func_ok(img, func, site):
    """校验声称的函数起点：前一字节是对齐填充，且从该起点线性解码能精确落到 site。"""
    if func is None or site is None:
        return {"ok": False, "why": "missing"}
    off = img.va2off(func)
    if off is None or off == 0:
        return {"ok": False, "why": "func not mapped"}
    prev = img.data[off - 1] if off > 0 else None
    pad = prev is not None and is_pad(prev)
    hit, n, over = decode_reaches(img, func, site)
    return {"ok": bool(pad and hit), "prev_byte": ("0x%02X" % prev) if prev is not None else None,
            "prev_is_padding": pad, "decode_reaches_site": hit,
            "insns_to_site": n, "overshoot": ("0x%08X" % over) if over else None}


def body_range(img, start, maxlen=0x8000):
    """从 start 线性解码，遇 ret / ret imm / 无条件 jmp 即止。"""
    end = None
    b = img.read(start, maxlen)
    if not b:
        return None
    for insn in MD.disasm(b, start):
        if insn.mnemonic in ("ret", "retf") or insn.mnemonic == "jmp":
            end = insn.address + insn.size
            break
    return (start, end) if end else None


# --------------------------------------------------------------------------
# 文本解析
# --------------------------------------------------------------------------
RE_RING4 = re.compile(r"④ 活表槽位见证：")
RE_WIT = re.compile(
    r"④ 活表槽位见证：(?P<cls>.+?)::slot(?P<slot>\d+)"
    r"（vt=(?P<vt>[0-9A-F]{8})，槽 (?P<slot2>\d+) 值=(?P<slotval>[0-9A-F]{8})，"
    r"COL=(?P<col>[0-9A-F]{8}) offset=(?P<off>\d+)，"
    r"RTTI=(?P<td>[0-9A-F]{8})→(?P<man>.+?)；"
    r"装表点 (?P<site>[0-9A-F]{8}) 位于 (?P<func>[0-9A-F]{8}) 体内，entry 体外）"
)
RE_UPG = re.compile(
    r"④升级句：(?P<cls>.+?)::slot(?P<slot>\d+)"
    r"（④ 表属类与行名类一致，均为 (?P<cls2>.+?)；"
    r"该槽即其 vt=(?P<vt>[0-9A-F]{8}) 表 slot(?P<slot2>\d+)，无归属歧义）"
)


def parse_ring4(text):
    """从第 4 列里切出 ④ 段并结构化。"""
    i = text.find("④ 活表槽位见证：")
    if i < 0:
        return None
    seg = text[i:]
    w = RE_WIT.search(seg)
    u = RE_UPG.search(seg)
    if not w or not u:
        return {"seg": seg, "wit": w, "upg": u, "ok": False}
    d = {
        "seg": seg,
        "core": seg[:u.end()],
        "tail": seg[u.end():],
        "cls": w.group("cls"),
        "slot": int(w.group("slot")),
        "slot2": int(w.group("slot2")),
        "vt": int(w.group("vt"), 16),
        "slotval": int(w.group("slotval"), 16),
        "col": int(w.group("col"), 16),
        "off": int(w.group("off")),
        "td": int(w.group("td"), 16),
        "man": w.group("man"),
        "site": int(w.group("site"), 16),
        "func": int(w.group("func"), 16),
        "upg_cls": u.group("cls"),
        "upg_cls2": u.group("cls2"),
        "upg_vt": int(u.group("vt"), 16),
        "upg_slot": int(u.group("slot")),
        "upg_slot2": int(u.group("slot2")),
        "ok": True,
    }
    return d


def col_name_match(row_class, mangled):
    """口径照 PROBE_802\\probe.py:col_name_match（批次 1 审计已确认的既有归一化）：
    非模板 = 类名须为装饰名子串；T_ 模板伪名 = 去 T_ / 去尾 _ / 按 _ 切分，各段均须出现在装饰名中。"""
    if not mangled:
        return False
    if row_class.startswith("T_"):
        s = row_class[2:]
        if s.endswith("_"):
            s = s[:-1]
        parts = [p for p in s.split("_") if p]
        return all(p in mangled for p in parts)
    return row_class in mangled


# --------------------------------------------------------------------------
def read_tsv_bytes(path):
    with open(path, "rb") as f:
        raw = f.read()
    return raw


def split_rows(raw):
    # 保留每行原始字节；行尾 CRLF/LF 都剥离
    out = []
    for ln in raw.split(b"\n"):
        if ln.endswith(b"\r"):
            ln = ln[:-1]
        out.append(ln)
    # 去掉文件末尾的空行
    while out and out[-1] == b"":
        out.pop()
    return out


def main():
    res = {"meta": {}, "rows": [], "issues": []}
    img = Image(EXE)
    res["meta"]["exe"] = {"path": EXE, "size": img.size, "sha256": img.sha,
                          "imagebase": "0x%08X" % img.imagebase,
                          "text": ["0x%08X" % img.text_lo, "0x%08X" % img.text_hi],
                          "sizeof_image": "0x%08X" % img.sizeof_image}
    assert img.sha == EXPECT_SHA, "gamemd.exe SHA256 与卡面不符!"
    assert img.size == EXPECT_SIZE
    assert img.imagebase == IB_EXPECT
    assert img.text_lo == TEXT_LO_EXPECT and img.text_hi == TEXT_HI_EXPECT

    cov_raw = read_tsv_bytes(COV)
    res["meta"]["coverage"] = {"size": len(cov_raw),
                               "sha256": hashlib.sha256(cov_raw).hexdigest().upper()}
    cov_rows = split_rows(cov_raw)
    res["meta"]["coverage"]["n_data_rows"] = len(cov_rows) - 1
    cov = {}
    for i, ln in enumerate(cov_rows[1:], start=2):   # 1-based 文件行号（表头=1）
        cols = ln.split(b"\t")
        if len(cols) != 8:
            continue
        cov[cols[0].decode()] = {"line": i, "cols": cols}

    delta_raw = read_tsv_bytes(DELTA)
    res["meta"]["delta"] = {"size": len(delta_raw),
                            "sha256": hashlib.sha256(delta_raw).hexdigest().upper()}
    d_rows = split_rows(delta_raw)
    assert len(d_rows) == 14, "delta.tsv 行数 %d != 14" % len(d_rows)
    hdr = d_rows[0].decode()
    res["meta"]["delta"]["header"] = hdr
    assert hdr.split("\t") == ["entry", "subsystem", "name", "one_line_semantics",
                               "grade", "evidence_path", "n_sources", "conflict"]

    sn_raw = read_tsv_bytes(SLOTN)
    sn_rows = split_rows(sn_raw)
    res["meta"]["slotn43"] = {"n_lines": len(sn_rows),
                              "n_data_rows": len(sn_rows) - 1,
                              "sha256": hashlib.sha256(sn_raw).hexdigest().upper()}
    assert len(sn_rows) - 1 == 43, "slotN43 数据行 %d != 43" % (len(sn_rows) - 1)
    sn = {}
    for i, ln in enumerate(sn_rows[1:], start=1):
        cols = ln.decode("utf-8").split("\t")
        sn[i] = {"entry": cols[0], "subsystem": cols[1], "name": cols[2],
                 "vt_count": cols[3], "slot_no": int(cols[4]), "col_ok": cols[5],
                 "install_ext": cols[6], "ring4_ok": cols[7], "reason": cols[8]}

    batch_idx = list(range(31, 44))     # slotN43 数据行 31..43
    expect_entries = [sn[i]["entry"] for i in batch_idx]
    got_entries = [d_rows[i].split(b"\t")[0].decode() for i in range(1, 14)]
    res["meta"]["batch_order_ok"] = (expect_entries == got_entries)
    res["meta"]["expect_entries"] = expect_entries
    res["meta"]["got_entries"] = got_entries
    res["meta"]["entry_unique_13"] = (len(set(got_entries)) == 13)

    # ---------- 先例（§E） ----------
    PREC = ["00464AC0", "004DE630", "004F42F0"]
    prec = {}
    for e in PREC:
        r = cov.get(e)
        if r:
            t = r["cols"][3].decode("utf-8", "replace")
            p = parse_ring4(t)
            prec[e] = p
    res["meta"]["precedents"] = {k: (v.get("seg") if v else None) for k, v in prec.items()}

    def skeleton(d, cls_override=None, man_override=None):
        """把 ④ core 归一为骨架：先替换 mangled / class，再替换 hex，再替换数字。"""
        core = d["core"]
        man = man_override if man_override is not None else d["man"]
        cls = cls_override if cls_override is not None else d["cls"]
        core = core.replace("→" + man, "→<MAN>")
        core = core.replace(cls, "<CLS>")
        core = re.sub(r"\b[0-9A-F]{8}\b", "<H>", core)
        core = re.sub(r"offset=\d+", "offset=<N>", core)
        core = re.sub(r"slot\d+", "slot<N>", core)
        core = re.sub(r"槽 \d+ 值", "槽 <N> 值", core)
        return core

    prec_skels = {}
    for e in PREC:
        p = prec.get(e)
        if p and p.get("ok"):
            prec_skels[e] = skeleton(p)
    res["meta"]["precedent_skeletons_equal"] = (len(set(prec_skels.values())) == 1)
    res["meta"]["precedent_skeleton"] = (list(prec_skels.values())[0]
                                        if prec_skels else None)

    # ---------- §E 全量先例普查（不只看 3 条） ----------
    prec_all = []
    for e, v in cov.items():
        t = v["cols"][3].decode("utf-8", "replace")
        if "④ 活表槽位见证" in t:
            prec_all.append((e, t, v["line"]))
    census = {"total": len(prec_all), "variantA": [], "variantB": [], "unparsed": []}
    for e, t, ln in prec_all:
        p = parse_ring4(t)
        if p and p.get("ok"):
            census["variantA"].append((e, skeleton(p)))
        elif "④升级句：" in t and "；类名归属：" in t:
            census["variantB"].append(e)
        else:
            census["unparsed"].append(e)
    my_p = parse_ring4(d_rows[1].split(b"\t")[3].decode("utf-8"))
    my_skel = skeleton(my_p) if (my_p and my_p.get("ok")) else None
    res["meta"]["precedent_census"] = {
        "total_rows_with_ring4": census["total"],
        "variantA_n": len(census["variantA"]),
        "variantB_n": len(census["variantB"]),
        "unparsed_n": len(census["unparsed"]),
        "unparsed_ids": census["unparsed"],
        "variantA_distinct_skeletons": len(set(s for _, s in census["variantA"])),
        "variantA_equals_batch_skeleton": all(s == my_skel for _, s in census["variantA"]),
    }

    # ---------- 逐行 ----------
    for ri, snidx in enumerate(batch_idx, start=1):
        cols = d_rows[ri].split(b"\t")
        assert len(cols) == 8, "row %d 列数 %d" % (ri, len(cols))
        entry_s = cols[0].decode()
        name = cols[2].decode()
        text = cols[3].decode("utf-8")
        row = {"n": ri, "sn_index": snidx, "entry": entry_s, "name": name,
               "subsystem": cols[1].decode(), "grade": cols[4].decode(),
               "n_sources": cols[6].decode(), "conflict": cols[7].decode(),
               "supposed_class": name.split("::")[0],
               "slot_no": sn[snidx]["slot_no"],
               "vt_count": sn[snidx]["vt_count"],
               "col_ok": sn[snidx]["col_ok"],
               "install_ext": sn[snidx]["install_ext"]}
        row["checks"] = {}

        # ===== §A =====
        cr = cov.get(entry_s)
        if not cr:
            row["A"] = {"ok": False, "why": "coverage.tsv 无该 entry"}
        else:
            ccols = cr["cols"]
            cov4 = ccols[3]
            d4 = cols[3]
            pref = d4.startswith(cov4)
            others = []
            for k in (0, 1, 2, 4, 5, 6, 7):
                others.append({"col": k + 1, "same": ccols[k] == cols[k],
                               "cov": ccols[k].decode("utf-8", "replace"),
                               "delta": cols[k].decode("utf-8", "replace")})
            row["A"] = {
                "ok": pref and all(o["same"] for o in others),
                "cov_line": cr["line"],
                "strict_prefix": pref,
                "cov4_len": len(cov4),
                "delta4_len": len(d4),
                "appended_len": len(d4) - len(cov4) if pref else None,
                "cov4_tail_char": cov4.decode("utf-8", "replace")[-1:] if cov4 else "",
                "append_head": d4[len(cov4):len(cov4) + 3].decode("utf-8", "replace")
                               if pref else None,
                "cov4_already_has_ring4": ("④ 活表槽位见证" in cov4.decode("utf-8", "replace")),
                "other_cols": others,
                "col5_grade_ok": (cols[4].decode() == "[已证]"),
            }

        # ===== 解析 ④ 文本 =====
        p = parse_ring4(text)
        row["ring4"] = {"parsed": bool(p and p.get("ok"))}
        if not p or not p.get("ok"):
            row["B"] = {"ok": False, "why": "④ 段不可解析"}
            row["D"] = {"ok": False, "why": "④ 段不可解析"}
            row["E"] = {"ok": False, "why": "④ 段不可解析"}
            row["F"] = {"ok": False, "why": "④ 段不可解析"}
            res["rows"].append(row)
            continue
        vt, slot, col, off, td, site, func = (p["vt"], p["slot"], p["col"], p["off"],
                                              p["td"], p["site"], p["func"])
        entry = int(entry_s, 16)
        row["vt"] = "0x%08X" % vt
        row["slot_in_text"] = slot
        row["col"] = "0x%08X" % col
        row["offset"] = off
        row["td"] = "0x%08X" % td
        row["mangled_text"] = p["man"]
        row["site"] = "0x%08X" % site
        row["func_text"] = "0x%08X" % func

        # ===== §B 6 项 =====
        c1_v = img.u32(vt + slot * 4)
        c1 = (c1_v == entry)
        c2_v = img.u32(vt - 4)
        c2 = (c2_v == col)
        c3_v = img.u32(col + 4)
        c3 = (c3_v == off)
        c4_v = img.u32(col + 12)
        c4 = (c4_v == td)
        c5_v = img.cstr(td + 8)
        c5 = (c5_v == p["man"])
        imm, insn = site_imm(img, site)
        c6 = (imm == vt)
        row["B"] = {
            "ok": all([c1, c2, c3, c4, c5, c6]),
            "c1": {"ok": c1, "read": ("0x%08X" % c1_v) if c1_v is not None else None,
                   "at": "0x%08X" % (vt + slot * 4), "want": entry_s},
            "c2": {"ok": c2, "read": ("0x%08X" % c2_v) if c2_v is not None else None,
                   "at": "0x%08X" % (vt - 4), "want": row["col"]},
            "c3": {"ok": c3, "read": c3_v, "at": "0x%08X" % (col + 4), "want": off},
            "c4": {"ok": c4, "read": ("0x%08X" % c4_v) if c4_v is not None else None,
                   "at": "0x%08X" % (col + 12), "want": row["td"]},
            "c5": {"ok": c5, "read": c5_v, "want": p["man"]},
            "c6": {"ok": c6, "read": ("0x%08X" % imm) if imm is not None else None,
                   "insn": (insn.mnemonic + " " + insn.op_str) if insn else None,
                   "is_mov_mem_imm": bool(is_mov_mem_imm(insn)),
                   "want": row["vt"]},
        }

        # 辅助：函数体定界（装表点位于 func 体内、entry 体外）
        fchk = func_ok(img, func, site)
        br = body_range(img, func) if fchk["ok"] else None
        aux = {"claimed_func": "0x%08X" % func,
               "func_start_valid": fchk,
               "body": ["0x%08X" % br[0], "0x%08X" % br[1]] if br else None,
               "site_in_body": bool(br and br[0] <= site < br[1]),
               "entry_out_of_body": bool(br and not (br[0] <= entry < br[1])),
               "detected_func": None,
               "detected_matches_claim": bool(fchk["ok"])}
        row["aux_func"] = aux

        # ===== §D 文本与事实一致 =====
        # 关键：不拿文本自身的值互比（那是同义反复）。这里只以「文本声称的装表点」为唯一锚，
        # 从二进制**正向**推出 vt→COL→offset→TD→mangled 全链，再与文本逐字段比对。
        imm_d, insn_d = site_imm(img, site)
        chain = {"site": "0x%08X" % site, "imm32_at_site": ("0x%08X" % imm_d) if imm_d else None}
        ok_chain = False
        if imm_d is not None:
            cc = col_chain(img, imm_d)
            if cc:
                chain.update({"vt": "0x%08X" % imm_d,
                              "COL": ("0x%08X" % cc["COL"]) if cc["COL"] else None,
                              "offset": cc["offset"],
                              "TD": ("0x%08X" % cc["TD"]) if cc["TD"] else None,
                              "mangled": cc["mangled"]})
                ok_chain = True
        row["D_chain"] = chain
        d_items = {
            "chain_derived": ok_chain,
            "vt_text_eq_chain_vt": ok_chain and imm_d == vt,
            "col_text_eq_chain_COL": ok_chain and col == cc["COL"],
            "off_text_eq_chain_offset": ok_chain and off == cc["offset"],
            "td_text_eq_chain_TD": ok_chain and td == cc["TD"],
            "mangled_text_eq_chain_cstr": ok_chain and p["man"] == cc["mangled"],
            "slot_text_eq_name_slot": slot == int(name.split("::slot")[1]),
            "slot_text_eq_slotn43": slot == sn[snidx]["slot_no"],
            "slot_all_four_agree": (slot == p["slot2"] == p["upg_slot"] == p["upg_slot2"]),
            "slotval_is_entry": (p["slotval"] == entry),
            "cls_eq_name_prefix": (p["cls"] == row["supposed_class"]),
            "upg_cls_eq_name_prefix": (p["upg_cls"] == row["supposed_class"]
                                       and p["upg_cls2"] == row["supposed_class"]),
            "upg_vt_eq_text_vt": p["upg_vt"] == vt,
            "cls_vs_mangled": col_name_match(row["supposed_class"], p["man"]),
            "has_D47": ("D-47" in p["seg"]),
            "points_section_12_6": ("§12.6" in p["seg"]),
            "mentions_123_yield": ("§12.3" in p["seg"] and "让位" in p["seg"]),
            "not_claim_passed_123": ("已过 §12.3" not in p["seg"]),
            "mention_panel": ("PANEL" in p["seg"]),
        }
        # 禁止项：出现 §12.4（重号前的过时指针）即独立记 FAIL
        neg = {"has_stale_12_4": ("§12.4" in p["seg"])}
        # 非阻断观察：模板伪名行的 <Class> 与 RTTI 解出名字**字面不等**（既定口径靠归一化）
        row["D_info"] = {
            "cls_exact_eq_rtti": (rtti_class(p["man"]) == row["supposed_class"]),
            "rtti_class": rtti_class(p["man"]),
            "is_template_pseudoname": row["supposed_class"].startswith("T_"),
        }
        row["D"] = d_items
        row["D_neg"] = neg
        row["D"]["ok"] = all(d_items.values()) and not any(neg.values())

        # ===== §E 格式合先例 =====
        sk = skeleton(p)
        row["E"] = {"ok": (sk in prec_skels.values()) if prec_skels else False,
                    "skeleton": sk,
                    "tail": p["tail"]}

        # ===== §F 反抄袭 =====
        seg = p["seg"]
        norm = re.sub(r"[0-9A-F]{8}", "ENTRY", seg)
        row["F"] = {"norm": norm}

        res["rows"].append(row)

    # ---- §F 汇总 ----
    norms = [r["F"].get("norm") for r in res["rows"] if r["F"].get("norm")]
    from collections import Counter
    dup = {k: v for k, v in Counter(norms).items() if v > 1}
    res["meta"]["F_norm_unique"] = (len(set(norms)) == len(norms) == 13)
    res["meta"]["F_dup_groups"] = dup
    # 收紧口径：再把 slot 号一起归一
    strict = []
    for r in res["rows"]:
        n = r["F"].get("norm") or ""
        n = re.sub(r"slot\d+", "slotN", n)
        n = re.sub(r"槽 \d+ 值", "槽N值", n)
        n = re.sub(r"offset=\d+", "offset=N", n)
        strict.append((n, r["entry"]))
    sg = {}
    for n, e in strict:
        sg.setdefault(n, []).append(e)
    sd = [v for v in sg.values() if len(v) > 1]
    res["meta"]["F_strict_dup_groups"] = sd

    # ---- §F 归类：同 vt 同 site 分组（事实相同，非抄袭）----
    groups = {}
    for r in res["rows"]:
        key = (r.get("vt"), r.get("site"))
        groups.setdefault(key, []).append(r["entry"])
    res["meta"]["F_same_vt_site_groups"] = {"%s|%s" % k: v for k, v in groups.items() if len(v) > 1}
    res["meta"]["F_distinct_vt"] = len(set(r.get("vt") for r in res["rows"]))
    res["meta"]["F_distinct_slot"] = len(set(r.get("slot_in_text") for r in res["rows"]))
    res["meta"]["F_distinct_cls"] = len(set(r["supposed_class"] for r in res["rows"]))
    res["meta"]["F_distinct_site"] = len(set(r.get("site") for r in res["rows"]))

    # ================= §C 行 32/33 四问四答 =================
    site_bldg = 0x0043B71F
    imm_bldg, insn_bldg = site_imm(img, site_bldg)
    vt_inf = 0x007EB058
    vt_bldg = imm_bldg
    C = {
        "site_0043B71F": {
            "insn": (insn_bldg.mnemonic + " " + insn_bldg.op_str) if insn_bldg else None,
            "is_mov_mem_imm": bool(is_mov_mem_imm(insn_bldg)),
            "imm32": ("0x%08X" % imm_bldg) if imm_bldg is not None else None,
        }
    }
    if vt_bldg is not None:
        cb = col_chain(img, vt_bldg)
        C["site_0043B71F"]["table_col"] = {
            "COL": "0x%08X" % cb["COL"] if cb and cb["COL"] else None,
            "offset": cb["offset"] if cb else None,
            "TD": "0x%08X" % cb["TD"] if cb and cb["TD"] else None,
            "mangled": cb["mangled"] if cb else None,
            "class": rtti_class(cb["mangled"]) if cb else None,
        }
        C["site_0043B71F"]["building_slots"] = len(table_slots(img, vt_bldg))

    # InfantryClass 表
    ci = col_chain(img, vt_inf)
    C["table_007EB058"] = {
        "COL": "0x%08X" % ci["COL"] if ci and ci["COL"] else None,
        "offset": ci["offset"] if ci else None,
        "TD": "0x%08X" % ci["TD"] if ci and ci["TD"] else None,
        "mangled": ci["mangled"] if ci else None,
        "class": rtti_class(ci["mangled"]) if ci else None,
        "slot_count": len(table_slots(img, vt_inf)),
    }

    # 全表枚举：这两条 entry 各被哪些表装在哪个槽
    C["tables_of_005B3570"] = enum_tables_of_entry(img, 0x005B3570)
    C["tables_of_005B35E0"] = enum_tables_of_entry(img, 0x005B35E0)
    for k in ("tables_of_005B3570", "tables_of_005B35E0"):
        C[k] = [{"vt": "0x%08X" % r["vt"], "slot": r["slot"],
                 "class": rtti_class(r["mangled"]), "mangled": r["mangled"],
                 "COL": "0x%08X" % r["COL"]} for r in C[k]]

    # 007EB058 的全部装表点（同一表多装表点是否正常）
    sw = find_install_sites(img, vt_inf)
    C["all_install_sites_007EB058"] = ["0x%08X" % a for a in sw["hits"]]
    C["install_scan_007EB058"] = sw["candidates"]
    if vt_bldg:
        swb = find_install_sites(img, vt_bldg)
        C["all_install_sites_007E3EBC"] = ["0x%08X" % a for a in swb["hits"]]
        C["install_scan_007E3EBC"] = swb["candidates"]

    # 行 32/33 声明的装表点
    C["claimed_sites"] = {}
    for e, s in (("005B3570", 0x00517D9D), ("005B35E0", 0x00521A11)):
        imm, insn = site_imm(img, s)
        cf = C.get("_claimed_func", {}).get(e)
        C["claimed_sites"][e] = {
            "site": "0x%08X" % s,
            "insn": (insn.mnemonic + " " + insn.op_str) if insn else None,
            "is_mov_mem_imm": bool(is_mov_mem_imm(insn)),
            "imm32": ("0x%08X" % imm) if imm is not None else None,
            "imm_eq_007EB058": (imm == vt_inf),
        }

    # 行 32/33 声明函数体的独立校验
    for e, s, f in (("005B3570", 0x00517D9D, 0x00517D90),
                    ("005B35E0", 0x00521A11, 0x00521960)):
        fchk = func_ok(img, f, s)
        br = body_range(img, f) if fchk["ok"] else None
        C["claimed_sites"][e].update({
            "claimed_func": "0x%08X" % f,
            "func_start_valid": fchk,
            "body": ["0x%08X" % br[0], "0x%08X" % br[1]] if br else None,
            "entry_in_body": bool(br and br[0] <= int(e, 16) < br[1]),
        })

    # 行 32/33 在同一张表里的槽位（用已知 vt 直接读）
    C["slot_of_entry"] = {}
    for e in ("005B3570", "005B35E0"):
        ev = int(e, 16)
        per = {}
        for tname, tvt in (("007EB058_Infantry", vt_inf), ("BuildingClass", vt_bldg)):
            if not tvt:
                continue
            slots = table_slots(img, tvt)
            hits = [i for i, v in enumerate(slots) if v == ev]
            per[tname] = {"vt": "0x%08X" % tvt, "slots": hits}
        C["slot_of_entry"][e] = per

    res["C"] = C

    # ---------- 全批 vt 的装表点全景（支撑 §C「同一表多装表点属正常」） ----------
    vtmap = {}
    for r in res["rows"]:
        if r.get("vt") is None:
            continue
        t = int(r["vt"], 16)
        vtmap.setdefault(t, {"rows": [], "chosen": set()})
        vtmap[t]["rows"].append(r["entry"])
        if r.get("site"):
            vtmap[t]["chosen"].add(int(r["site"], 16))
    pan = []
    for t in sorted(vtmap):
        sites = find_install_sites(img, t)["hits"]
        pan.append({
            "vt": "0x%08X" % t,
            "rows": vtmap[t]["rows"],
            "n_install_sites": len(sites),
            "install_sites": ["0x%08X" % s for s in sites],
            "chosen_site": ["0x%08X" % s for s in sorted(vtmap[t]["chosen"])],
            "chosen_in_enumerated": all(s in sites for s in vtmap[t]["chosen"]),
        })
    res["install_panorama"] = pan

    # 全文件级的过时指针扫描（不只看 ④ 段）
    res["meta"]["whole_file_12_4_hits"] = [i for i in range(1, len(d_rows))
                                           if "§12.4" in d_rows[i].decode("utf-8", "replace")]
    res["meta"]["whole_file_12_6_count"] = sum(
        1 for i in range(1, len(d_rows)) if "§12.6" in d_rows[i].decode("utf-8", "replace"))

    # ---------- 汇总 ----------
    def bad(pred):
        return [r["n"] for r in res["rows"] if not pred(r)]

    summary = {
        "total": len(res["rows"]),
        "A_bad": bad(lambda r: r["A"].get("ok")),
        "B_bad": bad(lambda r: r["B"].get("ok")),
        "D_bad": bad(lambda r: r["D"].get("ok")),
        "E_bad": bad(lambda r: r["E"].get("ok")),
        "F_bad": [],
        "pointer_12_6_count": sum(1 for r in res["rows"]
                                  if r["D"].get("points_section_12_6")),
        "pointer_12_4_count": sum(1 for r in res["rows"]
                                  if r["D"].get("has_stale_12_4")),
        "B_sub": {k: [r["n"] for r in res["rows"]
                      if not r["B"].get(k, {}).get("ok", False)]
                  for k in ("c1", "c2", "c3", "c4", "c5", "c6")},
        "aux_site_in_body_bad": [r["n"] for r in res["rows"]
                                 if not r["aux_func"].get("site_in_body")],
        "aux_entry_out_bad": [r["n"] for r in res["rows"]
                              if not r["aux_func"].get("entry_out_of_body")],
        "aux_func_start_invalid": [r["n"] for r in res["rows"]
                                   if not r["aux_func"].get("detected_matches_claim")],
        "D_neg_12_4_rows": [r["n"] for r in res["rows"]
                            if any(r.get("D_neg", {}).values())],
        "D_info_cls_literal_mismatch": [r["n"] for r in res["rows"]
                                        if not r.get("D_info", {}).get("cls_exact_eq_rtti")],
    }
    res["summary"] = summary

    # ---------- bytecheck.tsv ----------
    out = []
    out.append("\t".join(["n", "entry", "name", "slot_no",
                          "c1_u32vt_slot", "c2_u32vt-4_COL", "c3_u32COL+4_off",
                          "c4_u32COL+12_TD", "c5_cstrTD+8", "c6_site_imm32",
                          "verdict", "note"]))
    for r in res["rows"]:
        b = r["B"]
        if "c1" not in b:
            out.append("\t".join([str(r["n"]), r["entry"], r["name"], str(r["slot_no"]),
                                  "NA", "NA", "NA", "NA", "NA", "NA", "FAIL", "④unparsed"]))
            continue
        def cell(k):
            c = b[k]
            if not c.get("ok"):
                return "FAIL:%s" % (c.get("read"),)
            if k == "c6":
                return "OK:%s" % (c.get("insn"),)
            return "OK:%s" % (c.get("read"),)
        out.append("\t".join([str(r["n"]), r["entry"], r["name"], str(r["slot_no"]),
                              cell("c1"), cell("c2"), cell("c3"), cell("c4"),
                              cell("c5"), cell("c6"),
                              "PASS" if b["ok"] else "FAIL", ""]))
    with open(os.path.join(BASE, "bytecheck.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")

    with open(os.path.join(BASE, "verify_out.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)

    # ---------- 控制台汇总 ----------
    print("=" * 78)
    print("gamemd.exe", res["meta"]["exe"]["size"], res["meta"]["exe"]["sha256"])
    print("coverage.tsv", res["meta"]["coverage"]["size"], res["meta"]["coverage"]["sha256"],
          "rows", res["meta"]["coverage"]["n_data_rows"])
    print("delta.tsv", res["meta"]["delta"]["size"], res["meta"]["delta"]["sha256"])
    print("batch order ok:", res["meta"]["batch_order_ok"],
          "| 13 unique:", res["meta"]["entry_unique_13"])
    print("-" * 78)
    print("A_bad", summary["A_bad"])
    print("B_bad", summary["B_bad"], "sub", summary["B_sub"])
    print("D_bad", summary["D_bad"])
    print("E_bad", summary["E_bad"])
    print("ptr §12.6 =", summary["pointer_12_6_count"],
          "| stale §12.4 =", summary["pointer_12_4_count"])
    print("F norm unique:", res["meta"]["F_norm_unique"],
          "| strict dups:", len(res["meta"]["F_strict_dup_groups"]))
    print("  vt/slot/cls/site distinct:",
          res["meta"]["F_distinct_vt"], res["meta"]["F_distinct_slot"],
          res["meta"]["F_distinct_cls"], res["meta"]["F_distinct_site"])
    print("aux: site_in_body_bad", summary["aux_site_in_body_bad"],
          "| entry_out_bad", summary["aux_entry_out_bad"],
          "| func_start_invalid", summary["aux_func_start_invalid"])
    print("D_neg(§12.4) rows:", summary["D_neg_12_4_rows"])
    print("D_info 类名字面不等(模板伪名, 非阻断):", summary["D_info_cls_literal_mismatch"])
    print("-" * 78)
    print("precedent skeleton equal:", res["meta"]["precedent_skeletons_equal"])
    print("PRECEDENT SKEL:", res["meta"]["precedent_skeleton"])
    print("-" * 78)
    print("§C site 0043B71F:", json.dumps(C["site_0043B71F"], ensure_ascii=False))
    print("§C table 007EB058:", json.dumps(C["table_007EB058"], ensure_ascii=False))
    print("§C tables_of_005B3570:")
    for x in C["tables_of_005B3570"]:
        print("   ", json.dumps(x, ensure_ascii=False))
    print("§C tables_of_005B35E0:")
    for x in C["tables_of_005B35E0"]:
        print("   ", json.dumps(x, ensure_ascii=False))
    print("§C all install sites vt=007EB058:", C["all_install_sites_007EB058"],
          "(0xC7 candidates scanned: %d)" % C.get("install_scan_007EB058", -1))
    print("§C all install sites vt=%s:" % C["site_0043B71F"]["imm32"],
          C.get("all_install_sites_007E3EBC"))
    print("§C slot_of_entry:", json.dumps(C.get("slot_of_entry"), ensure_ascii=False))
    print("-" * 78)
    print("装表点全景（本批 8 张 vt）:")
    for p_ in pan:
        print("  vt=%s rows=%s sites(%d)=%s chosen=%s in_enum=%s"
              % (p_["vt"], ",".join(p_["rows"]), p_["n_install_sites"],
                 ",".join(p_["install_sites"]), ",".join(p_["chosen_site"]),
                 p_["chosen_in_enumerated"]))
    print("whole-file §12.4 hits:", res["meta"]["whole_file_12_4_hits"],
          "| §12.6 行数:", res["meta"]["whole_file_12_6_count"])
    pc = res["meta"]["precedent_census"]
    print("-" * 78)
    print("§E 全量先例普查: 总行数", pc["total_rows_with_ring4"],
          "| variantA(本批同骨架)", pc["variantA_n"],
          "| variantB(类名归属)", pc["variantB_n"],
          "| 不可解析", pc["unparsed_n"])
    print("   variantA 骨架种类数:", pc["variantA_distinct_skeletons"],
          "| 全部 == 本批骨架:", pc["variantA_equals_batch_skeleton"])
    print("§C claimed sites:", json.dumps(C["claimed_sites"], ensure_ascii=False, indent=1))
    print("=" * 78)


if __name__ == "__main__":
    main()
