# -*- coding: utf-8 -*-
"""FACT_INDEX v5.20：F24 引入语义重分类的 C′（三条限定）+ 旧档 C 标为已被 C′ 取代。
我独立复算：C′=18,712/1,363,708,720 ; excluded=6,011/226,255,638（EXCL 4,769/179,570,859 + UNDECIDED 1,242/46,684,779）;
C′+excluded = 24,723/1,589,964,358 = 档 A 精确闭合。
"""
import io, os, re, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC  = os.path.join(R14, 'R17_R79_FACTINDEX_V519')
DST  = os.path.join(R14, 'R17_R80_FACTINDEX_V520')
os.makedirs(DST, exist_ok=True)

raw = io.open(os.path.join(SRC, 'FACT_INDEX.tsv'), encoding='utf-8', newline='').read()
assert '\r' not in raw
lines = raw.split('\n')
data = [l for l in lines[1:] if l.strip()]
assert len(data) == 54
rows = [l.split('\t') for l in data]
for r in rows:
    assert len(r) == 5, (r[0], len(r))
f24 = {r[0]: r for r in rows}['F24']
old = f24[1]

m = re.search(r'675 行已做有界内容级搜索.*?不是「指针没连上」。', old, re.S)
assert m, old[:160]

NEW = (
 '675 行已做有界内容级搜索。**规模数只能当「某次测量的快照」引用，且必须连口径（含正则 flags）一起引**。'
 '**主引用值 · 档 A** = 24,723 文件 / 1,589,964,358 B = 1.589964 GB(10^9) = 1.480770 GiB(2^30)；'
 '口径 = 6 扩展名 .tsv/.txt/.json/.md/.csv/.log、根 `lead\\`、只排 `.git` 与本卡 out 目录、'
 '**含全部自身产物**、快照 2026-11-22T04:31Z；逐文件清单 `files_tier_A_snap2.tsv`，双实现正控同得 24,723（差 3 B 已定位为 38 秒时间差）。'
 '**语义重分类值 · C′** = 18,712 文件 / 1,363,708,720 B = 1.363709 GB = 1.270053 GiB'
 '（「被测对象优先」口径：内容第一顺位、名字只作嫌疑；逐文件清单 `files_tier_Cprime.tsv` 含 why 列），'
 '**我独立复算：C′ + 被排 6,011 / 226,255,638 B = 24,723 / 1,589,964,358 B，与档 A 精确闭合**。'
 '**引用 C′ 必须同引三条限定**：① 它是「被测对象优先」口径，与旧档 C 相比最大单项变化不是「排得更多」，'
 '而是把 **150,790,634 B 真反汇编从 `_out.txt` 里捞回（+169 件）**、并把 19,281,606 B 的 `_out.json` 排掉；'
 '② 口径外有 **1,242 件 / 46,684,779 B 落在 `EVIDENCE\\` 内的冲突件**（目录名声明 vs 内容形态相悖）**单列、既不计入 C′ 也不算已排除**，'
 '若要「干净上限」只能是 **18,712~19,954 文件 / 1,363,708,720~1,410,393,499 B**；'
 '③ 它对 `EVIDENCE` 族最敏感（该族占 C′ 的 19.9%），**不可写成「不含任何自身产物的下界」**——'
 '它仍含 657 件报告类文档（4,049,017 B）与 30 件孤本 `GOAL_backup_before_*`（49,533,898 B）。'
 '**旧档 C（23,347 / 1,300,742,927 B）已被 C′ 取代、不再引用**：其实体值可复现（= 档 A 减 selfkind 非空的 1,376 行），'
 '但其 `selfkind` 判据的语义自洽性被判为不成立（72 个 `*_report.md` 被排而 208 个裸 `REPORT.md` 被留；'
 '`*_out.json` 372 个 / 19,281,606 B 与 stdout 789 个 / 14,443,509 B 未覆盖）；'
 '其旧脚注「仍含 384 个 / 258,794,083 B」属**范围错标**（该数为档 A 全集口径；档 C 实际按 re.I 为 375 / 184,618,279，无 re.I 为 333 / 184,506,382，'
 '差 42 行 / 111,897 B 全为 `BEFORE_AFTER.txt`，根因是 `re.I` 标志丢失）。'
 '**漂移分解（11:55→12:31 这一对快照，逐字节闭合）**：旧 24,676 / 1,586,426,788 B + 新增 47 / 3,525,160 B '
 '+ 改写净 12,410 B = 新 24,723 / 1,589,964,358 B；其中自身产物 37 文件 / 净 +3,441,605 B、'
 '树真实增长 15 文件 / 净 +95,965 B ⇒ 该窗口约 97% 增量是测量与记录自身产物、约 2.7% 是树在长；'
 '**此分解只解释这一对快照，不可移用于历史漂移**。'
 '**三个旧数一律作废**：23,791（11-21「无产物」口径，不可比）；24,693 / 1,586,613,509（总量与自身清单差 17 文件 / 186,721 B）；'
 '24,692 / 1,506,032,984（由虚高的「总量−1」推出）。'
 '**最大的自身产物不是命中清单而是备份**：`*_out.txt` 1,270 个 / 204,774,282 B、`LEDGER.before_*` 20 个 / 87,604,146 B；'
 '`mev675.py` 的 `stage_scale` 只排除 `.git` 与 `--out` 目录。'
 '口径注意：扩展名限制缩小的是**体积比**（约 58 倍），**文件数比仅 2.86 倍**（68,038→23,791）。')

assert '\n' not in NEW
new_stmt = old.replace(m.group(0), NEW + '真实四环回指 = 0'
                       '（检测器对已知 11 行正控召回 11/11，故该 0 有判别力）'
                       '⇒ 791 行属「事实层面没有逐 entry 四环证据」，不是「指针没连上」。')
assert new_stmt != old

NEW_LIM = ('『改指针无解、不再投卡』是 Lead 行动裁决（台账 §1054），不入本条证据、不随数字一并作已证；'
           '数字与负结论；归因见 §16.1；R_OK 863 是「至少一个路径解析到真实文件」，不等于「逐 entry 专属证据」；'
           '引 §16.1 只能引其「判据」，其表内数字是历史快照（旧 478/374/802），数字须取现盘；'
           '规模数一律须标「测量时刻 + 脚本 + 遍历根 + 扩展名集合 + 排除项 + 正则 flags」，缺任一项即不可引用；'
           '**档 A 为主引用值；C′ 为语义重分类值**，引用 C′ 必须同引三条限定（被测对象优先口径 / 1,242 件 46,684,779 B 冲突件单列 / '
           '对 EVIDENCE 敏感且非下界）；**旧档 C 已被 C′ 取代、不得再引用**；'
           '旧档 C 的 375 与 333 两数分别对应 re.I 与无 re.I（差 42 行 / 111,897 B，全为 BEFORE_AFTER.txt）；'
           '漂移分解只成立于 11:55→12:31 这一对快照、沿用未审计的 selfkind 口径，不可移用于历史漂移；'
           '三个旧数（23,791、24,693、24,692）一律不得再引用；'
           '「1.29 GiB」是 `mev675.py:281` 用 /1024³ 却标 GB 的产物；「58 倍」只对体积成立。')
assert '\n' not in NEW_LIM

f24[1] = new_stmt
f24[4] = NEW_LIM
ADDS = [r'lead\next_re_20261117_r14\R17_R78_T1_RECLASS\REPORT.md',
        r'lead\next_re_20261117_r14\R17_R78_T1_RECLASS\files_tier_Cprime.tsv']
for a in ADDS:
    assert a not in f24[3]
    assert os.path.isfile(os.path.join(ROOT, a.replace('\\', '/'))), a
    f24[3] = f24[3] + ';' + a

out = '\n'.join([lines[0]] + ['\t'.join(r) for r in rows]) + '\n'
assert '\r' not in out
for ch in ('\u200b', '\u200c', '\u200d', '\ufeff', '\u2060', '\u00a0'):
    assert ch not in out, 'invisible U+%04X' % ord(ch)
assert new_stmt.count('（') == new_stmt.count('）'), (new_stmt.count('（'), new_stmt.count('）'))
# 关键数字自洽
assert 18712 + 6011 == 24723
assert 1363708720 + 226255638 == 1589964358
assert 4769 + 1242 == 6011 and 179570859 + 46684779 == 226255638

dst = os.path.join(DST, 'FACT_INDEX.tsv')
assert not os.path.exists(dst)
with open(dst, 'x', encoding='utf-8', newline='') as f:
    f.write(out)

back = io.open(dst, encoding='utf-8', newline='').read()
assert back == out
assert back.count('\n') == 55 and back.count('\t') == 55 * 4
brows = [l.split('\t') for l in back.split('\n')[1:] if l.strip()]
assert len(brows) == 54
for a, b in zip(rows, brows):
    assert a[0] == b[0] and len(b) == 5
    if a[0] != 'F24':
        assert a == b, 'unexpected change ' + a[0]
dist = {}
for b in brows:
    dist[b[2]] = dist.get(b[2], 0) + 1
assert dist.get('[已证]') == 27 and dist.get('[静态推断]') == 1 and dist.get('未取得') == 2 and dist.get('[流程]') == 24

print('OK', dst, os.path.getsize(dst), 'bytes')
print('sha256 =', hashlib.sha256(back.encode()).hexdigest().upper())
print('grade dist =', dist, '; F24 evidence items =', len(f24[3].split(';')))
