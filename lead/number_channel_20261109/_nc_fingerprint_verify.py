# -*- coding: utf-8 -*-
"""独立复核编排方实跑指纹（只读输入；本脚本不修改任何既有件）。
用法: python -I -X utf8 <本文件绝对路径>
指纹算法: hashlib.sha256(file bytes)；字节数 = len(raw bytes)。
"""
import hashlib
import json
import os

ROOT = r"D:\Project\ra2-campaign-forge"

EXPECTED = {
    "lead/orch_claims_20261109/ORCH_CLAIMS_AUDIT.md": ("9ebc406831a3fa402cf7006240b2b6c1314fed344dd1aa0c2a06f89b072140e4", 53432),
    "lead/orch_claims_20261109/_oc_stats_out.json": ("1f7aba12c7ab21e6c27eac491e790d2ed4bf7423cae2a9df9e35e545228b7834", 1127),
    "lead/orch_claims_20261109/_oc_recompute_out.json": ("541af3380dec0657c79f6d39999feaaa5d6e90d6fab34d8ce014844961370439", 1336),
    "lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md": ("f737d8a52b51ded87e2f20cd1368f73b4cf3fb7331c34384b0d4b802caf9c503", 45362),
    "lead/keff_calc_20261109/KEFF_CALC.md": ("4ad16cdb7dbb4b9e97ea306b55af6d51e2c262a52b10c75e56e1f5ffa1126e16", 34964),
    "lead/pvalue_recalc_20261109/_pv_PVALUE_RECALC.md": ("277df9910d4611e0072faf83bd65e3639667a01b511191d5f74b575e448911ac", 29780),
    "lead/score_decomp_20261109/SCORE_DECOMP.md": ("dfe7f68692eb7ae752358782acaaa1fc5a42ecbd0a6930205e0dcfe4f6544dcb", 42573),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

def main():
    rows = []
    for rel, (want_sha, want_bytes) in EXPECTED.items():
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        try:
            with open(p, "rb") as f:
                raw = f.read()
        except OSError as e:
            rows.append({"file": rel, "exists": False, "error": repr(e), "match": False})
            continue
        got_sha = hashlib.sha256(raw).hexdigest()
        got_bytes = len(raw)
        rows.append({
            "file": rel,
            "exists": True,
            "sha256": got_sha,
            "bytes": got_bytes,
            "want_sha256": want_sha,
            "want_bytes": want_bytes,
            "match": (got_sha == want_sha and got_bytes == want_bytes),
        })
    n_match = sum(1 for r in rows if r["match"])
    print(json.dumps({"n_files": len(rows), "n_match": n_match, "rows": rows},
                     ensure_ascii=False, indent=2))
    print("BINDING_SUMMARY n_match=%d/%d" % (n_match, len(rows)))
    # 逐件绑定行（供复核回件引用）
    for r in rows:
        if r["exists"]:
            print("被核对象 SHA256 = %s，字节数 = %d  [%s]" % (r["sha256"], r["bytes"], r["file"]))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
