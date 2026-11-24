#!/usr/bin/env python3
"""R94-T1 轮次窗口独立重推（执行员 win_t1.py）。

输入全部只读：
  lead/next_re_20261117_r14/R17_LEAD_BASELINE/STATUS_BOARD.before_rNN_HHMMSS.md
  lead/next_re_20261117_r14/_cards/R<NN>-T<N>-*.md
输出只写：
  lead/next_re_20261117_r14/_r94/_exec/win_t1.{py,json,log}
"""
import hashlib
import json
import os
import random
import re
import statistics
import sys
from datetime import datetime, timedelta, timezone

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
CARDS = os.path.join(R14, '_cards')
OUT = os.path.join(R14, '_r94', '_exec')
DATE = '2026-11-22'
TZ = timezone(timedelta(hours=8))
SNAP_RE = re.compile(r'^STATUS_BOARD\.before_r(\d+)_(\d{6})\.md$')
CARD_RE = re.compile(r'^R(\d+)-T(\d+)-.+\.md$')

PROTECTED = [
    os.path.join(R14, 'check_disc.py'),
    os.path.join(R14, 'recheck_verify.py'),
    os.path.join(R14, 'DISC_RECHECK.tsv'),
    os.path.join(R14, 'R14_COMMON.md'),
    os.path.join(R14, 'STATUS_BOARD.md'),
    os.path.join(R14, 'BOARD_ARCHIVE.md'),
    os.path.join(ROOT, 'lead', 'LEAD_LOCK'),
    os.path.join(ROOT, 'lead', 'LEDGER'),
    os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
]

LOG = []
CHECKS = []


def emit(s):
    LOG.append(str(s))
    print(s)


def flush_log():
    with open(os.path.join(OUT, 'win_t1.log'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(LOG) + '\n')


def die(reason):
    emit('FAIL: ' + reason)
    flush_log()
    sys.exit(1)


def check(cond, label):
    CHECKS.append({'label': label, 'pass': bool(cond)})
    if not cond:
        die('assertion failed: ' + label)


def sha256(path):
    if not os.path.isfile(path):
        return 'MISSING'
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def hhmmss_to_dt(s):
    y, mo, d = [int(x) for x in DATE.split('-')]
    hh, mm, ss = int(s[0:2]), int(s[2:4]), int(s[4:6])
    return datetime(y, mo, d, hh, mm, ss, tzinfo=TZ)


def iso(dt):
    return dt.isoformat()


def snapshot_scan():
    """解析主快照：只认严格 STATUS_BOARD.before_rNN_HHMMSS.md，排除 _add/_add2 等变体。"""
    raw = []
    for name in os.listdir(BASE):
        m = SNAP_RE.match(name)
        if m:
            raw.append({'round': int(m.group(1)), 'hhmmss': m.group(2),
                        'dt': hhmmss_to_dt(m.group(2)), 'file': name})
    raw.sort(key=lambda x: (x['round'], x['hhmmss']))
    by_round = {}
    for r in raw:
        by_round.setdefault(r['round'], []).append(r)
    # T(N) 取该轮最早的主快照时刻，与 recheck_verify.py 对 r56 的取法一致。
    tmap = {n: min(v, key=lambda x: x['hhmmss'])['dt'] for n, v in by_round.items()}
    return raw, by_round, tmap


def card_scan():
    cards = []
    for name in os.listdir(CARDS):
        m = CARD_RE.match(name)
        if not m:
            continue
        st = os.stat(os.path.join(CARDS, name))
        cards.append({'name': name, 'round': int(m.group(1)),
                      'task': int(m.group(2)),
                      'mtime': datetime.fromtimestamp(st.st_mtime, TZ)})
    cards.sort(key=lambda x: (x['round'], x['task'], x['name']))
    return cards


def in_window(dt, start, end):
    """左闭右开 [start, end)。"""
    return start <= dt < end


def old_window(tmap, k):
    """旧语义 窗口(K) = [T(K), T(K+1))；缺端点返回 None。"""
    if k in tmap and k + 1 in tmap:
        return (tmap[k], tmap[k + 1])
    return None


def new_window(tmap, k):
    """新语义 窗口(K) = [T(K-1), T(K))；缺端点返回 None。"""
    if k - 1 in tmap and k in tmap:
        return (tmap[k - 1], tmap[k])
    return None


def count_hits(cards, tmap, window_fn, rounds_override=None):
    hits = 0
    judgeable = 0
    detail = []
    for c in cards:
        n = rounds_override[c['name']] if rounds_override else c['round']
        w = window_fn(tmap, n)
        if w is None:
            detail.append({'name': c['name'], 'round': n, 'judgeable': False, 'hit': False})
            continue
        judgeable += 1
        hit = in_window(c['mtime'], w[0], w[1])
        if hit:
            hits += 1
        detail.append({'name': c['name'], 'round': n, 'judgeable': True, 'hit': hit})
    return hits, judgeable, detail


def shifted_card(cards, tmap):
    """反控 a：挑一张 H_NEW 当前命中且 +10 分钟会走出窗口的卡，只在内存里偏移。"""
    target = None
    for c in cards:
        w = new_window(tmap, c['round'])
        if w is not None and in_window(c['mtime'], w[0], w[1]) \
                and not in_window(c['mtime'] + timedelta(minutes=10), w[0], w[1]):
            if target is None or c['mtime'] > target['mtime']:
                target = c
    if target is None:
        return None
    sh = {c['name']: c['mtime'] + timedelta(minutes=10) if c['name'] == target['name']
          else c['mtime'] for c in cards}
    return {'name': target['name'], 'round': target['round'],
            'before': iso(target['mtime']), 'after': iso(target['mtime'] + timedelta(minutes=10)),
            'window': [iso(x) for x in new_window(tmap, target['round'])],
            'hits_override': sh}


def main():
    os.makedirs(OUT, exist_ok=True)
    emit('=== R94-T1 轮次窗口独立重推 ===')

    sha_before = {p: sha256(p) for p in PROTECTED}

    raw, by_round, tmap = snapshot_scan()
    emit('[1] 主快照序列（非 _add，严格 STATUS_BOARD.before_rNN_HHMMSS.md），逐条：')
    for r in raw:
        emit('    R%-3d %s  %s' % (r['round'], r['hhmmss'], r['file']))
    emit('主快照序列条数 = %d' % len(raw))
    emit('去重后轮次数 = %d' % len(by_round))
    dups = {str(n): [x['hhmmss'] for x in v] for n, v in sorted(by_round.items()) if len(v) > 1}
    emit('同轮多快照（T(N) 取最早）= %s' % json.dumps(dups, sort_keys=True))

    cards = card_scan()
    card_rounds = sorted(set(c['round'] for c in cards))
    emit('[2] 卡片目录解析：卡条数 = %d，轮次数 = %d' % (len(cards), len(card_rounds)))
    emit('    卡片轮次 = %s' % ' '.join('R%d' % n for n in card_rounds))

    # 正控 1：T(N) 与 recheck_verify.py 硬编码表锚点一致（r35/r55/r56/r57）。
    anchors = {35: '112234', 55: '174146', 56: '174645', 57: '174854'}
    anchor_ok = all(tmap.get(n) is not None and tmap[n] == hhmmss_to_dt(s)
                    for n, s in anchors.items())
    check(anchor_ok, 'positive-control T(N) matches recheck_verify.py anchors r35/r55/r56/r57')

    # [3] 位移剖面：delta -3..+3，旧语义窗口(N+delta) = [T(N+delta), T(N+delta+1))
    profile = {}
    for delta in range(-3, 4):
        n_hit = 0
        for c in cards:
            w = old_window(tmap, c['round'] + delta)
            if w is not None and in_window(c['mtime'], w[0], w[1]):
                n_hit += 1
        profile[str(delta)] = n_hit
    emit('[3] 位移剖面（旧语义窗口，delta=-3..+3）：%s' % json.dumps(profile, sort_keys=True))

    # [4] 两种语义的可判定与命中
    h_old_hits, h_old_judg, h_old_detail = count_hits(cards, tmap, old_window)
    h_new_hits, h_new_judg, h_new_detail = count_hits(cards, tmap, new_window)
    emit('[4] H_OLD 可判定卡数 = %d，命中数 = %d' % (h_old_judg, h_old_hits))
    emit('    H_NEW 可判定卡数 = %d，命中数 = %d' % (h_new_judg, h_new_hits))
    emit('    H_OLD 命中率 = %.4f，H_NEW 命中率 = %.4f' %
         (h_old_hits / h_old_judg if h_old_judg else 0.0,
          h_new_hits / h_new_judg if h_new_judg else 0.0))

    # 正控 2：与 R86 独立结论一致（峰值 delta=-1，delta=0 未命中）。
    check(max(profile, key=lambda k: profile[k]) == '-1',
          'positive-control delta profile peak at -1')
    check(profile['0'] == 0, 'positive-control delta=0 has zero hits')
    check(profile['-1'] == h_new_hits,
          'positive-control delta=-1 count equals H_NEW hits')

    # [5a] 反控 a：+10 分钟
    shift = shifted_card(cards, tmap)
    if shift is None:
        die('counterfactual a: no H_NEW matching card can be shifted out by +10min')
    shifted_hits = 0
    for c in cards:
        mt = shift['hits_override'][c['name']]
        w = new_window(tmap, c['round'])
        if w is not None and in_window(mt, w[0], w[1]):
            shifted_hits += 1
    emit('[5a] 反控 a：选取 %s (R%d)，mtime %s -> %s，窗口 %s' %
         (shift['name'], shift['round'], shift['before'], shift['after'],
          shift['window']))
    emit('     H_NEW 命中数 %d -> %d（下降 %d）' %
         (h_new_hits, shifted_hits, h_new_hits - shifted_hits))
    check(shifted_hits < h_new_hits, 'counterfactual a: +10min decreases H_NEW hits')

    # [5b] 反控 b：随机置换卡与轮次配对 200 次
    rnd = random.Random(94101117)
    round_pool = [c['round'] for c in cards]
    shuffled_hits = []
    for _ in range(200):
        perm = round_pool[:]
        rnd.shuffle(perm)
        ov = {c['name']: perm[i] for i, c in enumerate(cards)}
        h, _, _ = count_hits(cards, tmap, new_window, rounds_override=ov)
        shuffled_hits.append(h)
    hist = {}
    for h in shuffled_hits:
        hist[str(h)] = hist.get(str(h), 0) + 1
    emit('[5b] 反控 b：200 次随机置换，H_NEW 命中数 min=%d max=%d mean=%.3f median=%.1f' %
         (min(shuffled_hits), max(shuffled_hits), statistics.mean(shuffled_hits),
          statistics.median(shuffled_hits)))
    emit('     分布(命中数:次数) = %s' % json.dumps(hist, sort_keys=True))
    check(max(shuffled_hits) < h_new_hits,
          'counterfactual b: all 200 shuffles below baseline H_NEW hits')

    # [5c] 反控 c：全部当 R55
    single_round = 55
    ov = {c['name']: single_round for c in cards}
    h_single, j_single, _ = count_hits(cards, tmap, new_window, rounds_override=ov)
    rate = h_single / len(cards) if cards else 0.0
    emit('[5c] 反控 c：全部当 R55，H_NEW 命中 %d/%d，命中率 = %.6f（窗口 %s）' %
         (h_single, len(cards), rate,
          [iso(x) for x in new_window(tmap, single_round)]))
    check(h_single > 0 and h_single < h_new_hits,
          'counterfactual c: single-round baseline is nonzero but below full H_NEW hits')

    # [6] 缺端点轮次清单
    snap_rounds = set(tmap.keys())
    unjudg = {'H_OLD': [], 'H_NEW': []}
    for n in card_rounds:
        if old_window(tmap, n) is None:
            reason = []
            if n not in snap_rounds:
                reason.append('T(%d) absent' % n)
            if n + 1 not in snap_rounds:
                reason.append('T(%d) absent (needs forward endpoint)' % (n + 1))
            unjudg['H_OLD'].append({'round': n, 'reason': '; '.join(reason)})
        if new_window(tmap, n) is None:
            reason = []
            if n - 1 not in snap_rounds:
                reason.append('T(%d) absent (needs backward endpoint)' % (n - 1))
            if n not in snap_rounds:
                reason.append('T(%d) absent' % n)
            unjudg['H_NEW'].append({'round': n, 'reason': '; '.join(reason)})
    missing_snap = [n for n in range(min(snap_rounds), max(card_rounds) + 1)
                    if n not in snap_rounds]
    emit('[6] 缺端点轮次清单：')
    emit('     H_OLD 不可判定卡轮次 = %s' % json.dumps(unjudg['H_OLD'], sort_keys=True))
    emit('     H_NEW 不可判定卡轮次 = %s' % json.dumps(unjudg['H_NEW'], sort_keys=True))
    emit('     快照序列在 [35..94] 区间缺失的轮次 = %s' %
         json.dumps(missing_snap))
    emit('     r41 无主快照：H_OLD 窗口(40)、H_NEW 窗口(42) 及窗口(41) 本身均无法判定；未填补。')

    sha_after = {p: sha256(p) for p in PROTECTED}
    sha_equal = (sha_before == sha_after)
    emit('[7] live 文件 sha256 前后对比：')
    for p in PROTECTED:
        emit('     %s  %s  %s' % (sha_before[p], 'SAME' if sha_before[p] == sha_after[p] else 'CHANGED', p))
    check(sha_equal, 'protected live files unchanged (sha256 before == after)')

    payload = {
        'meta': {
            'card': 'R94-T1-WINDOW.md',
            'role': 'exec',
            'family': 'hy4',
            'date_assumed': DATE,
            'tz_offset_hours': 8,
            'main_snapshot_rule': 'STATUS_BOARD.before_rNN_HHMMSS.md only; _add/_add2 excluded; T(N)=earliest snapshot of round N',
        },
        'main_snapshot_sequence': [
            {'round': r['round'], 'hhmmss': r['hhmmss'], 'file': r['file'],
             'datetime': iso(r['dt'])} for r in raw
        ],
        'main_snapshot_count': len(raw),
        'distinct_snapshot_round_count': len(by_round),
        'duplicate_rounds': dups,
        'T_map': {str(n): iso(tmap[n]) for n in sorted(tmap)},
        'cards': [
            {'name': c['name'], 'round': c['round'], 'mtime': iso(c['mtime'])}
            for c in cards
        ],
        'card_count': len(cards),
        'card_round_count': len(card_rounds),
        'card_rounds': card_rounds,
        'delta_profile': profile,
        'judgeable': {'H_OLD': h_old_judg, 'H_NEW': h_new_judg},
        'hits': {'H_OLD': h_old_hits, 'H_NEW': h_new_hits},
        'counterfactuals': {
            'a_shift_plus_10min': {
                'card': shift['name'], 'round': shift['round'],
                'before': shift['before'], 'after': shift['after'],
                'window': shift['window'],
                'hits_before': h_new_hits, 'hits_after': shifted_hits,
                'drop': h_new_hits - shifted_hits,
            },
            'b_shuffle_200': {
                'trials': 200, 'min': min(shuffled_hits), 'max': max(shuffled_hits),
                'mean': statistics.mean(shuffled_hits),
                'median': statistics.median(shuffled_hits), 'histogram': hist,
                'baseline_h_new': h_new_hits,
            },
            'c_single_round_55': {
                'round': single_round, 'hits': h_single, 'cards': len(cards),
                'rate': rate, 'judgeable': j_single,
                'window': [iso(x) for x in new_window(tmap, single_round)],
            },
        },
        'missing_endpoint_rounds': {
            'unjudgeable_by_card_round': unjudg,
            'snapshot_absent_in_35_94': missing_snap,
            'note': 'r41 has no main snapshot; no gap was filled',
        },
        'sha256_before': sha_before,
        'sha256_after': sha_after,
        'sha256_equal': sha_equal,
        'checks': CHECKS,
    }
    with open(os.path.join(OUT, 'win_t1.json'), 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')
    emit('[8] 全部断言通过：%d 项；已写 win_t1.json / win_t1.log' % len(CHECKS))
    emit('结论：未改动任何 live 文件，sha256 前后完全一致。')
    flush_log()


if __name__ == '__main__':
    main()
