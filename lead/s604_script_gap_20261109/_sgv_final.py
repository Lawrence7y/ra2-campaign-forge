# -*- coding: utf-8 -*-
# _sgv_final.py —— 复核收尾：zip 截断变体等价性、台账vs真值符号计数、被核对象（调查回件 JSON）绑定指纹
# 路径统一经 safe_open 规范化并校验不越 BASE（零穿越；全部只读，输出仅 _sgv_final_out.txt）
import json, statistics, hashlib, re, os

BASE = os.path.normpath(r'D:\Project\ra2-campaign-forge')

def safe_open(rel, mode='rb'):
    rp = os.path.normpath(os.path.abspath(os.path.join(BASE, rel)))
    if not (rp == BASE or rp.startswith(BASE + os.sep)):
        raise PermissionError('path outside BASE: ' + rp)
    return open(rp, mode)

TRIPS = ['l1c_20261021', 'l1d_20261021', 'l1e_20261021', 'l3_20261021', 't55k_20261020']
WINDOWS = [(t, w) for t in TRIPS for w in (0, 1, 2)]

out_lines = []
def P(s=''):
    out_lines.append(s)
    print(s)

def num(tok):
    return float(tok.replace('*', '').replace('ms', '').replace('−', '-').strip())

def main():
    # 台账表
    with safe_open(r'lead\GOAL_THREE_TARGETS_20261018.md') as fh:
        lines = fh.read().decode('utf-8').splitlines()
    pat = re.compile(r'^\|\s*`(\w+)/w(\d)`\s*\|')
    TAB = {}
    for ln in lines[9705:9720]:
        m = pat.match(ln)
        cells = [c for c in ln.split('|')[1:-1]]
        TAB[(m.group(1), int(m.group(2)))] = tuple(num(c) for c in cells[1:6])

    per = {}
    for trip, w in WINDOWS:
        with safe_open(r'out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\%s\measure_w%d.json' % (trip, w)) as fh:
            d = json.loads(fh.read().decode('utf-8'))
        f = d['samples']['f']; t = d['samples']['t']
        edges = d['frame_edges']
        groups = {}
        for fi, ti in zip(f, t):
            groups.setdefault(fi, []).append(ti)
        fids = [e[0] for e in edges]
        et = {e[0]: e[1] for e in edges}
        n = len(fids)
        dur = {}; mg = {}
        for i, fid in enumerate(fids):
            ts = sorted(groups.get(fid, []))
            if len(ts) >= 2:
                mg[fid] = max(ts[j + 1] - ts[j] for j in range(len(ts) - 1))
            if i + 1 < n:
                dur[fid] = et[fids[i + 1]] - et[fid]
        fwd = {fids[i]: mg[fids[i + 1]] for i in range(n - 1) if fids[i] in mg and fids[i + 1] in mg}
        per[(trip, w)] = dict(fids=fids, dur=dur, mg=mg, fwd=fwd)

    def stats(ids, durmap, mgmap):
        k = len(ids) // 3; n = len(ids)
        fd = statistics.median([durmap[i] for i in ids[:k]]) * 1000.0
        sd = statistics.median([durmap[i] for i in ids[n - k:]]) * 1000.0
        fg = statistics.median([mgmap[i] for i in ids[:k]]) * 1000.0
        sg = statistics.median([mgmap[i] for i in ids[n - k:]]) * 1000.0
        return fd, fg, sd, sg

    P('[ZIP] zip 截断变体（帧0..n-2 时长配帧1..n-1 maxgap，末帧整体出局）vs C8a-wrap 同窗对照')
    identical = True
    hit2 = 0; hitd = 0
    for key in WINDOWS:
        r = per[key]
        pairs = [(r['dur'][r['fids'][i]], r['fwd'][r['fids'][i]], r['fids'][i])
                 for i in range(len(r['fids']) - 1)
                 if r['fids'][i] in r['dur'] and r['fids'][i] in r['fwd']]
        pairs.sort(key=lambda x: (x[0], x[2]))
        ids = [p[2] for p in pairs]
        fz, gz, sz, wz = stats(ids, r['dur'], r['fwd'])
        idsw = sorted([x for x in r['fids'] if x in r['dur'] and x in r['mg']],
                      key=lambda x: (r['dur'][x], x))
        mapw = dict(r['fwd'])
        if r['fids'][-1] in r['mg']:
            mapw[r['fids'][-1]] = r['mg'][r['fids'][-1]]
        fw, gw, sw, ww = stats(idsw, r['dur'], mapw)
        same = (abs(fz - fw) < 1e-12 and abs(gz - gw) < 1e-12 and
                abs(sz - sw) < 1e-12 and abs(wz - ww) < 1e-12)
        identical &= same
        td = TAB[key]
        hit2 += round(gz, 2) == td[1]; hit2 += round(wz, 2) == td[3]
        hitd += round(wz - gz, 3) == td[4]
        P('    %-16s zip-vs-wrap 逐位相同=%s  zip diff=%+.4f' % (key[0] + '/w' + str(key[1]), same, wz - gz))
    P('    zip 变体：两列 round2 命中 %d/30，diff round3 命中 %d/15，与 wrap 变体全部逐位相同=%s' % (hit2, hitd, identical))
    P('')

    P('[SIGN] 台账两列相对真值的单向性计数（机理句「15/15 抬高、13/15 压低」核对）')
    up = down = 0
    for key in WINDOWS:
        r = per[key]
        ids = sorted([x for x in r['fids'] if x in r['dur'] and x in r['mg']],
                     key=lambda x: (r['dur'][x], x))
        fd, fg, sd, sg = stats(ids, r['dur'], r['mg'])
        td = TAB[key]
        up += td[1] > fg
        down += td[3] < sg
    P('    台账快列 > 真值快列：%d/15 ；台账慢列 < 真值慢列：%d/15' % (up, down))
    P('')

    P('[BIND] 被核对象 = 调查回件 JSON（_sgv_reply_json.txt，逐字转写自任务书）')
    with safe_open(r'lead\s604_script_gap_20261109\_sgv_reply_json.txt') as fh:
        raw = fh.read()
    P('    被核对象 SHA256 = %s，字节数 = %d' % (hashlib.sha256(raw).hexdigest(), len(raw)))
    txt = raw.decode('utf-8')
    P('    首尾各 40 字符： %s ... %s' % (txt[:40], txt[-40:]))
    P('')
    P('[_sgv_final] END')
    with safe_open(r'lead\s604_script_gap_20261109\_sgv_final_out.txt', 'w') as fh:
        fh.write('\n'.join(out_lines) + '\n')

if __name__ == '__main__':
    main()
