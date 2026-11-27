#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R173 L：向 STATUS_BOARD.md 追加第 173 轮段（全 LF，CR 保持 0，总行数 <= 300）。

写前先判归档：若写入后的行数 >= 260，必须先归档最早 2 段到 BOARD_ARCHIVE.md
（保持 BOARD_ARCHIVE CR=2952、STATUS_BOARD CR=0）。本轮实测写入后约 270 行 ⇒ 走归档分支。
归档顺序与 R168/R169 一致：搬走**最早**的两段（不是最新），并从 STATUS_BOARD 头部删除。
"""
import hashlib, io, json, os, re, sys, time

TIER = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
BD = os.path.join(TIER, 'STATUS_BOARD.md')
AR = os.path.join(TIER, 'BOARD_ARCHIVE.md')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
stamp = time.strftime('%Y%m%d_%H%M%S')
LIMIT = 300
ARCH_TRIGGER = 260

fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

bd_raw = open(BD, 'rb').read()
ar_raw = open(AR, 'rb').read()
ck('A1 STATUS_BOARD CR == 0', bd_raw.count(b'\r') == 0, bd_raw.count(b'\r'))
ck('A2 BOARD_ARCHIVE CR == 2952', ar_raw.count(b'\r') == 2952, ar_raw.count(b'\r'))
bd = bd_raw.decode('utf-8')
bd_lines_before = bd.count('\n') + (0 if bd.endswith('\n') else 1)
ck('A3 写入前行数 == 258', bd_lines_before == 258, bd_lines_before)
ck('A4 尚无第 173 轮段', bd.count('R17 第 173 轮') == 0, bd.count('R17 第 173 轮'))

SEC = '''
## 🟢 R17 第 173 轮（2026-11-27 13:3x–14:0x）· F24 那句「差 +16,711,118 B **恰为被剔的 bounds 段**」被字节测反（bounds 段实测只有 **16,711,104 B**，差 14 B 是 JSON 结构开销）；F35 的「5 版共存」起点从 V534 订正为 **V540**（V553→V554）

**入口**：R172 待办 ③（coverage.tsv 与 PANEL.md 不可读）与 R172 交付里我自己写下的「差 +16,711,118 B 恰为被剔的 bounds 段」。两条都只做**可机械判定**，不改 grade、不改任何既有数字。八脚本 **133 断言**（a 18 / b 10 / c 19 / d 15 / e 18 / f 21 / g 28 / h 14，除 g 的 1 条 S-602 假 FAIL 外全 0 FAIL）。

| 项 | 盘上原说法（V553 的 F24） | 本轮实测 |
|---|---|---|
| 16,711,118 的身份 | 「bounds 段 16,711,118 B」 | **算术差**（17,624,355 − 913,237），不是段长 |
| bounds 值在盘上的跨度 | 未单独给 | **16,711,104 B** = 1,392,592 条 × 12 B |
| 删掉整条 bounds 成员 | 未给 | **16,711,116 B** |
| 以 16,711,118 为宽度能否删成合法 JSON | 未测 | **±32 B 内 65 个起点，0 个合法** |
| 三个宽度之差 | 未给 | 两两 **2 B**（104 vs 106 vs 108 的末位）|

**判据一（三口径分开测）**：顶层 span 扫描器必须**转义感知 + 括号配平**、且**不能** json.loads 后重新 dump（那样测不到原始字节跨度）。**反控三条**：小样本 `{"calls": {"1": ["2"]}, "bounds": ["A", "B"]}` 必须得 calls 跨度 16、bounds 跨度 10（含外层括号）；删 913,238 起 16,711,116 B 必须**合法**且键只剩 calls、删后 **913,239 B**；删 913,250 起 16,711,104 B 必须**不合法**。⇒ 正文「差额对、『恰为 bounds 段』错」，但**112 这个数一次都没改**，只在 limitations 补口径。

**判据二（F35 版本范围）**：V530..V553 共 **24** 个连续版本。V540..V544 五版 statement 长恒 **1054**、含「不是独立实现」各 **1** 次、limitations 该半句恒 **0** 次（两列互斥）；V545..V553 九版 limitations 该半句恒 **3** 次 = **R139 段 1 + R165 段 2（引文）**。原句 V534..V544 各 **1** 次、V545 起**不带引号 0 次 / 带引号 1 次**。**订正**：V534..V539 六版 statement 长 **156**、不含该半句 ⇒ 「两列相反」只在 **V540..V544** 成立，V534..V539 是「只有旧句」。

**判据三（一手权威，不依赖已失输入）**：`strict_panel.py` **6,481 B**、`731c98ea4910f5e9`；第 **78** 行 `if "[未证]" not in sem:`、第 **76** 行 `if grade == "[已证]":`，缩进 **8 vs 12** ⇒ 嵌套；`[未证]` 恰 **2** 次（行 14/78）、裸「未证」也恰 2 次、代码形态 **1** 次；`sem = r[3]` 第 **67** 行、`atlas_n` 自增第 **69** 行。血缘四点：四脚本全满足「同一 PROJ + 同一对输入 + 同一判据串」；`merge_panel.py` **三缺二**、全文「未证」**0** 次。**N2 反控最有判别力**：只用「同一 PROJ」误纳得 **5** 个，加另两条才是 **4** 个。

**F23 两口径与 COVERAGE 闭世界（第三次确认）**：清单 **4,417** 行 4 列；basename 精确 `coverage.tsv` 恰 **18** 条、**distinct 字节值 18**、**存活 0**；rel 含 `/COVERAGE/` 恰 **28** 条、其中 basename 为 coverage.tsv 的 **4** 条、**存活全 0**；`function_atlas.tsv` 清单恰 **1** 条 **427,038 B**、存活 0、全库 `os.walk` **0**、父目录不存在。**反控**：仓库根基准仍 **0**、`a2_sites.json` 判存活为真、basename→contains 条数 **18→41**。

**落盘**：V553 → **V554**（**123,851 B** / `5de4084b76bbd0e7…` / 55 行 5 列 / CR 0）；差分行**恰 2**（F24、F35）、每行变化单元**恰 1**（第 5 列）、SequenceMatcher 各 **1 insert 落末尾**（F24 位 16985 / F35 位 3276）、其余 **52 行 × 5 列逐字节相同**、母本 V553 一字未改；**+2,841 B**。门禁：`facts_floors` 五点重钉（`EXPECT_CUR`→V554、`CUR_SHA256`→`5de4084b…`、`TOTAL_BYTES`→123,851、`MASTER_SHA256` `ce436f7a…`→**`5f3ba93cb0f091e3`**，每步 ast 取常量 + **旧常量复算旧 MASTER 命中**作硬闸）；`gate_runner` 只改 `LEDGER` **1** 处（它本来就不持有 sha 字面量）。三段实跑：`check_disc` **exit 0**（C16 **171** 节 pinned 171 / unpinned 0）、`facts_floors` **exit 0**（D0 `5de4084b` / D8 123851 / D9 `5f3ba93c`）、`gate_runner` **G1=G2=G3=ok**；`GATE_VER` 仍 **R166**。`r173h` **14 断言 0 FAIL** 写后复验（H4 MASTER 自洽、H14 G3c/G3d 是 PASS 而非 None 假通过）。

**自错 S-596..S-606（十一条，全部由可失败断言当场抓出，无一条进入结论或正文数字）**：S-596 检索串写成「但不是独立实现」而正文夹 Markdown 星号；S-597 把「limitations 也含该半句」当应然，而那正是矛盾本身；S-598 断言「恒 1 次」实测恒 **3** 次（引文也算）；S-599 断言 atlas 清单 0 条、实测 **1** 条 427,038 B；S-600 断言 ast 取到 11 个常量、实测 **12** 个；S-601 拿 64 位 sha 的 `[:16]` 比 8 字符字面量；**S-602（最重）** 断言「gate_runner 里应出现旧 sha」而实测 0 次（它用正则从 facts_floors 读），方向写反致「写盘已发生、脚本 exit 1」；S-603 `'## §1228' in txt` 缺 `not`；S-604 LF 增量等式多算 +1；S-605 把「卡面禁反引号」误扩到 LEAD_LOCK 正文；S-606 K9 的相消理由写反。**族谱**：五条属「把结论/预期写成断言」（S-597/598/599/600/601），三条属「断言方向与名称相反」（S-602/603/S-604 同族）。**纪律新增一条**：**写盘必须全部落在最后一道断言之后**（S-602 的直接教训）。

**跨家族**：执行员 #407（hy4flash-free/exec）与审计员 #408（deepseek/audit）均已派发、两次 `wait_subagents` 轮询（各 >120 s），收口前**无回件、无 OVERTIME 标记** ⇒ **本轮无审计结论**，全部结论由主会话自测脚本产出，**不写「已过跨家族审计」**（与 R166 #388、R172 #403/#405 同类）。

**未取得**：① `coverage.tsv` / `function_atlas.tsv` 仍不可读（第三次闭世界确认）⇒ F23 的 458/291/293/1,196/1,654 与 F35 的 `n` 分母仍不可重数；② F23/F35 的 grade 未改（`未取得` / `[流程]`），改 grade 是裁定不是取证；③ C7 三死分支 exists/bytes=/none 仍各 0 行；④ C11 id 3/4/22/27/28 与 5 处永远通过子项未动；⑤ `a2_sites` 原始生成器与 86.19% 原值仍不可重算；⑥ `_ext/f_partial_triage/` 两件未补版本号。
'''

new_bd = bd.rstrip('\n') + '\n' + SEC
new_lines = new_bd.count('\n') + (0 if new_bd.endswith('\n') else 1)
print('   写入后行数（未归档）: %d' % new_lines)
ck('B1 写入后行数 >= 归档阈值 260 ⇒ 必须归档', new_lines >= ARCH_TRIGGER, new_lines)

# ---- 归档最早 2 段 ----
# 段 = 以 '\n## ' 开头的块（首个段从文件头或第一个 ## 起）
idx = [m.start() for m in re.finditer(r'(?m)^## ', new_bd)]
ck('B2 段数 >= 3（可搬走最早 2 段）', len(idx) >= 3, len(idx))
seg1 = new_bd[idx[0]:idx[1]]
seg2 = new_bd[idx[1]:idx[2]]
head = new_bd[:idx[0]]
rest = new_bd[idx[2]:]
ck('B3 被搬的两段都不含第 173 轮段', ('R17 第 173 轮' not in seg1) and ('R17 第 173 轮' not in seg2), True)
ck('B4 第 173 轮段仍在 rest 里', 'R17 第 173 轮' in rest, True)
ck('B5 head 是非段前言（不含 ## ）', '## ' not in head or head.strip() == '', repr(head[:40]))

arch_add = seg1.rstrip('\n') + '\n' + seg2.rstrip('\n') + '\n'
new_ar = ar_raw.decode('utf-8').rstrip('\n') + '\n' + arch_add
final_bd = head + rest
final_lines = final_bd.count('\n') + (0 if final_bd.endswith('\n') else 1)
print('   归档后看板行数: %d（搬走 %d 行）' % (final_lines, new_lines - final_lines))
ck('B6 归档后行数 < 260', final_lines < ARCH_TRIGGER, final_lines)
ck('B7 归档后行数 <= 300', final_lines <= LIMIT, final_lines)

ar_new_raw = new_ar.encode('utf-8')
ck('B8 归档后 BOARD_ARCHIVE CR 仍 2952', ar_new_raw.count(b'\r') == 2952, ar_new_raw.count(b'\r'))
bd_new_raw = final_bd.encode('utf-8')
ck('B9 归档后 STATUS_BOARD CR 仍 0', bd_new_raw.count(b'\r') == 0, bd_new_raw.count(b'\r'))
# S-607：首版 B10 断言「AR 增量 == len(arch_add)」——实测 12,649 vs 12,650。
# 原因：BOARD_ARCHIVE 末尾本来就有 **2** 个换行，rstrip 剥掉 2 个而只补回 1 个，
# 故真实增量 = len(arch_add) − 1。断言改成显式扣掉这一项。
_tail_nl = len(ar_raw) - len(ar_raw.rstrip(b'\n'))
ck('B10 归档前后字节闭合：AR 增量 == 搬走段字节 − (母本尾部换行数 − 1)',
   len(ar_new_raw) - len(ar_raw) == len(arch_add.encode('utf-8')) - (_tail_nl - 1),
   (len(ar_new_raw) - len(ar_raw), len(arch_add.encode('utf-8')), _tail_nl))

old_shas = {'STATUS_BOARD.md': hashlib.sha256(bd_raw).hexdigest(),
            'BOARD_ARCHIVE.md': hashlib.sha256(ar_raw).hexdigest()}
for name, blob in (('STATUS_BOARD.md', bd_raw), ('BOARD_ARCHIVE.md', ar_raw)):
    p = os.path.join(BASE, '%s.before_r173_r173_%s.bak' % (name, stamp))
    fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(blob)
    ck('C %s 备份 sha256 == 旧 sha' % name,
       hashlib.sha256(open(p, 'rb').read()).hexdigest() == old_shas[name], os.path.basename(p))

if fails:
    print('\n[FAIL-CLOSED] %d 条硬闸未过，不写盘。' % len(fails)); sys.exit(1)

with open(AR, 'w', encoding='utf-8', newline='') as f:
    f.write(new_ar)
with open(BD, 'w', encoding='utf-8', newline='') as f:
    f.write(final_bd)

bd_back = open(BD, 'rb').read()
ar_back = open(AR, 'rb').read()
ck('D1 STATUS_BOARD 回读一致', bd_back == bd_new_raw, len(bd_back))
ck('D2 BOARD_ARCHIVE 回读一致', ar_back == ar_new_raw, len(ar_back))
ck('D3 STATUS_BOARD CR 仍 0 / BOARD_ARCHIVE CR 仍 2952',
   bd_back.count(b'\r') == 0 and ar_back.count(b'\r') == 2952,
   (bd_back.count(b'\r'), ar_back.count(b'\r')))
ck('D4 最终看板行数 < 260（未触发下一轮立刻归档）',
   bd_back.count(b'\n') < ARCH_TRIGGER, bd_back.count(b'\n'))
ck('D5 第 173 轮段在看板里恰 1 次', bd_back.decode('utf-8').count('R17 第 173 轮') == 1,
   bd_back.decode('utf-8').count('R17 第 173 轮'))

print()
print('SUMMARY: %d assertions, %d FAIL' % (n, len(fails)))
print('STATUS_BOARD: %d B / %d 行 / CR %d / sha %s' % (len(bd_back), bd_back.count(b'\n'),
                                                      bd_back.count(b'\r'),
                                                      hashlib.sha256(bd_back).hexdigest()[:16]))
print('BOARD_ARCHIVE: %d B / %d 行 / CR %d / sha %s' % (len(ar_back), ar_back.count(b'\n'),
                                                       ar_back.count(b'\r'),
                                                       hashlib.sha256(ar_back).hexdigest()[:16]))
json.dump(dict(fails=fails, asserts=n,
               board=dict(bytes=len(bd_back), lines=bd_back.count(b'\n'), cr=bd_back.count(b'\r')),
               archive=dict(bytes=len(ar_back), lines=ar_back.count(b'\n'), cr=ar_back.count(b'\r')),
               archived_lines=new_lines - final_lines),
          open('/home/t628/projects/ra2-campaign-forge/_r173/r173l_board.json', 'w'),
          ensure_ascii=False, indent=1)
sys.exit(1 if fails else 0)
