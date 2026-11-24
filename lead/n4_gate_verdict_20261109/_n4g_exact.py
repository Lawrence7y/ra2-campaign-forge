# -*- coding: utf-8 -*-
"""_n4g_exact.py — 严格/宽松口径的精确断点，与三种最小改法落地后的整文件 SHA256。"""
import pathlib, re, hashlib, json
R = pathlib.Path('D:/Project/ra2-campaign-forge')
p = R / 'lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md'
t = p.read_text(encoding='utf-8')
b = p.read_bytes()
ln = t.splitlines()[121]
HEX = 'ee27b4caf4faa7920b602636bc0f43c1a265554fe6354659c59323fc11e3102e'
STRICT = r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?'   # 历史 GATE_CODE 原文
TIGHT = r'被核对象 SHA256 = [0-9a-fA-F]{64}'                # 本轮铁律固定格式（禁反引号）
LOOSE = r'被核对象[^。\n]{0,160}?SHA256\s*=\s*`?[0-9a-fA-F]{64}`?'

infix = '（审阅回件 `lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md`）'
o = {}
o['line122'] = ln
o['infix'] = infix
o['infix_len'] = len(infix)
o['space_between_被核对象_and_SHA256'] = '（审阅回件…）' in ln
o['hex_backticks'] = '`' + HEX + '`' in ln
o['strict_on_original'] = bool(re.findall(STRICT, ln))
o['tight_on_original'] = bool(re.findall(TIGHT, ln))
o['loose_on_original'] = bool(re.findall(LOOSE, ln))

variants = {
    'v1_only_drop_infix': ln.replace(infix, ''),
    'v2_only_drop_hex_backticks': ln.replace('`' + HEX + '`', HEX),
    'v3_drop_infix_insert_space': ln.replace(infix, ' '),
    'v4_canonical_full_line': '被核对象 SHA256 = ' + HEX + '，字节数 = 11948',
}
for k, v in variants.items():
    o[k] = {'text': v, 'gate_strict': bool(re.findall(STRICT, v)),
            'iron_tight': bool(re.findall(TIGHT, v)), 'loose': bool(re.findall(LOOSE, v))}

# 落地方式：替换第 122 行 / 在第 122 行后插入一行 / 仅追加一行到文件尾
def sha_of(newt):
    return hashlib.sha256(newt.encode('utf-8')).hexdigest(), len(newt.encode('utf-8'))
for k, newt in [
    ('replace_line122', t.replace(ln, variants['v4_canonical_full_line'], 1)),
    ('insert_after_line122', ''.join(t.splitlines(keepends=True)[:122] + [variants['v4_canonical_full_line'] + '\n'] + t.splitlines(keepends=True)[122:])),
    ('append_at_eof', t + '\n' + variants['v4_canonical_full_line'] + '\n'),
]:
    sh, n = sha_of(newt)
    o[k] = {'sha256': sh, 'bytes': n, 'gate_strict': len(re.findall(STRICT, newt)),
            'iron_tight': len(re.findall(TIGHT, newt))}
o['original'] = {'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}
print(json.dumps(o, ensure_ascii=False, indent=2))
