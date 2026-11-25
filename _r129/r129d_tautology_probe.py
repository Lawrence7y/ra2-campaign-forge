# -*- coding: utf-8 -*-
"""R129d：先测「每条校验式能否被伪造成永远通过」，再决定要不要动门禁。

思路（与既有的 claims-none 修法同族）：一条校验式的真正价值不在于「现在通过」，
而在于「换成空产物时必须不通过」。若某条校验式在空产物上仍然通过，它就是一价
永久免检票 —— 换成它、或早就是它，门禁都看不见。

测法：把 ROOT 换成一个只含「同名空文件」的沙箱，逐条重跑 run_expr。
反控：同一判据对「真产物」必须给通过（否则不是判据是误伤）。
"""
import sys, os, json, tempfile, shutil, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_r128'))
from peek import ROOT
import io, re

OUT = os.path.join(ROOT, '_r129', 'r129d_tautology_probe.json')
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
rows = [l.split('\t') for l in io.open(os.path.join(R14, 'DISC_RECHECK.tsv'), encoding='utf-8').read().split('\n') if l][1:]

def run_expr(path, expr, root):
    ap = os.path.join(root, path.replace('\\', '/'))
    if not os.path.isfile(ap): return False, 'FILE_MISSING'
    head = expr.split(' ')[0]
    txt = io.open(ap, encoding='utf-8', errors='replace').read()
    if head.startswith('grep='):
        pat = expr[5:].strip(); n = len(re.findall(pat, txt, re.M))
        return n >= 1, 'hits=%d' % n
    if head.startswith('grepcount='):
        rest = expr[len('grepcount='):].strip(); m = re.match(r'^(.*)=(\d+)$', rest, re.S)
        if not m: return False, 'BAD'
        n = len(re.findall(m.group(1), txt, re.M))
        return n == int(m.group(2)), '%d vs %s' % (n, m.group(2))
    m = re.search(r'[\(（](\d+)\s*B[\)）]', expr)
    if head == 'exists':
        if m: return os.path.getsize(ap) == int(m.group(1)), 'bytes'
        return False, 'exists-without-size-annotation'
    m2 = re.fullmatch(r'bytes=(\d+)', head)
    if m2: return os.path.getsize(ap) == int(m2.group(1)), 'bytes=%d' % os.path.getsize(ap)
    m3 = re.fullmatch(r'rows=(\d+)', head)
    if m3:
        n = 0; hdr = 0
        for ln in io.open(ap, encoding='utf-8', errors='replace'):
            s = ln.strip()
            if s.startswith('DISC_RECHECK '): continue
            if hdr == 0: hdr = 1; continue
            n += 1
        return n == int(m3.group(1)), 'rows=%d' % n
    if head == 'none': return None, 'none'
    return False, 'BAD_EXPR:' + head

sb = tempfile.mkdtemp(prefix='r129_empty_')
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': d if not isinstance(d, (dict, list)) else json.dumps(d, ensure_ascii=False)})
try:
    live_rows = [r for r in rows if len(r) == 7 and r[4].strip() not in ('', '（文档内锚）') and not r[5].strip().startswith('none')]
    add('D0 参与测试的行数 = %d（与 DISC_RECHECK 的 31 行一致）' % len(live_rows), len(live_rows) == 31, len(live_rows))
    taut, real_ok = [], 0
    for r in live_rows:
        p = r[4].strip(); e = r[5].strip()
        ap = os.path.join(sb, p.replace('\\', '/'))
        os.makedirs(os.path.dirname(ap), exist_ok=True)
        open(ap, 'wb').close()                      # 同名空文件
        ok_empty, det_empty = run_expr(p, e, sb)
        ok_real, det_real = run_expr(p, e, ROOT)
        if ok_real is True: real_ok += 1
        if ok_empty is True or ok_empty is None:
            taut.append((r[0], e[:60], det_empty))
    add('D1 真产物上 31 条校验式全部通过（前提）', real_ok == 31, real_ok)
    add('D2 空产物上仍能「通过」的校验式条数', True, {'count': len(taut), 'ids': [t[0] for t in taut]})
    for n, e, d in taut:
        print('  TAUT id=%s  %s  (%s)' % (n, e, d))
    # 反控：构造一个真·恒真校验式，判据必须抓到
    open(os.path.join(sb, 'ctl.txt'), 'wb').close()
    add('D3 反控：grep=.* 在空文件上命中（re.findall 对空串给 1 个匹配）⇒ 判据能抓恒真式',
        run_expr('ctl.txt', 'grep=.*', sb)[0] is True, run_expr('ctl.txt', 'grep=.*', sb))
    add('D4 反控：grep=xyz 在空文件上 0 命中 ⇒ 判据不误抓真判据',
        run_expr('ctl.txt', 'grep=xyz', sb)[0] is False, run_expr('ctl.txt', 'grep=xyz', sb))
    add('D5 反控：grep=^$ 在空文件上命中（空行） ⇒ 也是恒真式，判据抓到',
        run_expr('ctl.txt', 'grep=^$', sb)[0] is True, run_expr('ctl.txt', 'grep=^$', sb))
    add('D6 反控：rows=0 在空文件上给出 0 == 0 ⇒ 恒真式，判据抓到',
        run_expr('ctl.txt', 'rows=0', sb)[0] is True, run_expr('ctl.txt', 'rows=0', sb))
    add('D7 反控：bytes=0 在空文件上给出 0 == 0 ⇒ 恒真式，判据抓到',
        run_expr('ctl.txt', 'bytes=0', sb)[0] is True, run_expr('ctl.txt', 'bytes=0', sb))
finally:
    shutil.rmtree(sb, ignore_errors=True)

ok = sum(1 for x in ck if x['ok'])
json.dump({'checks': ck, 'pass': ok, 'total': len(ck), 'taut': taut},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'] + (('  | ' + str(x['detail'])) if not x['ok'] else ''))
print('%d/%d PASS' % (ok, len(ck)))
