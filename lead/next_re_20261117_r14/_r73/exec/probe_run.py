# -*- coding: utf-8 -*-
"""R73-E1 independent probe runner.

Usage:
  python3 probe_run.py --gate SRC --verifier SRC [--patch-root] [--patch-sep]
                       [--r55start HHMMSS] [--r55end HHMMSS]

Loads gate source and verifier source from arbitrary paths, applies the
minimal substitutions, execs the verifier first into a module object,
pre-registers it as sys.modules['recheck_verify'], then execs the gate.
stdout is the gate's own stdout; process exit code is the gate's.
"""
import io, os, sys, types

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(os.path.dirname(HERE))          # .../lead/next_re_20261117_r14
ROOT = os.path.dirname(os.path.dirname(R14))          # .../ra2-campaign-forge


def arg(name, default=None):
    if name in sys.argv:
        return sys.argv[sys.argv.index(name) + 1]
    return default


def has(name):
    return name in sys.argv


gate_src_path = arg('--gate')
ver_src_path = arg('--verifier')

gate_src = io.open(gate_src_path, encoding='utf-8').read()
ver_src = io.open(ver_src_path, encoding='utf-8').read()

# ---- verifier patches -------------------------------------------------------
if has('--patch-sep'):
    old = "ap = rel.replace('/', '\\\\')"
    new = "ap = rel.replace('\\\\', os.sep).replace('/', os.sep)"
    if old not in ver_src:
        sys.stderr.write('PATCH-FAIL: separator line not found verbatim\n')
        sys.exit(90)
    ver_src = ver_src.replace(old, new)

s55 = arg('--r55start')
e55 = arg('--r55end')
if s55 or e55:
    import re
    m = re.search(r"(\(\s*55\s*,\s*')(\d{6})('\s*,\s*')(\d{6})(')", ver_src)
    if not m:
        sys.stderr.write('PATCH-FAIL: row 55 not found\n')
        sys.exit(91)
    ns, ne = s55 or m.group(2), e55 or m.group(4)
    ver_src = ver_src[:m.start()] + m.group(1) + ns + m.group(3) + ne + m.group(5) + ver_src[m.end():]
    sys.stderr.write('PATCHED row55 start=%s end=%s\n' % (ns, ne))

# ---- gate patches -----------------------------------------------------------
if has('--patch-root'):
    old_root = "ROOT = r'D:\\Project\\ra2-campaign-forge'"
    if old_root not in gate_src:
        sys.stderr.write('PATCH-FAIL: ROOT line not found verbatim\n')
        sys.exit(92)
    gate_src = gate_src.replace(old_root, "ROOT = %r" % ROOT)
if has('--patch-sep'):
    # older gate has no separator hook; nothing to do, reported for symmetry
    sys.stderr.write('gate-sep-patch: n/a (gate has no separator literal)\n')

# ---- build verifier module --------------------------------------------------
vmod = types.ModuleType('recheck_verify')
vmod.__file__ = os.path.join(R14, 'recheck_verify.py')   # so _HERE resolves to R14
exec(compile(ver_src, ver_src_path, 'exec'), vmod.__dict__)
sys.modules['recheck_verify'] = vmod

# ---- run the gate -----------------------------------------------------------
g = {'__name__': '__main__', '__file__': gate_src_path,
     '__builtins__': __builtins__}
try:
    exec(compile(gate_src, gate_src_path, 'exec'), g)
except SystemExit as e:
    sys.exit(e.code if isinstance(e.code, int) else 0)
