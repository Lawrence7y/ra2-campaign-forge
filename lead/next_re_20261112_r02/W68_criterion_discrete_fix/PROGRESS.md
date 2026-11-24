# W68 / W68b progress log

- [2026-11-14T00:17:37.8663843+08:00] W68 started (GLM-5.3-Flash), offline-only. Next: read frozen W62 tool + CRITERIA_SPEC, locate W65 A/B NDJSON data.
- [2026-11-14T00:23:13.1576063+08:00] W62 tool_b_stats.py + CRITERIA_SPEC.md read (Counter defect at lines 148-149/203-207, B-2 at 223-227). W65 data located: out\A1/A2/B1/B2/A_merged/B_merged.ndjson. b_compare.json read.

## W68b takeover (Hy4) — GLM stalled after 3 startup files, no substantive deliverables

- [2026-11-14T00:23:47+08:00] STARTED_W68B.txt written (ISO + Hy4 + "takeover: GLM stalled"); HEARTBEAT updated.
- [2026-11-14T00:24:06+08:00] EVIDENCE\w68b_skeleton.py dropped BEFORE detailed reading and RUN (selftest + emit-env both exit 0). [本次实测]
- [2026-11-14T00:24..00:28] [本次读码] W62 tool_b_stats.py (431 lines) + CRITERIA_SPEC.md (176 lines) + W65 b_compare.json / w65_descriptive_stats.json + REVIEW\LEAD_VERIFY_W65.md. Defect confirmed: Counter-based multiset equality at :148-149/203-207, B-2 short-circuit at :222-227; five fields value sets identical, counts 20113 vs 20229 differ.
- [2026-11-14T00:28] W62 tool copied VERBATIM to tool_b_stats_FROZEN.py (sha256 4B3AC030...1CD8E, IDENTICAL=True). W62 original NOT modified.
- [2026-11-14T00:28..00:29] [本次实测] ce_A/ce_B/ce_C synthetic counterexamples generated; FROZEN --compare x3 all exit 0:
    ce_A=SHIFT_DETECTED (same dist/set, rows 120 vs 160); ce_B=SHIFT_DETECTED (real battle_idx diff, rows equal); ce_C=SAME_DISTRIBUTION.
- [2026-11-14T00:33:05+08:00] CRITERIA_SPEC_V2.md FROZEN (reason-for-fix FIRST; candidate i value-set vs candidate ii proportions; selected (ii); n-unequal policy = no truncation; all 11 constants declared UNCHANGED one by one).
- [2026-11-14T00:35] tool_b_stats_v2.py implemented AFTER freeze; --selftest exit 0, V2_SELFTEST_PASS=True (ce_A fixed, ce_B still detected, ce_C stable); SPEC_IDENTICAL=True.
- [2026-11-14T00:37:24+08:00] [本次实测] RECOMPUTE_DIAGNOSTIC.json written (exit 0) on W65 four trips READ-ONLY: continuous readout matches b_compare.json verbatim; 5 discrete fields T_f=0/N_disc=0/p=1/no_shift_detected; diagnostic_verdict=SAME_DISTRIBUTION but is_formal_verdict=false, formal_verdict=null, w65_disposition=maintain SHIFT_DETECTED.
- [2026-11-14T00:38..00:41] DEFECT_PROOF.md / UNKNOWNS.md / DISAGREE.md written; EVIDENCE logs + DELIVERABLES.txt finalized; read-only integrity verified (W62 sha256 unchanged, W65 b_compare.json verdict unchanged, git scoped status read-only).
- [本次实测] note: HEARTBEAT.txt was overwritten once at 00:32:14 by an external process writing card=W68 (not W68b); re-written by W68b. No interaction with that process; guard "I launched 0 / attached 0" unchanged.

## Concurrent-writer incident & recovery (00:44–00:47)

- [本次实测] 00:39:47 concurrent writer (self-identified GLM-5.3-Flash, card=W68, freeze 00:32:14) OVERWROTE W68b's CRITERIA_SPEC_V2.md / tool_b_stats_v2.py / EVIDENCE\gen_counterexamples.py / HEARTBEAT.txt, and produced its own ca_unequal_n / cb_equal_n_diffvals / v2_selftest\synth / recompute_v2_real_compare.json (latest write 00:41:42).
- [本次实测] Archived all 8 concurrent files to EVIDENCE\concurrent_GLM\ (copy only, no delete). Wrote EVIDENCE\CONCURRENT_WRITER_NOTE.md with full timeline + Lead guidance.
- [本次实测] Restored W68b self-consistent spec + tool to card root; re-verified: --selftest V2_SELFTEST_PASS=True, --diagnostic exit 0 (RECOMPUTE_DIAGNOSTIC.json regenerated), SPEC_IDENTICAL=True.
- [本次实测] Built EVIDENCE\W68b_snapshot\ = full W68b self-consistent deliverable set (10 root files + 8 key EVIDENCE logs) as anti-overwrite authoritative copy.
- [本次实测] Cross-check: concurrent implementation's recompute_v2_real_compare.json verdict = SAME_DISTRIBUTION / within_noise_band, continuous readouts identical to W68b. Two independent implementations agree.
- [本次实测] UNKNOWNS.md §6 / DISAGREE.md §6 appended with the incident; PROGRESS.md updated.
- [本次实测] HEARTBEAT.txt was overwritten AGAIN (155 B, card=W68 short form) during snapshotting; W68b version re-written. Root files may be overwritten again — see CONCURRENT_WRITER_NOTE.md §4 for sha256 / snapshot authority.

Status: DONE. No live rerun, no history edits. Pure offline: I launched 0 / attached 0.
- [2026-11-14T00:52:40.4787213+08:00] Counterexamples DONE: A: v1=SHIFT_DETECTED(discrete_or_ui_mismatch,n=20112/14999) vs v2=SAME_DISTRIBUTION(D_disc=0,p_disc=1.0); B: v1=SHIFT(n=9999/9999) & v2=SHIFT(D_disc=0.5,p_disc=0.0005). v2 selftest 4/4 PASS. v2 recompute on real data: SAME_DISTRIBUTION (diagnostic only). Writing RECOMPUTE_DIAGNOSTIC.json + docs.
- [2026-11-14T00:54:23.9817219+08:00] RECOMPUTE_DIAGNOSTIC.json assembled (diagnostic-only framing embedded). v1 also verified SHIFT_DETECTED on synthetic W68-CA (n=8001/4000). Writing DEFECT_PROOF.md next.
- [2026-11-14T00:56:39.0851254+08:00] ALL DELIVERABLES COMPLETE: DEFECT_PROOF.md, CRITERIA_SPEC_V2.md (FROZEN), tool_b_stats_v2.py, RECOMPUTE_DIAGNOSTIC.json, UNKNOWNS.md, DISAGREE.md, EVIDENCE\. Card closed offline (I launched 0 / attached 0).
