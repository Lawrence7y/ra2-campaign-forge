# -*- coding: utf-8 -*-
"""B2 15 行的 ① ② ④ 全量底账 + 4 张主虚表的构造期安装点。"""
import csv, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *

HERE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(HERE, "rows_b2.json"), encoding="utf-8"))

# 4 张主虚表（slot0=00410260），由 prep 实测
MAIN = {
    "BuildingClass": dict(vt=0x007E3EBC, col=0x007FC360, td=0x00818D60, n=322,
                          name=".?AVBuildingClass@@"),
    "BuildingTypeClass": dict(vt=0x007E4570, col=0x007FC618, td=0x008193A8, n=49,
                              name=".?AVBuildingTypeClass@@"),
    "CaptureManagerClass": dict(vt=0x007E4B40, col=0x007FCB60, td=0x0081B6C8, n=24,
                                name=".?AVCaptureManagerClass@@"),
    "FactoryClass": dict(vt=0x007E88D0, col=0x00800610, td=0x00822290, n=24,
                         name=".?AVFactoryClass@@"),
}
SMALL = {  # 陷阱③：小成员/次基类子表，绝不能当主表
    0x007E3E90: "BuildingClass sub vt (slot0=00410590)",
    0x007E3E98: "BuildingClass sub vt (slot0=00410580)",
    0x007E3EA0: "BuildingClass sub vt (slot0=004105E0)",
    0x007E4544: "BuildingTypeClass sub vt (slot0=00410590)",
    0x007E454C: "BuildingTypeClass sub vt (slot0=00410580)",
    0x007E4554: "BuildingTypeClass sub vt (slot0=004105E0)",
    0x007E4B14: "CaptureManagerClass sub vt",
    0x007E4B1C: "CaptureManagerClass sub vt",
    0x007E4B24: "CaptureManagerClass sub vt",
    0x007E88A4: "FactoryClass sub vt",
    0x007E88AC: "FactoryClass sub vt",
    0x007E88B4: "FactoryClass sub vt",
}

print("=== 主虚表安装点（.text 中 mov [mem], <vt>） ===")
for cls, M in MAIN.items():
    sites = find_vtable_imm_sites(M["vt"])
    print("\n-- %s  vt=%08X" % (cls, M["vt"]))
    for s in sites["c7_05"]:
        print("   C7 05  global %08X  at %08X" % (s["global_"], s["write_va"]))
    print("   C7 rm sites: %d  reg_load sites: %d"
          % (len(sites["c7_rm"]), len(sites["reg_load"])))
    for s in sites["c7_rm"]:
        ins = disasm(s["write_va"], 10)
        if ins:
            print("     %08X  %s %s" % (ins[0].address, ins[0].mnemonic, ins[0].op_str))
    for s in sites["reg_load"]:
        ins = disasm(s["load_va"], 10)
        if ins:
            print("     %08X  %s %s" % (ins[0].address, ins[0].mnemonic, ins[0].op_str))

# ---- 逐行 ① ② ④ ----
print("\n\n=== 逐行 ① ② ④ ===")
out = []
for r in rows:
    e = norm(r["entry"])
    ev = int(e, 16)
    cls_hint, _, slot_hint = r["name"].partition("::")
    slot_hint = slot_hint.replace("vslot", "").replace("slot", "")
    slot_hint = int(slot_hint)
    rec = dict(entry=e, name=r["name"], cls_hint=cls_hint, slot_hint=slot_hint)

    # ---- ① 入口 ----
    info = ATLAS.get(e)
    r1 = dict(in_text=in_text(ev), atlas_size=(info or {}).get("size"),
              atlas_ninsn=(info or {}).get("n_instr"))
    if info:
        body = disasm(ev, info["size"])
        r1["n_decoded"] = len(body)
        r1["skipdata_len"] = sum(i.size for i in body if i.id == 0)
        end = ev + info["size"]
        nxt = disasm(end - 8, 16)
        r1["tail_ok"] = True
        if body:
            r1["last_insn"] = "%s %s @%08X" % (body[-1].mnemonic, body[-1].op_str, body[-1].address)
    rec["ring1"] = r1

    # ---- ② 独立取证：在 4 张主表里找槽值 == entry ----
    slots = []
    for cls, M in MAIN.items():
        for k in range(M["n"]):
            if u32(M["vt"] + 4 * k) == ev:
                slots.append(dict(cls=cls, vt=M["vt"], slot=k, slot_va=M["vt"] + 4 * k,
                                  col=M["col"], td=M["td"], rtti=M["name"]))
    # 同时检查是否误落小表
    small_hits = []
    for sva, nm in SMALL.items():
        for k in range(8):
            if u32(sva + 4 * k) == ev:
                small_hits.append(dict(vt=sva, slot=k, note=nm))
    r2 = dict(slots=slots, small_hits=small_hits)
    if slots:
        s = [x for x in slots if x["cls"] == cls_hint]
        s = s[0] if s else slots[0]
        # 回扫校验：槽 VA -4 必须是 COL，COL sig==0，COL+0xC=TD，TD+8=名串
        col_back = u32(s["vt"] - 4)
        col = parse_col(col_back)
        tdi = parse_td(col["td"]) if col else None
        r2.update(slot_va=hx(s["slot_va"]), slot_bytes=va_read(s["slot_va"], 4).hex(" "),
                  slot_index=s["slot"], slot_matches_hint=(s["slot"] == slot_hint),
                  vt=hx(s["vt"]), col_back=hx(col_back), col_sig=(col or {}).get("sig"),
                  td=hx(col["td"]), rtti=(tdi or {}).get("name"),
                  vt_slot0=hx(u32(s["vt"])), main_vt=(u32(s["vt"]) == 0x410260))
    rec["ring2"] = r2
    out.append(rec)

    print("\n## %s  %s" % (e, r["name"]))
    print("   ① %s" % r1)
    print("   ② slots=%s small=%s" % (
        [(x["cls"], x["slot"]) for x in slots], [(x["vt"], x["slot"]) for x in small_hits]))
    if "slot_index" in r2:
        print("      槽 %s 4B=%s slot#%d hint=%d %s vt=%s COL_ok=%s TD=%s %s slot0=%s main=%s"
              % (r2["slot_va"], r2["slot_bytes"], r2["slot_index"], slot_hint,
                 "OK" if r2["slot_matches_hint"] else "MISMATCH", r2["vt"], r2["col_sig"],
                 r2["td"], r2["rtti"], r2["vt_slot0"], r2["main_vt"]))

json.dump(out, open(os.path.join(HERE, "rings12.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n-> rings12.json")
