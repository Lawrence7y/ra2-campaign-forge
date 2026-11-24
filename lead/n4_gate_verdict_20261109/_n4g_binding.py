# -*- coding: utf-8 -*-
"""_n4g_binding.py — 逐字符核 FAIL④：严格口径为何 0、宽松为何 1；并给最小改写后的结果。"""
import pathlib, re, json, hashlib
ROOT = pathlib.Path('D:/Project/ra2-campaign-forge')
t = (ROOT / 'lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md').read_text(encoding='utf-8')
lines = t.splitlines()
ln = lines[121]  # 第 122 行

o = {}
o['line122_verbatim'] = ln
o['line122_repr'] = repr(ln)
o['line122_codepoints_after_SHA256'] = [{'i': i, 'ch': c, 'cp': 'U+%04X' % ord(c)}
                                        for i, c in enumerate(ln) if 0 <= i - ln.find('SHA256') <= 80 and i >= ln.find('SHA256')]
# 找「被核对象」与「SHA256」之间的 infix
a = ln.find('被核对象'); z = ln.find('SHA256')
o['infix_between'] = ln[a + 4:z]
o['infix_repr'] = repr(ln[a + 4:z])
o['infix_len'] = len(ln[a + 4:z])
o['hex_has_backticks'] = '`ee27b4' in ln
o['bytes_field'] = re.findall(r'字节数\s*=\s*(\d+)', ln)

STRICT = r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?'
TIGHT = r'被核对象 SHA256 = [0-9a-fA-F]{64}'
LOOSE = r'被核对象[^。\n]{0,160}?SHA256\s*=\s*`?[0-9a-fA-F]{64}`?'
o['strict_matches'] = re.findall(STRICT, t)
o['tight_matches'] = re.findall(TIGHT, t)
o['loose_matches'] = re.findall(LOOSE, t)

# 逐字符对比：把铁律要求的「被核对象 SHA256 = 」与实写的分隔段
needle = '被核对象 SHA256 = '
o['required_prefix_verbatim'] = needle
o['required_prefix_present'] = needle in t
o['actual_prefix_until_hex'] = ln[a:ln.find('ee27b4')]

# 最小改写：只把 infix 全删 + 去 hex 反引号 + 去外层加粗；其余不动
rewritten = ('被核对象 SHA256 = ee27b4caf4faa7920b602636bc0f43c1a265554fe6354659c59323fc11e3102e'
             '，字节数 = 11948')
o['minimal_rewrite_full_line'] = rewritten
o['minimal_rewrite_strict_match'] = bool(re.findall(STRICT, rewritten))
o['minimal_rewrite_tight_match'] = bool(re.findall(TIGHT, rewritten))
o['minimal_rewrite_sha256'] = hashlib.sha256(t.replace(ln, rewritten).encode('utf-8')).hexdigest()
o['original_sha256'] = hashlib.sha256(t.encode('utf-8')).hexdigest()
print(json.dumps(o, ensure_ascii=False, indent=2))
