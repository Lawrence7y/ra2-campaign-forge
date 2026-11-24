import os
BASE = r"D:\Project\ra2-campaign-forge"
REQ = {
 "lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md": [
  (254,271),(314,316),(318,322),(354,358),(364,368),(370,370),(386,400),
  (437,461),(463,466),(474,474),(534,551),(563,571),(588,592),(607,611),
  (615,620),(690,704),(711,718),(721,731),(758,764)],
 "lead/layer_identity_20261109/LAYER_IDENTITY.md": [
  (13,13),(22,22),(52,52),(87,87),(104,104),(110,110),(122,128),(189,189),
  (200,200),(223,224),(240,242),(267,267),(337,339),(365,365),(376,376),
  (384,384),(393,393),(400,400)],
 "lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md": [
  (21,24),(104,111),(124,124),(126,126),(290,290)],
 "lead/keff_calc_20261109/KEFF_CALC.md": [(262,262),(314,314),(340,340),(430,442)],
 "lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md": [(148,150),(294,294),(302,302),(310,310)],
 "lead/score_decomp_20261109/SCORE_DECOMP.md": [(233,235),(239,239)],
 "lead/comparability_20261109/COMPARABILITY_AUDIT.md": [(158,158)],
 "lead/layer_identity_20261109/_li_LAYER_IDENTITY_PROOF_20261109.md": [(78,78),(125,125),(146,146)],
 "lead/GOAL_THREE_TARGETS_20261018.md": [(9200,9200)],
}
for rel, ranges in REQ.items():
    p = os.path.join(BASE, rel)
    lines = open(p, encoding="utf-8").read().split("\n")
    print("##### " + rel)
    for lo, hi in ranges:
        for n in range(lo, hi + 1):
            if 1 <= n <= len(lines):
                t = lines[n - 1]
                if len(t) > 260:
                    t = t[:260] + " ...[截断]"
                print(f"{n:5d}| {t}")
    print()
