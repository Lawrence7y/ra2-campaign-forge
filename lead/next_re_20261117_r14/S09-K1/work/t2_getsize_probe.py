"""T2：GetSize 双向核对。
判据A：本类 vtable 的槽12 处函数体首 B8 <imm32> C3，取 imm32。
判据B：构造器/分配点的 push <size> 或 operator new 参数，取立即数。
两处独立对上才算闭合。叠加槽12 位置校验（全镜像 B8 imm C3 ~837，非槽12 543，故必须查槽位）。"""
import struct
import re_lib as R

b = R.Bin()
rtti = R.RTTI(b)
text = b.sec(".text")
t_lo, t_hi = text["va"], text["va"] + text["rawsize"]

# 主 S09 类（RTTI 实测值；来自 t1_class_table.py）
S09 = [
    ("SidebarClass", 0x7F3058),
    ("DisplayClass", 0x7E6114),
    ("MouseClass", 0x7E1964),
    ("WWMouseClass", 0x7F7B2C),
    ("SelectClass@StripClass@SidebarClass", 0x7F2FCC),
    ("SBGadgetClass@SidebarClass", 0x7F2F44),
    ("CommandClass", 0x7EBE3C),
    ("TabClass", 0x7EDFB4),
    ("ScrollClass", 0x7F1094),
    ("GadgetClass", 0x7E92BC),
    ("Tactical", 0x7F4348),
    ("RadarClass", 0x7F0344),
    ("PowerClass", 0x7EFF54),
]

def slot_func(vt, n):
    return b.u32(vt + n * 4)

def getsize_imm(fv):
    """读 B8 <imm32> C3 体首，返回 imm；否则 None。"""
    try:
        d = b.read(fv, 6)
    except Exception:
        return None
    if len(d) >= 6 and d[0] == 0xB8 and d[5] == 0xC3:
        return struct.unpack("<I", d[1:5])[0]
    return None

def whatami_imm(fv):
    try:
        d = b.read(fv, 6)
    except Exception:
        return None
    if len(d) >= 6 and d[0] == 0xB8 and d[5] == 0xC3:
        return struct.unpack("<I", d[1:5])[0]
    return None

print("%-42s %-8s %-4s %-10s %-10s %-10s" % (
    "class", "vtable", "slot", "v[11]fn", "v[12]fn", "GetSize imm"))
for name, vt in S09:
    f11 = slot_func(vt, 11)
    f12 = slot_func(vt, 12)
    imm11 = whatami_imm(f11)
    imm12 = getsize_imm(f12)
    print("%-42s %08X 11/12 %08X %08X  size=%s what=%s" % (
        name, vt, f11, f12,
        hex(imm12) if imm12 is not None else "(non-B8C3)",
        hex(imm11) if imm11 is not None else "-"))
