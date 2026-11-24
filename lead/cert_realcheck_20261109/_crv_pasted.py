# 可粘贴的真校验实现（VERBATIM copy of the design's `realVerifier` field,
# wrapped by the reviewer ONLY with an importable module name + a test main).
# Reviewer addition is ONLY the `if __name__ == "__main__"` block at the end.
import hashlib, json, re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
SEAL_PATH = ROOT / "lead" / "cert_realcheck_20261109" / "_cr_seal.json"
PRE_REGISTERED_SEAL_SHA256 = "63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23"
EXPECTED_SEAL_BYTES = 4395
ANCHOR_RE = re.compile(r"^(.+):(\d+)$")
CALLER_BOOLEAN_KEYS = ("oracle_truth", "oracle_author", "oracle_sealed",
                       "predicate_author", "whitelist_sealed")
# 与 _fnr_check.py:62-67 逐字一致（未改该文件）
NON_VALUE_RE = re.compile(
    r"见台账|详见|参见|见附件|见上|见下表|以.{0,6}记载为准|不另下结论|不重录|"
    r"不予判定|暂不作判定|待判|待定|待补|待验|待查|待确认|尚需|尚未|需进一步|"
    r"是否|并非|不可重建|无法重建|未能重建|未验|未采集|无输出|"
    r"^(?:TBD|N/?A|待定|待指定|未定|未知|略|\.{2,}|…+)$")


def load_seal(seal_path=SEAL_PATH):
    """真读封印 + 真算 hash；防止攻击者连封印一起重写。"""
    problems = []
    if not seal_path.is_file():
        return None, ["SEAL_MISSING: no seal file on disk"]
    blob = seal_path.read_bytes()                      # REAL disk read
    if len(blob) != EXPECTED_SEAL_BYTES:
        problems.append("SEAL_BYTES_MISMATCH")
    if hashlib.sha256(blob).hexdigest() != PRE_REGISTERED_SEAL_SHA256:
        problems.append("SEAL_INTEGRITY: seal sha256 != pre-registered value")
    try:
        return json.loads(blob.decode("utf-8")), problems
    except Exception as e:
        return None, problems + ["SEAL_DECODE_ERROR: %s" % e]


def verify_one(cert, rec, root=ROOT, seal_ok=True):
    """验 1 份证书：真读盘、真算 hash、比对预注册值、查行号、查引文逐字在场。"""
    problems, checks = [], {}
    checks["ignored_caller_booleans"] = [k for k in CALLER_BOOLEAN_KEYS if k in cert]

    # (1) ORACLE 只来自封印，绝不读 cert 的 oracle_* 布尔
    oracle = rec.get("oracle", {})
    if oracle.get("truth") is not True:
        problems.append("ORACLE: pre-registered truth is not True")
    if not oracle.get("author") or oracle.get("author") == oracle.get("predicate_author"):
        problems.append("ORACLE: author not independent / absent")

    # (2) 证书声明必须与预注册记录逐字相等（防伪造锚点/同义引文/角色替换）
    anchor, quote = str(cert.get("anchor", "")), str(cert.get("quote", ""))
    if anchor != rec.get("anchor"): problems.append("ANCHOR_NOT_PRE_REGISTERED")
    if quote != rec.get("quote"):   problems.append("QUOTE_NOT_PRE_REGISTERED")
    if cert.get("roles") != rec.get("roles"): problems.append("ROLES_NOT_PRE_REGISTERED")
    if len(quote) < 10: problems.append("QUOTE_TOO_SHORT")

    # (3) 用封印的锚点解析路径，真读文件、真算 hash、比对预注册值
    m = ANCHOR_RE.match(str(rec.get("anchor", "")))
    rel, ln = (m.group(1), int(m.group(2))) if m else (None, None)
    lines = []
    if rel is None:
        problems.append("ANCHOR_FORMAT")
    else:
        p = root / rel
        if not p.is_file():
            problems.append("ANCHOR_FILE_MISSING: %s" % rel)
        else:
            b = p.read_bytes()                          # REAL disk read
            disk_hash = hashlib.sha256(b).hexdigest()   # REAL hash recomputation
            checks["disk_sha256"], checks["sealed_sha256"] = disk_hash, rec.get("file_sha256")
            checks["hash_matches_seal"] = (disk_hash == rec.get("file_sha256"))
            checks["byte_count_matches_seal"] = (len(b) == rec.get("bytes"))
            # 调用方声明的 hash 不被采信，只拿来与重算值对照
            if "declared_file_sha256" in cert and cert["declared_file_sha256"] != disk_hash:
                problems.append("HASH_MISMATCH_DECLARED: caller hash != recomputed disk hash")
            lines = b.decode("utf-8").splitlines()

    # (4) 行号必须存在
    if lines and (ln is None or ln < 1 or ln > len(lines)):
        problems.append("LINE_OUT_OF_RANGE: %s / %d lines" % (ln, len(lines)))

    # (5) 引文逐字在锚点行上（且已在 (2) 与预注册引文比对）
    if lines and ln and 1 <= ln <= len(lines):
        checks["quote_verbatim_on_anchor_line"] = quote in lines[ln - 1]
        if not checks["quote_verbatim_on_anchor_line"]:
            problems.append("QUOTE_NOT_ON_ANCHOR_LINE")

    # (6) 角色值：非指针 + 逐字在预注册证据窗口 + 窗口精确 hash（抓等长替换）
    lo, hi = rec.get("evidence_lines", [1, 1])
    if lines:
        window = "\n".join(lines[max(0, lo - 1):hi])
        span_hash = hashlib.sha256((window + "\n").encode("utf-8")).hexdigest()
        if span_hash != rec.get("evidence_span_sha256"):
            problems.append("EVIDENCE_SPAN_CHANGED")
        for r, v in rec.get("roles", {}).items():
            s = str(v)
            if NON_VALUE_RE.search(s): problems.append("ROLE_POINTER: %s" % r)
            if s not in window:        problems.append("ROLE_NOT_IN_EVIDENCE: %s" % r)

    # (7) 三态：文件缺失/内容矛盾 = FAIL；仅在证据区间外的字节变动 = STALE（NON_PASS）
    if not seal_ok: problems.append("SEAL_NOT_VERIFIED")
    if problems:                                      outcome = "FAIL"
    elif checks.get("hash_matches_seal") is False or \
         checks.get("byte_count_matches_seal") is False: outcome = "STALE"
    else:                                             outcome = "PASS"
    return {"item": list(rec["item"]), "outcome": outcome,
            "problems": problems, "checks": checks}


def verify_all(certs, root=ROOT, seal_path=SEAL_PATH):
    seal, seal_problems = load_seal(seal_path)
    seal_ok = not seal_problems
    if seal is None:   # 封印缺失 -> 全部 UNVERIFIED，绝不 vacuous PASS
        rows = [{"item": list(k), "outcome": "FAIL",
                 "problems": ["SEAL_MISSING: no pre-registered record"], "checks": {}}
                for k in sorted(certs)]
    else:
        rows = [verify_one(certs.get(tuple(r["item"]), {}), r, root, seal_ok)
                for r in seal["items"]]
    np_ = sum(r["outcome"] == "PASS"  for r in rows)
    ns  = sum(r["outcome"] == "STALE" for r in rows)
    nf  = sum(r["outcome"] == "FAIL"  for r in rows)
    return {"VERDICT": "PASS" if (rows and np_ == len(rows) and ns == 0
                                   and nf == 0 and seal_ok) else "NON_PASS",
            "seal_ok": seal_ok, "seal_problems": seal_problems,
            "n_pass": np_, "n_stale": ns, "n_fail": nf, "rows": rows}


# ===== REVIEWER-ONLY test driver (not part of the pasted snippet) ==========
if __name__ == "__main__":
    import copy
    seal = json.loads(SEAL_PATH.read_bytes().decode("utf-8"))
    good = {tuple(r["item"]): {"anchor": r["anchor"], "quote": r["quote"],
                               "roles": copy.deepcopy(r["roles"])}
            for r in seal["items"]}
    r_good = verify_all(good)
    forged = copy.deepcopy(good)
    for i, k in enumerate(sorted(forged)):
        forged[k]["anchor"] = "cfaa/NO_SUCH_%d.md:999999" % i
        forged[k]["quote"] = "本复核凭空编造的引文，未见于任何交付件。"
    r_bad = verify_all(forged)
    out = {
        "pasted_snippet_runs": True,
        "good": {k: r_good[k] for k in ("VERDICT", "n_pass", "n_stale",
                                        "n_fail", "seal_ok")},
        "P1_forged": {k: r_bad[k] for k in ("VERDICT", "n_pass", "n_stale",
                                            "n_fail", "seal_ok")},
        "note": "reviewer ran the PASTED snippet verbatim (only added a test "
                "driver), replicating step 3(a)/3(b).",
    }
    (ROOT / "lead" / "cert_realcheck_20261109" /
     "_crv_pasted_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))
