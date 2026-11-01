# -*- coding: utf-8 -*-
"""OOF spot driver: apply one mutation through the gate's PUBLIC env interface
(R062_MUTATE) and print the resulting red label set.

Independent of the frozen suite: the case's (address -> byte) map is taken from
the manifest, and the gate is driven directly.
"""
import json
import os
import sys

GATE_DIR = r"D:\Project\ra2-campaign-forge\re_atlas\tools"


def run(mut):
    sys.path.insert(0, GATE_DIR)
    os.environ.pop("R062_MUTATE", None)
    os.environ["R062_MUTATE"] = ",".join("%s=%s" % (k, v) for k, v in mut.items())
    import r062_upward_trace_contract as G
    G.load()
    R, n = G.check_body()
    return {"pass": n, "total": len(R), "red": sorted(l for l, c, _ in R if not c)}


if __name__ == "__main__":
    print(json.dumps(run(json.loads(sys.argv[1]))))
