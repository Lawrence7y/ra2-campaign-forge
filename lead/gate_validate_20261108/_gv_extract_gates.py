# -*- coding: utf-8 -*-
# _gv_extract_gates.py —— 门禁回归员·GLM 自写提取器（不复用审计方提取器）
# 解析 .zcode/workflow-runs/dwfrun-*.mjs，提取 const GATE_CODE，逐字解码为可运行 Python。
# 输出：_gv_gates/<run8>.py + _gv_gates_manifest.json + _gv_extract_out.txt
import json, re, hashlib, pathlib, datetime

ROOT = pathlib.Path('D:/Project/ra2-campaign-forge')
RUNS = ROOT / '.zcode' / 'workflow-runs'
OUT = ROOT / 'lead' / 'gate_validate_20261108' / '_gv_gates'
OUT.mkdir(parents=True, exist_ok=True)
lines_out = []

def log(s=''):
    print(s)
    lines_out.append(str(s))

JS_ESCAPES = {
    'n': '\n', 't': '\t', 'r': '\r', 'b': '\b', 'f': '\f', 'v': '\v', '0': '\0',
}

def js_unescape(s):
    """JS 双引号字符串体 -> 实际字符串（处理 \\x \\u 与常用转义；不处理八进制）。"""
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            n = s[i+1]
            if n == 'x':
                out.append(chr(int(s[i+2:i+4], 16))); i += 4; continue
            if n == 'u':
                # \uXXXX 或 \u{XXXX}
                if i + 2 < len(s) and s[i+2] == '{':
                    j = s.index('}', i+3)
                    out.append(chr(int(s[i+3:j], 16))); i = j + 1; continue
                out.append(chr(int(s[i+2:i+6], 16))); i += 6; continue
            if n in JS_ESCAPES:
                out.append(JS_ESCAPES[n]); i += 2; continue
            if n == '\n':  # 行续接
                i += 2; continue
            out.append(n); i += 2; continue
        out.append(c); i += 1
    return ''.join(out)

def split_js_array(src, start):
    """src[start]=='[' ，解析 JS 数组字面量，返回 (元素字符串列表, 结束索引)。"""
    assert src[start] == '['
    i = start + 1
    elems = []
    cur = []
    depth = 0
    in_str = False
    str_ch = ''
    while i < len(src):
        c = src[i]
        if in_str:
            cur.append(c)
            if c == '\\':
                cur.append(src[i+1]); i += 2; continue
            if c == str_ch:
                in_str = False
            i += 1; continue
        if c in ('"', "'", '`'):
            in_str = True; str_ch = c; cur.append(c); i += 1; continue
        if c == '[':
            depth += 1
        elif c == ']':
            if depth == 0:
                elems.append(''.join(cur).strip())
                return elems, i
            depth -= 1
        if depth == 0 and c == ',':
            elems.append(''.join(cur).strip()); cur = []
            i += 1; continue
        cur.append(c); i += 1
    raise ValueError('array not closed')

def parse_js_string_literal(tok):
    tok = tok.strip()
    if tok.startswith('"') and tok.endswith('"'):
        return js_unescape(tok[1:-1]), 'dq'
    if tok.startswith("'") and tok.endswith("'"):
        return js_unescape(tok[1:-1]), 'sq'
    if tok == '...':
        raise ValueError('spread element（需人工处理）')
    raise ValueError('非字符串字面量: %r' % tok[:60])

manifest = []
mjs_files = sorted(RUNS.glob('dwfrun-*.mjs'))
log('dwfrun-*.mjs 总数 = %d' % len(mjs_files))
for m in mjs_files:
    raw = m.read_bytes()
    text = raw.decode('utf-8', errors='replace')
    # 定位 payload JSON
    key = 'export const payload = '
    p0 = text.find(key)
    if p0 < 0:
        continue
    dec = json.JSONDecoder()
    payload, pend = dec.raw_decode(text, p0 + len(key))
    lowered = payload.get('lowered', '')
    run_id = payload.get('run', {}).get('id', m.stem.replace('dwfrun-', ''))
    if 'GATE_CODE' not in lowered:
        continue
    # 真门禁判定：存在 const GATE_CODE = [ ... ].join(...) 且被执行
    gd = re.search(r'const\s+GATE_CODE\s*=\s*\[', lowered)
    executed = bool(re.search(r'-c",\s*GATE_CODE', lowered))
    has_gate_ok = 'gateOk' in lowered
    info = {
        'mjs': str(m.relative_to(ROOT)).replace('\\', '/'),
        'run_id': run_id,
        'mtime': datetime.datetime.fromtimestamp(m.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'is_gate_def': bool(gd),
        'executed_as_gate': executed,
        'has_gateOk': has_gate_ok,
    }
    if not gd:
        # 只是 ask 文本里的提及
        info['why_not_gate'] = 'lowered 含 GATE_CODE 字样但无 const GATE_CODE 定义'
        manifest.append(info)
        log('MENTION-ONLY %s (%s)' % (run_id[:8], info['mtime']))
        continue
    start = gd.end() - 1
    elems, endidx = split_js_array(lowered, start)
    # trailing comma 会产生空 token；真正的空字符串元素应是 '""' 或 "''"（有引号）
    elems = [e for e in elems if e.strip() != '']
    tail = lowered[endidx:endidx+40]
    joined_with = re.match(r'\]\s*\.\s*join\(\s*(["\'`])(.*?)\1\s*\)', tail)
    # join 参数是 JS 字符串字面量体，需再还原一次转义（"\n" 才是真换行）
    sep = js_unescape(joined_with.group(2)) if joined_with else '\n'
    if not joined_with:
        log('WARN: %s 未识别 join 分隔符，tail=%r' % (run_id[:8], tail[:30]))
    join_repr = tail[:30].replace('\n', '\\n')
    decoded_lines = []
    modes = set()
    bad = []
    for idx, e in enumerate(elems):
        try:
            v, mode = parse_js_string_literal(e)
            decoded_lines.append(v)
            modes.add(mode)
        except ValueError as ex:
            bad.append((idx, str(ex)))
    gate_code = sep.join(decoded_lines)
    # 门禁上下文常量
    def constval(name):
        mm = re.search(r'const\s+%s\s*=\s*"((?:[^"\\]|\\.)*)"' % name, lowered)
        return js_unescape(mm.group(1)) if mm else None
    info['DIR'] = constval('DIR')
    info['DOC'] = constval('DOC')
    rootm = re.search(r"root\s*=\s*pathlib\.Path\('([^']+)'\)", gate_code)
    info['gate_scan_root'] = rootm.group(1) if rootm else None
    phases = re.findall(r'__host\.enterPhase\("((?:[^"\\]|\\.)*)"\)', lowered)
    info['phases'] = [js_unescape(p) for p in phases]
    # worldRead 调用序号
    wr = re.findall(r'worldRead\("([^"]+)",\s*"run"', lowered)
    info['worldRead_calls'] = wr
    h = hashlib.sha256(gate_code.encode('utf-8')).hexdigest()
    info['gate_sha256'] = h
    info['gate_bytes'] = len(gate_code.encode('utf-8'))
    info['gate_lines'] = len(decoded_lines)
    info['join'] = repr(sep)
    info['bad_elems'] = bad
    info['elem_quote_modes'] = sorted(modes)
    if bad:
        info['decoded'] = False
        log('DECODE-FAIL %s: %s' % (run_id[:8], bad[:2]))
    else:
        info['decoded'] = True
        runshort = run_id.split('-', 1)[1][:8] if '-' in run_id else run_id[:8]
        gp = OUT / ('%s.py' % runshort)
        gp.write_text(gate_code, encoding='utf-8')
        log('GATE %s | %s | root=%s | lines=%d bytes=%d sha=%s' % (
            run_id[:8], info['mtime'], info['gate_scan_root'], len(decoded_lines), info['gate_bytes'], h[:12]))
    manifest.append(info)

# 汇总
real = [x for x in manifest if x.get('decoded')]
mention = [x for x in manifest if not x.get('decoded') and not x.get('is_gate_def')]
faildec = [x for x in manifest if x.get('is_gate_def') and not x.get('decoded')]
log('')
log('=== 汇总：定义 GATE_CODE 的 dwfrun = %d；成功解码 = %d；仅提及未定义 = %d；解码失败 = %d' %
    (sum(1 for x in manifest if x.get('is_gate_def')), len(real), len(mention), len(faildec)))
mp = OUT.parent / '_gv_gates_manifest.json'
mp.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding='utf-8')
op = OUT.parent / '_gv_extract_out.txt'
op.write_text('\n'.join(lines_out) + '\n', encoding='utf-8')
print('manifest ->', mp)
