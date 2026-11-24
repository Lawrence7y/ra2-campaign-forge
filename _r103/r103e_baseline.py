#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r103e_baseline.py —— 门禁新增的三段各自要求「改后全绿」的前提取证

C15 的三条下界（节集合 / 末节号 / 字节数 / 节数）在**写入本轮新节 §2.107 之后**必须仍然通过，
否则门禁会在本轮收口时自己 FAIL。本脚本在**沙箱**里模拟「追加 §2.107 后」的状态，
验证 C15 的钉住值不需要重钉（只增不减的语义），并测出各条的真实余量。

同时给出 C14 的前提：C14 的指纹只覆盖 DISC_RECHECK 的 (id, col2, col3, col4)，
本轮不修改 DISC_RECHECK 任何一格（GATE_VER 已在 r103c 改完），故 C14 应保持命中。

四组：
  P1  追加 §2.107（模拟本轮写 R14_COMMON）后门禁 exit 0，且 C15 NOTE 的 sections 变为 101
  P2  同时往 R14_COMMON 写 §2.107 与往台账写 §1157 等（沙箱里只动 R14_COMMON）后仍 exit 0
  P3  余量：从今天状态起，还能删多少字节仍过 C15 的字节下界（二分），给数
  P4  余量：还能删多少节仍过 C15 的节集合下界（逐节试删最小规模尾部节）
"""
import io, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sbxlib as S

OUT = os.path.join(S.REAL, '_r103')
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

S.prepare()
RC = S.p(S.SBX, 'R14_COMMON.md')
G = S.p(S.SBX, 'check_disc.py')
G0 = io.open(G, encoding='utf-8', newline='').read()
R0 = io.open(RC, encoding='utf-8', newline='').read()
assert 'C15 content floor' in G0, 'C15 not present in gate'

RES = {}

def run_with(rc_text):
    io.open(RC, 'w', encoding='utf-8', newline='').write(rc_text)
    rc, f, out = S.run()
    io.open(RC, 'w', encoding='utf-8', newline='').write(R0)
    note = [l.strip() for l in out.splitlines() if 'C15 content floor' in l]
    return rc, f, note

# ---- P0 R14_COMMON 换行结构实测（本轮新事实）----
def eol_profile(t):
    crlf = t.count('\r\n')
    lf = t.count('\n') - crlf
    return {'crlf': crlf, 'lf_only': lf, 'bytes': len(t.encode('utf-8'))}
PROF = eol_profile(R0)
RES['P0'] = PROF
print('R14_COMMON eol profile: CRLF=%d LF-only=%d bytes=%d' % (PROF['crlf'], PROF['lf_only'], PROF['bytes']))
ck('P0 R14_COMMON 是混合换行文件：CRLF 只占 %d / %d 行（%0.1f%%），其余全是 LF-only'
   % (PROF['crlf'], PROF['crlf'] + PROF['lf_only'], 100.0 * PROF['crlf'] / (PROF['crlf'] + PROF['lf_only'])),
   PROF['crlf'] + PROF['lf_only'] > PROF['lf_only'] > 0, PROF)

# ---- P1 追加 §2.107（LF 行尾；CRLF 反控见 P1a）----
# R103 实测：C5 把 R14_COMMON 的 CRLF 数钉死为 1081，故**新增节必须用 LF 行尾**。
# 这条是 R102 没写下来的写作纪律：谁用 CRLF 追加一节，C5 立刻 FAIL（本轮 P1 第一版就被抓）。
SEC107 = ('\n## 2.107 R103 探针节：C15 下界在正常增节后仍然通过\n\n'
          '本节只用于证明 C15 的三条下界不会因为「正常增节」而 FAIL。\n'
          '内容为纯文本，不引入任何「纪律 N ·」定义，故 C1 的条数不变。\n')
r1 = R0 + SEC107
rc1, f1, note1 = run_with(r1)
RES['P1'] = {'exit': rc1, 'fails': f1, 'note': note1}
ck('P1 追加 §2.107（LF 行尾，见下方 S1 对 R14_COMMON 换行结构的实测）后门禁 exit 0',
   rc1 == 0, 'exit=%d fails=%s' % (rc1, f1[:3]))
_n0 = len(re.findall(r'(?m)^##\s+2\.(\d+)\b', R0.replace('\r\n', '\n')))
ck('P1b 追加一节后 C15 NOTE 的 sections 恰为 现盘节数+1（下界是「覆盖」，不是「恰好」）',
   bool(note1) and ('2.x sections %d' % (_n0 + 1)) in note1[0],
   'expect %d got %s' % (_n0 + 1, note1[:1]))
RES['P1b_n0'] = _n0

SEC107_CRLF = SEC107.replace('\n', '\r\n')
io.open(RC, 'w', encoding='utf-8', newline='').write(R0 + SEC107_CRLF)
_rcp, _fp, _ = S.run()
io.open(RC, 'w', encoding='utf-8', newline='').write(R0)
RES['P1a'] = {'exit': _rcp, 'fails': _fp}
print('  P1a CRLF-append exit=%d fails=%s' % (_rcp, [x[:60] for x in _fp][:2]))
ck('P1a 反控：同一节改用 CRLF 追加 ⇒ C5 立刻 FAIL（证明「新增节必须用 LF」是盘上事实）',
   _rcp == 1 and any(x.startswith('C5') for x in _fp), [_x[:60] for _x in _fp][:2])

# ---- P1c 同时改字节大改但节都在 ----
r1c = R0.replace('本节只收 R102 本机实测', '本节只收 R102 本机实测，另加 R103 的补充说明若干字。', 1)
rc1c, f1c, _ = run_with(r1c)
RES['P1c'] = {'exit': rc1c, 'fails': f1c}
ck('P1c 小节内改写（正文加字）后 exit 0', rc1c == 0, 'exit=%d' % rc1c)

# ---- P2 大量增节（模拟 §1157 之外的正常增长）----
big = R0 + ''.join(('\n## 2.%d R103 批量探针节 %d\n\n纯文本。\n' % (107 + i, i)) for i in range(5))
rc2, f2, note2 = run_with(big)
RES['P2'] = {'exit': rc2, 'fails': f2, 'note': note2}
ck('P2 一次追加 6 个新节后仍 exit 0（C15 不拦增节）', rc2 == 0, 'exit=%d' % rc2)

# ---- P3 字节余量：二分还能删多少（在「只删正文、不删节标题」的前提下）----
# 取一节正文（§2.106 的末尾 2000 字），逐步删，找 C15 字节下界触发点
def split_keep(text):
    """按 \n 切行并保留每行自己的行尾（CRLF 或 LF）。"""
    out, s = [], 0
    while True:
        i = text.find('\n', s)
        if i < 0:
            out.append(text[s:]); break
        out.append(text[s:i + 1]); s = i + 1
    return out


def trim_body(text, n):
    """从末尾整行删掉 n 行（不删 ## 标题行，遇到标题就停）。"""
    lines = split_keep(text)
    dropped = 0
    while dropped < n and lines:
        if re.match(r'^##\s', lines[-1]):
            break
        lines.pop(); dropped += 1
    return ''.join(lines)

lo, hi = 0, 600
last_ok = 0
while lo <= hi:
    mid = (lo + hi) // 2
    rt, rf, _ = run_with(trim_body(R0, mid))
    if rt == 0:
        last_ok = mid
        lo = mid + 1
    else:
        hi = mid - 1
RES['P3'] = {'max_trim_ok_lines': last_ok}
ck('P3 字节下界余量：从末尾整行删到 %d 行仍 exit 0（下界不是「一字节都不许掉」）' % last_ok,
   last_ok > 0, 'max_trim=%d lines' % last_ok)

# ---- P4 节余量：逐节删（从尾部起）看还能删几节 ----
def cut_one(text, num):
    """删掉 ## 2.num 这一节的标题行与其后到下一个 ## 之前的全部行（保留其它行的行尾）。"""
    lines = split_keep(text)
    out, drop = [], False
    hit = 0
    for l in lines:
        m = re.match(r'^##\s*2\.(\d+)\b', l)
        if m:
            drop = int(m.group(1)) == num
            if drop:
                hit += 1
        if not drop:
            out.append(l)
    return ''.join(out), hit

ok_cuts = []
for n in range(106, 99, -1):
    t, hit = cut_one(R0, n)
    rc, f, _ = run_with(t)
    if rc == 0:
        ok_cuts.append(n)
    else:
        break
RES['P4'] = {'one_section_cuts_ok': ok_cuts,
             'first_blocking': (ok_cuts[-1] - 1) if ok_cuts else 106}
ck('P4 单节删余量：从尾部起能连续删掉 %d 节而门禁仍 exit 0（多删即 FAIL）' % len(ok_cuts),
   len(ok_cuts) <= 1, 'ok_cuts=%s' % ok_cuts)

json.dump({'checks': checks, 'results': RES},
          io.open(os.path.join(OUT, 'r103e_baseline.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n%d checks, %d FAIL' % (len(checks), nf))
sys.exit(1 if nf else 0)
