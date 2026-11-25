# -*- coding: utf-8 -*-
"""R129l：裁定之后的反控 —— 六条新判据都必须能 FAIL，且不能误伤。

关键代价（必须量出来、不粉饰）：C11 的 ok 计数由 5 降到 0。因为本轮撤回的五条恰是
全表唯一五条能通过 recheck_verify 的行。也就是说：本轮把「5 条自洽但不可能的凭证」
换成了「0 条凭证」，而不是「5 条真凭证」。这是净损失，如实记；它换来的是
「不再有假声称躺在产物里」与「claims-none 的校验式必须有分辨力」两条真判据。

反控：
  M1 正控：不改动，exit 0 且 C10 ok(R129)、C17 pinned 0、C11B gap 12 个 id
  M2 往任一产物塞回一条时间上不可能的假声称并声明有 ⇒ exit 1（C17a 集合变了）
  M3 把某条 claims-none 行的校验式改坏 ⇒ exit 1（R129 新判据）
  M4 把 C17_PIN 改回 5 条但不改摘要 ⇒ exit 1（C17a TAMPERED）
  M5 把 C11B_PIN_GAP 改回 7 个 id ⇒ exit 1（C11b drifted）
  M6 把五条中一条的第 7 列改回「有」而不补行 ⇒ exit 1（C11 claims 有但无行）
"""
import io, os, sys, hashlib, subprocess, json

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(R14, 'check_disc.py')
DR = os.path.join(R14, 'DISC_RECHECK.tsv')
P3 = os.path.join(R14, 'R17_R61_FACTINDEX_V58', 'anchor_check.txt')
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': d if not isinstance(d, (dict, list)) else json.dumps(d, ensure_ascii=False)})

FILES = (GATE, DR, P3)
base = {p: io.open(p, 'rb').read() for p in FILES}
def run():
    r = subprocess.run([sys.executable, 'check_disc.py'], cwd=R14, capture_output=True, text=True, timeout=600)
    return r.returncode, r.stdout + r.stderr

code, out = run()
add('M1 正控：exit 0；C10 ok(R129)；C17 pinned 0；C11b gap 12 个 id；C11 ok=0',
    code == 0 and 'C10 self-check: ok(R129)' in out and '(pinned 0)' in out
    and 'gap(claims-none, can never FAIL)=12' in out and 'ok=0 fail=0' in out,
    {'code': code, 'tail': out[-400:]})

def with_file(path, old_sub, new_sub, label=''):
    raw = base[path].decode('utf-8')
    assert raw.count(old_sub) == 1, '%s: 目标串不是恰好一处（%d）' % (label, raw.count(old_sub))
    try:
        with io.open(path, 'wb') as f:
            f.write(raw.replace(old_sub, new_sub).encode('utf-8'))
        return run()
    finally:
        with io.open(path, 'wb') as f:
            f.write(base[path])

# M2 塞回假声称 + 声明有（两处都要改，先测只塞行）
FAKE = 'DISC_RECHECK discipline=3 round=R55 at=2026-11-22T17:39:19+08:00 anchors=sha256:%s conclusion=PASS\n' % ('a' * 64)
cur_p3 = base[P3].decode('utf-8')
try:
    with io.open(P3, 'wb') as f:
        f.write((cur_p3 + FAKE).encode('utf-8'))
    code, out = run()
finally:
    with io.open(P3, 'wb') as f:
        f.write(base[P3])
add('M2a 往 id 3 的产物塞回一条假声称（第 7 列仍是无）⇒ R128 判据命中 exit 1',
    code == 1 and 'claims-none but its product carries 1 self-description line' in out, {'code': code})

# M2b 同时把第 7 列改回「有」⇒ C11 会因 anchors 不匹配而 fail（假行不是真行）
def with_two(patches):
    try:
        for p, o, n in patches:
            raw = io.open(p, encoding='utf-8').read()
            assert raw.count(o) == 1
            with io.open(p, 'wb') as f:
                f.write(raw.replace(o, n).encode('utf-8'))
        return run()
    finally:
        for p in FILES:
            with io.open(p, 'wb') as f:
                f.write(base[p])

raw = base[P3].decode('utf-8')
raw_dr = base[DR].decode('utf-8')
row3 = [l for l in raw_dr.split('\n') if l.startswith('3\t') and len(l.split('\t')) == 7][0]
c = row3.split('\t'); c[6] = '有（后续轮回跑）'
row3_new = '\t'.join(c)
code, out = with_two([(P3, '\n'.join([l for l in raw.split('\n')])[-1] and (raw.rstrip('\n')), raw.rstrip('\n') + '\n' + FAKE),
                      (DR, row3, row3_new)])
add('M2b 塞回假声称 + 第 7 列改回有 ⇒ exit 1（anchors 与真行不同，C11 抓）',
    code == 1, {'code': code, 'hit': [l for l in out.splitlines() if 'C11 id 3' in l][:2]})

# M3 改坏一条 claims-none 校验式
code, out = with_file(DR, 'grep=控制组总判定：\\*\\*PASS', 'grep=控制组总判定：\\*\\*GONE')
add('M3 改坏 id 11 的校验式 ⇒ exit 1 命中 (R129)', code == 1 and '(R129)' in out, {'code': code})

# M4 C17_PIN 改回 5 条不改摘要
code, out = with_file(GATE, 'C17_PIN = set()',
                      "C17_PIN = {(3, 55, '2026-11-22T17:39:19+08:00')}")
add('M4 C17_PIN 改回非空但不改摘要 ⇒ exit 1（C17a 集合变了 + TAMPERED）',
    code == 1 and ('C17a' in out), {'code': code})

# M5 C11B_PIN_GAP 改回 7 个 id
code, out = with_file(GATE, 'C11B_PIN_GAP = [3, 4, 11, 12, 13, 14, 15, 17, 22, 26, 27, 28]',
                      'C11B_PIN_GAP = [11, 12, 13, 14, 15, 17, 26]')
add('M5 C11B_PIN_GAP 改回 7 个 id ⇒ exit 1（C11b drifted）', code == 1 and 'C11b' in out, {'code': code})

# M6 五条中一条改回「有」而不补行
code, out = with_two([(DR, row3, row3_new)])
add('M6 把 id 3 的第 7 列改回有但不补行 ⇒ exit 1（C11 claims 有但无有效行）',
    code == 1 and 'C11 id 3 claims recheck but has no valid' in out,
    {'code': code, 'hit': [l for l in out.splitlines() if 'C11 id 3' in l][:2]})

# 收尾
for p in FILES:
    add('M7 收尾断言 %s 字节回到基线（%s）' % (os.path.basename(p), hashlib.sha256(base[p]).hexdigest()[:16]),
        io.open(p, 'rb').read() == base[p])

ok = sum(1 for x in ck if x['ok'])
json.dump({'checks': ck, 'pass': ok, 'total': len(ck)},
          open(os.path.join(ROOT, '_r129', 'r129l_ruling_ctrl.json'), 'w'), ensure_ascii=False, indent=1)
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'] + (('  | ' + str(x['detail'])) if not x['ok'] else ''))
print('%d/%d PASS' % (ok, len(ck)))
sys.exit(0 if ok == len(ck) else 1)
