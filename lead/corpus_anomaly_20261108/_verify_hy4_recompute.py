# -*- coding: utf-8 -*-
"""_verify_hy4_recompute.py - independent re-verification (语料归因复核员·hy4) 2026-11-08.
Read-only on corpus; writes only _verify_* files in lead/corpus_anomaly_20261108/.
"""
import hashlib, json, os, struct, zlib, collections, glob, datetime
from statistics import median

ROOT = os.path.normcase(os.path.realpath('D:/Project/ra2-campaign-forge'))
TRIP = os.path.join(ROOT, 'out', 're_work', 'work_chain', 'CONTINUE_20261003',
                   'lead', 'qc161_u0400_trip')
W = os.path.join(ROOT, 'lead', 'corpus_anomaly_20261108')
PROXY = os.path.join(ROOT, 'lead', 'slowframe_round2_20261107', 'SLOWFRAME_PROXY.md')
SWL = os.path.join(ROOT, 'lead', 'slowwindow_n8_20261108', 'SLOW_WINDOW_LIMITS.md')
SCAN_PY = os.path.join(ROOT, 'lead', 'slowframe_round2_20261107', '_proxy_scan_corpus.py')
SCAN_OUT = os.path.join(ROOT, 'lead', 'slowframe_round2_20261107', '_proxy_scan_corpus_out.txt')
HARNESS = os.path.join(ROOT, 'lead', 'goal1_harness7_20261023', 'qc151_trip.harness7.py')
EARLY = os.path.join(ROOT, 'out', 're_work', 'work_chain', 'CONTINUE_20261003',
                    'lead', 'goal1_earlyend_analysis_20261018', 'EARLY_END_ANALYSIS.md')
ALLOWED = ROOT + os.sep

def R(*parts):
    p = os.path.normcase(os.path.realpath(os.path.join(*parts)))
    if not p.startswith(ALLOWED):
        raise ValueError('path outside repo: ' + p)
    return p

def Wr(name):
    if not name.startswith('_verify_') or '/' in name or chr(92) in name:
        raise ValueError('bad write name: ' + name)
    return R(W, name)

def sha(b): return hashlib.sha256(b).hexdigest()
def fsha(p):
    b = open(R(p), 'rb').read()
    return sha(b), len(b)

out = []
def say(*a):
    s = ' '.join(str(x) for x in a)
    out.append(s); print(s)

PAN = {
 'l1_20261023e4': {
   'measure_w0.json': ('8799e08dbc12e7f8674af9f7ade70d38fa4c46437861871b6d472c665616fdf9', 271414),
   'measure_w1.json': ('9439e8ef02725a76d3ce2dac2eba8b330a2e70b439dc4d3c79c0104590c7834e', 233984),
   'measure_w2.json': ('8d85ac02ff78e228fc12f65da2c3f8850e6fda0c1f3f35d5ca7aec5dbe2b0540', 106895)},
 'archive_T34': {
   'measure_w0.json': ('da30c275d8d985ddec019ce5a64f56c590b08a2f66499a7935d3b1b10df1cecd', 255493),
   'measure_w1.json': ('39f0aae1feff6c43894ce2011e2ea952d7ac7e5825271af888de3ae8eeb31d0c', 255071),
   'measure_w2.json': ('7cfe25d8447179772fdd827582c381e0e7d6685ed1f4eb98bf0230f4d140292b', 255122)},
 'archive_T36': {
   'measure_w0.json': ('20ecf4cf5274760bdf8c6c5747eaddbabf33367584ca3e70f9c128d56d89572f', 259112),
   'measure_w1.json': ('434c6267c9fc465a500c48c2c44d06cd0a8ceba058a95171550a170e2c72e485', 255059),
   'measure_w2.json': ('b389f1a0a155cae913e38e7c97189d363f2af81b9125f1088d2257218c20b448', 255074)},
 'archive_T43': {
   'measure_w0.json': ('818f2c00be1499063871e70f03902c8eee8dff4deff6c30909b2663a0674103f', 259244),
   'measure_w1.json': ('813744fad706f3990564064b3110b754d1aee6184a3939f199c8069474523650', 255094),
   'measure_w2.json': ('413223078e295f4ef9cc8b6a81a02cce9e642522f4083f5c9adbb5bdcf386358', 255062)},
}
PAN_MD = {
 PROXY: ('5fe880595965de4e0b39639c0d4a80d626476a9715f1cae5efd7361a0c8985d3', 26916),
 SWL:   ('e7c29e06f48b2380d5bec3f99e08ac2a4ce90d94da27b48b98d5eb2113a75d60', 23707),
}

say('=' * 100)
say('§0 被核对象指纹 (inline 归因回件逐字件 _verify_hy4_object.json)')
say('=' * 100)
ob = open(Wr('_verify_hy4_object.json'), 'rb').read()
o = json.loads(ob)
can = json.dumps(o, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
say('  被核对象 SHA256 =', sha(ob))
say('  字节数 =', len(ob), '; 字符数 =', len(ob.decode('utf-8')))
say('  canonical json.dumps 逐字节复现 =', can == ob)
say('  keys =', list(o.keys()), '; ranCommands =', o['ranCommands'],
    '; explainedCount =', o['explainedCount'], '; unexplainedCount =', o['unexplainedCount'])
say('  与 rollout 用户消息原文逐字提取件一致 (c2b777e2...) =',
    sha(ob) == 'c2b777e27358158b314e208c49e86179c2541b66e4633624995967c92471b385')

say('')
say('=' * 100)
say('§1 指纹核对: 12 件 measure_*.json + 2 件 md (hashlib 实算 vs 编排方盘点)')
say('=' * 100)
fp_ok = 0; fp_n = 0
for trip, files in PAN.items():
    for fn, (h, n) in files.items():
        H, N = fsha(os.path.join(TRIP, trip, fn))
        ok = (H == h and N == n); fp_n += 1; fp_ok += int(ok)
        say(' ', trip + '/' + fn, H, N, 'MATCH' if ok else '*** MISMATCH ***')
for p, (h, n) in PAN_MD.items():
    H, N = fsha(p); ok = (H == h and N == n); fp_n += 1; fp_ok += int(ok)
    say(' ', os.path.relpath(p, ROOT), H, N, 'MATCH' if ok else '*** MISMATCH ***')
say('  => 指纹一致 =', fp_ok, '/', fp_n)

say('')
say('=' * 100)
say('§2 既有普查口径 (核对「有效」判定标准是否事后调整)')
say('=' * 100)
sp = open(R(SCAN_PY), encoding='utf-8').read().splitlines()
for i, l in enumerate(sp, 1):
    if 'u_valid' in l or 'units_vals' in l or 'units有效' in l or 'n_ctr' in l:
        say('  _proxy_scan_corpus.py:%d = %s' % (i, l.strip()))
so = open(R(SCAN_OUT), encoding='utf-8').read().splitlines()
for i in (20, 23, 41, 62):
    say('  _proxy_scan_corpus_out.txt:%d = %s' % (i, repr(so[i-1])))
for label, p in [('scan.py', SCAN_PY), ('scan.out', SCAN_OUT), ('PROXY', PROXY),
                 ('_ca_A', os.path.join(W, '_ca_A_item_l1_w2_units12of25.md'))]:
    say('  mtime %-10s = %s  %s' % (label,
        datetime.datetime.fromtimestamp(os.path.getmtime(R(p))), os.path.relpath(p, ROOT)))
prox = open(R(PROXY), encoding='utf-8').read().splitlines()
say('  PROXY:221 =', repr(prox[220]))
say('  PROXY:222 =', repr(prox[221]))

say('')
say('=' * 100)
say('§3 【A】l1_20261023e4/measure_w2.json 独立重算')
say('=' * 100)
d = json.load(open(R(TRIP, 'l1_20261023e4', 'measure_w2.json'), encoding='utf-8'))
c = d['counters']
say('  len(counters) =', len(c))
for idx in (0, 1, 10, 11, 12, 13, 23, 24):
    row = c[idx]
    say('   [%02d] t_rel=%9.6f units=%-6s inf=%-6s g=%-6s b=%-6s techno=%-6s ws_kb=%-8s pf_kb=%-8s shape=%s'
        % (idx, row['t_rel'], row['units'], row['infantry'], row['g'], row['b'],
           row['techno'], row['ws_kb'], row['pf_kb'], row['shape']))
crit = {
 'not None':           lambda r: r['units'] is not None,
 'isinstance int/float': lambda r: isinstance(r['units'], (int, float)),
 'not None and != 0':  lambda r: r['units'] is not None and r['units'] != 0,
 'shape.g_valid True': lambda r: r['shape']['g_valid'] is True,
 'ws_kb > 1000':       lambda r: isinstance(r['ws_kb'], (int, float)) and r['ws_kb'] > 1000,
 '7 RPM 字段全非 null': lambda r: all(r[k] is not None for k in
                       ('units','infantry','aircraft','g','b','techno')),
}
for name, fn in crit.items():
    say('  口径 %-24s -> %d/25' % (name, sum(1 for r in c if fn(r))))
first_none = next((i for i, r in enumerate(c) if r['units'] is None), None)
say('  首个 units=None 行号 =', first_none, 't_rel =', c[first_none]['t_rel'])
say('  前 12 行 ws_kb 取值 =', sorted({r['ws_kb'] for r in c[:12]}),
    '; 后 13 行 ws_kb 取值 =', sorted({r['ws_kb'] for r in c[12:]}))
say('  verdict =', repr(d['verdict']), '; error =', repr(d['error']))
s = d['samples']; ts, fs = s['t'], s['f']
say('  samples t/f len =', len(ts), '/', len(fs))
say('  span =', round(ts[-1] - ts[0], 6), '; stats.max_stall_s =', d['stats']['max_stall_s'])
say('  max gap =', round(max(b - a for a, b in zip(ts, ts[1:])), 6), 's')
say('  f 全程恒定 =', len(set(fs)) == 1, '值 =', sorted(set(fs)))
say('  stats.fps_avg =', d['stats']['fps_avg'], '; logic_frames =', d['stats']['logic_frames'],
    '; note =', repr(d['stats']['note']))
say('  frame_edges =', d['frame_edges'])
say('  JSON 尾 120B =', repr(open(R(TRIP,'l1_20261023e4','measure_w2.json'),'rb').read()[-120:].decode('utf-8')))
for w in (0, 1):
    dd = json.load(open(R(TRIP, 'l1_20261023e4', 'measure_w%d.json' % w), encoding='utf-8'))
    nvalid = sum(1 for r in dd['counters'] if r['units'] is not None)
    say('  l1 w%d: counters=%d units非空=%d samples=%d fps_avg=%s frame_ms_p50=%s'
        % (w, len(dd['counters']), nvalid, len(dd['samples']['t']),
           dd['stats']['fps_avg'], dd['stats']['frame_ms_p50']))

say('')
say('=' * 100)
say('§4 l1 趟末 rec 行 (qc151_fields.json / except_set_diff.json 实读)')
say('=' * 100)
rec = json.load(open(R(TRIP, 'l1_20261023e4', 'qc151_fields.json'), encoding='utf-8'))
for r in rec:
    k, g = r['key'], r['group']
    if (g == 'MEASURE' and (k.startswith('measure_forensics_w') or k == 'verdict')) or \
       (g == 'ISOLATION' and k in ('iso_error','iso_verdict')) or \
       (g == 'TERM' and k in ('wait_returncode','terminate_sent')) or \
       (g == 'WER' and k in ('wer_report_count','wer_verdict')) or \
       (g == 'EXCEPT' and k in ('baseline_source','reset_verdict','pre_line_count',
                                'post_line_count','new_exception_count')):
        say('  %-10s | %-26s = %s' % (g, k, json.dumps(r['value'], ensure_ascii=False)[:230]))
ed = json.load(open(R(TRIP, 'l1_20261023e4', 'except_set_diff.json'), encoding='utf-8'))
say('  except_set_diff.json =', json.dumps(ed, ensure_ascii=False)[:300])

say('')
say('=' * 100)
say('§5 【B】fps_avg 独立重算 (T32/T34/T36/T40/T43 x w0/w1/w2, 共 15 窗)')
say('=' * 100)
trips = ['archive_T32','archive_T34','archive_T36','archive_T40','archive_T43']
for trip in trips:
    for w in (0, 1, 2):
        dd = json.load(open(R(TRIP, trip, 'measure_w%d.json' % w), encoding='utf-8'))
        ts, fs = dd['samples']['t'], dd['samples']['f']; st = dd['stats']
        calc = (fs[-1] - fs[0]) / (ts[-1] - ts[0]) if len(ts) >= 2 and ts[-1] > ts[0] else None
        a = st['fps_avg']
        diff = 'n/a' if (a is None or calc is None) else '%.12f' % abs(a - calc)
        say('  %-14s w%d: fps_avg=%-22s 自算=%-22s |diff|=%s  f %s->%s span=%s p50=%s frame_ms_p50=%s'
            % (trip, w, ('None' if a is None else '%.10f' % a),
               ('None' if calc is None else '%.10f' % calc), diff,
               fs[0], fs[-1], round(ts[-1]-ts[0],4),
               ('None' if st['fps_p50'] is None else '%.4f' % st['fps_p50']),
               ('None' if st['frame_ms_p50'] is None else '%.4f' % st['frame_ms_p50'])))

say('')
say('=' * 100)
say('§6 帧边沿推进止点 / 活跃时长 / units 签名 (T34/T36/T43 w0) + w1/w2 & trip verdict')
say('=' * 100)
for trip in ('archive_T34','archive_T36','archive_T43'):
    dd = json.load(open(R(TRIP, trip, 'measure_w0.json'), encoding='utf-8'))
    ts, fs = dd['samples']['t'], dd['samples']['f']
    edges = []; pf = None
    for t, f in zip(ts, fs):
        if pf is None or f != pf: edges.append((f, t)); pf = f
    t0 = edges[0][1]; active = edges[-1][1] - t0
    us = [r['units'] for r in dd['counters']]
    say('  %s: n_edges=%d f %s->%s 活跃时长=%.4fs 帧增量=%d max_stall_s=%s'
        % (trip, len(edges), edges[0][0], edges[-1][0], active,
           edges[-1][0]-edges[0][0], dd['stats']['max_stall_s']))
    say('      units 序列 =', us[:6], '... 尾部', us[-4:],
        '; infantry(row0) =', dd['counters'][0]['infantry'], '; gate.units0 =', dd['gate']['units0'])
    say('      末沿 t_rel =', round(edges[-1][1]-t0, 6), '; 窗总跨度 =', round(ts[-1]-ts[0],4))
    for w in (1, 2):
        dw = json.load(open(R(TRIP, trip, 'measure_w%d.json' % w), encoding='utf-8'))
        fset = set(dw['samples']['f'])
        say('      w%d: f 取值集合=%s logic_frames=%s fps_avg=%s note=%s'
            % (w, sorted(fset)[:5], dw['stats']['logic_frames'], dw['stats']['fps_avg'],
               repr(dw['stats']['note'])))
    rc = json.load(open(R(TRIP, trip, 'qc151_fields.json'), encoding='utf-8'))
    vr = [r for r in rc if r['group']=='MEASURE' and r['key']=='verdict']
    say('      trip-level MEASURE.verdict =', [r['value'] for r in vr],
        '; notes =', [str(r.get('note',''))[:120] for r in vr])
    fe = [r for r in rc if r['group']=='MEASURE' and r['key']=='measure_forensics_w1']
    say('      forensics_w1 =', json.dumps(fe[0]['value'], ensure_ascii=False)[:220] if fe else 'n/a')

say('')
say('=' * 100)
say('§7 自算 frame_ms_p50 (验证「frame_ms_p50 不受影响」)')
say('=' * 100)
for trip in trips:
    dd = json.load(open(R(TRIP, trip, 'measure_w0.json'), encoding='utf-8'))
    ts, fs = dd['samples']['t'], dd['samples']['f']
    edges = []; pf = None
    for t, f in zip(ts, fs):
        if pf is None or f != pf: edges.append((f, t)); pf = f
    dts = [(tb-ta)*1000.0 for (fa,ta),(fb,tb) in zip(edges, edges[1:]) if fb-fa == 1]
    mine = median(dts) if dts else None
    say('  %-14s frame_ms_p50(stats)=%s 自算(仅 df==1 沿)=%s 入样间隔=%d 边沿总数=%d'
        % (trip, dd['stats']['frame_ms_p50'], mine, len(dts), len(edges)))

say('')
say('=' * 100)
say('§8 _maps_fixed 实算 sha -> 图归属 (比对 measure JSON 的 map_sha256)')
say('=' * 100)
mp = {}
for p in glob.glob(os.path.join(TRIP, '_maps_fixed', '*')):
    if os.path.isfile(R(p)):
        mp[os.path.basename(p)] = fsha(p)[0]
for trip in ('l1_20261023e4','archive_T32','archive_T34','archive_T36','archive_T40','archive_T43'):
    dd = json.load(open(R(TRIP, trip, 'measure_w0.json'), encoding='utf-8'))
    m = dd['map_sha256']; hit = [n for n, h in mp.items() if h == m]
    say('  %-16s map_sha256=%s -> %s' % (trip, m[:12], hit if hit else '未在 _maps_fixed 找到'))

say('')
say('=' * 100)
say('§9 PNG 独立像素直读 (自写 stdlib zlib 解码, 不调用分析员 _ca_png_probe.py)')
say('=' * 100)
def png_probe(path):
    b = open(R(path), 'rb').read(); pos = 8; idat = b''; ihdr = None
    while pos < len(b):
        ln = struct.unpack('>I', b[pos:pos+4])[0]
        typ = b[pos+4:pos+8]; data = b[pos+8:pos+8+ln]
        if typ == b'IHDR': ihdr = struct.unpack('>IIBBBBB', data)
        elif typ == b'IDAT': idat += data
        pos += 12 + ln
        if typ == b'IEND': break
    w, h, depth, ctype = ihdr[0], ihdr[1], ihdr[2], ihdr[3]
    if ctype != 2 or depth != 8:
        return dict(sha=sha(b), size=len(b), wh=(w,h), err='ctype=%d depth=%d' % (ctype, depth))
    raw = zlib.decompress(idat); stride = w*3; prev = bytearray(stride)
    buf = bytearray(); p = 0
    for y in range(h):
        ft = raw[p]; p += 1; line = bytearray(raw[p:p+stride]); p += stride
        for i in range(stride):
            a = line[i-3] if i >= 3 else 0; up = prev[i]; ul = prev[i-3] if i >= 3 else 0
            if ft == 1: line[i] = (line[i] + a) & 255
            elif ft == 2: line[i] = (line[i] + up) & 255
            elif ft == 3: line[i] = (line[i] + ((a + up) >> 1)) & 255
            elif ft == 4:
                pa=abs(up-ul); pb=abs(a-ul); pc=abs(a+up-2*ul)
                pr = a if (pa<=pb and pa<=pc) else (up if pb<=pc else ul)
                line[i] = (line[i] + pr) & 255
        buf += line; prev = line
    n = w*h; sr=sg=sb=0; cnt = collections.Counter()
    for i in range(0, len(buf), 3):
        r,g,bl = buf[i], buf[i+1], buf[i+2]
        sr+=r; sg+=g; sb+=bl; cnt[(r>>4,g>>4,bl>>4)] += 1
    return dict(sha=sha(b), size=len(b), wh=(w,h), avg=(sr//n,sg//n,sb//n),
                top=[(c, round(k/n*100,2)) for c,k in cnt.most_common(6)])
pngs = [(trip+' measure_w1_end_x.png', os.path.join(TRIP, trip, 'measure_w1_end_x.png'))
        for trip in ('archive_T34','archive_T36','archive_T43')]
pngs += [('archive_T34 frame_target_01.png', os.path.join(TRIP,'archive_T34','frame_target_01.png')),
         ('l1 measure_w2_end_x.png', os.path.join(TRIP,'l1_20261023e4','measure_w2_end_x.png'))]
for label, p in pngs:
    say(' ', label, '->', png_probe(p))

say('')
say('=' * 100)
say('§10 EARLY_END_ANALYSIS.md 定谳原文 (:11 / :67-79) 与 harness 代码行')
say('=' * 100)
el = open(R(EARLY), encoding='utf-8').read().splitlines()
for i in (11, 67, 71, 75, 77, 79):
    say('  EARLY_END_ANALYSIS.md:%d = %s' % (i, el[i-1][:250]))
hs = open(R(HARNESS), encoding='utf-8').read().splitlines()
for i in (3898, 3900, 3911, 3912, 3913, 3930, 3932, 3944, 3945, 3953, 3980,
          3995, 3996, 3997, 4000, 4001, 4004, 4012, 4702, 4760, 4761, 4768):
    say('  harness7.py:%d = %s' % (i, hs[i-1].rstrip()[:190]))

say('')
say('=' * 100)
say('§11 写域纪律 / 语料未改 / 未 commit')
say('=' * 100)
allw = sorted(os.listdir(W))
say('  write-domain 文件清单 (%d 件) =' % len(allw), allw)
say('  _ca_ 件数 =', len([f for f in allw if f.startswith('_ca_')]),
    '; 本次 _verify_ 件 =', [f for f in allw if f.startswith('_verify_')])
cut = datetime.datetime(2026,11,8,19,0,0).timestamp()
recent = []
for trip in list(PAN) + ['archive_T32','archive_T40']:
    dp = os.path.join(TRIP, trip)
    if not os.path.isdir(R(dp)): continue
    for f in os.listdir(R(dp)):
        p = os.path.join(dp, f)
        if os.path.isfile(R(p)) and os.path.getmtime(R(p)) >= cut:
            recent.append(os.path.relpath(p, ROOT))
say('  语料目录内 2026-11-08 19:00 之后被修改的文件 =', recent if recent else '无')
for p in (SCAN_PY, SCAN_OUT, PROXY, SWL, HARNESS, EARLY):
    say('  只读件 mtime', datetime.datetime.fromtimestamp(os.path.getmtime(R(p))),
        os.path.relpath(p, ROOT))

open(Wr('_verify_hy4_out.txt'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
say('')
say('WROTE', Wr('_verify_hy4_out.txt'))
