"""② 产品主虚表 + ③b② 被调 QI 返回码 + ④ 工厂 ctor 写点"""
import re, json
import rt
from rt import im, IB, vt_name, vt_slots, is_text
from check11 import ENTRIES, CLAIM_VT, body, cstr_safe

def ctor_writes(ctor_va, limit=600):
    """线性反汇编 ctor，收集 mov dword [reg], imm 类写入"""
    insns = list(im.dis(ctor_va, limit, stop_ret=False))
    out = []
    for i in insns:
        m = re.match(r"^dword ptr \[(e[a-d]x|ecx|edx|esi|edi)\](\s*\+\s*0x[0-9a-f]+)?, (0x[0-9a-f]+)$", i.op_str)
        if i.mnemonic == "mov" and m:
            out.append((i.address, i.op_str, i.bytes.hex()))
        if i.mnemonic.startswith("ret"):
            break
    return out

def analyze(e):
    vt = CLAIM_VT[e]
    slots = vt_slots(vt, 6)
    insns = body(e)
    # 找 operator new 后紧跟的 ctor call
    calls = [(i.address, int(i.op_str,16), i.bytes.hex()) for i in insns
             if i.mnemonic == "call" and re.match(r"^0x[0-9a-f]+$", i.op_str)]
    new_call = [c for c in calls if c[1] == 0x7C8E17]
    ctor_call = [c for c in calls if c[1] != 0x7C8E17]
    r = {"entry": e, "vt": vt, "slot3": slots[3], "vt_name": cstr_safe(vt_name(vt)[0]),
         "new_call": new_call, "ctor_call": ctor_call}
    if ctor_call:
        ct = ctor_call[0][1]
        w = ctor_writes(ct)
        r["ctor_target"] = ct
        r["ctor_vt_writes"] = w
        cands = []
        for addr, txt, hx in w:
            m = re.search(r", (0x[0-9a-f]+)$", txt)
            val = int(m.group(1), 16)
            nm, col = vt_name(val)
            cands.append({"at": f"{addr:08X}", "ins": txt, "vt": f"{val:08X}",
                          "vt_name": cstr_safe(nm),
                          "slot0": f"{vt_slots(val,1)[0]:08X}" if vt_slots(val,1)[0] else None,
                          "nslots_probe": [f"{s:08X}" if s else None for s in vt_slots(val, 14)]})
        r["ctor_vt_cands"] = cands
    return r

if __name__ == "__main__":
    out = []
    for e in ENTRIES:
        a = analyze(e)
        out.append(a)
        print("="*100)
        print(f"entry {e}  ② vt={a['vt']:08X} slot3={a['slot3']:08X} name={a['vt_name']}")
        print(f"  new@{a['new_call']}  ctor@{a['ctor_call']}")
        for c in a.get("ctor_vt_cands", []):
            print(f"   ctor写 {c['at']}  {c['ins']:<40} vt={c['vt']} name={c['vt_name']} slot0={c['slot0']}")
    json.dump(out, open("prod11.json","w"), default=str, indent=1)
