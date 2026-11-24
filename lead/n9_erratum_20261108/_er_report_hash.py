# -*- coding: utf-8 -*-
# _er_report_hash.py — N9_SPEC_ERRATUM.md 撰写会话：关键件指纹独立复算（hashlib，纯磁盘只读）
# 用法: python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/n9_erratum_20261108/_er_report_hash.py"
import hashlib, os

BASE = r"D:\Project\ra2-campaign-forge"
FILES = [
    (r"lead\static_spec_n9_20261107\STATIC_COUNT_SPEC.md",        "5b933fe2fcb3cc35c5026cb57b45f29da29c90b67a618346af248744ed3ccdb9", 32281,  "orchestrator-fp"),
    (r"lead\spec_static_closure_20261108\STATIC_GAP_CLOSURE.md",  "e0c00683fb23b0b3777d71639f3d7d265208057969073e53fd2b7195d0c3e1f7", 28648,  "orchestrator-fp"),
    (r"lead\spec_static_closure_20261108\_sc_scan_out.txt",       "c715898ee1339fa6fdd303a2e93a75f7fec4d92ff725d5f2e6251d76a001a075", 44255,  "orchestrator-fp"),
    (r"lead\re_line_20261105\W8_STATIC_LOCATE\W8_STATIC_LOCATE.md","20e4eeac49254b274a8382e94505525a614ec5bf24ccb89316fcd8f914406262", 26485,  "orchestrator-fp"),
    (r"lead\static_spec_n9_20261107\_n9_STATIC_COUNT_SPEC.md",    "1817d9ce264b28d3630ee3d596fcaec798afa42733c4a366eaefe14daa5fe281", 19949,  "erratum-§0"),
    (r"lead\perf_repair_n11_20261108\PERF_REPAIR_HANDOFF.md",     "7a617a43b32fc2e38c7e46ff9d436f903810ad9cae919fc0eb891a0f9f5796e0", 29619,  "erratum-§0"),
    (r"lead\re_line_20261105\W8_STATIC_LOCATE\F8_VISIBILITY.md",  "ebacbfcae71c0de3c65d6a0cb573cc9467366f0ecc6bcb8bc570e018c3255bd0", 19335,  "erratum-§0"),
    (r"lead\spec_static_closure_20261108\_sc_CLOSURE_20261108.md","9b8695a3a107cecb4f7884f7e32749cbaaf0fbb333c7f7d19dabb7e425d81b67", 23490,  "erratum-§0"),
    (r"lead\perf_repair_n11_20261108\_n11_PERF_REPAIR_HANDOFF.md","cf73fd80", 22745, "review-prefix"),
    (r"lead\d13d14_cards_20261108\DECISION_QUESTIONS.md",         "0a709f2d", 27172, "review-prefix"),
    (r"lead\d13d14_cards_20261108\_n10_D13D14_CARDS_20261108.md", "8a36d60a", 30122, "review-prefix"),
    (r"lead\n9_erratum_20261108\_er_N9_205_P6_B0CD48_ERRATUM.md", "414795407eef7f000baad213db075899513c86c2ee71fbeb3a72e1c5ff95ae73", 15794, "reviewed-object"),
    (r"lead\n9_erratum_20261108\_er_check_b0cd48.py",             "f3896d81ce1697c8710950dc15834264ee14e1701198efc65e81b61df65f873b", 5209,  "erratum-产物"),
    (r"lead\n9_erratum_20261108\_er_check_b0cd48_out.txt",        "73f76c8c69a62db350c27759a50bdd8386f7c6c9dc249891877afd64f2ecd7a9", 3104,  "erratum-产物"),
    (r"ra2youli\gamemd.exe",  "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476", 4825360, "corpus-fp"),
    (r"ra2bench\gamemd.exe",  "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476", 4825360, "corpus-fp"),
]

print("== _er_report_hash.py 指纹复算 ==")
n_match = 0
for rel, exp, expb, src in FILES:
    p = os.path.join(BASE, rel)
    try:
        data = open(p, "rb").read()
    except OSError as e:
        print("FAIL %s -> %s" % (rel, e))
        continue
    sha = hashlib.sha256(data).hexdigest()
    n = len(data)
    ok_sha = sha == exp or (len(exp) < 64 and sha.startswith(exp))
    ok_b = n == expb
    n_match += 1 if (ok_sha and ok_b) else 0
    print("%s %s\n  sha256=%s bytes=%d  expect=%s…/%dB  SHA=%s BYTES=%s (src=%s)"
          % ("MATCH" if (ok_sha and ok_b) else "DIFF ", rel, sha, n, exp[:8], expb,
             "OK" if ok_sha else "DIFF", "OK" if ok_b else "DIFF", src))
print("SUMMARY match=%d/%d" % (n_match, len(FILES)))
