# -*- coding: utf-8 -*-
"""_me_auditcheck_snippet.py — compile-check the pasteable snippet in §4.4."""
import io, re, ast
HERE = r"D:/Project/ra2-campaign-forge/lead/masking_effect_20261109"
t = io.open(HERE + "/MASKING_EFFECT_AUDIT.md", encoding="utf-8").read()
blocks = re.findall(r"```python\n(.*?)\n```", t, re.S)
print("python code blocks found = %d" % len(blocks))
for i, b in enumerate(blocks, 1):
    try:
        ast.parse(b)
        print("  block %d: SYNTAX OK (%d lines)" % (i, len(b.splitlines())))
    except SyntaxError as e:
        print("  block %d: SYNTAX ERROR %s" % (i, e))
