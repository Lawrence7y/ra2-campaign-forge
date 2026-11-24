# -*- coding: utf-8 -*-
# R69 · FACT_INDEX v5.30 -> v5.31
# 只改 3 个单元格：F24.statement / F24.limitations / F29.limitations
# 依据：_r69/verify_f24_stmt_r69.py、_r69/recompute_audit_r69.py（均带正反控）
# 写入纪律：wx 独占备份 -> 断言旧 sha256 与 CR -> 一次性写入 -> 回读校验
import os, sys, hashlib, io

R14  = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
SRC  = os.path.join(R14, 'R17_R102_FACTINDEX_V530/FACT_INDEX.tsv')
DSTD = os.path.join(R14, 'R17_R103_FACTINDEX_V531')
DST  = os.path.join(DSTD, 'FACT_INDEX.tsv')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
DRY  = '--dry' in sys.argv

OLD_SHA = '2bcc30af97654933'      # 实测（本轮 verify_limref_r69.py 打印）
fails, buf = [], []
def W(s=''):
    print(s); buf.append(s)
def ck(n, c, d=''):
    W(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: fails.append(n)

raw = open(SRC, 'rb').read()
ck('旧文件 CR=0', raw.count(b'\r') == 0)
ck('旧文件 sha256 前缀 == 实测值 %s' % OLD_SHA,
   hashlib.sha256(raw).hexdigest().startswith(OLD_SHA), hashlib.sha256(raw).hexdigest()[:16])
ck('旧文件 55 行（表头+54）', raw.count(b'\n') == 55, str(raw.count(b'\n')))
W('[before] %d B  CR=%d  LF=%d  sha=%s' % (len(raw), raw.count(b'\r'), raw.count(b'\n'),
                                           hashlib.sha256(raw).hexdigest()[:16]))

text = raw.decode('utf-8')
lines = text.rstrip('\n').split('\n')
hdr = lines[0].split('\t')
rows = [l.split('\t') for l in lines[1:]]
ck('表头 5 列', hdr == ['fact_id', 'statement', 'grade', 'evidence_paths', 'limitations'])
ck('54 数据行', len(rows) == 54)
ck('每行 5 列', all(len(r) == 5 for r in rows))
idx = {r[0]: i for i, r in enumerate(rows)}

# ============ 改动 1：F24.statement ============
F24 = rows[idx['F24']]
old_stmt_frag = '**本值经 R53 重判、R54 落清单、R60 剔段、R62/R63 三件翻对象侧四步**'
new_stmt_frag = ('**本值经 R53 重判、R54 落清单、R60 剔段、R62/R63 三件翻对象侧、'
                 'R64 再翻一件五步**')
ck('正控：F24 原文含「四步」短语且仅 1 次', F24[1].count(old_stmt_frag) == 1,
   str(F24[1].count(old_stmt_frag)))
ck('反控：「五步」在原文中不存在（改动有判别力）', '五步' not in F24[1])

# 溯源括号：追加 R64 终值
old_trace = ('（溯源：4,518 件 / 724,479,859 B → 4,413 件 / 744,172,839 B → '
             '**4,413 件 / 727,461,721 B**）')
new_trace = ('（溯源：4,518 件 / 724,479,859 B → 4,413 件 / 744,172,839 B → '
             '4,413 件 / 727,461,721 B → 4,416 件 / 736,151,921 B → '
             '**4,417 件 / 737,517,286 B**）')
ck('正控：F24 含旧溯源括号且仅 1 次', F24[1].count(old_trace) == 1,
   str(F24[1].count(old_trace)))
ck('反控：新溯源括号在原文中不存在', new_trace not in F24[1])

new_stmt = F24[1].replace(old_stmt_frag, new_stmt_frag).replace(old_trace, new_trace)
ck('F24 statement 长度增加（只增不减）', len(new_stmt) > len(F24[1]),
   '%d -> %d' % (len(F24[1]), len(new_stmt)))
ck('F24 statement 除这两处外逐字节不变',
   new_stmt.replace(new_stmt_frag, old_stmt_frag).replace(new_trace, old_trace) == F24[1])
ck('新 statement 必含主引值 737,517,286', '737,517,286' in new_stmt)
ck('新 statement 不再出现孤立「四步」', '四步' not in new_stmt)

# ============ 改动 2：F24.limitations ============
old_lim_frag = '**限定向附三·语料值四次演进（v5.29）**'
new_lim_frag = '**限定向附三·语料值五次演进（v5.30，R69 更正步数与终值）**'
ck('正控：F24 limitations 含「四次演进」且仅 1 次', F24[4].count(old_lim_frag) == 1,
   str(F24[4].count(old_lim_frag)))

# 在「四次演进」那段之后追加一句 R69 更正说明（插在「限定向附四」之前）
marker4 = '**限定向附四·重复产出与两个口径（v5.30）**'
ck('正控：F24 limitations 含 v5.30 段落标记且仅 1 次', F24[4].count(marker4) == 1,
   str(F24[4].count(marker4)))
r69_note = ('**限定向附三附·R69 对 v5.29/v5.30 正文的两处更正**：'
            '① 原写「四步」但只枚举了 R53 / R54 / R60 / R62 三件翻四个动作，'
            '**漏了 R64 的 scan_mine.json 1,365,365 B**（`_r69/verify_f24_stmt_r69.py` 实测：'
            '枚举覆盖 8,690,200 B，而主引值−剔段值 = 10,055,565 B，差 1,365,365 B）；'
            '② 原溯源括号终值写 **727,461,721 B**（那是 R60 剔段后的 4,413 件值），'
            '**不是主引值 737,517,286 B**，两数相差 10,055,565 B。'
            '**本版两处均已改**：步数改为「五步」并补 R64，溯源括号补 4,416 / 736,151,921 与 '
            '**4,417 / 737,517,286** 两个中间终值。**主引值本身未变**（737,517,286 B 自 v5.29 起一直是它）。')
new_lim = F24[4].replace(old_lim_frag, new_lim_frag).replace(marker4, r69_note + marker4)
ck('F24 limitations 除两处外逐字节不变',
   new_lim.replace(new_lim_frag, old_lim_frag).replace(r69_note + marker4, marker4) == F24[4])
ck('F24 limitations 长度增加', len(new_lim) > len(F24[4]), '%d -> %d' % (len(F24[4]), len(new_lim)))

# ============ 改动 3：F29.limitations ============
F29 = rows[idx['F29']]
old_three = ('实测三件：① ILT 与 IMAGE_IMPORT_BY_NAME 名字区在 `.detour` 节（339/339）；'
             '② IAT 数组本身在 `.rdata`（339/339）；'
             '③ IAT 槽内容（绑定的 0x40F9xx 类地址）落在 `.text`（339/339）')
new_three = ('实测（`_r69/recompute_audit_r69.py` 手工遍历导入描述符，不经 pefile 高层封装）：'
             '导入共 **372** 条 = 按名 **339** + 按序数 **33**；'
             '① ILT **372** 条全在 `.detour`；IMAGE_IMPORT_BY_NAME 名字区 **339** 条全在 `.detour`'
             '（序数导入 33 条无名字区）；'
             '② IAT 数组 **371** 条在 `.rdata`、**1** 条在 `.detour`（`xyr.dll`，唯一一条按序数且 IAT 槽不在 .rdata）；'
             '③ IAT 槽内容 **339** 条在 `.text`、**33** 条为序数标记值 0x8xxxxxxx（不是地址）'
             '——故**不得用 IAT 槽值反推真实函数体地址**，导入名只能从 `.detour` 的明文 IBN 读。'
             '**v5.31 更正**：旧文三处「339/339」把三个不同分母并成一个 —— '
             'ILT 是 372、名字区是 339、IAT 槽是 371+1=372、槽内容是 339+33=372；'
             '339 只是「按名导入」子集，**序数导入 33 条原文完全未提**')
ck('正控：F29 limitations 含旧「实测三件」且仅 1 次', F29[4].count(old_three) == 1,
   str(F29[4].count(old_three)))
ck('反控：新「实测」段在原文中不存在', '手工遍历导入描述符' not in F29[4])
new_lim29 = F29[4].replace(old_three, new_three)
ck('F29 limitations 长度增加', len(new_lim29) > len(F29[4]), '%d -> %d' % (len(F29[4]), len(new_lim29)))
ck('F29 limitations 除该处外逐字节不变',
   new_lim29.replace(new_three, old_three) == F29[4])

# ============ F29.statement 的 VA/RVA 措辞 ============
old_va = '（VA=0x793000/raw=0x497000）'
new_va = '（VirtualAddress/RVA=0x793000、绝对 VA=0xB93000、raw=0x497000）'
ck('正控：F29 statement 含旧「VA=0x793000」且仅 1 次', F29[1].count(old_va) == 1,
   str(F29[1].count(old_va)))
new_stmt29 = F29[1].replace(old_va, new_va)
ck('F29 statement 长度增加', len(new_stmt29) > len(F29[1]))
ck('F29 statement 除该处外逐字节不变',
   new_stmt29.replace(new_va, old_va) == F29[1])

# ============ 组装新表 ============
rows[idx['F24']][1] = new_stmt
rows[idx['F24']][4] = new_lim
rows[idx['F29']][1] = new_stmt29
rows[idx['F29']][4] = new_lim29

out = '\n'.join([','.join(hdr)] + ['\t'.join(r) for r in rows]) if False else \
      '\n'.join(['\t'.join(hdr)] + ['\t'.join(r) for r in rows]) + '\n'
nb = out.encode('utf-8')

W('')
W('=== 变更面核对 ===')
newlines = ['\t'.join(r) for r in rows]
changed = [i for i in range(54) if newlines[i] != lines[i + 1]]
W('  变更行下标(0-based, 对应 rows): %s' % changed)
ck('只有 2 行变更（F24 idx=%d / F29 idx=%d）' % (idx['F24'], idx['F29']),
   changed == [idx['F24'], idx['F29']], str(changed))
ck('变更行 fact_id 恰为 F24/F29',
   [rows[i][0] for i in changed] == ['F24', 'F29'], str([rows[i][0] for i in changed]))
ck('grade 列一字未动',
   [rows[i][2] for i in range(54)] == [l.split('\t')[2] for l in lines[1:]])
ck('evidence_paths 列一字未动',
   [rows[i][3] for i in range(54)] == [l.split('\t')[3] for l in lines[1:]])
ck('fact_id 列一字未动', [rows[i][0] for i in range(54)] == [l.split('\t')[0] for l in lines[1:]])
ck('新文件 CR=0（全 LF）', nb.count(b'\r') == 0)
ck('新文件 55 行', nb.count(b'\n') == 55, str(nb.count(b'\n')))
W('  新 sha=%s  新字节=%d（旧 %d，+%d）'
  % (hashlib.sha256(nb).hexdigest()[:16], len(nb), len(raw), len(nb) - len(raw)))

if DRY:
    W('')
    W('[DRY] 不写盘')
    W('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
    sys.exit(0 if not fails else 1)

# ============ 写入纪律 ============
import time
ts = time.strftime('%Y%m%d_%H%M%S')
bk = os.path.join(BASE, 'SUPERSEDED.before_r69_factindex_v531_%s.tsv' % ts)
W('')
W('[backup] wx 独占创建 %s' % os.path.basename(bk))
with open(bk, 'xb') as f:          # x = 独占，存在即失败
    f.write(raw)
ck('备份回读字节一致', open(bk, 'rb').read() == raw)
ck('备份 sha 与旧文件相同',
   hashlib.sha256(open(bk, 'rb').read()).hexdigest() == hashlib.sha256(raw).hexdigest())

os.makedirs(DSTD, exist_ok=True)
with open(DST, 'xb') as f:         # 新版本目录用新文件名，wx 独占
    f.write(nb)
b2 = open(DST, 'rb').read()
ck('目标文件回读字节 == 预期', b2 == nb)
ck('目标文件 CR=0', b2.count(b'\r') == 0)
ck('目标文件 55 行', b2.count(b'\n') == 55)
ck('目标文件 sha 与预期一致',
   hashlib.sha256(b2).hexdigest() == hashlib.sha256(nb).hexdigest())
W('[after] %d B CR=%d LF=%d sha=%s' % (len(b2), b2.count(b'\r'), b2.count(b'\n'),
                                       hashlib.sha256(b2).hexdigest()[:16]))

# 源文件未动（v5.30 保留为历史版本）
ck('源 FACT_INDEX.tsv 未被改动（sha 不变）',
   hashlib.sha256(open(SRC, 'rb').read()).hexdigest().startswith(OLD_SHA))

W('')
W('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'write_factindex_v531.log'),
        'w', encoding='utf-8', newline='\n').write('\n'.join(buf) + '\n')
sys.exit(0 if not fails else 1)
