# -*- coding: utf-8 -*-
# _gt_extract_gates.py — 从 .zcode/workflow-runs/*.mjs 的 payload 中逐字解码提取
# 四个涉事门禁脚本，落盘为 _gt_gate_<short>.py，供原样实跑复现误报。
# 只读提取 + 写本任务写域；不改任何既有脚本。
import json
import re
import pathlib

RUNS = {
    'cd57bf1c': 'dwfrun-cd57bf1c-8be0-4292-a832-f17ea70a7485.mjs',  # B链集成 b2b_isolated
    '1c93b364': 'dwfrun-1c93b364-e57c-405d-a271-66cd59e4b850.mjs',  # 判据第二轮 dtrigger_round2
    '2b4e006c': 'dwfrun-2b4e006c-e09d-45f0-8094-fa5e890c1fb6.mjs',  # N-11 perf_repair
    '324c613e': 'dwfrun-324c613e-fb0e-42f5-9883-805fef5b80de.mjs',  # N-1 r2 a_residual
}
outdir = pathlib.Path('D:/Project/ra2-campaign-forge/lead/gate_template_20261108')
PLACEHOLDER = '\x00DLBACKSLASHN\x00'

for short, fn in RUNS.items():
    raw = pathlib.Path('D:/Project/ra2-campaign-forge/.zcode/workflow-runs/' + fn).read_text(encoding='utf-8')
    i = raw.find('{"lowered":')
    assert i >= 0, short + ': payload not found'
    payload, _ = json.JSONDecoder().raw_decode(raw[i:])
    src = payload['lowered']
    m = re.search(r'const GATE_CODE = \[(.*?)\]\.join\(', src, re.S)
    assert m, short + ': GATE_CODE not found'
    g = m.group(1)
    g = g.replace('\\' + '\\' + 'n', PLACEHOLDER)   # 项内双反斜杠+n（如有）
    g = g.replace('\\' + 'n', chr(10))              # 项间行分隔符
    g = g.replace(PLACEHOLDER, '\\' + '\\' + 'n')
    g = re.sub(r',\s*$', '', g.rstrip())  # JS 数组允许尾逗号，JSON 不允许
    items = json.loads('[' + g + ']')
    code = chr(10).join(items)
    # 必须能编译才落盘
    compile(code, '_gt_gate_' + short + '.py', 'exec')
    out = outdir / ('_gt_gate_' + short + '.py')
    out.write_text(code, encoding='utf-8', newline='')
    print(short, 'extracted bytes=', len(code.encode('utf-8')), 'sha256=', __import__('hashlib').sha256(code.encode('utf-8')).hexdigest()[:16])
