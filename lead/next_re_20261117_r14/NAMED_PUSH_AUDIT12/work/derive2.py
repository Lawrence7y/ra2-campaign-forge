"""补齐 ④ 双向取证：产品构造器写主表 + 工厂构造器写工厂表（唯一写点）"""
import json, struct, re
import rt
from rt import im, vt_name, vt_slots
from check11 import ENTRIES, CLAIM_VT
from derive import derive

PROD_VT = {"006C5210":0x007E88D0,"006C5390":0x007F6B30,"006C5510":0x007F73B8,
           "006C5690":0x007EF954,"006C5810":0x007F0188,"006C5990":0x007EFB9C,
           "006C5B10":0x007F00A8,"006C5C90":0x007E2A50,"006C5E10":0x007E3DF0,
           "006C5F90":0x007E8B38,"006C6110":0x007E32A4}

def imm_writers(vt):
    """全镜像找 imm32 == vt 的字节位置（写指令的立即数）"""
    pat = struct.pack("<I", vt)
    buf = bytes(im.buf)
    out, st = [], 0
    while True:
        k = buf.find(pat, st)
        if k < 0: break
        out.append(0x400000 + k)
        st = k + 1
    return out

def func_start_of(addr, back=64):
    """从 addr 往回找函数起点（前一条 ret/填充之后）"""
    for c in range(addr - 1, addr - back, -1):
        b = im.rd(c, 1)
        if b == b"\x90":
            continue
    # 退化：直接线性反汇编窗口并取第一条
    return None

def scan_ctor_store(ctor, vt, maxn=800):
    """在产品构造器中找写 vt 到 [obj] 的指令"""
    pat = struct.pack("<I", vt)
    hits = []
    for i in im.dis(ctor, maxn, stop_ret=False):
        if i.mnemonic == "mov" and i.bytes.endswith(pat):
            hits.append((i.address, i.bytes.hex(), i.op_str))
        if i.mnemonic.startswith("ret"):
            break
    return hits

def enrich(e):
    """derive() + 产品主表/双写点全量事实"""
    d = derive(e)
    pvt = PROD_VT[e]
    pc = d.get("ctor")
    stores = scan_ctor_store(pc, pvt) if pc else []
    d["prod_ctor"] = pc
    d["prod_vt"] = pvt
    d["prod_vt_name"] = vt_name(pvt)[0]
    d["prod_slot0"] = im.u32(pvt)
    d["prod_slot1"] = im.u32(pvt + 4)
    d["prod_slot8"] = im.u32(pvt + 0x20)
    d["prod_stores"] = stores
    fw = imm_writers(d["vt"])
    d["fac_vt_imm_sites"] = fw
    d["fac_write_ins_addr"] = fw[0] - 2 if fw else None
    d["fac_ctor_start"] = fw[0] - 0x0B if fw else None
    return d

if __name__ == "__main__":
    out = {}
    for e in ENTRIES:
        d = derive(e)
        pvt = PROD_VT[e]
        pc = d.get("ctor")
        stores = scan_ctor_store(pc, pvt) if pc else []
        d["prod_ctor"] = pc
        d["prod_vt"] = pvt
        d["prod_vt_name"] = vt_name(pvt)[0]
        d["prod_slot0"] = im.u32(pvt)
        d["prod_slot1"] = im.u32(pvt + 4)
        d["prod_slot8"] = im.u32(pvt + 0x20)
        d["prod_stores"] = stores
        # 工厂表写点（全镜像唯一）
        fw = imm_writers(d["vt"])
        d["fac_vt_imm_sites"] = fw
        d["fac_write_ins_addr"] = fw[0] - 2 if fw else None
        d["fac_ctor_start"] = fw[0] - 0x0B if fw else None   # c7 00 imm32 -> 立即数前 2 字节是 c7 00，函数体 4 条
        out[e] = d
        print("### %s" % e)
        print("  工厂表 vt %08X 立即数出现点: %s (全镜像 %d 处)" % (
            d["vt"], ["%08X" % x for x in fw], len(fw)))
        print("  工厂构造器 %s 写点 %s  %s" % (
            ("%08X" % d["fac_ctor_start"]) if d["fac_ctor_start"] else None,
            ("%08X" % d["fac_write_ins_addr"]) if d["fac_write_ins_addr"] else None,
            d.get("ctor_write_ins")))
        print("  产品构造器 %08X 写主表 %08X(%s) 的位置: %s" % (
            d["prod_ctor"], pvt, d["prod_vt_name"], ["%08X %s %s" % h for h in stores]))
        print("  产品主表 slot0=%08X slot1=%08X slot8=%08X" % (d["prod_slot0"], d["prod_slot1"], d["prod_slot8"]))
        print()
    json.dump(out, open("derive11b.json","w"), indent=1, default=str)
