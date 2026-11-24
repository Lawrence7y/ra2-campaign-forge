# -*- coding: utf-8 -*-
r"""_cr_real_verify.py -- a REAL truth-certificate verifier.

Difference from _fnr_check.py:certificate_ok (read-only, :95-124):
  * it actually OPENS the anchor file and READS ITS BYTES;
  * it RECOMPUTES hashlib.sha256 and compares with a PRE-REGISTERED seal;
  * it checks the line number exists, and the quote is VERBATIM on that line;
  * it checks role values are non-pointers AND verbatim in the evidence window;
  * the ORACLE truth/author come from the pre-registered, hash-sealed record,
    NOT from any caller-supplied boolean. Caller booleans are explicitly
    ignored and listed in `ignored_caller_booleans`.

The seal (_cr_seal.json) is bound by a hard-coded SHA256 constant below. It was
produced by _cr_build_seal.py in an earlier phase; the constant is the
commitment. At verify time the seal file is RE-READ and RE-HASHED.

OUTCOMES: PASS | STALE | FAIL.
  FAIL  = determinate contradiction (missing file, bad anchor/line/quote,
          pointer value, seal broken, oracle label absent/false/same-author,
          or caller's declared hash disagrees with the recomputed hash).
  STALE = the artifact bytes differ from the pre-registered seal, but the
          certified span itself still matches. The blind ORACLE was made
          against the OLD bytes, so its label cannot be transported. STALE is
          a NON-PASS: the gate must not count it as evidence.
  PASS  = all real checks succeeded.

Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/cert_realcheck_20261109/_cr_real_verify.py
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import time
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "cert_realcheck_20261109"
SEAL_PATH = WDIR / "_cr_seal.json"

# PRE-REGISTERED commitment, hard-coded. Printed by _cr_build_seal.py phase 1.
PRE_REGISTERED_SEAL_SHA256 = (
    "63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23"
)
EXPECTED_SEAL_BYTES = 4395

ANCHOR_RE = re.compile(r"^(.+):(\d+)$")
# copied verbatim from _fnr_check.py:62-67 (no modification of that file)
NON_VALUE_RE = re.compile(
    r"见台账|详见|参见|见附件|见上|见下表|以.{0,6}记载为准|不另下结论|不重录|"
    r"不予判定|暂不作判定|待判|待定|待补|待验|待查|待确认|尚需|尚未|需进一步|"
    r"是否|并非|不可重建|无法重建|未能重建|未验|未采集|无输出|"
    r"^(?:TBD|N/?A|待定|待指定|未定|未知|略|\.{2,}|…+)$"
)
CALLER_BOOLEAN_KEYS = ("oracle_truth", "oracle_author", "oracle_sealed",
                       "predicate_author", "whitelist_sealed")


class Stats:
    def __init__(self):
        self.n_read_bytes = 0
        self.n_bytes_hashed = 0
        self.n_sha256 = 0
        self.n_lines_decoded = 0
        self.elapsed_ms = 0.0

    def as_dict(self):
        return {"n_read_bytes_calls": self.n_read_bytes,
                "bytes_read": self.n_bytes_hashed,
                "n_sha256_calls": self.n_sha256,
                "n_lines_decoded": self.n_lines_decoded,
                "elapsed_ms": round(self.elapsed_ms, 3)}


def load_seal(seal_path: Path, stats: Stats):
    """Read and verify the pre-registered seal. Returns (seal, problems)."""
    problems = []
    if not seal_path.is_file():
        return None, ["SEAL_MISSING: no seal file on disk"]
    blob = seal_path.read_bytes()                       # REAL disk read
    stats.n_read_bytes += 1
    stats.n_bytes_hashed += len(blob)
    got = hashlib.sha256(blob).hexdigest()              # REAL recomputation
    stats.n_sha256 += 1
    if len(blob) != EXPECTED_SEAL_BYTES:
        problems.append("SEAL_BYTES_MISMATCH: %d != %d"
                        % (len(blob), EXPECTED_SEAL_BYTES))
    if got != PRE_REGISTERED_SEAL_SHA256:
        problems.append("SEAL_INTEGRITY: sha256 %s != pre-registered %s"
                        % (got, PRE_REGISTERED_SEAL_SHA256))
    try:
        seal = json.loads(blob.decode("utf-8"))
    except Exception as e:
        return None, problems + ["SEAL_DECODE_ERROR: %s" % e]
    return seal, problems


def verify_one(cert: dict, seal_rec: dict, root: Path, stats: Stats,
               seal_ok: bool):
    """Verify ONE certificate against the pre-registered seal AND the disk."""
    problems, checks, ignored = [], {}, []
    for k in CALLER_BOOLEAN_KEYS:
        if k in cert:
            ignored.append(k)

    # -- 1. ORACLE comes from the SEAL, never from caller booleans -----------
    oracle = seal_rec.get("oracle", {})
    if oracle.get("truth") is not True:
        problems.append("ORACLE: pre-registered truth is not True")
    if oracle.get("author", "") == oracle.get("predicate_author", "") or \
       not oracle.get("author"):
        problems.append("ORACLE: author not independent / absent")
    checks["oracle_from_seal"] = {
        "truth": oracle.get("truth"), "author": oracle.get("author"),
        "predicate_author": oracle.get("predicate_author")}

    # -- 2. anchor / quote / roles must equal the PRE-REGISTERED record -----
    anchor = str(cert.get("anchor", ""))
    quote = str(cert.get("quote", ""))
    if anchor != seal_rec.get("anchor", ""):
        problems.append("ANCHOR_NOT_PRE_REGISTERED: %r != %r"
                        % (anchor, seal_rec.get("anchor")))
    if quote != seal_rec.get("quote", ""):
        problems.append("QUOTE_NOT_PRE_REGISTERED: %r != %r"
                        % (quote[:40], str(seal_rec.get("quote", ""))[:40]))
    if cert.get("roles") != seal_rec.get("roles"):
        problems.append("ROLES_NOT_PRE_REGISTERED: caller roles differ from seal")
    if len(quote) < 10:
        problems.append("QUOTE_TOO_SHORT")

    # -- 3. parse the seal's anchor, resolve the path, READ THE FILE ---------
    m = ANCHOR_RE.match(str(seal_rec.get("anchor", "")))
    if not m:
        problems.append("ANCHOR_FORMAT: seal anchor is not file:line")
        rel, ln = None, None
    else:
        rel, ln = m.group(1), int(m.group(2))
    lines, disk_hash, disk_bytes = [], None, None
    if rel is not None:
        p = root / rel                                  # root may be a sandbox
        checks["resolved_path"] = str(p)
        if not p.is_file():
            problems.append("ANCHOR_FILE_MISSING: %s not found on disk" % rel)
        else:
            b = p.read_bytes()                          # REAL disk read
            stats.n_read_bytes += 1
            stats.n_bytes_hashed += len(b)
            disk_bytes = len(b)
            disk_hash = hashlib.sha256(b).hexdigest()   # REAL recomputation
            stats.n_sha256 += 1
            checks["disk_sha256"] = disk_hash
            checks["disk_bytes"] = disk_bytes
            checks["sealed_sha256"] = seal_rec.get("file_sha256")
            checks["sealed_bytes"] = seal_rec.get("bytes")
            if disk_hash != seal_rec.get("file_sha256"):
                checks["hash_matches_seal"] = False
            else:
                checks["hash_matches_seal"] = True
            if disk_bytes != seal_rec.get("bytes"):
                # A byte-count delta alone is a staleness witness, NOT a
                # determinate contradiction: the certified span may be intact.
                checks["byte_count_matches_seal"] = False
            else:
                checks["byte_count_matches_seal"] = True
            # a caller-declared hash is NOT trusted; we recompute and compare
            if "declared_file_sha256" in cert and \
               cert["declared_file_sha256"] != disk_hash:
                problems.append("HASH_MISMATCH_DECLARED: caller's hash != "
                                "recomputed disk hash")
            try:
                lines = b.decode("utf-8").splitlines()
                stats.n_lines_decoded += len(lines)
            except UnicodeDecodeError as e:
                problems.append("DECODE_ERROR: %s" % e)
    checks["n_lines"] = len(lines)

    # -- 4. line number exists ------------------------------------------------
    if lines:
        if ln is None or ln < 1 or ln > len(lines):
            problems.append("LINE_OUT_OF_RANGE: %s (file has %d lines)"
                            % (ln, len(lines)))
        else:
            checks["anchor_line_text"] = lines[ln - 1][:220]

    # -- 5. quote VERBATIM on the anchored line AND in the whole file ---------
    if lines and ln is not None and 1 <= ln <= len(lines):
        on_line = quote in lines[ln - 1]
        in_file = quote in "\n".join(lines)
        checks["quote_verbatim_on_anchor_line"] = on_line
        checks["quote_verbatim_in_file"] = in_file
        if not on_line:
            problems.append("QUOTE_NOT_ON_ANCHOR_LINE: quote absent from line %d"
                            % ln)

    # -- 6. role values: non-pointer AND verbatim in evidence window ---------
    lo, hi = seal_rec.get("evidence_lines", [1, 1])
    window = "\n".join(lines[max(0, lo - 1):hi]) if lines else ""
    # exact certified-span hash: catches same-byte-count edits inside the
    # evidence window that are outside the quoted substring / role values.
    if lines:
        span = "\n".join(lines[max(0, lo - 1):hi]) + "\n"
        span_hash = hashlib.sha256(span.encode("utf-8")).hexdigest()
        stats.n_sha256 += 1
        checks["evidence_span_sha256"] = span_hash
        checks["sealed_span_sha256"] = seal_rec.get("evidence_span_sha256")
        if span_hash != seal_rec.get("evidence_span_sha256"):
            problems.append("EVIDENCE_SPAN_CHANGED: certified lines %d-%d "
                            "differ from pre-registered span" % (lo, hi))
    role_rows = {}
    for r, v in seal_rec.get("roles", {}).items():
        s = str(v)
        pointer = bool(NON_VALUE_RE.search(s))
        present = (s in window)
        role_rows[r] = {"value": s, "pointer": pointer,
                        "verbatim_in_evidence_window": present}
        if pointer:
            problems.append("ROLE_POINTER: %s = %r" % (r, s[:40]))
        if not present:
            problems.append("ROLE_NOT_IN_EVIDENCE: %s = %r not in lines %d-%d"
                            % (r, s[:40], lo, hi))
    checks["roles"] = role_rows
    checks["ignored_caller_booleans"] = ignored

    # -- 7. classification: FAIL > STALE > PASS ------------------------------
    if not seal_ok:
        problems.append("SEAL_NOT_VERIFIED: pre-registered commitment failed")
    if problems:
        outcome = "FAIL"
    elif checks.get("hash_matches_seal") is False or \
            checks.get("byte_count_matches_seal") is False:
        outcome = "STALE"   # bytes changed, certified span still intact
    else:
        outcome = "PASS"
    return {"item": list(seal_rec["item"]), "outcome": outcome,
            "problems": problems, "checks": checks}


def verify_all(certs: dict, root: Path = ROOT,
               seal_path: Path = SEAL_PATH, stats: Stats = None):
    """certs: {tuple(item_key): caller cert dict}. Returns full result."""
    if stats is None:
        stats = Stats()
    t0 = time.perf_counter()
    seal, seal_problems = load_seal(seal_path, stats)
    seal_ok = not seal_problems
    by_key = {}
    if seal:
        for rec in seal["items"]:
            by_key[tuple(rec["item"])] = rec
    if seal is None:
        # No pre-registered records at all: report the whole item universe as
        # UNVERIFIED rather than silently vacuously passing an empty row list.
        rows = [{"item": list(k), "outcome": "FAIL",
                 "problems": ["SEAL_MISSING: no pre-registered record"] ,
                 "checks": {"ignored_caller_booleans":
                            [x for x in CALLER_BOOLEAN_KEYS if x in
                             certs.get(k, {})]}}
                for k in sorted(certs)]
    else:
        rows = []
        for key in sorted(by_key):
            rec = by_key[key]
            cert = certs.get(key, {})
            rows.append(verify_one(cert, rec, root, stats, seal_ok))
    stats.elapsed_ms = (time.perf_counter() - t0) * 1000.0
    n_pass = sum(1 for r in rows if r["outcome"] == "PASS")
    n_stale = sum(1 for r in rows if r["outcome"] == "STALE")
    n_fail = sum(1 for r in rows if r["outcome"] == "FAIL")
    return {"VERDICT": "PASS" if (len(rows) > 0 and n_pass == len(rows)
                                  and n_stale == 0 and n_fail == 0
                                  and seal_ok) else "NON_PASS",
            "seal_ok": seal_ok, "seal_problems": seal_problems,
            "n_items": len(rows), "n_pass": n_pass,
            "n_stale": n_stale, "n_fail": n_fail,
            "rows": rows, "stats": stats.as_dict()}


def certs_from_seal(seal_path: Path = SEAL_PATH):
    """Build honest caller certs by reading the seal (a stand-in for a
    certificate issuer). Includes NO oracle booleans on purpose."""
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    out = {}
    for rec in seal["items"]:
        out[tuple(rec["item"])] = {
            "anchor": rec["anchor"], "quote": rec["quote"],
            "roles": copy.deepcopy(rec["roles"]),
        }
    return out


# ---------------------------------------------------------------------------
# TEST HARNESS: P1 forgery, 5 real whitelist items, 5 tamper classes, fp/fn
# ---------------------------------------------------------------------------
FORGED_QUOTE = "本复核凭空编造的引文，未见于任何交付件。"


def build_sandbox(seal_path: Path = SEAL_PATH):
    """Copy the 4 real artifact files into the write domain. Read-only dirs
    are NEVER modified; tampering happens only on these copies."""
    sb = WDIR / "_cr_sandbox"
    if sb.exists():
        shutil.rmtree(sb)
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    rels = sorted({r["anchor"].rsplit(":", 1)[0] for r in seal["items"]})
    for rel in rels:
        dst = sb / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dst)
    return sb, rels


def main():
    WDIR.mkdir(parents=True, exist_ok=True)
    out = {}
    good = certs_from_seal()

    # ---- STEP 3(b): 5 real whitelist items ---------------------------------
    r_real = verify_all(good)
    out["step3b_real_5"] = {
        "VERDICT": r_real["VERDICT"], "n_items": r_real["n_items"],
        "n_pass": r_real["n_pass"], "n_stale": r_real["n_stale"],
        "n_fail": r_real["n_fail"], "seal_ok": r_real["seal_ok"],
        "stats": r_real["stats"],
        "per_item": [{"item": r["item"], "outcome": r["outcome"],
                      "problems": r["problems"]} for r in r_real["rows"]],
    }
    print("=== STEP 3(b): 5 real whitelist items ===")
    print(json.dumps(out["step3b_real_5"], ensure_ascii=False, indent=1))

    # ---- STEP 3(a): P1 forged anchors + fabricated quotes ------------------
    forged = copy.deepcopy(good)
    for i, k in enumerate(sorted(forged)):
        forged[k]["anchor"] = "cfaa/NO_SUCH_%d.md:999999" % i
        forged[k]["quote"] = FORGED_QUOTE
    r_p1 = verify_all(forged)
    out["step3a_P1_forged"] = {
        "VERDICT": r_p1["VERDICT"], "n_pass": r_p1["n_pass"],
        "n_fail": r_p1["n_fail"], "n_stale": r_p1["n_stale"],
        "per_item": [{"item": r["item"], "outcome": r["outcome"],
                      "problems": r["problems"]} for r in r_p1["rows"]],
    }
    print("\n=== STEP 3(a): P1 forged anchors + fabricated quotes ===")
    print(json.dumps(out["step3a_P1_forged"], ensure_ascii=False, indent=1))

    # ---- STEP 3(c): 5 tamper classes --------------------------------------
    sb, rels = build_sandbox()
    rul = "lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md"
    n11 = "lead/n11_wording_fix_20261108/N11_WORDING_FIX.md"
    k1 = ("lead/matrix_ab_ruling_20261109/", "需谁批准")
    seal = json.loads(SEAL_PATH.read_text(encoding="utf-8"))
    rec1 = next(r for r in seal["items"] if tuple(r["item"]) == k1)

    def run_case(name, cert_mut=None, disk_mut=None, root=ROOT, note=""):
        c = copy.deepcopy(good)
        if cert_mut:
            cert_mut(c, rec1)
        if disk_mut:
            disk_mut(sb, rels)
        r = verify_all(c, root=root)
        row = next(x for x in r["rows"] if tuple(x["item"]) == k1)
        return {"case": name, "VERDICT_of_item": row["outcome"],
                "problems": row["problems"], "n_pass": r["n_pass"],
                "n_fail": r["n_fail"], "n_stale": r["n_stale"],
                "note": note}

    def d_one_char(sandbox, _rels):
        p = sandbox / rul
        b = p.read_bytes()
        old = "批准人一律 = **乙设计责任人**".encode("utf-8")
        new = "批准人一律 = **乙设计责任X**".encode("utf-8")
        assert old in b
        p.write_bytes(b.replace(old, new, 1))

    def d_replace(sandbox, _rels):
        (sandbox / rul).write_bytes((ROOT / n11).read_bytes())

    def d_append(sandbox, _rels):
        p = sandbox / rul
        with p.open("ab") as fh:                 # append-only, outside evidence
            fh.write(b"\n<!-- appended after seal; evidence span untouched -->\n")

    cases = []
    # T1 one character changed INSIDE the certified line (sandbox copy)
    cases.append(run_case(
        "T1_one_character_changed", disk_mut=d_one_char, root=sb,
        note="one char inside anchored quote line; sandbox copy only"))
    # T2 line number changed
    def c_lineno(c, rec):
        c[k1]["anchor"] = rec["anchor"].replace(":108", ":109")
    cases.append(run_case("T2_line_number_changed", cert_mut=c_lineno,
                          note="anchor :108 -> :109"))
    # T3 synonym (quote paraphrased)
    def c_syn(c, rec):
        c[k1]["quote"] = rec["quote"].replace("一律 =", "全部 =")
    cases.append(run_case("T3_quote_synonym", cert_mut=c_syn,
                          note="一律 = -> 全部 = (same meaning)"))
    # T4 file substituted in sandbox
    cases.append(run_case("T4_file_replaced", disk_mut=d_replace, root=sb,
                          note="RULING_MATRIX_AB.md replaced by N11 bytes"))
    # T5 caller-declared hash mismatch; disk pristine
    def c_hash(c, rec):
        c[k1]["declared_file_sha256"] = "0" * 64
    cases.append(run_case("T5_declared_hash_mismatch", cert_mut=c_hash,
                          note="caller claims wrong sha256 while disk is clean"))
    # EXTRA T6: append-only edit outside evidence span -> STALE
    build_sandbox()
    cases.append(run_case("T6_append_only_edit_STALE", disk_mut=d_append,
                          root=sb,
                          note="extra case for 2(c): bytes changed, quote intact"))
    out["step3c_tamper"] = cases
    print("\n=== STEP 3(c): 5 tamper classes (+1 STALE case) ===")
    for c in cases:
        print(json.dumps(c, ensure_ascii=False))

    # ---- STEP 3(d): fp / fn on the constructed corpus ----------------------
    good_cases = [{"id": "G%d_%s" % (i + 1, r["item"][1]),
                   "label": "GOOD", "outcome": r["outcome"]}
                  for i, r in enumerate(r_real["rows"])]
    bad_cases = [{"id": "P1_forged_%d" % (i + 1), "label": "BAD",
                  "outcome": r["outcome"]} for i, r in enumerate(r_p1["rows"])]
    for c in cases:
        bad_cases.append({"id": c["case"], "label": "BAD",
                          "outcome": c["VERDICT_of_item"]})
    fp = [g for g in good_cases if g["outcome"] != "PASS"]
    fn = [b for b in bad_cases if b["outcome"] == "PASS"]
    out["step3d_fp_fn"] = {
        "n_good": len(good_cases), "n_bad": len(bad_cases),
        "false_positives": len(fp), "false_negatives": len(fn),
        "fp_ids": [g["id"] for g in fp], "fn_ids": [b["id"] for b in fn],
        "good_cases": good_cases, "bad_cases": bad_cases,
        "caveat": "constructed, non-random corpus; NOT a population FP/FN rate",
    }
    print("\n=== STEP 3(d): fp / fn ===")
    print(json.dumps(out["step3d_fp_fn"], ensure_ascii=False, indent=1))

    # ---- cost estimate (measured, not guessed) -----------------------------
    out["step2d_cost"] = {
        "measured_single_full_run": r_real["stats"],
        "unique_artifact_files": 4,
        "certificates": 5,
        "artifact_bytes_on_disk": 36851 + 27825 + 18966 + 20271,
        "seal_bytes": EXPECTED_SEAL_BYTES,
        "total_bytes_if_no_cache": 36851 + 27825 + 18966 + 20271 + 20271
                                    + EXPECTED_SEAL_BYTES,
        "total_bytes_with_cache": 36851 + 27825 + 18966 + 20271
                                  + EXPECTED_SEAL_BYTES,
        "note": "no caching implemented: 5 artifact read_bytes + 1 seal read; "
                "11 sha256 calls (1 seal + 5 files + 5 evidence spans)",
        "projected_302_items_note":
                "if all 302 items were certified: ~302 file reads; with 4-file "
                "cache ~107,818 B; without cache linear in 302 x mean artifact",
    }
    print("\n=== STEP 2(d): cost ===")
    print(json.dumps(out["step2d_cost"], ensure_ascii=False, indent=1))

    (WDIR / "_cr_verify_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8",
        newline="\n")
    print("\nWROTE _cr_verify_out.json (write domain only)")


if __name__ == "__main__":
    main()
