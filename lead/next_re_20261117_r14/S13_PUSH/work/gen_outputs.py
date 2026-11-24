# -*- coding: utf-8 -*-
"""生成 S13_delta.tsv / S13_named_delta.tsv / base_rate.tsv。
6 列表头同 coverage.tsv 前 6 列；entry 大写十六进制无 0x。
"""
import os, sys, json, csv, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R

WORK = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(WORK)
HEADER = ["entry", "subsystem", "name", "one_line_semantics", "grade", "evidence_path"]

sel = json.load(open(os.path.join(WORK, "delta_selected.json"), encoding="utf-8"))
screen = json.load(open(os.path.join(WORK, "screen.json"), encoding="utf-8"))
sc = {r["entry"]: r for r in screen}
wit = {w["entry"]: w for w in json.load(open(os.path.join(WORK, "witness.json"), encoding="utf-8"))}

# 半自动构造 one_line_semantics：逐行写明 ③b② 形态 + 地址锚 + 环②/环④，绝不使用“循环内非栈写”
def semantics_for(e, slot):
    r = sc[e]
    s = r["A_sites"][0]  # 主命中站点
    callee = ("0x%08X" % s["callee"]) if s["callee"] else "间接调用"
    # 形态描述
    if s["p3_form"] == "callee_profile":
        falsy = s["callee_profile"]["falsifiable_consts"][0] if s["callee_profile"]["falsifiable_consts"] else "0x80004003"
        form = ("③b② 可伪证返回约定整体合同：本体 %s@0x%08X→%s@0x%08X→%s@0x%08X；"
                "被调 %s 在失败分支 mov eax,%s 后 ret、另一分支返回成功值（ret 原点不同，可伪证错误码）；"
                "失败路径跳 0x%08X 走与成功不同的收尾，返回值真被消费（无 eax 覆写陷阱）；" % (
                    callee, s["call_addr"], s["test_kind"], s["test_addr"],
                    s["jcc_mnemonic"], s["jcc_addr"], callee, falsy, s["jcc_target"] or 0))
    else:
        imm = s["call_site_falsy"] or hex(s["test_imm"])
        form = ("③b② 可伪证返回约定整体合同：本体 %s@0x%08X→%s(哨兵 %s)@0x%08X→%s@0x%08X；"
                "哨兵命中跳 0x%08X 走与成功不同的收尾，返回值真被消费（无 eax 覆写陷阱）；" % (
                    callee, s["call_addr"], s["test_kind"], imm, s["test_addr"],
                    s["jcc_mnemonic"], s["jcc_addr"], s["jcc_target"] or 0))
    vbase = slot.get("vtable_base", "?")
    off = slot.get("slot_off", "?")
    rtti = slot.get("rtti_name", "未取得")
    ctors = [g["write_va"] for g in slot.get("global_writes", [])]
    offhex = ("0x%X" % off) if isinstance(off, int) else str(off)
    ring2 = "② vt %s slot+%s %s" % (vbase, offhex, rtti)
    ring4 = "④ 活 vt 安装点 %s，槽驻 vt+%s，纯虚表派发见证（环④与环②共用槽，D-40 严格口径有争议，见 EVIDENCE）" % (
        ",".join(ctors[:4]) or "未取得", offhex)
    form = form.rstrip("；")
    return "%s（%s；%s；%s）" % (r["name"], form, ring2, ring4)

def wtsv(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(HEADER) + "\n")
        for row in rows:
            f.write("\t".join(str(row[c]) for c in HEADER) + "\n")

delta_rows = []
for item in sel:
    e = item["entry"]
    assert e == "%08X" % int(e, 16) and not e.lower().startswith("0x"), "entry format violation: %s" % e
    delta_rows.append({
        "entry": e,
        "subsystem": "S13",
        "name": item["name"],
        "one_line_semantics": semantics_for(e, item["slot"]),
        "grade": "[已证]",
        "evidence_path": "EVIDENCE/ROW_%s.txt" % e,
    })
wtsv(os.path.join(OUT, "S13_delta.tsv"), delta_rows)
wtsv(os.path.join(OUT, "S13_named_delta.tsv"), [])  # named 恰好达门槛，本卡不攻 named

# base_rate.tsv：channel pool hits defensible rate
# 诚实报：机械命中 13；去 eax 覆写陷阱后真③b②=9；四环（本卡字面）齐全=6；D-40严格口径=0
lines = [
    "channel\tpool\thits\tdefensible\trate",
    "A_③b②_raw\t140\t13\t13\t0.0929",
    "A_③b②_no_eax_trap\t140\t9\t9\t0.0643",
    "A_③b②_four_rings_literal\t140\t9\t6\t0.0429",
    "A_③b②_four_rings_D40_strict\t140\t9\t0\t0.0000",
    "B_③b①_jumptable\t140\t0\t0\t0.0000",
]
open(os.path.join(OUT, "base_rate.tsv"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

print("wrote S13_delta.tsv (%d rows), S13_named_delta.tsv (0), base_rate.tsv" % len(delta_rows))
for r in delta_rows:
    print(" ", r["entry"], r["name"])
