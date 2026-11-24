# -*- coding: utf-8 -*-
"""FACT_INDEX v5.18：F24 第五次改写 —— 撤回档 C 作为引用值，只引档 A。
起因：审计员 T1（R42）判定档 C 判据不成立，且 F24 自带的「384 个 / 258,794,083 B」脚注与实测不符
（我实测 375 行 / 184,618,279 B；审计员实测 333 行 / 184,506,382 B；两者都与脚注差约 74 MB）。
处置：statement 只保留档 A；limitations 记录档 C 撤回及其理由与三个实测数。
纪律：只改 F24 statement + limitations；单元格禁换行；其余 53 行逐字节不变；禁不可见字符；括号配平。
"""
import io, os, re, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC  = os.path.join(R14, 'R17_R76_FACTINDEX_V517')
DST  = os.path.join(R14, 'R17_R77_FACTINDEX_V518')
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
old_stmt = f24[1]

m = re.search(r'675 行已做有界内容级搜索.*?不是「指针没连上」。', old_stmt, re.S)
assert m, old_stmt[:160]

NEW = (
 '675 行已做有界内容级搜索。**规模数只能当「某次测量的快照」引用，且必须连口径一起引**。'
 '**唯一可引用值 · 档 A** = 24,723 文件 / 1,589,964,358 B = 1.589964 GB(10^9) = 1.480770 GiB(2^30)；'
 '口径 = 6 扩展名 .tsv/.txt/.json/.md/.csv/.log、根 `lead\\`、只排 `.git` 与本卡 out 目录、'
 '**含全部自身产物**、快照 2026-11-22T04:31Z；逐文件清单 `files_tier_A_snap2.tsv` 可 sum(bytes) 复核；'
 '双实现正控（PowerShell BFS 与 Python os.scandir）同得 24,723，差 3 B 已定位为 38 秒时间差。'
 '**档 C（23,347 文件 / 1,300,742,927 B）已撤回、不得引用**：其 `selfkind` 分类经跨家族审计判为不成立——'
 '同类对象里 72 个 `*_report.md`（1,029,652 B）被判为自身产物而排除，'
 '208 个裸 `REPORT.md`（2,267,327 B）却全部空标签被留在域内；'
 '且它自带的「仍含 384 个 / 258,794,083 B 回滚副本」脚注与实测不符'
 '（我实测 375 行 / 184,618,279 B，审计员实测 333 行 / 184,506,382 B，两者均与脚注差约 74 MB）。'
 '**漂移分解（11:55→12:31 这一对快照，逐字节闭合）**：旧 24,676 / 1,586,426,788 B + 新增 47 / 3,525,160 B '
 '+ 改写净 12,410 B = 新 24,723 / 1,589,964,358 B；其中**自身产物 37 文件 / 净 +3,441,605 B**、'
 '**树真实增长 15 文件 / 净 +95,965 B** ⇒ 该窗口约 **97%** 增量是测量与记录自身产物、约 **2.7%** 是树在长；'
 '**但此分解只解释这一对快照，不可移用于历史漂移**。'
 '**三个旧数一律作废**：23,791（11-21「无产物」口径，与含产物测量不可比）；'
 '24,693 / 1,586,613,509（总量与它自己的清单差 17 文件 / 186,721 B）；'
 '24,692 / 1,506,032,984（由虚高的「总量−1」推出，不可复现）。'
 '**最大的自身产物不是命中清单而是备份**：`*_out.txt` 1,270 个 / 204,774,282 B、'
 '`LEDGER.before_*` 20 个 / 87,604,146 B（后者单类就大于 `_hits_primary.tsv` 的 80,580,525 B）；'
 '`mev675.py` 的 `stage_scale` 只排除 `.git` 与 `--out` 目录，**不排除自身产物**。'
 '口径注意：扩展名限制缩小的是**体积比**（约 58 倍），**文件数比仅 2.86 倍**（68,038→23,791）。')

assert '\n' not in NEW
new_stmt = old_stmt.replace(m.group(0), NEW + '真实四环回指 = 0'
                            '（检测器对已知 11 行正控召回 11/11，故该 0 有判别力）'
                            '⇒ 791 行属「事实层面没有逐 entry 四环证据」，不是「指针没连上」。')
assert new_stmt != old_stmt

NEW_LIM = ('『改指针无解、不再投卡』是 Lead 行动裁决（台账 §1054），不入本条证据、不随数字一并作已证；'
           '数字与负结论；归因见 §16.1；R_OK 863 是「至少一个路径解析到真实文件」，不等于「逐 entry 专属证据」；'
           '引 §16.1 只能引其「判据」，其表内数字是历史快照（旧 478/374/802），数字须取现盘；'
           '规模数一律须标「测量时刻 + 脚本 + 遍历根 + 扩展名集合 + 排除项」，缺任一项即不可引用；'
           '**只引档 A**；档 C 已撤回——理由是分类判据经跨家族审计判为不成立（208 个裸 REPORT.md / 2,267,327 B '
           '被留在域内、72 个 *_report.md / 1,029,652 B 被排除，同类对象被劈成两半且方向相反），'
           '且其自带脚注「384 个 / 258,794,083 B」与两份独立实测均差约 74 MB；'
           '审计另指出同族漏排：`*_out.json` 372 个 / 19,281,606 B 与含 stdout/stderr 的 789 个 / 14,443,509 B 未被任何判据覆盖；'
           '漂移分解只成立于 11:55→12:31 这一对快照、且沿用未审计的 selfkind 口径，不可移用于历史漂移；'
           '三个旧数（23,791、24,693、24,692）一律不得再引用；'
           '「1.29 GiB」是 `mev675.py:281` 用 /1024³ 却标 GB 的产物，勿写作 GB；「58 倍」只对体积成立。')
assert '\n' not in NEW_LIM

f24[1] = new_stmt
f24[4] = NEW_LIM
ADDS = [r'lead\next_re_20261117_r14\R17_R75_T1_AUDITSELF\REPORT.md']
for a in ADDS:
    assert a not in f24[3]
    assert os.path.isfile(os.path.join(ROOT, a.replace('\\', '/'))), a
    f24[3] = f24[3] + ';' + a

out = '\n'.join([lines[0]] + ['\t'.join(r) for r in rows]) + '\n'
assert '\r' not in out
for ch in ('\u200b', '\u200c', '\u200d', '\ufeff', '\u2060', '\u00a0'):
    assert ch not in out, 'invisible U+%04X' % ord(ch)
assert new_stmt.count('（') == new_stmt.count('）'), (new_stmt.count('（'), new_stmt.count('）'))
assert '档 C = 23,347 文件 / 1,300,742,927 B 不得当作' not in new_stmt, 'old tier-C phrasing still present'

dst = os.path.join(DST, 'FACT_INDEX.tsv')
assert not os.path.exists(dst)
with open(dst, 'x', encoding='utf-8', newline='') as f:
    f.write(out)

back = io.open(dst, encoding='utf-8', newline='').read()
assert back == out
assert back.count('\n') == 55, back.count('\n')
assert back.count('\t') == 55 * 4, back.count('\t')
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
