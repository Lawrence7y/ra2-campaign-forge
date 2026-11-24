"""S09-K1 通用 RE 库：基于 audit_lib.Bin，增加 RTTI 解析、虚表定界、反汇编辅助。

纪律：capstone 全程 skipdata=True；VA 寻址 ImageBase=0x400000。
只读 gamemd.exe。
"""
import os
import sys
import struct
import capstone

# 允许 import lead audit_lib
_ROOT = r"D:\Project\ra2-campaign-forge"
_AUDIT = os.path.join(_ROOT, r"lead\next_re_20261116_r12\_lead_audit")
if _AUDIT not in sys.path:
    sys.path.insert(0, _AUDIT)
from audit_lib import Bin, md32, linear_from, boundary_check, sweep_calls, sweep_disps  # noqa

IMAGE_BASE = 0x400000

# 已知线索常量（仅作交叉校验，不作判据）：来自 R8_ui_crt.md / kb11，须本卡重新取证
CLUE_VTABLES = {
    0x7F3058: "SidebarClass?",
    0x7F2F44: "SBGadgetClass?",
    0x7F2FCC: "SelectClass@StripClass@SidebarClass?",
    0x7E1964: "MouseClass?",
    0x7F7B2C: "WWMouseClass?",
    0x7E6114: "DisplayClass?",
    0x7F4348: "TacticalClass?",
    0x7EBE3C: "CommandClass?",
}


def is_int_ptr(v, lo=0x400000, hi=0x900000):
    return lo <= v <= hi


class RTTI:
    """从 .rdata 自建 RTTI 表。正确的链：COL + 0xC -> TD; TD + 8 -> name."""

    def __init__(self, b: Bin):
        self.b = b
        self.rdata = b.sec(".rdata")
        self.tds = {}      # td_va -> name(str)
        self.cols = {}     # col_va -> dict(offset, cdOffset, td, chd, name, vtable, slots)
        self.vtable_to_col = {}  # vtable_va -> col_va
        self._scan_tds()
        self._scan_cols()
        self._link_vtables()

    def _u32(self, va):
        return self.b.u32(va)

    def _cstr(self, va, maxn=256):
        out = bytearray()
        for i in range(maxn):
            try:
                ch = self.b.read(va + i, 1)[0]
            except Exception:
                return None
            if ch == 0:
                return out.decode("utf-8", errors="replace")
            out.append(ch)
        return None

    def _in_rdata(self, va, n=4):
        s = self.rdata
        return s["va"] <= va and va + n <= s["va"] + s["rawsize"]

    def _scan_tds(self):
        """TypeDescriptor(x86 MSVC): +0 pVFTable(指向 RTTI TD 虚表, 常量),
        +4 spare(0), +8 name(char[] 内联, '.?AV...' / '.?AU...', NUL 结尾).

        ⚠️ name 是**内联数组**不是指针；正确链是 COL+0xC -> TD, TD+8 -> name 字符串。
        读 u32(TD+8) 得到的是 '.?AV' 的 ASCII，绝不可当指针。
        本镜像所有 TD 的 pVFTable 常量 = 0x7F9594，可作签名。
        """
        # 扫描所有有 raw 数据的节（本镜像 TD 在 .data，COL 在 .rdata）
        TD_VFT = 0x7F9594
        for s in self.b.sections:
            buf = self.b.pe.__data__[s["raw"]:s["raw"] + s["rawsize"]]
            base = s["va"]
            for i in range(0, len(buf) - 16, 4):
                va = base + i
                pvf = struct.unpack_from("<I", buf, i)[0]
                if pvf != TD_VFT:
                    continue
                spare = struct.unpack_from("<I", buf, i + 4)[0]
                if spare != 0:
                    continue
                nm = self._cstr(va + 8)
                if not nm:
                    continue
                if nm.startswith(".?AV") or nm.startswith(".?AU"):
                    self.tds[va] = nm

    def _scan_cols(self):
        """CompleteObjectLocator(x86): +0 sig(=0), +4 offset, +8 cdOffset,
        +0xC pTypeDescriptor, +0x10 pCHD."""
        # COL 在 .rdata（也扫所有节以防万一）
        for s in self.b.sections:
            buf = self.b.pe.__data__[s["raw"]:s["raw"] + s["rawsize"]]
            base = s["va"]
            for i in range(0, len(buf) - 20, 4):
                va = base + i
                sig, off, cd = struct.unpack_from("<III", buf, i)
                if sig != 0:
                    continue
                td = struct.unpack_from("<I", buf, i + 0xC)[0]
                chd = struct.unpack_from("<I", buf, i + 0x10)[0]
                if td not in self.tds:
                    continue
                # fail-closed 校验：TD+8 必须给出可读名字
                nm = self.tds[td]
                if not nm or nm == "?":
                    continue
                if not (is_int_ptr(chd)):
                    continue
                self.cols[va] = dict(col=va, section=s["name"], offset=off, cdOffset=cd,
                                     td=td, chd=chd, name=nm, vtable=None, slots=None)

    def _link_vtables(self):
        """vtable[-4] = COL pointer。扫所有节所有 dword == col_va 的位置。"""
        colset = set(self.cols.keys())
        for s in self.b.sections:
            buf = self.b.pe.__data__[s["raw"]:s["raw"] + s["rawsize"]]
            base = s["va"]
            for i in range(0, len(buf) - 4, 4):
                v = struct.unpack_from("<I", buf, i)[0]
                if v in colset:
                    pos = base + i
                    vt = pos + 4
                    col_va = v
                    self.vtable_to_col.setdefault(vt, col_va)
                    if self.cols[col_va]["vtable"] is None:
                        self.cols[col_va]["vtable"] = vt

    def parent_of(self, col_va):
        """从 CHD 读父类名（第一个 base class，跳过自身）。返回 (parent_name, nbase, bases_list)."""
        rec = self.cols[col_va]
        chd = rec["chd"]
        try:
            sig, attrs, nbase, pbase = struct.unpack("<IIII", self.b.read(chd, 16))
        except Exception:
            return (None, None, [])
        bases = []
        for i in range(min(nbase, 32)):
            bcd = self.b.u32(pbase + i * 4)
            if not is_int_ptr(bcd):
                bases.append((None, None))
                continue
            try:
                td = self.b.u32(bcd)
                nm = self.tds.get(td)
                if nm is None and is_int_ptr(td):
                    nm = self._cstr(td + 8)   # name 内联在 TD+8
                bases.append((td, nm))
            except Exception:
                bases.append((None, None))
        # 通常 bases[0] 是自身；父类是 bases[1:]
        parent = None
        for td, nm in bases[1:]:
            if nm and nm != rec["name"]:
                parent = nm
                break
        return (parent, nbase, bases)

    def demangle(self, nm):
        """'.?AVSidebarClass@@' -> 'SidebarClass'."""
        if not nm:
            return nm
        s = nm
        for p in (".?AV", ".?AU"):
            if s.startswith(p):
                s = s[len(p):]
                break
        if s.endswith("@@"):
            s = s[:-2]
        return s


def vtable_slots(b: Bin, vt_va, next_boundary=None, maxslots=600):
    """从 vtable 起点读槽，直到遇到非代码指针或到达 next_boundary。

    返回 (slots, end_va, reason)。slots = [(slot_index, slot_va, func_va), ...]
    ⚠️ 槽值是编译器放进去的函数地址，"槽值即函数"，不再用像不像函数二次筛选。
    但定界仍需：下一个 COL 引用点 / 非 .text 指针 / 表间边界。
    """
    text = b.sec(".text")
    slots = []
    i = 0
    va = vt_va
    while i < maxslots:
        if next_boundary is not None and va >= next_boundary:
            break
        try:
            fv = b.u32(va)
        except Exception:
            break
        # 槽值应在 .text 内（含 0 = 纯虚插槽，保留但标记）
        intext = (text["va"] <= fv < text["va"] + text["rawsize"])
        if fv == 0:
            slots.append((i, va, 0))
        elif intext:
            slots.append((i, va, fv))
        else:
            # 非 .text 指针：可能是表尾（下一个 COL 指针、对齐、其它数据）
            break
        va += 4
        i += 1
    return slots, va, "non-text-or-boundary"


if __name__ == "__main__":
    b = Bin()
    for s in b.sections:
        print("%-8s va=%08X vsize=%08X raw=%08X rawsize=%08X" %
              (s["name"], s["va"], s["vsize"], s["raw"], s["rawsize"]))
    r = RTTI(b)
    print("TDs:", len(r.tds), "COLs:", len(r.cols), "vtable->col:", len(r.vtable_to_col))
    # 交叉校验线索虚表
    for vt, label in CLUE_VTABLES.items():
        col = r.vtable_to_col.get(vt)
        if col:
            rec = r.cols[col]
            print("vt=%08X %-42s -> COL=%08X name=%s" % (vt, label, col, rec["name"]))
        else:
            print("vt=%08X %-42s -> (no COL at vt-4; col=%08X)" % (vt, label,
                  b.u32(vt - 4) if True else 0))
