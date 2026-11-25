# -*- coding: utf-8 -*-
"""R129f：R129 那条新判据的反控 —— 它必须能 FAIL。

四条反控（沿用 R126 S-161 之后的稳妥做法：正本改名藏起，把改过的副本放到正本路径上跑，
finally 恢复并断言 sha；**不用临时目录**，因为 check_disc.py 用写死的绝对路径读文档）：
  F1 正控：不改任何东西，exit 0 且 C10 显示 ok(R129)
  F2 把某条 claims-none 行的校验式改成当前不成立的式子 ⇒ exit 1 且命中断言 (R129)
  F3 把同一条改成「永远成立」的 rows=0（空表也算 0 行）⇒ exit 1 且命中同一条新判据
  F4 把某条 claims-none 行的产物路径指向不存在的文件 ⇒ exit 1（C7 与 C11 都会响）
收尾断言：三份正本字节回到改动前。
"""
import io, os, sys, hashlib, subprocess, shutil, datetime, json

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(R14, 'check_disc.py')
DR = os.path.join(R14, 'DISC_RECHECK.tsv')
RC = os.path.join(R14, 'R14_COMMON.md')
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')

sha = lambda b: hashlib.sha256(b).hexdigest()[:16]
base = {p: io.open(p, 'rb').read() for p in (GATE, DR, RC)}
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': d if not isinstance(d, (dict, list)) else json.dumps(d, ensure_ascii=False)})

def run():
    r = subprocess.run([sys.executable, 'check_disc.py'], cwd=R14,
                       capture_output=True, text=True, timeout=600)
    return r.returncode, r.stdout + r.stderr

# F1 正控
code, out = run()
add('F1 正控：不改动，exit 0 且 C10 显示 ok(R129)',
    code == 0 and 'C10 self-check: ok(R129)' in out, {'code': code, 'tail': out[-200:]})

def with_dr_replaced(old_sub, new_sub, label):
    """把 DISC_RECHECK.tsv 中 old_sub 换成 new_sub，跑一次门禁，finally 恢复。"""
    raw = base[DR].decode('utf-8')
    assert raw.count(old_sub) == 1, '%s: 目标串不是恰好一处（%d）' % (label, raw.count(old_sub))
    tmp = raw.replace(old_sub, new_sub)
    try:
        with io.open(DR, 'wb') as f:
            f.write(tmp.encode('utf-8'))
        return run()
    finally:
        with io.open(DR, 'wb') as f:
            f.write(base[DR])

# F2 改成不成立的式子
code, out = with_dr_replaced('grep=控制组总判定：\\*\\*PASS', 'grep=控制组总判定：\\*\\*NOPE', 'F2')
add('F2 把 id 11 的校验式改成当前不成立 ⇒ exit 1 且命中新判据 (R129)',
    code == 1 and 'claims-none but its check expression no longer holds' in out and '(R129)' in out,
    {'code': code, 'hit': [l for l in out.splitlines() if 'claims-none but its check' in l][:2]})

# F3 改成恒真式
code, out = with_dr_replaced('grep=控制组总判定：\\*\\*PASS', 'rows=0', 'F3')
add('F3 把 id 11 改成 rows=0（空表也算 0 行 ⇒ 恒真式）⇒ exit 1 且命中新判据',
    code == 1 and 'check expression no longer holds' in out,
    {'code': code, 'hit': [l for l in out.splitlines() if 'claims-none but its check' in l][:2]})

# F4 产物路径指向不存在
# S-188：首版拿「产物路径」当替换目标，但 id 11 与 12 共用同一个产物 ⇒ 出现 2 次而断言炸了。
# 换成「整行」做目标（含 id 与校验式，行内唯一）。
_row11 = [l for l in base[DR].decode('utf-8').split('\n') if l.startswith('11\t')]
assert len(_row11) == 1
code, out = with_dr_replaced(_row11[0], _row11[0].replace('checkC3_report.md', 'no_such_file.md'), 'F4')
add('F4 把 id 11/12 的产物路径改成不存在 ⇒ exit 1',
    code == 1 and 'FILE_MISSING' in out, {'code': code})

# 收尾：三份正本字节必须回到基线
for p in (GATE, DR, RC):
    add('F5 收尾断言 %s 字节回到基线（%s）' % (os.path.basename(p), sha(base[p])),
        io.open(p, 'rb').read() == base[p], sha(io.open(p, 'rb').read()))

ok = sum(1 for x in ck if x['ok'])
json.dump({'checks': ck, 'pass': ok, 'total': len(ck)},
          open(os.path.join(ROOT, '_r129', 'r129f_gate_ctrl.json'), 'w'), ensure_ascii=False, indent=1)
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'] + (('  | ' + str(x['detail'])) if not x['ok'] else ''))
print('%d/%d PASS' % (ok, len(ck)))
sys.exit(0 if ok == len(ck) else 1)
