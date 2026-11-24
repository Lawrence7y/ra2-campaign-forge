# -*- coding: utf-8 -*-
# 终稿轮自验（1/3）：八件上游指纹 + 诊断轮 10 证据件绑定重验 + 被核稿双件 + 漂移抽查。
# 只读（drift 抽查为单层 glob，无递归）；hashlib 实算；产出 _siw_verify_out.txt。
import hashlib, json, pathlib, time

R = pathlib.Path('D:/Project/ra2-campaign-forge')
WD = R / 'lead/gate_subject_id_20261109'
t0 = time.perf_counter()
lines = []
fails = []

def fp(rel, exp_sha, exp_n, tag):
    p = R / rel
    if not p.is_file():
        lines.append('[%s] %-88s MISSING' % (tag, rel))
        fails.append(rel)
        return
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    n = len(b)
    ok = (h == exp_sha and n == exp_n)
    lines.append('[%s] %-88s %s %8d B  %s' % (tag, rel, h, n, 'OK' if ok else 'DRIFT! exp=%s/%d' % (exp_sha, exp_n)))
    if not ok:
        fails.append(rel)

UP = [
    ('lead/counterpart_fix_20261109/COUNTERPART_FIX.md', 'e291f5a8f8b2c303b31e7f06989233e122460d9838817271fa425cae066ff416', 32830),
    ('lead/counterpart_fix_20261109/_cf_counterpart_vs_tighten_20261109.md', '9878bb7ec170599dd8d74eacfa0a7be0806294d91d8be994a456ad6ed864ddb4', 32840),
    ('lead/strict_exposure_20261109/STRICT_EXPOSURE.md', '3a4b1bb7cf7f0bd501b3e99d575c4907dd0e17f5557dd0b8826e5fb07fe2bdc8', 23798),
    ('lead/u5u6_mirror_20261109/U5U6_MIRROR_TEXTS.md', 'f320a80110806e6b57281988085d40776b43e719123db29cdb6564fe68c6c545', 24897),
    ('lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md', '823476680c4c7aab7ead279a3f47724dbd1b2fed977087ae86c35a4eef36258c', 30536),
    ('lead/text_fix_unified_20261109/UNIFIED_TEXT_FIX.md', 'ec0fb8ec47cfb71be5b28bc8a76f9152a6cbd377e741e7be1902a0958fbba154', 42172),
    ('lead/PENDING_DECISIONS.md', '3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7', 52419),
    ('lead/GOAL_THREE_TARGETS_20261018.md', '2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede', 759518),
]
EV = [
    ('lead/gate_subject_id_20261109/_si_scan_out.json', '4ba1c43e576989e624e986b4ead34aba7eface4b47a5e7c9e14ace59fc352f85', 180681),
    ('lead/gate_subject_id_20261109/_si_fp_out.txt', 'e27d1f54282611c3f71f59b79399e72cefff6e67aeaf9e76131bc3e95c576ece', 10565),
    ('lead/gate_subject_id_20261109/_si_gatescan_out.json', 'c8024cb7e538dfbc3766acc08d231789b80d601d7cc4bba4e05ed89d8ff87d94', 611043),
    ('lead/gate_subject_id_20261109/_si_wfscan_out.json', 'e326df6b4040dc9e5471f891c8db55d8ede1681434336de5e5626c43e2029f52', 180256),
    ('lead/gate_subject_id_20261109/_si_gatecensus_out.json', '44ca323a505cad7cdcae4297baff260f57f76173474f5e996ccf84d70e68966d', 11870),
    ('lead/gate_subject_id_20261109/_si_wfextract_out.txt', '4167956c3d5f6ae68656bce60c053d1ab09de95059cf7d269e33f914df6217d1', 45230),
    ('lead/gate_subject_id_20261109/_si_gate_counterpart_extracted.py', 'b25c8c40c2ad484abb473b28145fd3a5e6a02d790aa526fb9baae28d62ce0939', 2281),
    ('lead/gate_subject_id_20261109/_si_gate_self_extracted.py', '83a81c084e1f2df5d997d125a0f6d26f445d077abee62355b2f8c9989eea82ec', 1402),
    ('lead/gate_subject_id_20261109/_si_exploit_out.txt', '151f4f94b890403ba4785a7d570ad11abbe68a4aa12363967682729167e2c587', 5717),
    ('lead/gate_subject_id_20261109/_si_fix_lib.py', '54751e9a10bca4becfae3449d4a19155dc7744dff77a8a22d7d70d9a7fd70eee', 2850),
]
DRAFT_SHA = '8c67dc3fc950baf16e4e39b650ca25210e24e3512307a09eaf30cc9cecd6f4dc'

lines.append('== A. 八件上游指纹（编排方派发常量 vs 本轮 hashlib 实算）==')
for rel, s, n in UP:
    fp(rel, s, n, 'UP')
lines.append('')
lines.append('== B. 诊断轮 10 证据件绑定行现值重验（被核稿 §5.1 所载哈希 vs 现算）==')
for rel, s, n in EV:
    fp(rel, s, n, 'EV')
lines.append('')
lines.append('== C. 被核稿双件（复核回件绑定行对象）==')
for nm in ['GATE_SUBJECT_ID_FIX.md', '_si_SUBJECT_ID_DEFECT.md']:
    fp('lead/gate_subject_id_20261109/' + nm, DRAFT_SHA, 23441, 'DR')
lines.append('')
lines.append('== D. 漂移抽查（复核回件所称 06:34/06:36 落主件两域 + 07 时点新进 3 域；单层 glob）==')
for d in ['lead/handoff_pack_20261109', 'lead/s604_script_hunt_20261109',
          'lead/c07_protocol_attacks_20261109', 'lead/oldwording_sweep_20261109',
          'lead/s604_verdict_entry_20261109']:
    p = R / d
    if not p.is_dir():
        lines.append('[DR] %-46s 目录不存在' % d)
        continue
    mds = sorted(p.glob('*.md'))
    items = [(m.name, m.stat().st_size) for m in mds]
    mx = max(items, key=lambda x: x[1])[0] if items else '(无 md)'
    bare = [n for n, _ in items if not n.startswith('_')]
    lines.append('[DR] %-46s md=%d max=%s maxIsUnderscore=%s bareCount=%d' % (
        d, len(items), mx, str(mx.startswith('_')), len(bare)))
    for n, sz in items:
        lines.append('      - %-52s %8d B' % (n, sz))
elapsed = time.perf_counter() - t0
lines.append('')
lines.append('SUMMARY: upstreamOK=%d/8 evidenceOK=%d/10 draftsOK=%d/2 fails=%s' % (
    8 - sum(1 for r in fails if r.startswith(('lead/c', 'lead/u', 'lead/s6', 'lead/t', 'lead/P', 'lead/G'))),
    10 - sum(1 for r in fails if '_si_' in r), 2 - sum(1 for r in fails if 'DEFECT' in r or r.endswith('FIX.md')), fails))
lines.append('dirsVisited=0（无 walk；仅指定文件 stat/read + 5 域单层 glob）elapsedSec=%.3f' % elapsed)
out = '\n'.join(lines) + '\n'
(WD / '_siw_verify_out.txt').write_text(out, encoding='utf-8')
print(out)
