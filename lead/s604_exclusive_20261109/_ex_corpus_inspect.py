# -*- coding: utf-8 -*-
# _ex_corpus_inspect.py —— 语料结构体检（只读）：t 分辨率 / f 语义 / frame_edges 语义 / 窗间 f 是否重置
# 写域 = lead/s604_exclusive_20261109/。零真机、零采样代码。python -I -X utf8
import json, os, hashlib

BASE = os.path.normpath('D:/Project/ra2-campaign-forge')
CORPUS_REL = ('out', 're_work', 'work_chain', 'CONTINUE_20261003', 'lead', 'qc161_u0400_trip')
OUT_REL = ('lead', 's604_exclusive_20261109', '_ex_corpus_inspect_out.txt')

TRIPS = ['l1c_20261021', 'l1d_20261021', 'l1e_20261021', 'l3_20261021', 't55k_20261020']

out_lines = []
def P(s=''):
    out_lines.append(s)
    print(s)

def safe_open(rel_parts, mode='rb', **kw):
    rp = os.path.normpath(os.path.abspath(os.path.join(BASE, *rel_parts)))
    if not (rp == BASE or rp.startswith(BASE + os.sep)):
        raise PermissionError('path outside BASE: ' + rp)
    return open(rp, mode, **kw)

def main():
    for trip in TRIPS:
        for w in (0, 1, 2):
            with safe_open(list(CORPUS_REL) + [trip, 'measure_w%d.json' % w]) as fh:
                raw = fh.read()
            d = json.loads(raw.decode('utf-8'))
            t = d['samples']['t']; f = d['samples']['f']
            edges = d['frame_edges']
            top_keys = sorted(d.keys())
            n = len(t)
            # t 分辨率：相邻样本 t 差的最小非零值
            diffs = [t[i+1] - t[i] for i in range(n - 1)]
            pos = [x for x in diffs if x > 0]
            min_pos = min(pos) if pos else None
            # f 的 min/max；f 与 edges 起点的关系
            fmin, fmax = min(f), max(f)
            efids = [e[0] for e in edges]
            e0, e1 = edges[0], edges[-1]
            # 边界样本计数：t 恰好等于某个 edge 起点的样本数（bisect 变体的边界效应量级）
            edge_ts = set(e[1] for e in edges)
            n_hit = sum(1 for x in t if x in edge_ts)
            # 每帧样本数分布（首帧/末帧）
            groups = {}
            for fi, ti in zip(f, t):
                groups.setdefault(fi, []).append(ti)
            gsizes = [len(groups.get(fid, [])) for fid in efids]
            P(f'{trip}/w{w}: top_keys={top_keys}')
            P(f'  n_samp={n} f范围=[{fmin},{fmax}] edges数={len(edges)} edges首fid={e0[0]} 末fid={e1[0]} '
              f'edges首t={e0[1]!r} 末t={e1[1]!r}')
            P(f'  t[0]={t[0]!r} t[1]={t[1]!r} t[-1]={t[-1]!r}  min相邻差={min_pos!r}')
            P(f'  f是否从0连续: {fmin == 0 and fmax == len(edges) - 1}  '
              f't恰等edge起点样本数={n_hit}  帧样本数min={min(gsizes)} max={max(gsizes)}')
            P(f'  sha256={hashlib.sha256(raw).hexdigest()[:16]}… bytes={len(raw)}')
    P('[_ex_corpus inspect] END')
    with safe_open(OUT_REL, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out_lines) + '\n')

if __name__ == '__main__':
    main()
