# -*- coding: utf-8 -*-
"""基线指纹快照/复核工具（写域内自用）。
用法:
  python -I -X utf8 _integrity_check.py snapshot  -> 对既有只读目录建 sha256 基线, 写 _baseline_snapshot.json
  python -I -X utf8 _integrity_check.py verify    -> 重算并与基线比对, 报 MATCH/DRIFT/NEW
只读既有目录; 快照与报告全部落在本脚本所在写域内。
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))  # lead 的上一级 = 仓库根
LEAD = os.path.join(REPO, "lead")

# 需要盯防的既有只读目录(本任务涉及的证据件所在目录 + 上轮交付目录)
WATCHED = [
    "re_chain_synthesis_20261111",
    "playerctrl_semantics_20261111",
    "slot2_fullscan_20261111",
    "re_crashwriter_static_20261110",
    "re_orphan_owners_20261110",
    "re_map_preset_decode_20261110",
    "re_loadbench_diff_20261110",
    "stale_pass_20261109",
    "re_dispatch_20261111",
]

# 收尾回执点名复核的关键件
KEY_FILES = [
    r"lead\re_chain_synthesis_20261111\CHAIN_SYNTHESIS.md",
    r"lead\re_chain_synthesis_20261111\LEDGER_SECTION_DRAFT.md",
    r"lead\re_chain_synthesis_20261111\_repro_ps_disasm.txt",
    r"lead\playerctrl_semantics_20261111\_ps_disasm.py",
    r"ra2bench\gamemd.exe",
]


def sha256_of(path):
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            n += len(b)
            h.update(b)
    return h.hexdigest(), n


def collect():
    out = {}
    for d in WATCHED:
        full = os.path.join(LEAD, d)
        if not os.path.isdir(full):
            out[d] = {"_error": "dir missing"}
            continue
        for name in sorted(os.listdir(full)):
            p = os.path.join(full, name)
            if not os.path.isfile(p):
                continue
            digest, size = sha256_of(p)
            out["%s/%s" % (d, name)] = {"sha256": digest, "size": size}
    for rel in KEY_FILES:
        p = os.path.join(REPO, rel.replace("\\", os.sep))
        if os.path.isfile(p):
            digest, size = sha256_of(p)
            out["__KEY__" + rel] = {"sha256": digest, "size": size}
        else:
            out["__KEY__" + rel] = {"_error": "missing"}
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "verify"
    snap_path = os.path.join(HERE, "_baseline_snapshot.json")
    if mode == "snapshot":
        data = collect()
        with open(snap_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
        print("SNAPSHOT files=%d -> %s" % (len(data), snap_path))
        return
    # verify
    with open(snap_path, "r", encoding="utf-8") as f:
        base = json.load(f)
    now = collect()
    drift, new, missing = [], [], []
    for k, v in base.items():
        if k not in now:
            missing.append(k)
        elif now[k].get("sha256") != v.get("sha256"):
            drift.append(k)
    for k in now:
        if k not in base:
            new.append(k)
    print("VERIFY watched=%d drift=%d missing=%d new=%d" % (len(base), len(drift), len(missing), len(new)))
    for k in drift:
        print("DRIFT  %s" % k)
    for k in missing:
        print("MISSING %s" % k)
    for k in new:
        print("NEW    %s" % k)
    # 关键件点名输出
    print("--- key files ---")
    for k in sorted(now):
        if k.startswith("__KEY__"):
            v = now[k]
            print("%s  %s  %s" % (v.get("sha256", "?"), v.get("size", "?"), k[len("__KEY__"):]))
    sys.exit(0 if not drift and not missing else 1)


if __name__ == "__main__":
    main()
