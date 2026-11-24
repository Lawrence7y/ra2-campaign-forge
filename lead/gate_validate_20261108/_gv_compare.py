# -*- coding: utf-8 -*-
# _gv_compare.py —— 逐门禁「原 vs 修正」对照
# 配置逐字转录自 _gv_gates/<run8>.py 的检查项（对照表注明出处行）。
import json, pathlib, subprocess, sys

REPO = pathlib.Path('D:/Project/ra2-campaign-forge')
GV = REPO / 'lead' / 'gate_validate_20261108'
OUT = GV / '_gv_out'
CFG = OUT / 'cfg'
CFG.mkdir(exist_ok=True)

CONFIGS = {
  '01a1190d': dict(root='lead/n1_r2_verify_20261108', doc='N1_R2_ACCEPTANCE.md', sections=6,
                   elements=['绑定锚', '身份', '替代关系', '未验', 'ACCEPT'],
                   plain_fields=['acceptanceId', 'reviewerRole', 'reviewerSessionId', 'sourceTaskId',
                                 'inputHashes', 'artifactHashes', 'decision', 'unresolved', 'timestamp'],
                   min_bindings=1),
  '1552e9fe': dict(root='lead/bexec_n4_20261108', doc='B_EXECUTION_SPEC.md', sections=6,
                   elements=['调用边', '未验', 'APPROVE_SCOPE'],
                   plain_fields=['absent_both', 'vanished', 'new_first_appearance', 'new_write',
                                 'rewritten_same_content', 'leftover_unchanged'],
                   min_bindings=1),
  '1893d8fa': dict(root='lead/r2_final_grade_20261108', doc='R2_FINAL_GRADE.md', sections=6,
                   elements=['维度 A', '维度 B', '维度 C', '维度 D', '升格', '阻塞项', '未验', '不选判据'],
                   min_bindings=1),
  '1c93b364': dict(root='lead/dtrigger_round2_20261107', doc='CRITERIA_ROUND2.md', sections=8,
                   elements=[], min_bindings=4),
  '289e4267': dict(root='lead/five_read_n7_20261107', doc='FIVE_READ_COST_RECHECK.md', sections=6,
                   elements=['输入清单', '分母', '纳排', '双窗口', '未验'], min_bindings=1),
  '29dbbd2b': dict(root='lead/slowwindow_n8_20261108', doc='SLOW_WINDOW_LIMITS.md', sections=6,
                   elements=['帧级单位数', '节点数', '路径调用次数', '引擎阶段时间', '可识别', '未验', 'N-11'],
                   min_bindings=1),
  '2b4e006c': dict(root='lead/perf_repair_n11_20261108', doc='PERF_REPAIR_HANDOFF.md', sections=6,
                   elements=['HANDOFF_COMPLETE', '最小字段', '采集时机', '同图控制', '代价上限', 'N-10', '未验', '不放行采集'],
                   min_bindings=1),
  '324c613e': dict(root='lead/a_residual_n1_20261108', doc='A_RESIDUAL_REFERENCES.md', sections=6,
                   elements=['未验', '替代关系'],
                   plain_fields=['W9-2', 'W9-9', 'W9-19', 'W8-6', 'W8-11', 'W8-8', 'W8-7'],
                   json_records=dict(file='ACCEPTANCE_RECORDS.json',
                                     required=['itemId', 'reviewerRole', 'reviewerSessionId', 'sourceTaskId',
                                               'inputHashes', 'artifactHashes', 'decision', 'unresolved', 'timestamp']),
                   min_bindings=1),
  '40c7f252': dict(root='lead/d14_dual_20261107', doc='D14_DUAL_RECHECK.md', sections=6, elements=[],
                   plain_fields=['0.0395', '0.3461', '64 moving', '97'], min_bindings=1),
  '4285508a': dict(root='lead/static_spec_n9_20261107', doc='STATIC_COUNT_SPEC.md', sections=6,
                   elements=['读数时机', '未验'], plain_fields=['F6', 'F7', 'F8'], min_bindings=1),
  '4e0fdea9': dict(root='lead/slowframe_r3_20261108', doc='S604_GAP_RECHECK.md', sections=6,
                   elements=['空档', '慢1/3', '快1/3', '可引用', '不可引用', '未验', '不改台账'],
                   plain_fields=[':9724', ':9725'], min_bindings=1),
  '62a22c31': dict(root='lead/d13d14_cards_20261108', doc='DECISION_QUESTIONS.md', sections=6,
                   elements=['D-13', 'D-14', 'proposed', 'decided', 'BLOCKED', '双口径', '不实施采集', '不解除暂停', '未验'],
                   min_bindings=1),
  '673b3560': dict(root='lead/gate_validate_20261108', doc='GATE_TEMPLATE_REGRESSION.md', sections=6,
                   elements=['回归', '误报消除', '真违规', '未放松', '门禁数', '对照', '未验'], min_bindings=1),
  '858e5e0b': dict(root='lead/gate_template_20261108', doc='GATE_FALSE_POSITIVES.md', sections=6,
                   elements=['误报模式', '禁词子串', '措辞不匹配', '版本锚', '修正模板', '不可引用', '未验'],
                   tpl='GATE_TEMPLATE_FIXED.py.txt', min_bindings=1),
  'a05ccb49': dict(root='lead/r2_unclosed_b_20261108', doc='B_BREAKPOINTS_2_6.md', sections=6,
                   elements=['崩点2', '崩点3', '崩点4', '崩点5', '崩点6', '闭合', '未闭合', '未验', '不选判据'],
                   min_bindings=1),
  'a3231918': dict(root='lead/matrix_binding_20261108', doc='MATRIX_BINDING_FACTS.md', sections=6,
                   elements=['甲', '乙', '九 hunk', 'A—D', '预审', 'R3', '签发人', '不代决', '未验'],
                   plain_fields=['absent_both', 'vanished'], min_bindings=1),
  'aa9b3bc5': dict(root='lead/r2_unclosed_cd_20261108', doc='CD_BREAKPOINTS.md', sections=6,
                   elements=['emit', '9.7', '独立证成', 'B3', 'B4', '闭合', '未闭合', '未验', '不选判据'],
                   min_bindings=1),
  'c3fa20e3': dict(root='lead/slowframe_round2_20261107', doc='SLOWFRAME_PROXY.md', sections=6,
                   elements=[], min_bindings=1),
  'cd57bf1c': dict(root='lead/b2b_isolated_20261107', doc='INTEGRATION_REPORT.md', sections=6,
                   elements=[], min_bindings=1),
  'ce616060': dict(root='lead/deliverable_anchor_20261108', doc='ANCHOR_AND_DUALFILE_SPEC.md', sections=6,
                   elements=['版本锚', '双件并存', '绑定行', '现盘自身', '实例', '规范', '未验'], min_bindings=1),
  'eb56be4f': dict(root='lead/crash_diag_n6_20261107', doc='CRASH_DIAGNOSIS_HANDOFF.md', sections=6,
                   elements=['A5', 'P1', 'UAF', '正常退出', '新鲜性', '未验'], min_bindings=1),
  'fda7c34e': dict(root='lead/criteria_r3_verify_20261108', doc='R2_BREAKPOINTS_CLOSURE.md', sections=6,
                   elements=['维度 A', '维度 B', '维度 C', '维度 D', '闭合', '未闭合', '升格', '未验', '不选判据'],
                   min_bindings=1),
}

orig = {r['run8']: r for r in json.loads((OUT / '_gv_replay_original.json').read_text(encoding='utf-8'))}
lines = []
W = lines.append
rows = []
for run8, cfg in sorted(CONFIGS.items()):
    cpath = CFG / ('cfg_%s.json' % run8)
    cpath.write_text(json.dumps(cfg, ensure_ascii=False), encoding='utf-8')
    r = subprocess.run([sys.executable, '-I', '-X', 'utf8', str(GV / '_gv_fixed_rules.py'),
                        '--root', str(REPO / cfg['root']), '--doc', cfg['doc'],
                        '--config', str(cpath)], capture_output=True, timeout=600)
    stdout = r.stdout.decode('utf-8', 'replace').strip()
    try:
        fixed = json.loads(stdout)
    except Exception as e:
        fixed = {'ok': None, 'problems': ['RUNNER-ERROR: ' + str(e)[:100] + ' | ' + r.stderr.decode('utf-8', 'replace')[:200]], 'warnings': []}
    o = orig.get(run8, {})
    oprobs = o.get('problems') or []
    row = {
        'run8': run8,
        'domain': cfg['root'],
        'orig_ok': o.get('ok'), 'orig_exit': o.get('exit'), 'orig_problems': oprobs,
        'fixed_ok': fixed.get('ok'), 'fixed_problems': fixed.get('problems'),
        'fixed_n_warn': len(fixed.get('warnings') or []),
        'fixed_bindings': fixed.get('bindings'),
        'fixed_self_anchor': fixed.get('self_anchor'),
        'derived_copies': fixed.get('derived_copies'),
        'edge_hits': fixed.get('edge_hits'),
        'dual_files': fixed.get('dual_files'),
        'sections_found': fixed.get('sections_found'),
    }
    rows.append(row)
    W('%s | orig(ok=%s n=%d) -> fixed(ok=%s n=%d warn=%d)' % (
        run8, o.get('ok'), len(oprobs), fixed.get('ok'), len(fixed.get('problems') or []), row['fixed_n_warn']))
    for p in (fixed.get('problems') or []):
        W('    FIXED-PROBLEM %s' % json.dumps(p, ensure_ascii=False)[:200])

(OUT / '_gv_compare_out.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
(OUT / '_gv_compare.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')
print('\n'.join(lines))
print('--- rows written:', len(rows))
