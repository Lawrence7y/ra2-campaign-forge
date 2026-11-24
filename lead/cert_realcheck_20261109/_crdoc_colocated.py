# -*- coding: utf-8 -*-
r"""_crdoc_colocated.py -- corrected co-located double-rewrite experiment.

The first attempt inside _crdoc_run.py rewrote the seal + the hard-coded
commitment but FORGOT to update the caller's certificate for the tampered
item; verify_one then correctly reported QUOTE_NOT_PRE_REGISTERED / FAIL.
This script performs the FULL attack (seal + artifact + caller cert +
hard-coded constant all rewritten together), which is the reviewer's Part C.

Only NEW files under _crdoc_sandbox are written. No existing file is modified.
Run:
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/cert_realcheck_20261109/_crdoc_colocated.py
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "cert_realcheck_20261109"
SB = WDIR / "_crdoc_colocated_sandbox"
sys.path.insert(0, str(ROOT / "lead" / "gate_r9sem_20261109"))

spec = importlib.util.spec_from_file_location(
    "crv_crdoc_coloc", WDIR / "_cr_real_verify.py")
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)

seal_bytes = (WDIR / "_cr_seal.json").read_bytes()
seal = json.loads(seal_bytes.decode("utf-8"))
k1 = ("lead/matrix_ab_ruling_20261109/", "需谁批准")
rul = "lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md"

if SB.exists():
    shutil.rmtree(SB)
rels = sorted({r["anchor"].rsplit(":", 1)[0] for r in seal["items"]})
for rel in rels:
    dst = SB / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes((ROOT / rel).read_bytes())

# (1) attacker replaces the certified line with a wholly fabricated claim
p = SB / rul
lines = p.read_bytes().decode("utf-8").splitlines(keepends=True)
lines[107] = "ATTACKER-FABRICATED-SEMANTIC-CLAIM-123 批准人 一律 = 攻击者编造值\n"
p.write_bytes("".join(lines).encode("utf-8"))
blob = p.read_bytes()

# (2) attacker rewrites the seal record for that item (hash / bytes / span)
fake_seal = copy.deepcopy(seal)
fr = next(r for r in fake_seal["items"] if tuple(r["item"]) == k1)
fr["quote"] = "ATTACKER-FABRICATED-SEMANTIC-CLAIM-123 批准人 一律 = 攻击者编造值"
fr["roles"] = {"具体施事值": "攻击者编造值", "批准人角色头": "批准人",
               "赋值算子": "一律 ="}
fr["file_sha256"] = hashlib.sha256(blob).hexdigest()
fr["bytes"] = len(blob)
fr["evidence_span_sha256"] = hashlib.sha256(
    (fr["quote"] + "\n").encode("utf-8")).hexdigest()
fake_path = SB / "_crdoc_fake_seal.json"
fake_path.write_text(json.dumps(fake_seal, ensure_ascii=False, indent=1,
                                sort_keys=True), encoding="utf-8", newline="\n")
fb = fake_path.read_bytes()

# (3) attacker rewrites the hard-coded commitment (same write domain)
old_sha, old_bytes = V.PRE_REGISTERED_SEAL_SHA256, V.EXPECTED_SEAL_BYTES
V.PRE_REGISTERED_SEAL_SHA256 = hashlib.sha256(fb).hexdigest()
V.EXPECTED_SEAL_BYTES = len(fb)

# (4) attacker also supplies a matching caller certificate for item 1
certs = V.certs_from_seal()
certs[k1] = {"anchor": fr["anchor"], "quote": fr["quote"],
             "roles": copy.deepcopy(fr["roles"])}

r = V.verify_all(certs, root=SB, seal_path=fake_path)
V.PRE_REGISTERED_SEAL_SHA256, V.EXPECTED_SEAL_BYTES = old_sha, old_bytes

out = {
    "VERDICT": r["VERDICT"], "seal_ok": r["seal_ok"],
    "n_pass": r["n_pass"], "n_stale": r["n_stale"], "n_fail": r["n_fail"],
    "per_item": [{"item": x["item"], "outcome": x["outcome"],
                  "problems": x["problems"]} for x in r["rows"]],
    "fake_seal_sha256": hashlib.sha256(fb).hexdigest(),
    "note": "FULL co-located double rewrite: seal + artifact + caller cert + "
            "hard-coded constant, all inside the same write domain",
}
(WDIR / "_crdoc_colocated_out.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8",
    newline="\n")
print(json.dumps(out, ensure_ascii=False, indent=1))
