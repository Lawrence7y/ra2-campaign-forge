#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R173 K：追加 LEAD_LOCK 的 PD 段（纯追加，CR 保持 137）。"""
import hashlib, json, os, sys, time

LL = '/home/t628/projects/ra2-campaign-forge/lead/LEAD_LOCK'
BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/R17_LEAD_BASELINE'
OLD_CR, OLD_LF = 137, 7546
stamp = time.strftime('%Y%m%d_%H%M%S')
fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

raw = open(LL, 'rb').read()
ck('A1 CR == 137', raw.count(b'\r') == OLD_CR, raw.count(b'\r'))
ck('A2 LF == 7,546', raw.count(b'\n') == OLD_LF, raw.count(b'\n'))
txt = raw.decode('utf-8')
ck('A3 尚无 PD 段', txt.count('\nPD ·') == 0, txt.count('\nPD ·'))
ck('A4 末段是 PC9', txt.count('PC9.') == 1, txt.count('PC9.'))
old_sha = hashlib.sha256(raw).hexdigest()

SEC = '''
PD · R17 第 173 轮（2026-11-27 13:3x–14:0x）· F24 的一句「恰为被剔的 bounds 段」当场被字节测反；F35 的版本范围复算成立但起点要改；F23 的 COVERAGE 闭世界第三次确认

PD1. 🔴 **交付一：16,711,118 是算术差，不是 bounds 段的字节数.** F24 两列共 **8** 次出现（statement 4 + limitations 4），「恰为被剔的 bounds 段」型 **1** 次（statement 内）。顶层 span 扫描器（转义感知 + 括号配平，非 json 反序列化再 dump）实测：**bounds 值跨度 16,711,104 B** = **1,392,592** 条 × **12 B**；calls 值跨度 913,228 B。三口径 **16,711,104 / 16,711,116 / 16,711,118** 两两差 2 B。**可失败**：±32 B 窗口内以 16,711,118 为宽度试删 **65** 个起点，合法 JSON **0** 个；删 913,238 起 16,711,116 B **合法**（键只剩 calls、913,239 B）；删 913,250 起 16,711,104 B **不合法**。⇒ 差 14 B 是 JSON 结构开销（键名 8 + 冒号 1 + 空白 1 + 结构字符）。**8 个 16,711,118 一字未动**，只补口径。

PD2. 🔴 **交付二：F35 「V540..V544 五版共存」成立，但共存起点是 V540 不是 V534.** V534..V539 六版 statement 长 **156**、不含该半句，原句只在 limitations ⇒ 「两列相反」只在 V540..V544 成立。V540..V544：statement 恒 1054 且「不是独立实现」各 1 次、limitations 该半句恒 0 次。V545..V553：limitations 该半句恒 **3** 次 = R139 段 1 + R165 段 2（引文），三处闭合。原句 V534..V544 各 1 次、V545 起不带引号 0 次 / 带引号 1 次 ⇒ 回收是真改文本。

PD3. ✅ **交付三：一手权威与血缘四点不依赖任何已失输入.** `strict_panel.py` 6,481 B / `731c98ea4910f5e9`；78 行 `if "[未证]" not in sem:`、76 行 `if grade == "[已证]":`，缩进 8 vs 12 嵌套；`[未证]` 恰 2 次（14/78）、裸「未证」也恰 2 次、代码形态 1 次；`sem = r[3]` 第 67 行、`atlas_n` 自增第 69 行。四脚本全满足三点血缘；`merge_panel.py` 三缺二、「未证」0 次。

PD4. 📌 **交付四：F23 18/4 两口径与 COVERAGE 闭世界.** basename 精确 18 条（distinct 字节 18）、存活 0；rel 含 `/COVERAGE/` 28 条、其中 basename coverage.tsv 4 条、存活全 0；`COVERAGE/` 目录不存在；`function_atlas.tsv` 清单 1 条 427,038 B、存活 0、全库 walk 0。反控：仓库根 0、`a2_sites.json` 判活为真、basename→contains 18→41。

PD5. ✅ **交付五：V553→V554 与门禁重钉.** **123,851 B** / `5de4084b76bbd0e7…` / 55 行 / CR 0；差分行恰 2（F24/F35）、变化单元恰 1（第 5 列）、各 1 insert 落末尾、其余 52×5 逐字节相同、母本一字未改；**+2,841 B**。门禁五点：`EXPECT_CUR`→V554、`CUR_SHA256`→5de4084b…、`TOTAL_BYTES`→123,851、`MASTER_SHA256` `ce436f7a…`→**`5f3ba93cb0f091e3`**（每步 ast 取常量 + 旧常量复算旧 MASTER 命中作硬闸）；`gate_runner` 只改 `LEDGER` 1 处。三段实跑 `check_disc` exit 0（C16 171 节 pinned 171）/ `facts_floors` exit 0（D0 5de4084b、D8 123851、D9 5f3ba93c）/ `gate_runner` G1=G2=G3=ok；`GATE_VER` 仍 R166。

PD6. 🔴 **S-602（本轮最重的一条）：一条方向写反的断言让「写盘已发生、脚本 exit 1」.** `r173g` 的写前硬闸 4 条全过后写 `facts_floors`，但 `gate_runner` 的写盘放在 D2 之后，而 D2 断言「gate_runner 里应出现旧 sha」—— 实测 **0** 次，因为 gate_runner 用 `^CUR_SHA256` 正则**从 facts_floors 源码读**该常量（第 185 行），自己只钉 `LEDGER` 目录。**处置**：不断言「应该有」，改断言「确实不持有该字面量、且读它的正则存在」；并由 `r173h` **14 断言 0 FAIL** 写后复验（H4 MASTER 自洽、H14 G3c/G3d 为 PASS 而非 None 假通过）。**族谱**：与 S-588（两串相加却断言恰 5）、S-597（把矛盾当应然）、S-603（`in` 缺 `not`）同族 —— **断言方向必须与断言名称同向，且写盘必须全部落在最后一道断言之后**。

PD7. 📌 **S-596..S-603 八条自错（全部由可失败断言当场抓出，无一条进结论）.** S-596 检索串写成「但不是独立实现」而正文夹 Markdown 星号；S-597 把「limitations 也含该半句」当应然，而那正是矛盾本身；S-598 断言「恒 1 次」实测恒 3 次（引文也算）；S-599 断言 atlas 清单 0 条、实测 1 条 427,038 B；S-600 断言 ast 取到 11 个常量、实测 12 个；S-601 拿 64 位 sha 的 `[:16]` 比 8 字符字面量；S-602 见 PD6；S-603 `'## §1228' in txt` 缺 `not`。**八条中五条属「把结论/预期写成断言」族**（S-597/S-598/S-599/S-600/S-601）。

PD8. 📌 **未取得（不粉饰）.** ① `coverage.tsv` 与 `function_atlas.tsv` **仍不可读**（本轮第三次闭世界确认：清单 18/28/1 条、存活全 0）⇒ F23 的 458/291/293/1,196/1,654 与 F35 的 `n` 分母仍不可重数；② F23/F35 的 **grade 未改**（`未取得` / `[流程]`），改 grade 是裁定不是取证；③ C7 三死分支 exists/bytes=/none 仍各 **0** 行；④ C11 id 3/4/22/27/28 与 5 处永远通过子项未动；⑤ `a2_sites` 原始生成器与 86.19% 原值仍不可重算；⑥ `_ext/f_partial_triage/` 两件未补版本号；⑦ 跨家族回件本轮**未拿到**（见 PD9）。
PD9. 📌 **跨家族：本轮派发未回件.** 执行员 #407（hy4flash-free/exec）与审计员 #408（deepseek/audit）均已派发并两次 `wait_subagents` 轮询（各 >120 s），收口前**无回件、无 OVERTIME 标记** ⇒ 本轮结论**全部由主会话自测脚本产出**，**不写「已过跨家族审计」**（与 R166 #388、R172 #403/#405 同类）。
'''

new_txt = txt.rstrip('\n') + '\n' + SEC
new_raw = new_txt.encode('utf-8')
ck('B1 追加后 CR 仍 137', new_raw.count(b'\r') == OLD_CR, new_raw.count(b'\r'))
ck('B2 旧内容是新文件前缀', new_raw.startswith(raw.rstrip(b'\n')), True)
ck('B3 PD 段标记恰 1 次', new_txt.count('\nPD · R17 第 173 轮') == 1, new_txt.count('\nPD · R17 第 173 轮'))
ck('B4 PC9 仍在', new_txt.count('PC9.') == 1, new_txt.count('PC9.'))
ck('B5 PD1..PD9 九条齐全', all(('\nPD%d.' % i) in new_txt for i in range(1, 10)),
   [i for i in range(1, 10) if ('\nPD%d.' % i) not in new_txt])

bak = os.path.join(BASE, 'LEAD_LOCK.before_r173_PD_%s.bak' % stamp)
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(raw)
ck('C1 备份独占创建、sha256 == 旧 sha', hashlib.sha256(open(bak, 'rb').read()).hexdigest() == old_sha,
   os.path.basename(bak))

if fails:
    print('\n[FAIL-CLOSED] %d 条硬闸未过，不写盘。' % len(fails)); sys.exit(1)

with open(LL, 'w', encoding='utf-8', newline='') as f:
    f.write(new_txt)
back = open(LL, 'rb').read()
ck('D1 回读逐字节一致', back == new_raw, len(back))
ck('D2 回读 CR 仍 137', back.count(b'\r') == OLD_CR, back.count(b'\r'))
ck('D3 LF 增量 == 段内换行', back.count(b'\n') - raw.count(b'\n') == SEC.count('\n') + 1,
   back.count(b'\n') - raw.count(b'\n'))

print()
print('SUMMARY: %d assertions, %d FAIL' % (n, len(fails)))
print('LEAD_LOCK: %d B / CR %d / LF %d / sha %s' % (len(back), back.count(b'\r'), back.count(b'\n'),
                                                    hashlib.sha256(back).hexdigest()[:16]))
json.dump(dict(fails=fails, asserts=n, bytes=len(back), cr=back.count(b'\r'), lf=back.count(b'\n'),
               sha=hashlib.sha256(back).hexdigest(), backup=os.path.basename(bak)),
          open('/home/t628/projects/ra2-campaign-forge/_r173/r173k_leadlock.json', 'w'),
          ensure_ascii=False, indent=1)
sys.exit(1 if fails else 0)
