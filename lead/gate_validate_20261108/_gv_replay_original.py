# -*- coding: utf-8 -*-
# _gv_replay_original.py —— 原样重放 22 个历史门禁
# 复刻工作流执行方式：python -I -X utf8 -c <GATE_CODE>，解析 stdout JSON。
import json, pathlib, subprocess, sys, hashlib

ROOT = pathlib.Path('D:/Project/ra2-campaign-forge')
GDIR = ROOT / 'lead' / 'gate_validate_20261108' / '_gv_gates'
OUT = ROOT / 'lead' / 'gate_validate_20261108' / '_gv_out'
OUT.mkdir(exist_ok=True)

manifest = json.loads((ROOT / 'lead' / 'gate_validate_20261108' / '_gv_gates_manifest.json').read_text(encoding='utf-8'))
by_short = {}
for x in manifest:
    if x.get('decoded'):
        short = x['run_id'].split('-', 1)[1][:8]
        by_short[short] = x

lines_out = []
def log(s=''):
    print(s)
    lines_out.append(str(s))

results = []
for gp in sorted(GDIR.glob('*.py')):
    short = gp.stem
    code = gp.read_text(encoding='utf-8')
    r = subprocess.run([sys.executable, '-I', '-X', 'utf8', '-c', code],
                       capture_output=True, timeout=120)
    entry = {
        'run8': short,
        'run_id': by_short.get(short, {}).get('run_id'),
        'mjs_mtime': by_short.get(short, {}).get('mtime'),
        'scan_root': by_short.get(short, {}).get('gate_scan_root'),
        'exit': r.returncode,
    }
    try:
        g = json.loads(r.stdout.decode('utf-8', 'replace').strip())
        entry['ok'] = g.get('ok')
        entry['problems'] = g.get('problems')
        entry['bindings'] = g.get('bindings', g.get('sha256Bindings'))
        entry['docBytes'] = g.get('docBytes')
        entry['copies'] = g.get('copies')
    except Exception as e:
        entry['parse_error'] = str(e)
        entry['stdout_head'] = r.stdout.decode('utf-8', 'replace')[:300]
        entry['stderr_head'] = r.stderr.decode('utf-8', 'replace')[:300]
    results.append(entry)
    probs = entry.get('problems')
    n = len(probs) if isinstance(probs, list) else '?'
    log('%s | exit=%s | ok=%s | problems=%s %s' % (
        short, r.returncode, entry.get('ok'), n,
        (probs[:3] if isinstance(probs, list) else (entry.get('parse_error') or entry.get('stderr_head',''))[:120])))

(OUT / '_gv_replay_original_out.txt').write_text('\n'.join(lines_out) + '\n', encoding='utf-8')
(OUT / '_gv_replay_original.json').write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding='utf-8')
print('---')
print('total=%d' % len(results))
