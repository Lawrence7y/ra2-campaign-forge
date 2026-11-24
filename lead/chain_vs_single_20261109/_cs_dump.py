# -*- coding: utf-8 -*-
# _cs_dump.py : 完整勘察两份 JSON 的 sources / single_layer_vs_chain / by_family / 一行样本
import os, json, pprint
ROOT = r"D:\Project\ra2-campaign-forge"
os.chdir(ROOT)
CUR = "lead/gate_pipeline_20261109/_gp_regression_out.json"
UNI = "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json"

for tag, rel in [("CURRENT(74)", CUR), ("UNION(72)", UNI)]:
    with open(rel, "r", encoding="utf-8") as f:
        o = json.load(f)
    print("\n" + "="*100)
    print(tag, rel)
    print("="*100)
    print("\n--- sources ---")
    pprint.pprint(o["sources"], width=140)
    print("\n--- not_in_corpus ---")
    pprint.pprint(o["not_in_corpus"], width=140)
    print("\n--- single_layer_vs_chain ---")
    pprint.pprint(o["single_layer_vs_chain"], width=140)
    print("\n--- by_family (keys + counts) ---")
    for k, v in o["by_family"].items():
        print("  %-30s %r" % (k, v))
    print("\n--- rows[0] full ---")
    pprint.pprint(o["rows"][0], width=140)
    print("\n--- all row ids (id|family|expect) ---")
    for i, r in enumerate(o["rows"]):
        print("  %2d %-34s %-24s %s" % (i, r["id"], r["family"], r["expect"]))
