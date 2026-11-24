# -*- coding: utf-8 -*-
"""Inspect carrier creation receipts, files count, tz, and machine state for relevant trips."""
import glob
import json
import os

TRIP_BASE = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

trips = [
    "l1c_20261021", "l1d_20261021", "l1e_20261021", "l3_20261021",
    "l3_20261031ha", "l3_20261031hb",
    "l3_1101v3a", "l3_1101v3b", "l3_1101v3c",
    "l3_1101v4b", "l3_1101v4c", "l3_1101v4d", "l3_1101v4e"
]

print(f"{'Trip':<16} | {'Map Sha':<12} | {'Carrier Files'} | {'Uptime / Boot / System notes'}")
print("-" * 80)

for t in trips:
    td = os.path.join(TRIP_BASE, t)
    
    # Map sha
    msha = "unknown"
    w0_path = os.path.join(td, "measure_w0.json")
    if os.path.exists(w0_path):
        with open(w0_path, "r", encoding="utf-8") as f:
            msha = json.load(f).get("map_sha256", "unknown")[:12]
            
    # Carrier count
    # 1. carrier_creation_receipt.json
    cr_path = os.path.join(td, "carrier_creation_receipt.json")
    c_count = "None"
    if os.path.exists(cr_path):
        try:
            with open(cr_path, "r", encoding="utf-8") as f:
                crd = json.load(f)
            files = crd.get("files") or crd.get("copied_files") or crd.get("manifest")
            if files:
                c_count = str(len(files))
            else:
                c_count = str(crd.get("count", "exists"))
        except Exception:
            c_count = "err"
            
    # 2. carrier_manifest_pre_delete.json
    cm_path = os.path.join(td, "carrier_manifest_pre_delete.json")
    cm_count = "None"
    if os.path.exists(cm_path):
        try:
            with open(cm_path, "r", encoding="utf-8") as f:
                cmd = json.load(f)
            if isinstance(cmd, list):
                cm_count = str(len(cmd))
            elif isinstance(cmd, dict):
                cm_count = str(len(cmd.get("files", [])))
        except Exception:
            cm_count = "err"

    # 3. Check qc151_fields.json for carrier or tz or uptime
    qf_path = os.path.join(td, "qc151_fields.json")
    sys_notes = []
    if os.path.exists(qf_path):
        try:
            with open(qf_path, "r", encoding="utf-8") as f:
                qfd = json.load(f)
            for item in qfd:
                k = item.get("key", "")
                v = item.get("value")
                if "carrier" in k and "count" in k:
                    sys_notes.append(f"{k}={v}")
                if "uptime" in k.lower() or "boot" in k.lower():
                    sys_notes.append(f"{k}={v}")
                if "tz" in k.lower() or "timezone" in k.lower():
                    sys_notes.append(f"{k}={v}")
        except Exception:
            pass

    # Check for any gate2 or boot info file
    boot_files = glob.glob(os.path.join(td, "*boot*")) + glob.glob(os.path.join(td, "*uptime*"))
    for bf in boot_files:
        sys_notes.append(os.path.basename(bf))

    print(f"{t:<16} | {msha:<12} | receipt:{c_count}, pre_del:{cm_count} | {', '.join(sys_notes[:4])}")
