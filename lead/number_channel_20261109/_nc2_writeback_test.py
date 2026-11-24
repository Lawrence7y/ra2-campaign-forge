# -*- coding: utf-8 -*-
"""_nc2_writeback_test.py —— 纠正回写 7 步 + 全链自洽 + 篡改探针。

复刻 #2→#12：数字源里 10/5 被纠正为 13/6，散文占位符一字不动。
零真机、零采样；临时源只落本任务写域，实跑完删除。
用法：python -I -X utf8 <绝对路径>/_nc2_writeback_test.py > <绝对路径>/_nc2_writeback_test_out.txt
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os

_ROOT = r"D:\Project\ra2-campaign-forge"
_D = os.path.join(_ROOT, "lead", "number_channel_20261109")
_spec = importlib.util.spec_from_file_location(
    "nc2ph_wb", os.path.join(_D, "_nc2_placeholder.py"))
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

TMP = os.path.join(_D, "_nc2_number_source_test.json")


def build_store():
    claims = m.build_demo(_ROOT)
    # 演示「错值」起点：把两个实跑值改成任务书里被证伪的 10 / 5，并重封摘要
    out = []
    for c in claims:
        if c["id"] == "domains_nonempty":
            c = dict(c); c["value"] = 10; c = m.seal_claim(c)
        if c["id"] == "bindings_zero":
            c = dict(c); c["value"] = 5; c = m.seal_claim(c)
        out.append(c)
    return {"version": 0, "prev_sha256": "", "history": [],
            "claims": out, "block_sha256": "", "binding_line": ""}


def main():
    lines = []
    store = build_store()
    st1 = m.save_source(TMP, store)
    v0 = st1["block_sha256"]
    hdr0 = m.taskbook_header(st1)
    lines.append("STEP1 initial: version=%d block=%s" % (st1["version"], v0[:16]))
    lines.append("       header0 = %r" % hdr0)

    tb_a = hdr0 + '\n"【背景】沿用 {{N.bindings_zero}} 与 {{N.domains_nonempty}}。"\n'
    lines.append("STEP2 taskbook A (before correction) chain: %r" %
                 m.check_chain(tb_a, st1))

    r1 = m.correct_value(TMP, "bindings_zero", 6,
                         evidence="GATE_REJUDGE_32.md:53 实测 6 域")
    r2 = m.correct_value(TMP, "domains_nonempty", 13,
                         evidence="GATE_REJUDGE_32.md:51 实测 13 域")
    st3 = m.load_source(TMP)
    lines.append("STEP3 corrected: changed=%s/%s version=%d block=%s prev=%s" %
                 (r1["changed"], r2["changed"], st3["version"],
                  st3["block_sha256"][:16], st3["prev_sha256"][:16]))
    lines.append("       chain: prev==v0 ? %s | v0==v2 ? %s" %
                 (st3["prev_sha256"] == v0, st3["block_sha256"] == v0))
    lines.append("       per-claim source_block==block ? %s" %
                 all(c.get("source_block_sha256") == st3["block_sha256"]
                     for c in st3["claims"]))
    lines.append("       history: %s" % json.dumps(st3["history"], ensure_ascii=False))

    lines.append("STEP4 stale taskbook B (old hash): %r" % m.check_chain(tb_a, st3))
    hdr3 = m.taskbook_header(st3)
    tb_b = hdr3 + '\n"【背景】沿用 {{N.bindings_zero}} 与 {{N.domains_nonempty}}。"\n'
    lines.append("STEP5 fresh taskbook B chain: %r" % m.check_chain(tb_b, st3))
    v = m.validate_claim_numbers(st3["claims"], strict=True, root=_ROOT)
    rendered = m.render("【背景】沿用 {{N.bindings_zero}} 与 {{N.domains_nonempty}}。",
                        v["by_id"])["text"]
    lines.append("       rendered prose: %r" % rendered)
    lines.append("       contains corrected 6 / 13: %s %s" %
                 ("6" in rendered, "13" in rendered))
    lines.append("STEP6 prose placeholders unchanged across correction: %s" %
                 (m.PLACEHOLDER.findall(tb_a) == m.PLACEHOLDER.findall(tb_b)))

    # ★ 篡改探针：抹 history / 断 prev / 改值不改摘要 / 断链尖
    tampered = []
    for name, mut in [
        ("WIPE_HISTORY", lambda s: s.update(history=[])),
        ("BREAK_PREV", lambda s: s.update(prev_sha256="0" * 64)),
        ("CHANGE_VALUE_NO_RESEAL",
         lambda s: s["claims"][0].update(value=999)),
        ("BREAK_CLAIM_BLOCK_HASH",
         lambda s: s["claims"][0].update(source_block_sha256="f" * 64)),
        ("NO_BINDING_LINE", None),
    ]:
        s = json.loads(json.dumps(st3, ensure_ascii=False))
        if mut:
            mut(s)
        text = hdr3 if name != "NO_BINDING_LINE" else "no binding line here"
        chk = m.check_chain(text, s)
        tampered.append({"tamper": name, "ok": chk["ok"],
                         "problem": chk["problem"]})
    lines.append("STEP7 tamper probes: %s" % json.dumps(tampered, ensure_ascii=False))
    lines.append("       all tamper rejected: %s" % all(not x["ok"] for x in tampered))

    os.remove(TMP)
    lines.append("STEP8 temp source removed: %s" % (not os.path.exists(TMP)))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
