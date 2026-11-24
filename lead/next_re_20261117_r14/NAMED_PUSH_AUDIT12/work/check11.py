"""批量机器核验 11 行：③b② 站点/分支、② 槽与 RTTI、产品主虚表、①direct caller、④ 构造器写点"""
import re, json, struct
import rt
from rt import im, IB, vt_name, vt_slots, is_text

ENTRIES = ["006C5210","006C5390","006C5510","006C5690","006C5810","006C5990",
           "006C5B10","006C5C90","006C5E10","006C5F90","006C6110"]
# 执行器 delta 声称的 ② vt 基址（作为线索，逐个自查）
CLAIM_VT = {
 "006C5210":0x007F3D98,"006C5390":0x007F3DB0,"006C5510":0x007F3DC8,"006C5690":0x007F3DE0,
 "006C5810":0x007F3DF8,"006C5990":0x007F3E10,"006C5B10":0x007F3E28,"006C5C90":0x007F3E40,
 "006C5E10":0x007F3E58,"006C5F90":0x007F3E70,"006C6110":0x007F3E88}

def cstr_safe(s):
    if s is None: return None
    try: return s.encode("latin1").decode("latin1")
    except Exception: return repr(s)

def body(entry):
    va = int(entry, 16)
    insns = list(im.dis(va, 300, stop_ret=False))
    for k, i in enumerate(insns):
        if i.mnemonic.startswith("ret"):
            nxt = insns[k+1:k+3]
            if nxt and all(x.mnemonic == "nop" for x in nxt):
                return insns[:k+1]
    return insns

def analyze_body(e):
    insns = body(e)
    r = {"entry": e, "n_insns": len(insns),
         "len": insns[-1].address+insns[-1].size-int(e,16) if insns else 0,
         "guards": [], "calls": [], "ind_calls": [], "branch_after_test": [], "rets": []}
    for i in insns:
        if i.mnemonic == "mov" and re.search(r"eax, 0x8[0-9a-f]{7}$", i.op_str):
            r["guards"].append((i.address, i.bytes.hex(), i.op_str))
        if i.mnemonic == "push" and re.match(r"^0x[0-9a-f]+$", i.op_str):
            r["size_push"] = (i.address, i.op_str)
        if i.mnemonic == "call":
            m = re.match(r"^0x([0-9a-f]+)$", i.op_str)
            if m:
                r["calls"].append((i.address, int(m.group(1),16), i.bytes.hex()))
            else:
                r["ind_calls"].append((i.address, i.op_str, i.bytes.hex()))
        if i.mnemonic in ("test","cmp") :
            r.setdefault("tests", []).append((i.address, i.op_str, i.bytes.hex()))
        if i.mnemonic.startswith("j"):
            r.setdefault("jccs", []).append((i.address, i.bytes.hex(), i.mnemonic, i.op_str))
        if i.mnemonic.startswith("ret"):
            r["rets"].append((i.address, i.op_str))
    return r

def scan_text_for_target(target):
    """统计 .text 中 e8/e9 rel32 指向 target 的指令；以及任何 4 字节 == target 的数据引用"""
    hits = []
    base = 0x401000
    end = 0x7E038D
    off = base
    while off < end:
        b = im.rd(off, 5)
        if len(b) < 5: break
        if b[0] in (0xE8, 0xE9):
            rel = struct.unpack("<i", b[1:5])[0]
            tgt = off + 5 + rel
            if tgt == target:
                hits.append((off, b.hex()))
        off += 1
    return hits

def data_refs(target):
    """在镜像内找 4 字节等于 target 的位置（vt 槽 / 表项）"""
    pat = struct.pack("<I", target)
    out = []
    start = 0
    buf = bytes(im.buf)
    while True:
        k = buf.find(pat, start)
        if k < 0: break
        va = IB + k
        out.append((va, im.sec_of(va)))
        start = k+1
    return out

def find_writer_of_imm(imm, limit=0x7E038D):
    """.text 中写 imm 到 [reg] 或 [reg+N] 的指令（mov dword ptr [reg], imm）"""
    hits = []
    off = 0x401000
    while off < limit:
        b = im.rd(off, 10)
        if len(b) < 6: break
        if b[0] == 0xC7 and b[1] & 0xC0 == 0xC0:  # mov r/m32, imm32
            modrm = b[1]
            mod = modrm >> 6
            rm = modrm & 7
            if mod == 0 and rm != 5:
                val = struct.unpack("<I", b[2:6])[0]
                if val == imm:
                    hits.append((off, b[:6].hex(), f"mov [{reg_name(rm)}], {imm:08X}"))
                off += 6
                continue
            elif mod == 1:
                val = struct.unpack("<I", b[3:7])[0] if len(b) >= 7 else None
                if val == imm:
                    hits.append((off, b[:7].hex(), f"mov [{reg_name(rm)}+disp8], {imm:08X}"))
                off += 7
                continue
        off += 1
    return hits

REGS = ["eax","ecx","edx","ebx","esp","ebp","esi","edi"]
def reg_name(rm): return REGS[rm]

if __name__ == "__main__":
    res = []
    for e in ENTRIES:
        a = analyze_body(e)
        vt = CLAIM_VT[e]
        slots = vt_slots(vt, 6)
        nm, col = vt_name(vt)
        dc = scan_text_for_target(int(e,16))
        dr = data_refs(int(e,16))
        a.update(dict(vt=vt, vt_slots=slots, vt_name=nm, vt_col=col,
                      direct_callers=dc, n_direct=len(dc),
                      data_refs=[(f"{va:08X}", s) for va, s in dr]))
        res.append(a)
    json.dump(res, open("check11.json","w"), default=str, indent=1)
    for a in res:
        print("="*100)
        print(f"entry {a['entry']}  len={a['len']}B  insns={a['n_insns']}")
        print(f"  guards: " + " | ".join(f"{x[0]:08X} {x[1]} => {x[2]}" for x in a["guards"]))
        print(f"  size_push: {a.get('size_push')}")
        print(f"  direct calls: " + " | ".join(f"{x[0]:08X}->{x[1]:08X} [{x[2]}]" for x in a["calls"]))
        print(f"  indirect: " + " | ".join(f"{x[0]:08X} {x[1]} [{x[2]}]" for x in a["ind_calls"]))
        print(f"  tests: " + " | ".join(f"{x[0]:08X} {x[1]} [{x[2]}]" for x in a.get("tests",[])))
        print(f"  jccs: " + " | ".join(f"{x[0]:08X} {x[2]} {x[3]} [{x[1]}]" for x in a.get("jccs",[])))
        print(f"  rets: " + " | ".join(f"{x[0]:08X} ret{x[1]} " for x in a["rets"]))
        print(f"  ② vt {a['vt']:08X} slots0-5 = " + ", ".join(f"{s:08X}" if s else "None" for s in a["vt_slots"]))
        print(f"  ② RTTI name = {cstr_safe(a['vt_name'])}  COL={a['vt_col'] and hex(a['vt_col'])}")
        print(f"  direct callers of entry = {a['n_direct']}  {a['direct_callers']}")
        print(f"  data refs = {a['data_refs']}")
