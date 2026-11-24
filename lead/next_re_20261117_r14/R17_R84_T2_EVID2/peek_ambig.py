#!/usr/bin/env python3
import os
LEAD=r"D:\Project\ra2-campaign-forge\lead"
rels=[
"next_re_20261117_r14/PROBE_UNNAMED_R2/EVIDENCE/poolstats_out.txt",
"next_re_20261117_r14/W173_layer_add/EVIDENCE/w173_selfaudit.txt",
"next_re_20261117_r14/W177-B/EVIDENCE/S0_baseline.txt",
"next_re_20261117_r14/P0_ADJ5/_audit/EVIDENCE/baseline_mine.txt",
"next_re_20261117_r14/S05_KPROVED2/_audit/EVIDENCE/holders_mine.json",
"next_re_20261117_r14/S05_KPROVED3/_audit/EVIDENCE/q9_baseline_mine.json",
"next_re_20261117_r14/S09_KPROVED5/_audit/EVIDENCE/ring2_recompute.json",
"next_re_20261117_r14/S09_KPROVED6/_audit/EVIDENCE/S7b_baseline.json",
"next_re_20261117_r14/S13_K8/_audit/EVIDENCE/ring3_audit.json",
"next_re_20261112_r02/W68_criterion_discrete_fix/EVIDENCE/concurrent_GLM/gen_counterexamples.stdout.txt",
"next_re_20261117_r14/S10_K5/_audit/EVIDENCE/a9_false_kill_sweep.txt",
"next_re_20261117_r14/S21_DIRECT/_audit/EVIDENCE/recs_enriched.json",
]
for rel in rels:
    p=os.path.join(LEAD,rel.replace("/",os.sep))
    print("="*80)
    print(rel)
    try:
        t=open(p,"rb").read(1500).decode("utf-8",errors="replace")
        print(t)
    except Exception as e:
        print("ERR",e)
