# -*- coding: utf-8 -*-
"""FACT_INDEX v5.16：F24 的规模段第三次重写（档 A + 档 C 双档 + 清单锚 + 三旧数作废）。
纪律：读 v5.15 → 只改 F24 statement/limitations/evidence_paths → 其余逐字节不变 → 禁不可见字符 → 括号配平。
"""
import io, os, re, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC  = os.path.join(R14, 'R17_R73_FACTINDEX_V515')
DST  = os.path.join(R14, 'R17_R74_FACTINDEX_V516')
os.makedirs(DST, exist_ok=True)

raw = io.open(os.path.join(SRC, 'FACT_INDEX.tsv'), encoding='utf-8', newline='').read()
assert '\r' not in raw
lines = raw.split('\n')
data = [l for l in lines[1:] if l.strip()]
assert len(data) == 54
rows = [l.split('\t') for l in data]
byid = {r[0]: r for r in rows}
f24 = byid['F24']
old_stmt = f24[1]

m = re.search(r'675 行已做有界内容级搜索.*?不是「指针没连上」。', old_stmt, re.S)
assert m, old_stmt[:200]

NEW_SCALE = (
    '675 行已做有界内容级搜索。**规模数只能当「某次测量的快照」引用，且必须连口径一起引；三个旧数已作废**：'
    '① 作废 23,791 文件 / 1,383,739,755 B（2026-11-21 记录，当日「无产物」，与后来的含产物测量**不可比**，故不可与下述两档并列）；'
    '② 作废 24,693 / 1,586,613,509 与 24,692 / 1,506,032,984（2026-11-22 两次转录）——前者总量与它自己的逐文件清单不符'
    '（清单仅 24,676 行 / 1,586,426,788 B，差 17 文件 / 186,721 B），后者由虚高的「总量−1」推出，**二者均不可复现**。'
    '**改用下述两档（各有逐文件清单可 sum(bytes) 复核）**：'
    '**档 A** = 24,723 文件 / 1,589,964,358 B = 1.589964 GB(10^9) = 1.480770 GiB(2^30)，'
    '口径 = 6 扩展名 .tsv/.txt/.json/.md/.csv/.log、根 `lead\\`、只排 `.git` 与本卡 out 目录、**含全部自身产物**、'
    '快照 2026-11-22T04:31Z，清单 `files_tier_A_snap2.tsv`；'
    '**档 C** = 23,347 文件 / 1,300,742,927 B = 1.300743 GB = 1.211411 GiB，'
    '口径 = 档 A 再排 1,376 个 / 289,221,428 B 的测量与记录类自身产物（清单 `files_tier_C.tsv`）——'
    '注意此档**仍含** 384 个 / 258,794,083 B 的其它回滚副本，**不是「不含任何自身产物」的下界**。'
    '**最大的自身产物不是命中清单而是备份**：`LEDGER.before_*` 20 个文件即 87,604,146 B、`*_out.txt` 1,270 个即 204,774,282 B；'
    '`mev675.py` 的 `stage_scale` 只排除 `.git` 与 `--out` 目录，**不排除自身产物**。'
    '口径注意：扩展名限制缩小的是**体积比**（约 58 倍），**文件数比仅 2.86 倍**（68,038→23,791）。')

new_stmt = old_stmt.replace(m.group(0), NEW_SCALE + '真实四环回指 = 0'
                            '（检测器对已知 11 行正控召回 11/11，故该 0 有判别力）'
                            '⇒ 791 行属「事实层面没有逐 entry 四环证据」，不是「指针没连上」。')
assert new_stmt != old_stmt

NEW_LIM = ('『改指针无解、不再投卡』是 Lead 行动裁决（台账 §1054），不入本条证据、不随数字一并作已证；'
           '数字与负结论；归因见 §16.1；R_OK 863 是「至少一个路径解析到真实文件」，不等于「逐 entry 专属证据」；'
           '引 §16.1 只能引其「判据」，其表内数字是历史快照（旧 478/374/802），数字须取现盘；'
           '规模数一律须标「测量时刻 + 脚本 + 遍历根 + 扩展名集合 + 排除项」，缺任一项即不可引用；'
           '三个旧数（23,791、24,693、24,692）**一律不得再引用**，理由见 statement；'
           '档 A 与档 C 的差不是「误差」，是「是否计入度量与记录自身产物」这件口径；'
           '「1.29 GiB」是 `mev675.py:281` 用 /1024³ 却标 GB 的产物，勿写作 GB；「58 倍」只对体积成立。')

EV_ADDS = [r'lead\next_re_20261117_r14\R17_R72_T1_CLEANSCALE\REPORT.md',
           r'lead\next_re_20261117_r14\R17_R72_T1_CLEANSCALE\files_tier_A_snap2.tsv',
           r'lead\next_re_20261117_r14\R17_R72_T1_CLEANSCALE\files_tier_C.tsv']

f24[1] = new_stmt
f24[4] = NEW_LIM
for a in EV_ADDS:
    assert a not in f24[3]
    f24[3] = f24[3] + ';' + a

out = '\n'.join([lines[0]] + ['\t'.join(r) for r in rows]) + '\n'
assert '\r' not in out
for ch in ('\u200b', '\u200c', '\u200d', '\ufeff', '\u2060', '\u00a0'):
    assert ch not in out, 'invisible U+%04X' % ord(ch)
assert new_stmt.count('（') == new_stmt.count('）'), (new_stmt.count('（'), new_stmt.count('）'))

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
    assert a[0] == b[0]
    if a[0] != 'F24':
        assert a == b, 'unexpected change ' + a[0]
dist = {}
for b in brows:
    dist[b[2]] = dist.get(b[2], 0) + 1
assert dist.get('[已证]') == 27 and dist.get('[静态推断]') == 1 and dist.get('未取得') == 2 and dist.get('[流程]') == 24

# 新增锚必须真实存在
for a in EV_ADDS:
    p = os.path.join(ROOT, a.replace('\\', '/'))
    assert os.path.isfile(p), a

print('OK', dst, os.path.getsize(dst), 'bytes')
print('sha256 =', hashlib.sha256(back.encode()).hexdigest().upper())
print('grade dist =', dist)
print('evidence items =', len(f24[3].split(';')))
