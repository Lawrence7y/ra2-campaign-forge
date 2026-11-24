#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W44 repair: the first K1 finally's heal() restored the PREP-time
ra2forge_install.json (the v0.3 legacy record) over the v12 install record.

This restores the v12 install record from the verbatim text captured in
install.ndjson, verifies its sha256 matches the recorded one, and re-runs
verify --json. w44_common.heal() has been fixed to never touch the install
record again.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w44_lib as L
import w44_common as C


def main() -> int:
    sink = L.Sink("repair")
    ok = False
    try:
        rec = None
        for line in (C.OUT / "install.ndjson").read_text(encoding="utf-8").splitlines():
            d = json.loads(line)
            if d.get("step") == "install_record":
                rec = d
        if rec is None:
            raise RuntimeError("no install_record in install.ndjson")
        text = rec["text"]
        parsed = json.loads(text)          # must be complete, valid JSON
        sink.step("record_text", chars=len(text), recorded_size=rec["size"],
                  recorded_sha256=rec["sha256"],
                  package_id=parsed.get("package_id"),
                  version=parsed.get("version"))
        dst = C.GAME / "ra2forge_install.json"
        dst.write_text(text, encoding="utf-8")
        got = L.sha256_file(dst)
        sink.step("record_restored", sha256=got, expected=rec["sha256"],
                  byte_identical=(got == rec["sha256"]),
                  size=dst.stat().st_size)
        if got != rec["sha256"]:
            raise RuntimeError("restored manifest sha256 mismatch")
        v = C.v12_cmd(sink, "verify_after_repair",
                      ["verify", "--game", str(C.GAME), "--json"])
        sink.step("verify_after_repair_exit", exit_code=v["exit_code"],
                  stdout_tail=v["stdout_tail"][-3000:])
        seal = C.GAME / "ra2forge_install.json.seal"
        sink.step("seal_state", present=seal.is_file(),
                  size=seal.stat().st_size if seal.is_file() else None,
                  sha256=L.sha256_file(seal) if seal.is_file() else None)
        ok = (v["exit_code"] == 0)
        sink.step("repair_result", ok=ok)
    except Exception as e:
        sink.step("FATAL", error=repr(e))
    finally:
        sink.step("meta_end", kind="meta_end", phase="repair", ok=ok)
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
