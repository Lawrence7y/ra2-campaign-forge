# -*- coding: utf-8 -*-
"""_nc_writeback_test.py —— 实测「同一数字跨任务书重复出现」的纠正回写机制。

场景复刻 #2 -> #12：第一次派发写了 5 个 bindings=0 域（错），子任务纠正为 6，
下一批任务书如果没复贴新块哈希就 FAIL。全部只在本任务写域内造临时 JSON。
"""
import importlib.util
import io
import json
import os
import sys

D = r"D:\Project\ra2-campaign-forge\lead\number_channel_20261109"
spec = importlib.util.spec_from_file_location("ncph", D + r"\_nc_placeholder.py")
ncph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ncph)

SRC = D + r"\_nc_number_source_demo.json"
if os.path.exists(SRC):
    os.remove(SRC)


def make_claim(cid, value, unit, kind, label, **kw):
    return {
        "id": cid, "value": value, "unit": unit,
        "scope": {"label": label, "numerator": "gateProblems 非空的域",
                  "denominator": "全部 32 域", "condition": "本轮 DIR"},
        "source_kind": kind,
        "sha256": ncph.sha256_hex((cid + str(value)).encode("utf-8")),
        "domain": "gate_rejudge32_20261109", "artifact": "GATE_REJUDGE_32.md",
        "source_ref": "demo", **kw,
    }


store = {
    "version": 0, "prev_sha256": "", "history": [],
    "claims": [
        make_claim("bindings_zero", 5, "域", "实跑", "全量载体",
                   command="python -I -X utf8 <rejudge>", stdout_sha256="a" * 64),
        make_claim("domains_nonempty", 10, "域", "实跑", "全量载体",
                   command="python -I -X utf8 <rejudge>", stdout_sha256="b" * 64),
    ],
}
store = ncph.save_source(SRC, store)
v0 = store["block_sha256"]
hdr0 = ncph.taskbook_header(store)
print("STEP1 initial: version=%d block=%s" % (store["version"], v0[:16]))
print("       header0 = %r" % hdr0)

# 任务书 A（旧值）：引用占位符，复贴当前哈希 -> 通过
tb_a = hdr0 + '\n"【背景】bindings=0 的域有 {{N.bindings_zero}}，仍报问题的域 {{N.domains_nonempty}}。"\n'
print("STEP2 taskbook A (before correction) chain:", ncph.check_chain(tb_a, store))

# 子任务纠正：#12 实测 6 域 / 13 域；只能改数字源，散文一字不动
r1 = ncph.correct_value(SRC, "bindings_zero", 6,
                        evidence="GATE_REJUDGE_32.md:53 实测 6 域")
r2 = ncph.correct_value(SRC, "domains_nonempty", 13,
                        evidence="GATE_REJUDGE_32.md:51 实测 13 域")
store2 = ncph.load_source(SRC)
v1 = store2["block_sha256"]
hdr1 = ncph.taskbook_header(store2)
print("STEP3 corrected: changed=%s/%s version=%d block=%s prev=%s" %
      (r1["changed"], r2["changed"], store2["version"], v1[:16],
       store2["prev_sha256"][:16]))
print("       chain: v0==v1 ?", v0 == v1, "| prev==v0 ?", store2["prev_sha256"] == v0)

# 任务书 B 若仍复贴旧哈希（#2 纠正后下一批仍写 10/5 的复刻）-> 必须 FAIL
tb_b_stale = hdr0 + '\n"【背景】沿用 {{N.bindings_zero}}。"\n'
print("STEP4 stale taskbook B (old hash):", ncph.check_chain(tb_b_stale, store2))

# 任务书 B' 复贴新哈希、散文完全不改动占位符 -> 自动拿到纠正后的值
tb_b_fresh = hdr1 + '\n"【背景】沿用 {{N.bindings_zero}} 与 {{N.domains_nonempty}}。"\n'
fresh = ncph.render(tb_b_fresh, ncph.validate_claim_numbers(
    store2["claims"], strict=False)["by_id"])
print("STEP5 fresh taskbook B chain:", ncph.check_chain(tb_b_fresh, store2))
print("       rendered prose:", fresh["text"].split("\n")[-2])
print("       contains corrected 6 / 13:", "6 域" in fresh["text"], "13 域" in fresh["text"])
print("       history entries:", json.dumps(store2["history"], ensure_ascii=False))

# 回写不改散文：tb_a 与 tb_b_fresh 的占位符串完全一致
import re
pa = re.findall(r"\{\{N\.[^}]+\}\}", tb_a)
pb = re.findall(r"\{\{N\.[^}]+\}\}", tb_b_fresh)
print("STEP6 prose placeholders unchanged across correction:", pa == pb, pa)

os.remove(SRC)
print("STEP7 temp source removed:", not os.path.exists(SRC))
