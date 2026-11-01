# -*- coding: utf-8 -*-
"""OOF spot driver for R-061: drive the gate's PUBLIC library API
run_case(mut_dict) with a mutation taken from the manifest, print the red set.

Independent of the frozen suite: no CASES literal is consulted here; the
mutation comes straight from out/_r061_freeze5.json.
"""
import importlib
import json
import os
import sys

TOOLS = r"D:\Project\ra2-campaign-forge\re_atlas\tools"


def run(mut):
    sys.path.insert(0, TOOLS)
    G = importlib.import_module("r061_witness_this_contract")
    G.load()
    R, n = G.run_case(mut)
    return {"pass": n, "total": len(R), "red": sorted(l for l, c, _ in R if not c)}


if __name__ == "__main__":
    m = json.loads(sys.argv[1])
    print(json.dumps(run({int(k, 16) if isinstance(k, str) else int(k): int(v)
                          for k, v in m.items()})))
