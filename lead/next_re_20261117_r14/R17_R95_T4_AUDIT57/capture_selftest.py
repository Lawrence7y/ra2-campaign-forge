# -*- coding: utf-8 -*-
"""捕获 recheck_verify.py --self-test 的 UTF-8 输出，供审计留证（不改任何被测文件）。"""
import io, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.join(os.path.dirname(HERE), '')  # parent = next_re_20261117_r14
R14 = os.path.abspath(os.path.join(HERE, '..'))
OUT = os.path.join(HERE, 'q4_selftest_output.txt')
env = dict(os.environ)
env['PYTHONIOENCODING'] = 'utf-8'
p = subprocess.run([sys.executable, os.path.join(R14, 'recheck_verify.py'), '--self-test'],
                   cwd=R14, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
out = p.stdout.decode('utf-8', 'replace')
with io.open(OUT, 'w', encoding='utf-8', newline='') as f:
    f.write('cmd: python recheck_verify.py --self-test\n')
    f.write('cwd: %s\n' % R14)
    f.write(out)
    f.write('\nEXITCODE=%d\n' % p.returncode)
print('written', OUT, 'exit', p.returncode)
