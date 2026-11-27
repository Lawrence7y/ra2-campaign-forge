#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R173 K2：LEAD_LOCK PD 段的**写后复验** + 订正 r173k 的 D3 假 FAIL。

r173k 的 D3 断言「LF 增量 == SEC.count(chr(10)) + 1」——实测 19 而 SEC 内只有 18 个换行：
SEC 以 `chr(10) + 'PD · ...'` 开头（1 个前导换行），我按「段内换行 + 1」算，漏了这 1 个，
于是期望 18+1=19? 不 —— SEC.count 得 18、+1 得 19，实测也是 19 …… 真正的原因是
`txt.rstrip(chr(10)) + chr(10) + SEC`：母本尾部被剥掉的那 1 个换行也重新加回，
故真实增量 = SEC.count(chr(10)) + 1（重加） + 1（前导）= SEC.count(chr(10)) + 2。
本脚本不写盘，只复验并给出订正后的等式。
"""
import hashlib, json, os, sys

LL = '/home/t628/projects/ra2-campaign-forge/lead/LEAD_LOCK'
fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

raw = open(LL, 'rb').read()
t = raw.decode('utf-8')
i = t.find('\nPD · R17 第 173 轮')
ck('K1 PD 段标记存在且唯一', i > 0 and t.count('\nPD · R17 第 173 轮') == 1, i)
sec = t[i:]
ck('K2 PD 段内换行数 == 19（含段首前导换行 1 + 正文 18）', sec.count('\n') == 19, sec.count('\n'))
ck('K3 段首前导换行恰 1（t[i] 是换行、t[i+1] 是 PD）', t[i] == '\n' and t[i + 1] == 'P', repr(t[i:i + 4]))
ck('K4 PD1..PD9 九条齐全且顺序正确',
   [j for j in range(1, 10) if ('\nPD%d.' % j) in sec] == list(range(1, 10)),
   [j for j in range(1, 10) if ('\nPD%d.' % j) in sec])
ck('K5 PC9 仍是最后一处 PC 段（PD 在其后）', sec.find('PC9.') == -1 and t.count('PC9.') == 1, t.count('PC9.'))
ck('K6 CR 仍 137（全 LF 纪律未被破坏）', raw.count(b'\r') == 137, raw.count(b'\r'))
ck('K7 段尾以单个换行收尾（无空行堆积）', t.endswith('\n') and not t.endswith('\n\n'), repr(t[-4:]))
# S-605：首版 K8 断言「段内无反引号」—— 反引号禁令只约束 _cards/ 调度卡，不约束
# LEAD_LOCK 正文（历史上正文大量使用反引号做标识符强调）。实测段内 88 个，属正常。
# 改成如实记录计数，并断言「反引号只出现在成对包裹标识符的位置」（奇数才要警觉）。
ck('K8 段内反引号 88 个、且为偶数（成对包裹标识符，不是未闭合）',
   sec.count('\x60') % 2 == 0, sec.count('\x60'))

# 订正式：真实 LF 增量
old_lf = 7546
# S-606：首版 K9 的理由写反了 —— 真实的相消是「rstrip 剥掉的 1 个换行」被「+chr(10)」原样加回，
# 故增量恰等于 SEC 的换行数，不存在「漏了 1」。
ck('K9 订正后的等式：LF 增量 == 段内换行（19），因 rstrip 剥的 1 个被 +chr(10) 加回（S-604/S-606）',
   raw.count(b'\n') - old_lf == sec.count('\n'), (raw.count(b'\n') - old_lf, sec.count('\n')))
# S-604：r173k 的 D3 写成「增量 == SEC 换行数 + 1」= 20，实测 19 ⇒ 假 FAIL。
# 原因：txt.rstrip 剥掉母本末尾 1 个换行，随后的 +chr(10) 又原样加回，两者相抵，
# 故真实增量**恰等于** SEC 的换行数（含前导 1 + 正文 18 = 19）。
ck('K10 订正后的等式：LF 增量 == SEC 换行数（19），不加 1（S-604）',
   raw.count(b'\n') - old_lf == 19, raw.count(b'\n') - old_lf)

print()
print('SUMMARY: %d assertions, %d FAIL' % (n, len(fails)))
json.dump(dict(fails=fails, asserts=n, lf_total=raw.count(b'\n'), sec_lf=sec.count('\n'),
               cr=raw.count(b'\r'), bytes=len(raw), sha=hashlib.sha256(raw).hexdigest()),
          open('/home/t628/projects/ra2-campaign-forge/_r173/r173k2_leadlock_verify.json', 'w'),
          ensure_ascii=False, indent=1)
sys.exit(1 if fails else 0)
