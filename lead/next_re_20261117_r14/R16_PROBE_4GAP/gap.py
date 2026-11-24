# -*- coding: utf-8 -*-
"""
R16-PROBE-4GAP —— ④ 缺口按「证据来源类别」重新普查（度量卡，不判 grade、不写 ④ 正文）。

两件事，一次跑完：
  §2.1 粗分桶：对 1,654 行 `[已证]` 逐行判第 4 列（one_line_semantics）里 ④ 的形态，
        给互斥分桶 + 缺口-严 / 缺口-宽 两个数。
  §2.2 按 M78 的 F1/F2/F3/F4（F4 再分子类）重新归属，用现盘数据核旧数。

口径（照卡面 §2.1 字面，不另立）：
  has_4_slot_witness  第 4 列含 `④ 活表槽位见证`
  has_4_direct_sites  第 4 列含形如 `④ … 直调` 的直调站点表述
  has_4_install_only  第 4 列含 `④ … 活 vt` / `安装点` / `构造安装`
  has_only_label      含 `③b④` 但上述三种都不含
  has_nothing         第 4 列完全不含 `④`
  ⇒ 卡面只列了 5 个旗，没覆盖「含 ④、三者都不是、也没有 ③b④」的那一档。
    本脚本把它单列成第 6 桶 has_4_other（不并进任何旗），否则分桶不互斥、加起来不等于 1,654。

缺口：
  缺口-严 = 1654 − (slot_witness + direct_sites + install_only)
  缺口-宽 = 1654 − (上述三者 + only_label)

来源类别：不重写分类器，import `D47_SURFACE/surface.py` 的 classify()（只读、只调函数，
其 __main__ 段不触发），取 form + reason。reason 即 F4 的四个子类。

跑法：
  python gap.py                 # 分桶 + 矩阵（写 gap.tsv / gap_detail.tsv / matrix.tsv / summary.json）
  python gap.py --scan          # 外加：对缺口里行数最多的 3 个类别做全量可派生性实扫
  python gap.py --scan-all      # 外加：对所有类别都扫（更慢）
只读：本脚本只写 R16_PROBE_4GAP\；sys.dont_write_bytecode=True，不留 .pyc。
"""
import sys

sys.dont_write_bytecode = True                   # 只读纪律：连 __pycache__ 都不落

import os
import re
import io
import json
import time
import hashlib
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
PANEL = os.path.join(R14, 'COVERAGE', 'PANEL.md')
COMMON = os.path.join(R14, 'R14_COMMON.md')
D47 = os.path.join(R14, 'D47_SURFACE')
PROBE802 = os.path.join(R14, 'PROBE_802')
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
PIN = os.path.join(HERE, '_pin_coverage.tsv')      # 读数快照（live 文件在并表期间会漂）

# 允许 --cov <path> 指定读数目标；默认用本目录的快照，没有快照才读 live。
for _i, _a in enumerate(sys.argv):
    if _a == '--cov' and _i + 1 < len(sys.argv):
        COV = sys.argv[_i + 1]
if COV == os.path.join(R14, 'COVERAGE', 'coverage.tsv') and os.path.isfile(PIN):
    COV = PIN
    _pinned = True
else:
    _pinned = (os.path.abspath(COV) == os.path.abspath(PIN))

GRADE_PROVED = '[已证]'

# ---------------------------------------------------------------- ④ 形态判定（§2.1）
# 每个 ④ 只判它自己所在的那个小句：窗口取 ④ 之后 100 字，遇到 ；;。 就截断，
# 免得「本行另一个 ④ 小句里的字」被算到这个 ④ 头上。
WINDOW = 100

RE_SLOT_WIT = re.compile(r'④\s*活表槽位见证')
# `④ … 直调`（卡面字面）。另把 `④direct E8` 单列成 sensitivity，不混进主线。
RE_DIRECT_CN = re.compile(r'^④[^；;。]{0,80}?直调')
RE_DIRECT_EN = re.compile(r'^④\s*direct\s*E8', re.I)
# `④ … 活 vt` / `安装点` / `构造安装`
RE_INSTALL = re.compile(r'^④[^；;。]{0,80}?(?:活\s*vt|安装点|构造安装)')
RE_LABEL = re.compile(r'③b④')


def clause(text, start):
    """取 ④ 起的小句：到 ；;。 为止，最多 WINDOW 字。"""
    w = text[start:start + WINDOW]
    m = re.search(r'[；;。]', w)
    return w[:m.start()] if m else w


def flags_of(sem):
    """返回该行第 4 列的 ④ 形态旗（按卡面字面）。"""
    f = dict(slot_witness=False, direct_sites=False, install_only=False,
             direct_en=False, n_ring4=0, other_heads=[])
    for m in re.finditer('④', sem):
        f['n_ring4'] += 1
        cl = clause(sem, m.start())
        if RE_SLOT_WIT.match(cl):
            f['slot_witness'] = True
        elif RE_DIRECT_CN.match(cl):
            f['direct_sites'] = True
        elif RE_DIRECT_EN.match(cl):
            f['direct_en'] = True           # 只作 sensitivity
            f['other_heads'].append(cl[:24])
        elif RE_INSTALL.match(cl):
            f['install_only'] = True
        else:
            f['other_heads'].append(cl[:24])
    return f


def bucket_of(f, sem):
    """互斥分桶，优先级 slot > direct > install > ③b④ label > other > nothing。"""
    if f['slot_witness']:
        return 'B1_slot_witness'
    if f['direct_sites']:
        return 'B2_direct_sites'
    if f['install_only']:
        return 'B3_install_only'
    if RE_LABEL.search(sem):
        return 'B4_only_label_3b'
    if f['n_ring4']:
        return 'B5_other_ring4_text'   # 有 ④ 字样，但不是使用见证（本卡新增的第 6 桶）
    return 'B6_nothing'


# `other` 桶再按「它到底是什么」分族——这是本卡新发现的死角所在
OTHER_FAMILY = [
    ('different_source_disclaimer', re.compile(r'④\s*不同源')),
    ('class_consistency_claim', re.compile(r'④\s*表属类与行名类一致')),
    ('dtor_trap_disclaimer', re.compile(r'④\s*锚点不在析构器')),
    ('ruling_reference', re.compile(r'④\s*，?§12\.3')),
    ('ctor_install_worded_other', re.compile(r'④\s*(?:构造器|行外\s*ctor|活\s*COM\s*类对象)')),
    ('loop_io_claim', re.compile(r'④\s*完整循环\s*I/O')),
    ('bare_addr_or_other', None),
]


def other_family(sem):
    for name, rx in OTHER_FAMILY:
        if rx is None:
            return name
        if rx.search(sem):
            return name
    return 'bare_addr_or_other'


# ---------------------------------------------------------------- 输入
def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def load_coverage():
    rows = []
    with io.open(COV, encoding='utf-8-sig') as fh:
        for i, ln in enumerate(fh):
            if i == 0:                            # 表头是逗号分隔（已知的坑），跳过
                continue
            c = ln.rstrip('\r\n').split('\t')
            if len(c) != 8:
                continue
            rows.append(dict(entry=c[0].strip().upper(), subsystem=c[1].strip(),
                             name=c[2], sem=c[3], grade=c[4], ev=c[5],
                             n_sources=c[6], conflict=c[7]))
    return rows


def source_classifier():
    """import D47 的 classify()（只读复用），不重写分类器。"""
    sys.path.insert(0, D47)
    import surface as S                            # noqa
    audit = S.load_audit_records()
    trace = S.load_census_trace()
    return S, audit, trace


def load_p802():
    """显式加载 PROBE_802/probe.py，注册成独立模块名 `p802`。

    注意：D47_SURFACE/work/ 里也有一个 probe.py，且 surface.py 已 `import probe`，
    所以 sys.modules['probe'] 是 D47 的那个。直接 `import probe` 会拿错模块
    （本卡第一版就踩了：AttributeError: no attribute 'sha256'）。
    """
    import importlib.util
    name = 'p802'
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(PROBE802, 'probe.py'))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- 主流程
def build():
    t0 = time.time()
    rows = load_coverage()
    proved = [r for r in rows if r['grade'] == GRADE_PROVED]
    S, audit, trace = source_classifier()

    for r in proved:
        f = flags_of(r['sem'])
        r.update(f)
        r['bucket'] = bucket_of(f, r['sem'])
        d = S.classify(r, audit, trace)
        r['f_form'] = d['form']
        r['f_reason'] = d['reason']
        r['source_class'] = d['form'] if d['form'] != 'F4' else 'F4:' + d['reason']
        if r['bucket'] == 'B5_other_ring4_text':
            r['other_family'] = other_family(r['sem'])

    n = len(proved)
    three = ('slot_witness', 'direct_sites', 'install_only')
    written = [r for r in proved if any(r[k] for k in three)]
    gap_strict = [r for r in proved if not any(r[k] for k in three)]
    gap_wide = [r for r in gap_strict if not RE_LABEL.search(r['sem'])]

    buckets = collections.Counter(r['bucket'] for r in proved)
    fams = collections.Counter(r.get('other_family') for r in proved
                               if r['bucket'] == 'B5_other_ring4_text')

    # ---- 来源类别 × 缺口矩阵
    classes = collections.OrderedDict()
    order = ['F1', 'F2', 'F3', 'F4:name_only_no_ring4', 'F4:census_no_ring4',
             'F4:no_ring4_described', 'F4:slot_pivot_not_stated_as_ring4']
    seen = collections.Counter(r['source_class'] for r in proved)
    for k in order:
        if seen.get(k):
            classes[k] = k
    for k in seen:
        if k not in classes:
            classes[k] = k

    matrix = []
    for k in classes:
        sub = [r for r in proved if r['source_class'] == k]
        m = dict(source_class=k, rows_now=len(sub),
                 ring4_written=sum(1 for r in sub if any(r[x] for x in three)),
                 gap_strict=sum(1 for r in sub if not any(r[x] for x in three)),
                 gap_wide=sum(1 for r in sub
                              if not any(r[x] for x in three)
                              and not RE_LABEL.search(r['sem'])),
                 slot_wit=sum(1 for r in sub if r['slot_witness']),
                 direct=sum(1 for r in sub if r['direct_sites']),
                 install=sum(1 for r in sub if r['install_only']),
                 label_only=sum(1 for r in sub if r['bucket'] == 'B4_only_label_3b'),
                 other4=sum(1 for r in sub if r['bucket'] == 'B5_other_ring4_text'),
                 sem_unproved=sum(1 for r in sub if '[未证]' in r['sem']),
                 in_atlas_hint='')
        matrix.append(m)

    # ---- 写 gap.tsv（卡面指定的 9 列，一字不改）
    with io.open(os.path.join(HERE, 'gap.tsv'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('entry\tsubsystem\tgrade\thas_4_slot_witness\thas_4_direct_sites\t'
                 'has_4_install_only\thas_only_label\thas_nothing\tsource_class\n')
        for r in proved:
            fh.write('%s\t%s\t%s\t%d\t%d\t%d\t%d\t%d\t%s\n' % (
                r['entry'], r['subsystem'], r['grade'],
                1 if r['slot_witness'] else 0,
                1 if r['direct_sites'] else 0,
                1 if r['install_only'] else 0,
                1 if r['bucket'] == 'B4_only_label_3b' else 0,
                1 if r['bucket'] == 'B6_nothing' else 0,
                r['source_class']))

    # ---- gap_detail.tsv：多给本卡实际判据（分桶、其他 ④ 的字面家族、④ 出现次数）
    with io.open(os.path.join(HERE, 'gap_detail.tsv'), 'w', encoding='utf-8',
                 newline='\n') as fh:
        fh.write('entry\tsubsystem\tbucket\tn_ring4\tother_family\tf_form\tf_reason\t'
                 'has_3b4\tsem_has_unproved\n')
        for r in proved:
            fh.write('%s\t%s\t%s\t%d\t%s\t%s\t%s\t%d\t%d\n' % (
                r['entry'], r['subsystem'], r['bucket'], r['n_ring4'],
                r.get('other_family', '-'), r['f_form'], r['f_reason'],
                1 if RE_LABEL.search(r['sem']) else 0,
                1 if '[未证]' in r['sem'] else 0))

    # ---- matrix.tsv
    with io.open(os.path.join(HERE, 'matrix.tsv'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('source_class\trows_now\tring4_written\tgap_strict\tgap_wide\t'
                 'slot_wit\tdirect\tinstall\tlabel_only\tother4\tsem_unproved\t'
                 'derivable_mechanism\tneed_new_evidence\n')
        for m in matrix:
            fh.write('%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%s\t%s\n' % (
                m['source_class'], m['rows_now'], m['ring4_written'], m['gap_strict'],
                m['gap_wide'], m['slot_wit'], m['direct'], m['install'],
                m['label_only'], m['other4'], m['sem_unproved'],
                MECHANISM.get(m['source_class'], 'TBD'), NEED.get(m['source_class'], 'TBD')))

    summary = dict(
        generated=time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        cov_sha256=sha256(COV), cov_bytes=os.path.getsize(COV),
        rows_total=len(rows), proved=n,
        buckets=dict(buckets),
        other_family=dict(fams),
        ring4_written=len(written),
        gap_strict=len(gap_strict), gap_wide=len(gap_wide),
        label_3b4_rows=sum(1 for r in proved if RE_LABEL.search(r['sem'])),
        direct_en_rows=sum(1 for r in proved if r['direct_en']),
        matrix=matrix,
        classes_total=len(classes),
        secs=round(time.time() - t0, 2),
    )
    with io.open(os.path.join(HERE, 'summary.json'), 'w', encoding='utf-8') as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1)

    # ---- 屏显
    print('coverage rows (data)   :', len(rows))
    print('[已证]                 :', n)
    print('--- 互斥分桶 ---')
    for k in sorted(buckets):
        print('  %-22s %5d  (%.2f%%)' % (k, buckets[k], 100.0 * buckets[k] / n))
    print('  %-22s %5d' % ('SUM', sum(buckets.values())))
    print('--- B5 other 的 ④ 字面家族（有 ④ 字样但不是使用见证）---')
    for k, v in fams.most_common():
        print('  %-30s %5d' % (k, v))
    print('--- 缺口 ---')
    print('  ring4_written (三旗任一) : %d' % len(written))
    print('  缺口-严                  : %d' % len(gap_strict))
    print('  缺口-宽                  : %d' % len(gap_wide))
    print('  ③b④ 行(全表[已证]内)     : %d'
          % sum(1 for r in proved if RE_LABEL.search(r['sem'])))
    print('  ④direct E8（sensitivity）: %d' % sum(1 for r in proved if r['direct_en']))
    print('--- 来源类别 × 缺口 ---')
    print('  %-34s %6s %6s %6s %6s' % ('class', 'rows', 'written', 'gapS', 'gapW'))
    for m in matrix:
        print('  %-34s %6d %6d %6d %6d' % (m['source_class'], m['rows_now'],
                                           m['ring4_written'], m['gap_strict'],
                                           m['gap_wide']))
    print('  %-34s %6d %6d %6d %6d' % ('TOTAL', sum(m['rows_now'] for m in matrix),
                                       sum(m['ring4_written'] for m in matrix),
                                       sum(m['gap_strict'] for m in matrix),
                                       sum(m['gap_wide'] for m in matrix)))
    print('secs                   :', summary['secs'])
    print('wrote gap.tsv / gap_detail.tsv / matrix.tsv / summary.json')
    return proved, gap_strict, gap_wide, matrix


# 机制 / 是否需新取证（结论文字，由 REPORT 展开；这里给矩阵列的可机读短文）
MECHANISM = {
    'F1': '④ 已在 AUDIT*/verdict.tsv 的 ring4_at 里（PASS + same_source=no），机械通道=转写；'
          '实扫 122 缺口行：108 有审计记录、76 的装表指令可解且装表点在 entry 体外',
    'F2': '④ 有独立于槽位的派发点/真实调用者；缺口 10 行是「有形态未成文」',
    'F3': '仅 direct call → D-40 判不足；无槽位/派发点通道',
    'F4:name_only_no_ring4': '名字侧无槽位；唯一机械通道=扫 .rdata dd entry→RTTI 定表→.text 体外装表点。'
                             '实扫 757：V1 0 / V2 0 / V3 2',
    'F4:census_no_ring4': '纯分类追踪（trace.source=vtable）；V1 215 但 215/215 与 ② 同一张表'
                          '（§12.3 ④② 同源判死），只剩 V3 1',
    'F4:no_ring4_described': '语义栏一句 ④ 都没写；机械通道同上；本卡未单独实扫（与上一类同形态）',
    'F4:slot_pivot_not_stated_as_ring4': '② 疑似就是那个槽 ⇒ §12.3 同源风险，需另找独立链',
}
NEED = {
    'F1': 'no-文档转写（76 行，≤1 张卡）', 'F2': 'marginal-10 行',
    'F3': 'yes-但已被 D-40 判死（direct 不算 ④）',
    'F4:name_only_no_ring4': 'yes-新取证已判死（实扫 2 行 / 757）',
    'F4:census_no_ring4': 'yes-已被 §12.3 判死（实扫 0–1 行 / 388）',
    'F4:no_ring4_described': 'yes-同 name_only 形态，预期同量级',
    'F4:slot_pivot_not_stated_as_ring4': 'yes-先解 ②/④ 同源，再谈 ④',
}


# ---------------------------------------------------------------- §2.3 可派生性实扫
def scan_f1_audit(proved):
    """F1 的机械可补通道与 F4 不同：它的 ④ 已经在 `NAMED_PUSH_AUDIT*/verdict.tsv` 的
    `ring4_at` 里了（D47 就是照那一列归的 F1），只是没转写进 coverage 的语义栏。
    所以这里不扫二进制，直接解 `ring4_at` 的锚点字节，判三件事：
      (a) 锚点是否真的解码成装表指令（MOV imm32 → .rdata vtable）；
      (b) 装表点是否在 entry **体外**（体内 = ctor 自己写 vptr，属 ②，不是 ④）；
      (c) 是否另有 dispatch / direct 站点（有则可升级为 F2，与槽解耦）。
    """
    S, audit, trace = source_classifier()
    P = load_p802()                                # 取 atlas size 判体内外
    atlas_sizes = P.load_atlas_sizes()

    sub = [r for r in proved if r['source_class'] == 'F1'
           and not any(r[x] for x in ('slot_witness', 'direct_sites', 'install_only'))]
    rows = []
    for r in sub:
        e = int(r['entry'], 16)
        size = atlas_sizes.get(r['entry'])
        body = (e, e + size) if size else None
        apath, rec = audit.get(r['entry'], ('-', {}))
        r4 = rec.get('ring4_at', '') or ''
        anch = S.anchors_in(r4, r['entry'])
        fm = S.forms(anch, r['entry'])
        installs = [a['va'] for a in anch
                    if a['kind'] == 'MOV_IMM' and a['info'].get('vt')]
        outside = [s for s in installs if not (body and body[0] <= s < body[1])]
        inside = [s for s in installs if body and body[0] <= s < body[1]]
        rows.append(dict(entry=r['entry'], subsystem=r['subsystem'], name=r['name'],
                         reason=r['f_reason'], verdict=rec.get('verdict', '-'),
                         same_source=rec.get('same_source', '-') or '-',
                         audit=os.path.basename(os.path.dirname(apath)) or '-',
                         n_anch=len(anch),
                         n_install=len(installs),
                         n_outside=len(outside),
                         n_inside=len(inside),
                         dispatch=1 if 'dispatch' in fm else 0,
                         direct=1 if 'direct' in fm else 0,
                         in_atlas=1 if size else 0,
                         sem_unproved=1 if '[未证]' in r['sem'] else 0,
                         r4=r4.replace('\t', ' ')))
    path = os.path.join(HERE, 'scan_F1_audit.tsv')
    with io.open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('entry\tsubsystem\tname\tf_reason\taudit_verdict\tsame_source\taudit_dir\t'
                 'n_anch\tn_install_decoded\tn_install_outside_body\tn_install_inside_body\t'
                 'has_dispatch\thas_direct\tin_atlas\tsem_unproved\tring4_at\n')
        for r in rows:
            fh.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%s\n' % (
                r['entry'], r['subsystem'], r['name'], r['reason'], r['verdict'],
                r['same_source'], r['audit'], r['n_anch'], r['n_install'], r['n_outside'],
                r['n_inside'], r['dispatch'], r['direct'], r['in_atlas'],
                r['sem_unproved'], r['r4']))
    agg = dict(source_class='F1', gap_rows=len(rows),
               has_audit_record=sum(1 for r in rows if r['audit'] != '-'),
               install_decoded=sum(1 for r in rows if r['n_install'] > 0),
               install_outside_body=sum(1 for r in rows if r['n_outside'] > 0),
               install_inside_only=sum(1 for r in rows
                                       if r['n_inside'] > 0 and r['n_outside'] == 0),
               has_dispatch=sum(1 for r in rows if r['dispatch']),
               has_direct=sum(1 for r in rows if r['direct']),
               no_anchor=sum(1 for r in rows if r['n_install'] == 0),
               in_atlas=sum(1 for r in rows if r['in_atlas']),
               sem_unproved=sum(1 for r in rows if r['sem_unproved']),
               clean_outside=sum(1 for r in rows
                                 if r['n_outside'] > 0 and not r['sem_unproved']),
               file=os.path.basename(path))
    print('[scan] F1 (审计表转写通道) n=%-4d 有审计记录 %-4d 解出装表指令 %-4d 体外装表 %-4d '
          '仅体内 %-3d dispatch %-2d direct %-3d 无锚 %-3d → %s'
          % (agg['gap_rows'], agg['has_audit_record'], agg['install_decoded'],
             agg['install_outside_body'], agg['install_inside_only'], agg['has_dispatch'],
             agg['has_direct'], agg['no_anchor'], agg['file']))
    return agg


def scan_classes(proved, matrix, topk=3, all_classes=False):
    """对指定类别做全量可派生性实扫，复用 PROBE_802 已验证的 analyze()/judge_real()。"""
    P = load_p802()                                # 只读复用，不重写扫描器

    sha = P.sha256(EXE)
    if sha != P.EXPECT_SHA:
        print('!! binary sha mismatch:', sha)
        return None
    atlas_sizes = P.load_atlas_sizes()
    img = P.Image(EXE)
    ts = P.TextScan(img)
    ranges = P.body_ranges(atlas_sizes)
    yrpp = P.load_yrpp_idents()
    bad = [(k, ts.direct.get(int(k, 16), 0), v) for k, v in P.ANCHORS.items()
           if ts.direct.get(int(k, 16), 0) != v]
    print('\n[scan] sha256 ok ; .text insns %d (skip %d) ; anchors %s ; YRpp idents %d'
          % (ts.n_insn, ts.n_skip,
             'OK 3/3' if not bad else 'MISMATCH %s' % bad, len(yrpp)))

    targets = [m['source_class'] for m in matrix if m['gap_strict']]
    targets.sort(key=lambda k: -[m['gap_strict'] for m in matrix
                                if m['source_class'] == k][0])
    if not all_classes:
        targets = targets[:topk]

    out = []
    for k in targets:
        if k == 'F1':
            # F1 的 ④ 已在审计表里，机械通道是「转写」不是「重扫二进制」
            out.append(scan_f1_audit(proved))
            continue
        sub = [r for r in proved if r['source_class'] == k and not any(
            r[x] for x in ('slot_witness', 'direct_sites', 'install_only'))]
        rows = []
        for r in sub:
            a = P.analyze(img, ts, r, atlas_sizes, ranges)
            v1, v2, v3, form, verdict, reason, anchored = P.judge_real(a, yrpp)
            rows.append(dict(entry=a['entry'], subsystem=a['subsystem'], name=a['name'],
                             vt_count=a['vt_count'], slot_no=a['slot_no'],
                             has_ext=1 if a['has_ext'] else 0,
                             v1=v1, v2=v2, v3=v3, form=form, verdict=verdict,
                             anchored=1 if anchored else 0,
                             direct=a['direct'], direct_v=a['direct_v'],
                             sem_unproved=1 if '[未证]' in a['sem'] else 0,
                             site=('%08X' % a['ext_inst'][0][1]) if a['ext_inst'] else '-',
                             reason=reason.replace('\t', ' ')))
        safe = re.sub(r'[^0-9A-Za-z_]+', '_', k).strip('_')
        path = os.path.join(HERE, 'scan_%s.tsv' % safe)
        with io.open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('entry\tsubsystem\tname\tvt_count\tslot_no\thas_ext\tV1\tV2\tV3\t'
                     'witness_form\tverdict\tanchored\tdirect\tdirect_v\tsem_unproved\t'
                     'install_site\treason\n')
            for r in rows:
                fh.write('%s\t%s\t%s\t%d\t%s\t%d\t%s\t%s\t%s\t%s\t%s\t%d\t%d\t%d\t%d\t%s\t%s\n' % (
                    r['entry'], r['subsystem'], r['name'], r['vt_count'], r['slot_no'],
                    r['has_ext'], r['v1'], r['v2'], r['v3'], r['form'], r['verdict'],
                    r['anchored'], r['direct'], r['direct_v'], r['sem_unproved'],
                    r['site'], r['reason']))
        agg = dict(source_class=k, gap_rows=len(rows),
                   V1=sum(1 for r in rows if r['v1'] == 'y'),
                   V1_anchored=sum(1 for r in rows if r['v1'] == 'y' and r['anchored']),
                   V1_unanchored=sum(1 for r in rows if r['v1'] == 'y' and not r['anchored']),
                   V2=sum(1 for r in rows if r['v2'] == 'y'),
                   V3=sum(1 for r in rows if r['v3'] == 'y'),
                   any_witness=sum(1 for r in rows if r['form'] != 'none'),
                   verdict_yes=sum(1 for r in rows if r['verdict'] == 'yes'),
                   verdict_risk=sum(1 for r in rows if r['verdict'] == 'risk'),
                   direct_gt0=sum(1 for r in rows if r['direct'] > 0),
                   direct_zero=sum(1 for r in rows if r['direct'] == 0),
                   sem_unproved=sum(1 for r in rows if r['sem_unproved']),
                   yes_and_clean=sum(1 for r in rows
                                     if r['verdict'] == 'yes' and not r['sem_unproved']),
                   sites_distinct=len(set(r['site'] for r in rows if r['site'] != '-')),
                   rows_exclusive_site=0,
                   file=os.path.basename(path),
                   yes_rows=[(r['entry'], r['name'], r['form']) for r in rows
                             if r['verdict'] == 'yes'])
        share = collections.Counter(r['site'] for r in rows if r['site'] != '-')
        agg['rows_exclusive_site'] = sum(1 for r in rows
                                         if r['site'] != '-' and share[r['site']] == 1)
        out.append(agg)
        print('[scan] %-34s n=%-5d V1 %-4d(锚定 %-3d) V2 %-3d V3 %-3d 任一 %-4d '
              'yes %-4d risk %-4d sem[未证] %-4d'
              % (k, agg['gap_rows'], agg['V1'], agg['V1_anchored'], agg['V2'],
                 agg['V3'], agg['any_witness'], agg['verdict_yes'],
                 agg['verdict_risk'], agg['sem_unproved']))
        print('       站点 distinct %d / 独占 %d ; 名义上限(yes) %d ; 干净 yes %d ; → %s'
              % (agg['sites_distinct'], agg['rows_exclusive_site'],
                 agg['verdict_yes'], agg['yes_and_clean'], agg['file']))
    with io.open(os.path.join(HERE, 'scan_summary.json'), 'w', encoding='utf-8') as fh:
        json.dump(dict(sha=sha, text_insns=ts.n_insn, anchors_ok=not bad,
                       yrpp_idents=len(yrpp), classes=out), fh,
                  ensure_ascii=False, indent=1)
    return out


if __name__ == '__main__':
    proved, gap_strict, gap_wide, matrix = build()
    if '--scan' in sys.argv:
        scan_classes(proved, matrix, topk=3,
                     all_classes=('--scan-all' in sys.argv))
