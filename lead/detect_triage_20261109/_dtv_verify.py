# -*- coding: utf-8 -*-
"""_dtv_verify.py -- INDEPENDENT re-verification of the detection triage reply.

Read-only over all protected domains; writes ONLY _dtv_*.json / _dtv_*.md
inside lead/detect_triage_20261109/.  Bytecode writing is disabled so importing
protected detector sources cannot create/modify __pycache__ there.

Checks:
  (2) re-run kd.analyse + cf.analyze on all 173 raw files, compare per-piece
      verdicts/sha against BOTH frozen outputs, cf-vs-kd per-piece on all 173;
  (3) re-derive the 4-level triage per-piece from scratch (no use of
      _dt_triage_out.json as truth), compare against the reply's rows;
  (4) independent missed-A search: enumerate every *.py basename in the two
      ledgers AND in the read-only deliverable, map to detector verdicts and
      to ALL cited PASS/exit=0 lines; find any production+ledger+confirmed
      piece that the reply failed to put at A level;
  (6) arithmetic self-consistency A+B+C+D=40;
  (7) boundary checks: fingerprints vs frozen, git status/HEAD.
"""
import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(sys.argv[1]).resolve()
WD = ROOT / "lead/detect_triage_20261109"
KD_DIR = ROOT / "lead/k1bit_detect_20261109"
CF_DIR = ROOT / "lead/check_family_20261109"
SP_DIR = ROOT / "lead/stale_pass_20261109"
RS_DIR = ROOT / "lead/refsync_scope_20261109"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def jread(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def sha(p):
    b = Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


kd = load("_dtv_kd", KD_DIR / "_kd_detect.py")
cfmod = load("_dtv_cf", CF_DIR / "_cf_detect.py")

listfile = CF_DIR / "_cf_filelist.txt"
rels = []
for ln in listfile.read_text(encoding="utf-8").splitlines():
    t = ln.strip()
    if t:
        rels.append(t[2:] if t.startswith("./") else t)

frozen_kd = jread(KD_DIR / "_kd_detect_out.json")
frozen_cf = jread(CF_DIR / "_cf_detect_out.json")
reply_repro = jread(WD / "_dt_repro_out.json")
reply_triage = jread(WD / "_dt_triage_out.json")
reply_scope = jread(WD / "_dt_scope_out.json")
reply_leak = jread(WD / "_dt_leak_out.json")
report_md = (WD / "_dt_REPORT.md").read_text(encoding="utf-8")
table_md = (WD / "_dt_table.md").read_text(encoding="utf-8")

out = {}

# ================================================================ (2) detector
kd_rows = []
cf_rows = []
for rel in rels:
    p = ROOT / rel
    if not p.is_file():
        kd_rows.append(dict(rel=rel, verdict="MISSING"))
        cf_rows.append(dict(rel=rel, verdict="MISSING"))
        continue
    raw = p.read_bytes()
    text = raw.decode("utf-8-sig", errors="replace")
    a = kd.analyse(rel, raw)
    b = cfmod.analyze(rel, text)
    kd_rows.append(dict(rel=rel, verdict=a["verdict"], sha256=a["sha256"],
                        bytes=a["bytes"], has_k=a.get("has_k"),
                        attribution=a.get("attribution"),
                        collapse=[c["kind"] for c in a.get("collapse", [])]))
    cf_rows.append(dict(rel=rel, verdict=b["verdict"],
                        sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)))

cnt_kd = Counter(r["verdict"] for r in kd_rows)
cnt_cf = Counter(r["verdict"] for r in cf_rows)
my_conf = [r["rel"] for r in kd_rows if r["verdict"] == "CONFIRMED_K1BIT"]
my_susp = [r["rel"] for r in kd_rows if r["verdict"] == "SUSPECT"]
my_cf_conf = [r["rel"] for r in cf_rows if r["verdict"] == "CONFIRMED"]
my_cf_susp = [r["rel"] for r in cf_rows if r["verdict"] == "SUSPECT"]

by_rel_frozen_kd = {r["rel"]: r for r in frozen_kd["rows"]}
by_rel_frozen_cf = {r["rel"]: r for r in frozen_cf["rows"]}
by_rel_my_kd = {r["rel"]: r for r in kd_rows}
by_rel_my_cf = {r["rel"]: r for r in cf_rows}

kd_verdict_mismatches = [r["rel"] for r in kd_rows
                         if by_rel_frozen_kd.get(r["rel"], {}).get("verdict") != r["verdict"]]
kd_sha_mismatches = [r["rel"] for r in kd_rows
                     if by_rel_frozen_kd.get(r["rel"], {}).get("sha256") != r.get("sha256")]
cf_verdict_mismatches = [r["rel"] for r in cf_rows
                         if by_rel_frozen_cf.get(r["rel"], {}).get("verdict") != r["verdict"]]
cf_conf_mismatches = sorted(set(my_conf) ^ set(frozen_cf["confirmed"]))
kd_conf_mismatches = sorted(set(my_conf) ^ set(frozen_kd["confirmed"]))

# per-piece cf-vs-kd comparison on the full 173 (not just the 40)
cf_kd_disagree = []
for rel in rels:
    k = by_rel_my_kd[rel]["verdict"]
    c = by_rel_my_cf[rel]["verdict"]
    if k != c:
        cf_kd_disagree.append(dict(rel=rel, kd=k, cf=c))
conf_disagree = [x for x in cf_kd_disagree
                 if (x["kd"] == "CONFIRMED_K1BIT") != (x["cf"] == "CONFIRMED")]

out["detector"] = dict(
    n=len(rels), counts_kd=dict(cnt_kd), counts_cf=dict(cnt_cf),
    my_confirmed_n=len(my_conf), my_suspect_n=len(my_susp),
    my_cf_confirmed_n=len(my_cf_conf), my_cf_suspect_n=len(my_cf_susp),
    frozen_counts_kd=frozen_kd["counts"], frozen_counts_cf=None,
    counts_match_frozen_kd=(dict(cnt_kd) == frozen_kd["counts"]),
    confirmed_equal_frozen_kd=(my_conf == frozen_kd["confirmed"]),
    suspect_equal_frozen_kd=(my_susp == frozen_kd["suspect"]),
    confirmed_equal_frozen_cf=(my_cf_conf == frozen_cf["confirmed"]),
    suspect_equal_frozen_cf=(my_cf_susp == frozen_cf["suspect"]),
    kd_verdict_mismatches=kd_verdict_mismatches,
    kd_sha_mismatches=kd_sha_mismatches,
    cf_verdict_mismatches=cf_verdict_mismatches,
    cf_conf_mismatches=cf_conf_mismatches,
    kd_conf_mismatches=kd_conf_mismatches,
    n_cf_kd_verdict_disagreements=len(cf_kd_disagree),
    n_cf_kd_confirmed_disagreements=len(conf_disagree),
    cf_kd_disagreements=cf_kd_disagree,
    reply_confirmed_equal_mine=(reply_repro["kd"]["confirmed"] == my_conf),
    confirmed_40_mine=my_conf,
)

# ================================================================ (3) per-piece 4-level triage
PROD = {
    "lead/d27_ruling_20261106/check_d27.py": ("D-27", 129),
    "lead/d28_ruling_20261106/check_d28.py": ("D-28", 117),
    "lead/d29_ruling_20261106/check_d29.py": ("D-29", 105),
    "lead/d30_ruling_20261106/check_d30.py": ("D-30", 92),
}
ledgers = [ROOT / "lead/PENDING_DECISIONS.md",
           ROOT / "lead/GOAL_THREE_TARGETS_20261018.md"]
ledger_lines = {p.name: p.read_text(encoding="utf-8").splitlines() for p in ledgers}
ledger_text = "\n".join("\n".join(v) for v in ledger_lines.values())

# independent ledger hit scan for the 4 production gates (all `*.py` names)
my_hits = {}
for rel in PROD:
    nm = Path(rel).name
    h = {}
    for lname, lines in ledger_lines.items():
        h[lname] = [i + 1 for i, s in enumerate(lines) if nm in s]
    my_hits[rel] = h

# independent full-rel citation scan for every confirmed row
my_rows = []
for rel in my_conf:
    k = by_rel_my_kd[rel]
    nm = Path(rel).name
    full_rel_cited = rel in ledger_text
    basename_hits = [(lname, [i + 1 for i, s in enumerate(lines) if nm in s])
                     for lname, lines in ledger_lines.items()]
    basename_hits = [(a, b) for a, b in basename_hits if b]
    is_prod = rel in PROD
    sandbox_marker = next((g for g in ("_cm_tmp", "_cmv_tmp", "_sp_sandbox")
                           if ("/" + g + "/") in rel), None)
    if is_prod:
        level, group = "A", "生产件"
        ruling, line = PROD[rel]
        ledger_line = "PENDING_DECISIONS.md:%d" % line
    else:
        level, group = "D", ("沙箱 " + sandbox_marker if sandbox_marker else "OTHER")
        ruling, line, ledger_line = "", None, ""
    my_rows.append(dict(rel=rel, level=level, group=group, ruling=ruling,
                        ledger_line=ledger_line, sha256=k["sha256"], bytes=k["bytes"],
                        full_rel_cited=full_rel_cited, basename_hits=basename_hits,
                        sandbox_marker=sandbox_marker))

my_counts = {lv: sum(r["level"] == lv for r in my_rows) for lv in "ABCD"}
my_groups = Counter(r["group"] for r in my_rows)
reply_rows = {r["rel"]: r for r in reply_triage["rows"]}
per_piece_diffs = []
for r in my_rows:
    q = reply_rows.get(r["rel"])
    if q is None:
        per_piece_diffs.append(dict(rel=r["rel"], issue="MISSING_IN_REPLY"))
        continue
    for k in ("level", "group", "sha256", "bytes", "ledger_line"):
        if r[k] != q[k]:
            per_piece_diffs.append(dict(rel=r["rel"], field=k, mine=r[k], reply=q[k]))
extra_in_reply = sorted(set(reply_rows) - {r["rel"] for r in my_rows})

# table.md / report binding lines
BIND_RE = re.compile(r"^被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)$")
binding = []
for i, s in enumerate(report_md.splitlines(), 1):
    m = BIND_RE.match(s)
    if m:
        binding.append(dict(line=i, sha256=m.group(1), bytes=int(m.group(2))))
table_row_re = re.compile(r"^\| (\d+) \| `([^`]+)` \| \*\*([ABCD])\*\* \|")
table_rows = []
for i, s in enumerate(table_md.splitlines(), 1):
    m = table_row_re.match(s)
    if m:
        table_rows.append(dict(line=i, n=int(m.group(1)), rel=m.group(2), level=m.group(3)))
table_diffs = []
by_n = {r["n"]: r for r in table_rows}
for r in my_rows:
    n = my_conf.index(r["rel"]) + 1
    t = by_n.get(n)
    if t is None or t["rel"] != r["rel"] or t["level"] != r["level"]:
        table_diffs.append(dict(n=n, rel=r["rel"], mine=r["level"], table=t))

out["triage"] = dict(
    my_counts=my_counts, my_groups=dict(my_groups), sum_counts=sum(my_counts.values()),
    reply_counts=reply_triage["counts"], reply_group_counts=reply_triage["group_counts"],
    my_ledger_hits=my_hits,
    n_rows=len(my_rows), n_reply_rows=len(reply_rows),
    per_piece_diffs=per_piece_diffs, extra_in_reply=extra_in_reply,
    n_full_rel_cited_sandbox=sum(r["full_rel_cited"] for r in my_rows
                                 if r["level"] == "D"),
    sandbox_basename_hits=[r for r in my_rows if r["level"] == "D" and r["basename_hits"]],
    n_table_rows=len(table_rows), table_diffs=table_diffs,
    binding_lines=binding, n_binding_lines=len(binding),
    binding_equal_reply=([(b["sha256"], b["bytes"]) for b in binding]
                         == [(b["sha256"], b["bytes"]) for b in reply_triage["binding"]]),
)

# ================================================================ (4) missed-A search
all_py_names = sorted(set(re.findall(r"[A-Za-z0-9_]+\.py", ledger_text)))
deliverable = RS_DIR / "REFSYNC_SCOPE_FIX.md"
deliv_lines = deliverable.read_text(encoding="utf-8").splitlines()
deliv_names = sorted(set(re.findall(r"[A-Za-z0-9_]+\.py",
                                    "\n".join(deliv_lines))))
union_names = sorted(set(all_py_names) | set(deliv_names))

# every ledger line that contains a *.py name AND a PASS/exit=0 style claim
pass_re = re.compile(r"exit\s*=\s*0|PASS|门禁|SELF_TEST", re.I)
cited = []
for lname, lines in ledger_lines.items():
    for i, s in enumerate(lines, 1):
        if pass_re.search(s):
            for nm in re.findall(r"[A-Za-z0-9_]+\.py", s):
                cited.append(dict(file=lname, line=i, name=nm, text=s.strip()[:180]))
for i, s in enumerate(deliv_lines, 1):
    if pass_re.search(s):
        for nm in re.findall(r"[A-Za-z0-9_]+\.py", s):
            cited.append(dict(file=deliverable.name, line=i, name=nm,
                              text=s.strip()[:180]))

# resolve each candidate name to every live file in the 173 census (and any
# extra non-check_*.py production file explicitly under lead/*_ruling dirs)
name_to_files = {}
for nm in union_names:
    hits = [r for r in rels if Path(r).name == nm]
    name_to_files[nm] = hits

# all CONFIRMED pieces that are production (not in a sandbox dir) and whose PASS
# is cited in a ledger, regardless of whether the reply把它们列 A
sandbox_tokens = ("_cm_tmp", "_cmv_tmp", "_sp_sandbox")
confirmed_set = set(my_conf)
a_candidates = []
for c in cited:
    nm = c["name"]
    for f in name_to_files.get(nm, []):
        if f in confirmed_set and not any(t in f for t in sandbox_tokens):
            a_candidates.append(dict(source="%s:%d" % (c["file"], c["line"]),
                                     name=nm, rel=f, verdict=by_rel_my_kd[f]["verdict"],
                                     reply_level=reply_rows.get(f, {}).get("level")))

# out-of-census: any *.py named on a cited PASS line that is NOT check_*.py,
# is CONFIRMED by kd.analyse, and is absent from the 173 census.
# Bounded path index from `find` output (a full-root rglob was too slow here);
# we restrict to names actually cited on PASS lines, plus every non-check_*.py
# under lead/ with the "_scan"/"_gate"/"_verify" family markers named in the
# reply's own reusable enumeration method.
# Path index produced out-of-band by Bash `find` (NOT Windows FIND.EXE) as
# `_dtv_allpy.txt` in this write domain; exact command:
#   find . -path ./.git -prune -o -type f -name '*.py' -print > _dtv_allpy.txt
index_path = WD / "_dtv_allpy.txt"
find_txt = index_path.read_text(encoding="utf-8", errors="replace")
find_info = dict(source="_dtv_allpy.txt (Bash find, EXIT=0)",
                 n_lines=len(find_txt.splitlines()),
                 stderr_bytes=(WD / "_dtv_find_stderr.txt").stat().st_size)
all_py_rels = [s[2:] if s.startswith("./") else s
               for s in find_txt.splitlines() if s.strip()]
name_to_all = {}
for rel in all_py_rels:
    name_to_all.setdefault(Path(rel).name, []).append(rel)

cited_noncheck = sorted({c["name"] for c in cited if not c["name"].startswith("check_")})
scan_family = [rel for rel in all_py_rels
               if ("scan" in Path(rel).name or "gate" in Path(rel).name
                   or "verify" in Path(rel).name) and not Path(rel).name.startswith("check_")]
scan_names = {Path(rel).name for rel in scan_family}
probe_names = sorted(set(cited_noncheck) | scan_names)
noncheck_confirmed_cited = []
for nm in probe_names:
    for rel in name_to_all.get(nm, []):
        if rel in by_rel_my_kd:      # already in 173 census
            continue
        p = ROOT / rel
        if not p.is_file():
            continue
        a = kd.analyse(rel, p.read_bytes())
        if a["verdict"] != "CONFIRMED_K1BIT":
            continue
        srcs = []
        for fname, lines2 in ledger_lines.items():
            for i2, s2 in enumerate(lines2, 1):
                if pass_re.search(s2) and nm in s2:
                    srcs.append("%s:%d" % (fname, i2))
        for i2, s2 in enumerate(deliv_lines, 1):
            if pass_re.search(s2) and nm in s2:
                srcs.append("%s:%d" % (deliverable.name, i2))
        noncheck_confirmed_cited.append(dict(
            sources=srcs, rel=rel,
            sha256=a["sha256"], bytes=a["bytes"], verdict=a["verdict"],
            has_k=a.get("has_k"), attribution=a.get("attribution"),
            collapse=[x["kind"] for x in a.get("collapse", [])],
            in_reply_confirmed_40=(rel in reply_repro["kd"]["confirmed"]),
            in_reply_rows_40=(rel in reply_rows)))

# independent ledger-wide production-gate enumeration: all lines with 门禁/exit=0
gate_lines = []
for lname, lines in ledger_lines.items():
    for i, s in enumerate(lines, 1):
        if "门禁" in s and re.search(r"exit\s*=\s*0", s):
            gate_lines.append(dict(file=lname, line=i, text=s.strip()[:220]))

out["leak"] = dict(
    n_py_names_ledgers=len(all_py_names), n_py_names_deliverable=len(deliv_names),
    n_py_names_union=len(union_names),
    n_cited_pass_name_lines=len(cited), cited=cited,
    gate_lines=gate_lines,
    a_candidates=a_candidates,
    a_candidates_not_A=[x for x in a_candidates if x["reply_level"] != "A"],
    noncheck_confirmed_cited=noncheck_confirmed_cited,
    reply_registered_gates=[r["name"] for r in reply_leak["registered_gates"]],
    reply_registered_not_confirmed=[r["name"]
                                    for r in reply_leak["registered_not_confirmed"]],
    reply_carrier_one=reply_scope["carrier_one"],
    find_info=find_info,
    n_all_py_files=len(all_py_rels),
    n_scan_family_files=len(scan_family),
    n_probe_names=len(probe_names),
    cited_noncheck_names=cited_noncheck,
)

# ================================================================ (6) arithmetic
out["arithmetic"] = dict(
    reply_counts=reply_triage["counts"],
    sum_reply=sum(reply_triage["counts"].values()),
    n_rows_reply=reply_triage["n"],
    n_confirmed_reply=reply_repro["kd"]["n_confirmed"],
    my_counts=my_counts, sum_mine=sum(my_counts.values()),
    n_table_rows=len(table_rows),
    a_plus_b_plus_c_plus_d_equals_40=(sum(reply_triage["counts"].values()) == 40),
    counts_equal_rows=(reply_triage["n"] == sum(reply_triage["counts"].values())),
    counts_equal_confirmed=(reply_repro["kd"]["n_confirmed"]
                            == sum(reply_triage["counts"].values())),
    table_rows_equal_40=(len(table_rows) == 40),
    group_sum=sum(reply_triage["group_counts"].values()),
    group_sum_equals_40=(sum(reply_triage["group_counts"].values()) == 40),
)

# ================================================================ (7) boundary / binding
base7 = {
    "lead/k1bit_detect_20261109/_kd_detect_out.json": "00f77fe0d5582d8eaec42f1b908d9f48c4b94b65b0b09b3b1e4609280f7ac239",
    "lead/k1bit_detect_20261109/K1BIT_DETECTOR.md": "40d79857bebc28fb1dd1d2f03afc7f1dc825b4b9cf9a56e55a0a93179ca32ad1",
    "lead/k1bit_detect_20261109/_kd_literal_vs_semantic_out.json": "af84560f288a0f74cac5f9f1f95f64f68c767e8a0aee32e869d1b0fc2ab9cc2f",
    "lead/check_family_20261109/_cf_detect_out.json": "17e83a81ecf0cca951825d3191bb0772011de1af3269d793922a8db068e5c3c2",
    "lead/stale_pass_20261109/STALE_PASS_INVENTORY.md": "a72d79b23b1329207a2c612d4244dec407ffaa4e0b91c397c3febb7a9cddd798",
    "lead/PENDING_DECISIONS.md": "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7",
    "lead/GOAL_THREE_TARGETS_20261018.md": "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede",
}
fp = []
for rel, want in base7.items():
    h, n = sha(ROOT / rel)
    fp.append(dict(rel=rel, sha256=h, bytes=n, want=want, match=(h == want)))
A4 = []
for rel in PROD:
    h, n = sha(ROOT / rel)
    A4.append(dict(rel=rel, sha256=h, bytes=n))
out["boundary"] = dict(
    fingerprints=fp, n_match=sum(x["match"] for x in fp),
    A4=A4,
    binding_lines_strict=all(BIND_RE.match(s) is not None
                             for s in report_md.splitlines()
                             if s.startswith("被核对象 SHA256 =")),
    n_binding_lines=len(binding),
    binding_first7_equal_base=([(b["sha256"], b["bytes"]) for b in binding[:7]]
                               == [(x["sha256"], x["bytes"]) for x in fp]),
    binding_last4_equal_A4=([(b["sha256"], b["bytes"]) for b in binding[7:]]
                            == [(x["sha256"], x["bytes"]) for x in A4]),
    report_sha256=hashlib.sha256((WD / "_dt_REPORT.md").read_bytes()).hexdigest(),
    report_bytes=(WD / "_dt_REPORT.md").stat().st_size,
)

(WD / "_dtv_verify_out.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

# ---- console summary (short, ASCII-safe where possible)
print("ROOT", ROOT.as_posix())
print("DETECTOR n=%d kd_counts=%s cf_counts=%s" % (out["detector"]["n"],
      json.dumps(out["detector"]["counts_kd"], ensure_ascii=False),
      json.dumps(out["detector"]["counts_cf"], ensure_ascii=False)))
print("DETECTOR kd_verdict_mismatches=%d kd_sha_mismatches=%d cf_verdict_mismatches=%d cf_conf_mismatches=%d" %
      (len(kd_verdict_mismatches), len(kd_sha_mismatches),
       len(cf_verdict_mismatches), len(cf_conf_mismatches)))
print("DETECTOR n_cf_kd_disagreements=%d n_confirmed_disagreements=%d" %
      (len(cf_kd_disagree), len(conf_disagree)))
print("TRIAGE my_counts=%s sum=%d per_piece_diffs=%d extra_in_reply=%d table_rows=%d table_diffs=%d" %
      (json.dumps(my_counts), sum(my_counts.values()), len(per_piece_diffs),
       len(extra_in_reply), len(table_rows), len(table_diffs)))
print("TRIAGE my_ledger_hits=%s" % json.dumps(my_hits, ensure_ascii=False))
print("TRIAGE binding_lines=%d strict=%s eq_reply=%s" %
      (len(binding), out["boundary"]["binding_lines_strict"],
       out["triage"]["binding_equal_reply"]))
print("LEAK names ledger=%d deliverable=%d union=%d cited_lines=%d gate_lines=%d" %
      (len(all_py_names), len(deliv_names), len(union_names), len(cited), len(gate_lines)))
print("LEAK a_candidates=%d not_A=%d noncheck_confirmed_cited=%d" %
      (len(a_candidates), len(out["leak"]["a_candidates_not_A"]),
       len(noncheck_confirmed_cited)))
for x in out["leak"]["a_candidates_not_A"]:
    print("  MISSED_A?", json.dumps(x, ensure_ascii=False))
for x in noncheck_confirmed_cited:
    print("  OUT_OF_CENSUS", json.dumps(x, ensure_ascii=False))
print("ARITHMETIC %s" % json.dumps(out["arithmetic"], ensure_ascii=False))
print("BOUNDARY fp_match=%d/7 strict=%d first7=%s last4=%s report_sha=%s report_bytes=%d" %
      (out["boundary"]["n_match"], out["boundary"]["binding_lines_strict"],
       out["boundary"]["binding_first7_equal_base"],
       out["boundary"]["binding_last4_equal_A4"],
       out["boundary"]["report_sha256"], out["boundary"]["report_bytes"]))
print("WROTE", (WD / "_dtv_verify_out.json").as_posix())
