"""MSVC RTTI 解析：从 PE 里恢复**类继承图**与 **vtable 地址表**。

这是 `M2 oracle 骨架` 的第一半，也是 `M1 渲染接管`（定位 `Blitter`/`BSurface`）的地基。
为什么要做：`gamemd.exe` 保留了 307 个 C++ 类名（见 docs/REWRITE_RESEARCH.md §1.2），
而 MSVC 的 RTTI 结构里带基类链、vtable 第 `-1` 槽指回 `CompleteObjectLocator`，
于是"类名 → 继承链 → vtable 地址 → 各虚函数地址"可以**程序化恢复**。

### 关于布局：不靠记忆，靠自洽性检验

MSVC 的 RTTI 结构在不同版本里布局不同（VC6/VC7 与 VS2005+ 的 `TypeDescriptor`
头部宽度、以及 vtable 里存的是**绝对地址**还是 **RVA** 都不一样）。这里不预设版本，
而是：

1. 扫描全部 `.?AV…@@` 装饰名；
2. 对每个名字试几种"头部宽度"假设，看哪种能让**绝大多数** TypeDescriptor 的第一个
   dword 指向同一个合法地址（那正是共享的 `type_info` vtable）——**自洽的那个就是对的**；
3. 之后所有结构都按这个假设解析，并在每一步做合法性校验（签名、指针落在节内、基类数合理）。

VC6/VC7 与 VS2005+ 的指针字段差异也用同一招处理：对每个 TypeDescriptor 地址，
既试"绝对地址"也试"RVA"，取命中数多的那个方案。
"""

from __future__ import annotations

import json
import re
import struct
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from ra2opt import pe

# 装饰名：.?AV<class>@@ / .?AU<struct>@@ / .?AW<enum>@@
NAME_RE = re.compile(rb"\.\?A([VUW])([^\x00]{1,220}?)@@")

# 头部宽度候选项（字节）：标题 8 = pVFTable+_m_data，12/16 = 更多保留字段
HEADER_HYPOTHESES = (8, 12, 16)

MAX_BASE_CLASSES = 24        # 合理性上限：超过就认为不是 ClassHierarchyDescriptor
IMAGE_BASE_DEFAULT = 0x400000

# MSVC 的接口按约定以 I 开头（IUnknown / IPersistStream / IHouse …）。
# 基类数组里"自己 + 主基类链 + 接口/混入"是连续排列的，遇到第一个接口名就认为类链结束。
INTERFACE_RE = re.compile(r"^I[A-Z]")


def split_chain(base_names: list) -> tuple:
    """把 RTTI 基类数组拆成 (类继承链, 接口/混入列表)。

    数组形如 `[自己, 主基类, …, 根类, 接口…, 混入…]`。
    """
    chain: list = []
    for i, n in enumerate(base_names[1:]):
        if INTERFACE_RE.match(n):
            return chain, base_names[1 + i:]
        chain.append(n)
    return chain, []


@dataclass
class Image:
    """PE 镜像的字节视图与地址换算。"""

    path: Path
    data: bytes
    info: pe.PEInfo
    image_base: int

    @classmethod
    def load(cls, path) -> "Image":
        info = pe.read(path)
        return cls(path=Path(path), data=Path(path).read_bytes(),
                   info=info, image_base=info.image_base or IMAGE_BASE_DEFAULT)

    # -- 地址换算 ---------------------------------------------------------
    def rva2off(self, rva: int) -> int | None:
        for s in self.info.sections:
            size = max(s.virtual_size, s.raw_size)
            if s.virtual_address <= rva < s.virtual_address + size:
                off = s.raw_offset + (rva - s.virtual_address)
                return off if 0 <= off < len(self.data) else None
        return None

    def off2rva(self, off: int) -> int | None:
        for s in self.info.sections:
            end = s.raw_offset + s.raw_size
            if s.raw_offset <= off < end:
                return s.virtual_address + (off - s.raw_offset)
        return None

    def u32(self, off: int) -> int | None:
        if off is None or off < 0 or off + 4 > len(self.data):
            return None
        return struct.unpack_from("<I", self.data, off)[0]

    def u32_at_va(self, va: int) -> int | None:
        return self.u32(self.rva2off(va - self.image_base))

    def cstr_at(self, off: int, limit: int = 240) -> str:
        end = self.data.find(b"\x00", off, off + limit)
        if end < 0:
            end = off + limit
        return self.data[off:end].decode("latin-1", "replace")

    # -- 区段查询 ---------------------------------------------------------
    def section_of_rva(self, rva: int) -> str | None:
        for s in self.info.sections:
            size = max(s.virtual_size, s.raw_size)
            if s.virtual_address <= rva < s.virtual_address + size:
                return s.name
        return None

    def is_executable_va(self, va: int) -> bool:
        off = self.rva2off(va - self.image_base)
        if off is None:
            return False
        rva = va - self.image_base
        return self.section_of_rva(rva) == ".text"

    def in_image(self, va: int) -> bool:
        return self.rva2off(va - self.image_base) is not None


@dataclass
class RawName:
    mangled: str
    kind: str
    name: str
    string_off: int
    string_rva: int
    string_va: int


@dataclass
class ClassInfo:
    name: str
    kind: str
    type_descriptor_va: int
    vtable_va: int | None = None
    col_va: int | None = None
    vfunc_count: int = 0
    vfuncs: list = field(default_factory=list)
    bases: list = field(default_factory=list)      # 由派生到基的顺序
    base_names: list = field(default_factory=list)
    header_delta: int = 0
    vtable_candidates: int = 0                     # COL 地址在镜像里被几处引用过

    def as_dict(self, with_vfuncs: bool = True) -> dict:
        d = {
            "name": self.name,
            "kind": self.kind,
            "type_descriptor_va": "%08X" % self.type_descriptor_va,
            "col_va": "%08X" % self.col_va if self.col_va else None,
            "vtable_va": "%08X" % self.vtable_va if self.vtable_va else None,
            "vfunc_count": self.vfunc_count,
            "bases": self.base_names,
        }
        if with_vfuncs:
            d["vfuncs"] = ["%08X" % a for a in self.vfuncs]
        return d


# ---------------------------------------------------------------------------
# 步骤 1：收集装饰名
# ---------------------------------------------------------------------------

def find_names(img: Image) -> list:
    """扫描所有装饰名。注意 `off2rva()` 返回的是 **RVA**，VA 要再加镜像基址——
    这里把两者都存下来，避免后面把 RVA 当 VA 用（踩过一次）。"""
    out = []
    for m in NAME_RE.finditer(img.data):
        kind = m.group(1).decode()
        mangled = img.cstr_at(m.start(), 240)
        name = mangled[4:-2] if mangled.endswith("@@") else mangled[4:]
        rva = img.off2rva(m.start())
        if rva is None:
            continue
        out.append(RawName(mangled=mangled, kind=kind, name=name,
                           string_off=m.start(), string_rva=rva,
                           string_va=rva + img.image_base))
    return out


# ---------------------------------------------------------------------------
# 步骤 2：自洽地选出 TypeDescriptor 头部宽度
# ---------------------------------------------------------------------------

def infer_header_delta(img: Image, names: list) -> tuple:
    """返回 (header_delta, 期望的 type_info vftable 地址, 诊断信息)。

    判据：正确的头部宽度下，绝大多数 TypeDescriptor 的第一个 dword（pVFTable）
    会指向**同一个**地址（`type_info` 的 vtable），且该地址落在已加载节内。
    """
    report = {}
    best = (None, None, -1.0)
    for delta in HEADER_HYPOTHESES:
        vtables = Counter()
        valid = 0
        for n in names:
            pvft = img.u32_at_va(n.string_va - delta)
            if pvft and img.in_image(pvft):
                vtables[pvft] += 1
                valid += 1
        if not valid:
            report[delta] = {"valid": 0, "top_share": 0.0, "top": None, "distinct": 0}
            continue
        top_v, top_c = vtables.most_common(1)[0]
        share = top_c / valid
        report[delta] = {"valid": valid, "top_share": round(share, 4),
                         "top": "%08X" % top_v, "distinct": len(vtables)}
        if share > best[2]:
            best = (delta, top_v, share)
    return best[0], best[1], report


# ---------------------------------------------------------------------------
# 步骤 3–6：解析 COL / CHD / 基类数组 / vtable
# ---------------------------------------------------------------------------

def _scan_for_values(img: Image, values: set) -> dict:
    """单遍 dword 扫描全镜像，返回 {被匹配的值: [命中处的 RVA, ...]}。

    RTTI 里的指针字段都是 4 字节对齐，所以按 dword 步进即可——307 个目标值下
    也用不着更复杂的索引。
    """
    hits: dict = {}
    data = img.data
    for off in range(0, len(data) - 3, 4):
        v = struct.unpack_from("<I", data, off)[0]
        if v in values:
            rva = img.off2rva(off)
            if rva is not None:
                hits.setdefault(v, []).append(rva)
    return hits


def _resolve_pointer(img: Image, value: int, schemes=("abs", "rva")) -> int | None:
    """把字段值解释成 VA。返回 image-relative VA（即地址）或 None。"""
    for scheme in schemes:
        va = value if scheme == "abs" else value + img.image_base
        if va and img.in_image(va):
            return va
    return None


def _vtable_run(img: Image, vt_va: int, limit: int = 512) -> list:
    """从 vt_va 起读出连续的"指向 .text 的 dword"——即虚函数地址列表。"""
    addrs: list = []
    off = img.rva2off(vt_va - img.image_base)
    while off is not None and len(addrs) < limit:
        v = img.u32(off)
        if v is None or not img.is_executable_va(v):
            break
        addrs.append(v)
        off += 4
    return addrs


def parse(img: Image, verbose: bool = False) -> dict:
    raw_names = find_names(img)
    header_delta, expected_vfptr, header_report = infer_header_delta(img, raw_names)

    diagnostics = {
        "raw_names": len(raw_names),
        "header_hypotheses": {str(k): v for k, v in header_report.items()},
        "header_delta": header_delta,
        "type_info_vftable_va": "%08X" % expected_vfptr if expected_vfptr else None,
    }
    if header_delta is None:
        raise RuntimeError("无法为 TypeDescriptor 找到自洽的头部宽度；见 header_hypotheses")

    # 只有"名字前面正好有一个指向 type_info vftable 的头"的才算 TypeDescriptor。
    # 这条过滤很关键：镜像里还有形如 .?AV…@@ 的普通字符串（不是类型对象）。
    classes: dict = {}
    rejected = 0
    for n in raw_names:
        td_va = n.string_va - header_delta
        pvft = img.u32_at_va(td_va)
        if not pvft or not img.in_image(pvft):
            rejected += 1
            continue
        if expected_vfptr is not None and pvft != expected_vfptr:
            rejected += 1
            continue
        ci = classes.get(td_va)
        if ci is None:
            classes[td_va] = ClassInfo(name=n.name, kind=n.kind,
                                       type_descriptor_va=td_va,
                                       header_delta=header_delta)
        elif len(n.name) < len(ci.name):
            ci.name = n.name      # 同一个描述符被多次引用时取较短名
    diagnostics["rejected_names"] = rejected

    # 找 CompleteObjectLocator：某个 dword == 某个 TypeDescriptor 地址，其位置 = COL+12
    td_hits = _scan_for_values(img, set(classes.keys()))
    col_to_td: dict = {}          # col_va -> td_va
    chd_of_col: dict = {}         # col_va -> chd_va
    for td_va, rvas in td_hits.items():
        for rva in rvas:
            col_rva = rva - 12
            if col_rva < 0:
                continue
            sig = img.u32(img.rva2off(col_rva))
            cd_off = img.u32(img.rva2off(col_rva + 8))
            u32_at16 = img.u32(img.rva2off(col_rva + 16))
            if sig not in (0, 1) or cd_off is None:
                continue
            # pClassDescriptor：绝对地址或 RVA
            chd_va = _resolve_pointer(img, u32_at16) if u32_at16 is not None else None
            if chd_va is None:
                continue
            num = img.u32_at_va(chd_va + 8)
            if num is None or not (1 <= num <= MAX_BASE_CLASSES):
                continue
            col_va = col_rva + img.image_base
            if col_va not in col_to_td:
                col_to_td[col_va] = td_va
                chd_of_col[col_va] = chd_va
            classes[td_va].col_va = classes[td_va].col_va or col_va

    # 基类链：CHD -> BaseClassArray -> BaseClassDescriptor[]
    # 注意：一个类可能有多个 COL（多继承 → 多个 vtable），但继承链只有一个。
    # 只按第一个 COL 解析一次，否则链会被重复拼接。
    seen_td = set()
    for col_va in sorted(col_to_td):
        td_va = col_to_td[col_va]
        if td_va in seen_td:
            continue
        seen_td.add(td_va)
        ci = classes[td_va]
        chd_va = chd_of_col[col_va]
        num = img.u32_at_va(chd_va + 8) or 0
        bca_raw = img.u32_at_va(chd_va + 12)
        if bca_raw is None:
            continue
        bca_va = _resolve_pointer(img, bca_raw)
        if bca_va is None:
            continue
        for i in range(num):
            bcd_raw = img.u32_at_va(bca_va + 4 * i)
            if bcd_raw is None:
                break
            bcd_va = _resolve_pointer(img, bcd_raw)
            if bcd_va is None:
                break
            base_td = img.u32_at_va(bcd_va)
            if base_td is None:
                break
            base = classes.get(base_td)
            ci.bases.append(base_td)
            ci.base_names.append(base.name if base else "?(%08X)" % base_td)

    # vtable：某处存着 COL 地址，其位置 = vtable-4。
    # COL 地址在镜像里可能被多处引用（跳转表、其他表…），所以选"后面连续 .text 指针最长"
    # 的那个位置——真正的 vtable 才是连续一长串代码地址。
    col_hits = _scan_for_values(img, set(col_to_td.keys()))
    for col_va, rvas in col_hits.items():
        ci = classes[col_to_td[col_va]]
        for rva in rvas:
            vt_va = rva + 4 + img.image_base
            addrs = _vtable_run(img, vt_va)
            if len(addrs) > ci.vfunc_count:
                ci.vtable_va = vt_va
                ci.vfuncs = addrs
                ci.vfunc_count = len(addrs)
                ci.vtable_candidates = len(rvas)

    diagnostics.update({
        "classes": len(classes),
        "with_col": sum(1 for c in classes.values() if c.col_va),
        "with_vtable": sum(1 for c in classes.values() if c.vtable_va),
        "with_bases": sum(1 for c in classes.values() if len(c.base_names) > 1),
    })
    return {"classes": classes, "diagnostics": diagnostics}


# ---------------------------------------------------------------------------
# 输出
# ---------------------------------------------------------------------------

def render_hierarchy(classes: dict, max_depth: int = 12) -> str:
    """把继承关系渲染成缩进树。

    父节点取 `split_chain()` 的**最后一个类**（直接基类），不能拿 `base_names[1]`
    ——多继承下那可能是接口，会把整个类层次挂错位置。
    """
    known = {c.name for c in classes.values()}
    children: dict = {}
    roots = []
    for ci in classes.values():
        chain, _ = split_chain(ci.base_names)
        parent = chain[-1] if chain else None
        if parent and parent in known:
            children.setdefault(parent, []).append(ci.name)
        else:
            roots.append(ci.name)

    lines: list = []

    def walk(name: str, depth: int):
        lines.append("  " * depth + name)
        if depth >= max_depth:
            return
        for kid in sorted(set(children.get(name, []))):
            walk(kid, depth + 1)

    for root in sorted(set(roots)):
        walk(root, 0)
    return "\n".join(lines)


def render_focus_table(classes: dict, wanted) -> str:
    """给指定类名打印 vtable 地址 / 虚函数数 / 基类链——M1 直接用这张表。"""
    by_name = {c.name: c for c in classes.values()}
    out = [f"{'类名':<20} {'vtable':>9} {'虚函数':>5}  继承链 + 接口/混入", "-" * 96]
    for w in wanted:
        c = by_name.get(w)
        if c is None:
            out.append(f"{w:<20} {'(未找到)':>9}")
            continue
        chain, extra = split_chain(c.base_names)
        vt = ("%08X" % c.vtable_va) if c.vtable_va else "(无)"
        tail = " → ".join(chain) if chain else "—"
        if extra:
            uniq = list(dict.fromkeys(extra))
            tail += f"　+{len(uniq)} 接口/混入"
        out.append(f"{c.name:<20} {vt:>9} {c.vfunc_count:>5}  {tail}")
    return "\n".join(out)


def render_class_card(classes: dict, name: str, max_children: int = 14) -> str:
    """单个类的"名片"：vtable / 虚函数数 / 继承链 / 子类。"""
    by_name = {c.name: c for c in classes.values()}
    c = by_name.get(name)
    if c is None:
        return f"{name}: (未找到)"
    chain, extra = split_chain(c.base_names)
    kids = sorted(x.name for x in classes.values()
                  if len(x.base_names) >= 2 and x.base_names[1] == name)
    lines = [f"{c.name}"]
    if c.vtable_va:
        lines.append(f"  vtable {c.vtable_va:08X}　虚函数 {c.vfunc_count} 个"
                     f"（首位 {('%08X' % c.vfuncs[0]) if c.vfuncs else '—'}）")
    else:
        lines.append("  无 vtable（纯接口/抽象或未 emit RTTI）")
    lines.append("  继承：" + (" → ".join(chain) if chain else "（根类）"))
    if extra:
        lines.append("  接口/混入：" + ", ".join(dict.fromkeys(extra)))
    if kids:
        shown = kids[:max_children]
        more = f" …+{len(kids) - len(shown)}" if len(kids) > len(shown) else ""
        lines.append(f"  子类（{len(kids)}）：" + ", ".join(shown) + more)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# M1 专用：软件 blit 实现族（接管点清单）
# ---------------------------------------------------------------------------

BLIT_TOKENS = (
    # 注意顺序：长 token 必须排在短 token 之前，否则 "Trans" 会把 "Translucent…" 吃掉。
    # 下面这三个 Translucent* 是完整名字，必须排在 "Trans" 前面。
    ("Translucent50NonzeroAlpha", "半透明 50%：非零 alpha 写回"),
    ("Translucent50ZeroAlpha", "半透明 50%：零 alpha"),
    ("TranslucentWriteAlpha", "半透明：写回 alpha"),
    ("MultWriteAlpha", "乘性写回 alpha"),
    ("WriteAlpha", "写回 alpha"),
    ("ZReadWrite", "读写深度缓冲"),
    ("ZRead", "读深度缓冲"),
    ("ZRemap", "深度重映射"),
    ("Lucent75", "75% 半透明"),
    ("Lucent50", "50% 半透明"),
    ("Lucent25", "25% 半透明"),
    ("Darken", "变暗（阴影）"),
    ("Xlat", "调色板重映射（阵营颜色）"),
    ("Warp", "扭曲（超时空效果）"),
    ("Trans", "透明（跳过色键）"),
    ("Plain", "不透明"),
    ("Alpha", "alpha 混合"),
    ("Dest", "目标混合"),
    ("Remap", "重映射"),
    ("Stretch", "拉伸缩放"),
)
DEPTH_TOKENS = {"E": "8 位调色板", "G": "16 位 RGB", "F": "浮点/其他"}


def decode_blit_name(name: str) -> tuple:
    """把 `?$BlitPlainXlat@G` / `?$RLEBlitTransXlat@E` 解码成 (模板名, 位深, [语义…])。

    MSVC 对模板类的命名（`?$` 前缀、`@` 后是位深实参）把 blit 语义编码得很清楚，
    这正好是 M1 需要的"哪个地址实现哪种 blit"。

    `RLE` 前缀要单独处理：那批派生自 **另一个抽象基类 `RLEBlitter`**（走 RLE 压缩路径），
    不是 `Blitter` 的子类——只按 `Blitter` 找会漏掉一半实现（实测踩过）。
    """
    if not name.startswith("?$"):
        return name, "", []
    body = name[2:]
    depth = ""
    if "@" in body:
        body, depth = body.rsplit("@", 1)
    rle = body.startswith("RLE")
    if rle:
        body = body[3:]
    if body.startswith("Blit"):
        body = body[4:]
    tokens: list = []
    rest = body
    while rest:
        for tok, desc in BLIT_TOKENS:
            if rest.startswith(tok):
                tokens.append(desc)
                rest = rest[len(tok):]
                break
        else:
            tokens.append(rest)
            break
    if rle:
        tokens.insert(0, "RLE 压缩路径")
    return ("RLEBlit" if rle else "Blit") + body, DEPTH_TOKENS.get(depth, depth), tokens


# 两个抽象基类，各自一族。只认其中一个会漏掉一半实现。
BLIT_BASES = ("Blitter", "RLEBlitter")


def _subtree(classes: dict, root: str) -> list:
    kids: dict = {}
    for c in classes.values():
        if len(c.base_names) >= 2:
            kids.setdefault(c.base_names[1], []).append(c)
    out, stack = [], [root]
    while stack:
        cur = stack.pop()
        for k in kids.get(cur, []):
            out.append(k)
            stack.append(k.name)
    return out


def render_blit_targets(classes: dict) -> str:
    """M1 接管点清单：所有软件 blit 实现 + 各自的虚函数地址。"""
    by_name = {c.name: c for c in classes.values()}
    missing = [b for b in BLIT_BASES if b not in by_name]
    if missing:
        return f"未找到抽象基类 {missing}（该 exe 可能不是预期的版本）"

    family = []
    for base in BLIT_BASES:
        family.extend(_subtree(classes, base))
    family.sort(key=lambda c: c.name)

    out = [
        "# M1 接管点清单：RA2 软件 blit 实现族",
        "#",
        "# 来源：gamemd.exe 的 MSVC RTTI（ra2re rtti 解析，非人工标注）",
    ]
    for base in BLIT_BASES:
        b = by_name[base]
        out.append(f"# {base:<11} 抽象基类 vtable = {b.vtable_va:08X}，"
                   f"虚函数 {b.vfunc_count} 个，子类 {len(_subtree(classes, base))} 个")
    out += [
        f"# 具体实现合计 {len(family)} 个",
        "#",
        "# 为什么重要：每个可见像素都要走一次这些函数，是「多单位卡顿」里 CPU 时间的主要去处",
        "# （实测确认：轻载场景下忙时 Top 5 热点全是这个族），也是 L1（渲染解耦 + GPU 化）",
        "# 要拦截或替换的目标。",
        "#",
        "# 格式：模板名 <TAB> 位深 <TAB> 语义 <TAB> vtable <TAB> 虚函数地址…",
        "",
    ]
    for c in family:
        tmpl, depth, toks = decode_blit_name(c.name)
        out.append(f"{c.name}\t{depth}\t{'/'.join(toks)}\t"
                   f"{c.vtable_va:08X}\t" + " ".join("%08X" % a for a in c.vfuncs))
    return "\n".join(out)


def dump(img: Image, out_dir, *, wanted=None, with_vfuncs: bool = True,
         verbose: bool = False) -> dict:
    """解析并写出 `symbols.json` + `hierarchy.txt`，返回结果字典。"""
    from ra2opt import safewrite

    result = parse(img, verbose=verbose)
    classes = result["classes"]
    diag = result["diagnostics"]

    payload = {
        "source": str(img.path),
        "image_base": "%08X" % img.image_base,
        "text_sha256": pe.text_section_sha256(img.path),
        "diagnostics": diag,
        "classes": {c.name: c.as_dict(with_vfuncs) for c in
                    sorted(classes.values(), key=lambda x: x.name)},
    }

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    safewrite.write_bytes(out, "symbols.json",
                          json.dumps(payload, ensure_ascii=False, indent=1).encode("utf-8"),
                          allow_create=True)
    safewrite.write_bytes(out, "hierarchy.txt",
                          render_hierarchy(classes).encode("utf-8"),
                          allow_create=True)
    safewrite.write_bytes(out, "m1_blit_targets.txt",
                          render_blit_targets(classes).encode("utf-8"),
                          allow_create=True)
    result["payload"] = payload
    result["out_dir"] = str(out)
    return result
