# -*- coding: utf-8 -*-
"""T1 复核员独立探针：只读。验证 T1 报告的数据面断言（不设深度上限、不剪枝）。
运行：python -I -X utf8 _t1review_probe.py
"""
import hashlib
import json
import os

ROOT = r"D:\Project\ra2-campaign-forge"
TREES = [
    os.path.join(ROOT, "out", "re_work", "work_chain", "CONTINUE_20261003",
                 "lead", "qc161_u0400_trip"),
    os.path.join(ROOT, "lead", "qc161_u0400_trip"),
]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


diff_tally = {}
post_n = 0
state_n = 0
tripdirs = {}
for tree in TREES:
    tag = "chain" if "re_work" in tree else "root"
    for dp, dns, fns in os.walk(tree):
        for fn in fns:
            fp = os.path.join(dp, fn)
            b = tripdirs.setdefault(dp, {"tag": tag, "receipt": None,
                                         "posts": []})
            b["tag"] = tag
            if fn == "carrier_creation_receipt.json":
                b["receipt"] = fp
            elif fn == "except_set_diff.json":
                try:
                    with open(fp, "rb") as f:
                        d = json.loads(f.read().decode("utf-8",
                                                       errors="replace"))
                    k = (d.get("pre_line_count"),
                         d.get("new_exception_count"))
                except Exception as e:
                    k = ("PARSE_ERR", repr(e)[:40])
                diff_tally[k] = diff_tally.get(k, 0) + 1
            elif fn.startswith("except_post_") and fn.endswith(".txt"):
                post_n += 1
                b["posts"].append(fp)
            elif fn == "carrier_post_state.json":
                state_n += 1

print("[D-unbounded] diff=%d post=%d state=%d"
      % (sum(diff_tally.values()), post_n, state_n))
chain_diff = root_diff = 0
for dp, b in tripdirs.items():
    if b["tag"] == "chain":
        chain_diff += sum(1 for f in os.listdir(dp)
                          if f == "except_set_diff.json")
    else:
        root_diff += sum(1 for f in os.listdir(dp)
                         if f == "except_set_diff.json")
print("    per-tree diff: chain=%d root=%d" % (chain_diff, root_diff))
for k in sorted(diff_tally.keys(), key=lambda x: (str(x[0]), str(x[1]))):
    print("    %s -> %d" % (k, diff_tally[k]))

match = diff = noex = 0
differ = []
trips_with_both = 0
for parent, b in sorted(tripdirs.items()):
    if b["receipt"] is None or not b["posts"]:
        continue
    trips_with_both += 1
    try:
        with open(b["receipt"], "rb") as f:
            rec = json.loads(f.read().decode("utf-8", errors="replace"))
    except Exception as e:
        noex += 1
        print("    receipt parse fail: %s %r" % (parent, e))
        continue
    ex = (rec.get("files") or {}).get("except.txt")
    if not ex:
        noex += 1
        continue
    inh = str(ex.get("sha256_dst") or "")
    for pp in b["posts"]:
        ph = sha(pp)
        if ph == inh:
            match += 1
        else:
            diff += 1
            differ.append((os.path.relpath(pp, ROOT), inh[:16], ph[:16]))
print("[E-unbounded] trips(receipt+post)=%d  posts match=%d differ=%d  "
      "receipt-without-except-copy=%d" % (trips_with_both, match, diff, noex))
for x in differ[:10]:
    print("    differ:", x)

td = os.path.join(TREES[0], "l3_20261031hb")
with open(os.path.join(td, "carrier_creation_receipt.json"), "rb") as f:
    rec = json.loads(f.read().decode("utf-8", errors="replace"))
ex = rec["files"]["except.txt"]
print("[SPOT l3_20261031hb] receipt: src=%s" % ex["src"])
print("    sha256_src=%s sha256_dst=%s size=%s"
      % (ex["sha256_src"], ex["sha256_dst"], ex["size"]))
posts = sorted(fn for fn in os.listdir(td)
               if fn.startswith("except_post_") and fn.endswith(".txt"))
for fn in posts:
    print("    post: %s sha=%s" % (fn, sha(os.path.join(td, fn))))
evd = os.path.join(td, "evidence")
for dp, dns, fns in os.walk(evd):
    for fn in fns:
        if fn == "except.txt":
            p = os.path.join(dp, fn)
            print("    evidence: %s sha=%s" % (os.path.relpath(p, td), sha(p)))
print("    ct exists=%s  carrier_delete_result.json exists=%s"
      % (os.path.exists(os.path.join(td, "ct")),
         os.path.exists(os.path.join(td, "carrier_delete_result.json"))))
