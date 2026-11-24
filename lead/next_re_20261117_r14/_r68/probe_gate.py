# -*- coding: utf-8 -*-
# R68 诊断探针：在 Linux 上以「路径分隔符无关 + ROOT 正确」的方式跑真 check_disc.py / recheck_verify.py
# 只做两处等值替换（ROOT、反斜杠→本机 sep），不改任何判据。
import io, os, sys, types
R14 = os.path.dirname(os.path.abspath(__file__)).replace('/_r68','')
ROOT = '/home/t628/projects/ra2-campaign-forge'

def load(name, path, subs):
    s = io.open(path, encoding='utf-8').read()
    for a, b in subs:
        assert a in s, (name, a)
        s = s.replace(a, b)
    m = types.ModuleType(name)
    m.__file__ = path
    code = compile(s, path, 'exec')
    exec(code, m.__dict__)
    return m

# 1) recheck_verify：把 rel.replace('/','\\') 改为 rel.replace('\\', os.sep)
rv = load('recheck_verify',
          os.path.join(R14, 'recheck_verify.py'),
          [("ap = rel.replace('/', '\\\\')", "ap = rel.replace('\\\\', '/')")])
sys.modules['recheck_verify'] = rv

# 2) check_disc：ROOT 换成真根
cd = load('check_disc_probe',
          os.path.join(R14, 'check_disc.py'),
          [("ROOT = r'D:\\Project\\ra2-campaign-forge'", "ROOT = %r" % ROOT)])
