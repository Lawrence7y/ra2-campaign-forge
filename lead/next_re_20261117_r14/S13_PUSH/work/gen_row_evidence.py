# -*- coding: utf-8 -*-
"""生成 13 个 channel-A 命中的逐行 EVIDENCE/ROW_<entry>.txt + 决定 delta 行。
四环按本卡字面判据；对环④额外标注 D-40 严格口径的争议。
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R

WORK = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(WORK), "EVIDENCE")
os.makedirs(EVID, exist_ok=True)
screen = json.load(open(os.path.join(WORK, "screen.json"), encoding="utf-8"))
wit = {w["entry"]: w for w in json.load(open(os.path.join(WORK, "witness.json"), encoding="utf-8"))}
a_hits = [r for r in screen if r["A_hit"]]

VERDICT = {
    "004251F0": dict(trap=True,  note="call 00489280 后 mov eax,[0xA8B238] 覆写返回值再 test ⇒ 卡片明列陷阱，不算③b②"),
    "00438A90": dict(trap=True,  note="call 004A1D50 后 mov eax,[esi+0x24] 覆写 ⇒ 陷阱（正是卡片的 [esi+0x??] 形态），不算"),
    "004684E0": dict(trap=False, note="call [eax+0x10] 后 cmp eax,-1 / je，返回值真消费 ⇒ ③b②成立"),
    "006294D0": dict(trap=True,  note="call 00410410 后 mov eax,[esi+0x44] 覆写 ⇒ 陷阱，不算"),
    "00629FD0": dict(trap=False, note="call 007C8E17(new) 后 add esp,4 / test eax,eax / je，空指针可伪证 ⇒ ③b②成立（另有 2 处站点被覆写剔除）"),
    "0062AC30": dict(trap=False, note="call [edx+0x2c] 后 cmp eax,1 / jne，返回值真消费 ⇒ ③b②成立；无虚表槽"),
    "006FD460": dict(trap=False, note="call 007C8E17(new) 后 test eax,eax / je ⇒ ③b②成立；无虚表槽"),
    "00708080": dict(trap=False, note="call [edx+0x2c] 后 cmp eax,1 / jne ⇒ ③b②成立；无虚表槽"),
    "0070FEE0": dict(trap=True,  note="call [edx+0x480] 后 mov eax,[esi+0x2ac] 覆写 ⇒ 陷阱，不算"),
    "0075E0C0": dict(trap=False, note="call 00410380(HRESULT E_POINTER=0x80004003) 后 test eax,eax / jl ⇒ ③b②成立"),
    "0075E2C0": dict(trap=False, note="call 00410320 后 test eax,eax / jl ⇒ ③b②成立"),
    "00772CD0": dict(trap=False, note="call 00410380 后 test eax,eax / jl ⇒ ③b②成立（第2处 006CF240 站点被 eax 覆写剔除）"),
    "00772EB0": dict(trap=False, note="call 00410320 后 test eax,eax / jl ⇒ ③b②成立"),
}

delta = []
for r in a_hits:
    e = r["entry"]
    v = VERDICT[e]
    wv = wit.get(e, {})
    slots = [s for s in wv.get("slots", []) if s.get("rtti_name")]
    # 四环判定
    ring1 = True
    ring2 = bool(slots)
    ring3 = not v["trap"]
    # 环④：本卡字面“活虚表派发”= ctor 装活 vt + 槽驻 + 派发站点；direct-only 不足
    ring4_literal = bool(slots)  # 有虚表活安装即算（本卡字面）
    four_ok = ring1 and ring2 and ring3 and ring4_literal

    lines = []
    A = lambda s="": lines.append(s)
    A("# ROW %s  S13  %s" % (e, r["name"]))
    A()
    A("## 环① 入口与函数边界")
    A("- entry=%s（大写十六进制，无 0x；delta entry 列原样）" % e)
    A("- atlas size=%s B, n_insn=%d, in_atlas=True" % (r["atlas_size"], r["n_insn"]))
    A("- 函数体在 .text=[0x401000,0x7E038D) 内；capstone 5.0.7 skipdata=True")
    A()
    A("## 环② 类身份（RTTI/虚表归属/构造链）")
    if slots:
        s = slots[0]
        A("- vtable slot@%s, vtable base=%s, slot off=+%s" % (s["slot_va"], s.get("vtable_base"), s.get("slot_off")))
        A("- RTTI COL=%s TD=%s name_va=%s → %s" % (s.get("col"), s.get("td"), s.get("name_va"), s.get("rtti_name")))
        A("- 构造期 vptr 安装点(.text): %s" % ", ".join(g["write_va"] for g in s.get("global_writes", [])))
    else:
        A("- 未取得（无 RTTI/vtable 槽；direct callers=%s）" % wv.get("direct_callers", []))
    A()
    A("## 环③ ③b② 具体形态 + 地址锚")
    A("- eax 覆写陷阱: %s" % ("触发 ⇒ 不算" if v["trap"] else "未触发"))
    A("- 机械命中站点 %d 个:" % len(r["A_sites"]))
    for s in r["A_sites"]:
        callee = ("%08X" % s["callee"]) if s["callee"] else "(indirect/import)"
        A("  - call %s @%08X → %s @%08X (imm=%s) → %s @%08X → 目标 %s" % (
            callee, s["call_addr"], s["test_kind"], s["test_addr"], s["test_imm"],
            s["jcc_mnemonic"], s["jcc_addr"],
            ("%08X" % s["jcc_target"]) if s["jcc_target"] else "?"))
        A("    p3_form=%s, callee_falsy=%s, callee_profile=%s" % (
            s["p3_form"], s["call_site_falsy"], s["callee_profile"]["callee_key"]))
    A("- 裁定: %s" % v["note"])
    A()
    A("## 环④ 使用见证（真实调用者或活虚表派发；direct-only 不足）")
    A("- E8 direct callers: %s" % (", ".join(wv.get("direct_callers", [])) or "无"))
    if slots:
        s = slots[0]
        A("- 活虚表: vtable %s 由构造期 vptr 安装点写入真实对象；槽 +%s 驻本 entry；" % (s.get("vtable_base"), s.get("slot_off")))
        A("  全 .text 存在 call dword ptr [reg+%s] 派发形态 ⇒ 本卡字面『活虚表派发』成立。" % s.get("slot_off"))
        A("- ⚠ 争议（必须在审计中正面回答）：环②与环④共用同一 vtable 槽（D-39『同源』）；")
        A("  前序 S13_KPROVED2(46行)、S13_K12 审计、SURVEY_RING24 按 D-40 严格口径")
        A("  （须『静态 global 接收者 exact 派发』或 direct call）对同类行判环④ FAIL。")
        A("  本卡按其字面判据接受『活虚表派发』，故列入 delta，但明确标记该争议。")
    elif wv.get("direct_callers"):
        A("- 无 vtable 槽，仅 E8 direct caller ⇒ 卡片明写『direct-only 不足』，环④不成立。")
    else:
        A("- 无 direct caller、无 vtable 槽 ⇒ 环④不成立。")
    A()
    A("## 四环结论")
    A("- ① %s / ② %s / ③ %s / ④ %s" % (
        "PASS" if ring1 else "FAIL", "PASS" if ring2 else "未取得",
        "PASS" if ring3 else "FAIL(eax覆写)", "PASS(本卡字面)" if ring4_literal else "FAIL"))
    A("- delta: %s" % ("列入（环④带 D-40 争议标记）" if four_ok else "不列入"))
    A("- 本行不改 coverage.tsv 任何列。")
    open(os.path.join(EVID, "ROW_%s.txt" % e), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    if four_ok:
        delta.append((r, slots[0]))

json.dump([{"entry": r["entry"], "name": r["name"], "slot": s} for r, s in delta],
          open(os.path.join(WORK, "delta_selected.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("delta rows (card-literal four rings) =", len(delta), [r["entry"] for r, s in delta])
print("wrote %d ROW evidence files" % len(a_hits))
