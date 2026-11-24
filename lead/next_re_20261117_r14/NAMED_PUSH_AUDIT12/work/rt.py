"""RTTI + 结构读取工具（独立实现，不引用执行器产物）"""
import struct
from aud import Img, IB

im = Img()

def vt_slots(vt, n=32):
    """读 vtable 前 n 个槽"""
    return [im.u32(vt + 4*i) for i in range(n)]

def col_from_vt(vt):
    """vtable[-1] = COL 指针"""
    return im.u32(vt - 4)

def ptr(v, base_hint=True):
    """本镜像的 RTTI 指针是绝对 VA；给一个 RVA 也能兜底。"""
    if v is None:
        return None
    if v >= IB:
        return v
    return IB + v

def col_info(col):
    if col is None:
        return None
    sig = im.u32(col)
    off = im.u32(col + 4)
    cd = im.u32(col + 8)
    td_raw = im.u32(col + 0xC)
    chd_raw = im.u32(col + 0x10)
    self_raw = im.u32(col + 0x14)
    td = ptr(td_raw)
    name = im.cstr(td + 8, 300) if td else None
    return dict(col=col, sig=sig, off=off, cd=cd, td=td, td_raw=td_raw,
                chd=ptr(chd_raw), chd_raw=chd_raw, self=ptr(self_raw), name=name)

def vt_name(vt):
    c = col_from_vt(vt)
    if not c:
        return None, None
    ci = col_info(c)
    return (ci or {}).get("name"), c

def is_text(va):
    return 0x401000 <= va < 0x7E038D

def dump_vt(vt, n=12, tag=""):
    ci_name, col = vt_name(vt)
    print(f"  vt {vt:08X} [{tag}] COL={col and hex(col)} name={ci_name}")
    for i, s in enumerate(vt_slots(vt, n)):
        mark = ""
        if s and is_text(s):
            mark = " .text"
        print(f"    slot{i:<2} (+0x{4*i:02X}) = {s:08X}{mark}")
