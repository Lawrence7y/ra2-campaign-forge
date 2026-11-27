#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R173 I：追加 R14_COMMON §2.178（纯追加，CR 保持 1081）。"""
import hashlib, io, json, os, sys, time

TIER = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
RC = os.path.join(TIER, 'R14_COMMON.md')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
OLD_CR, OLD_LF = 1081, 13878
stamp = time.strftime('%Y%m%d_%H%M%S')
fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

raw = open(RC, 'rb').read()
ck('A1 母本 CR == 1081', raw.count(b'\r') == OLD_CR, raw.count(b'\r'))
ck('A2 母本 LF == 13,878', raw.count(b'\n') == OLD_LF, raw.count(b'\n'))
old_sha = hashlib.sha256(raw).hexdigest()
txt = raw.decode('utf-8')
ck('A3 尚未有 §2.178', '## 2.178' not in txt, txt.count('## 2.178'))

SEC = '''## 2.178 · R173：F24 的「bounds 段 16,711,118 B」被证为**算术差不是字节跨度**（实测段长 16,711,104，差 14 B 是 JSON 结构开销）；F35 的「V540..V544 共存 / V545 起回收」逐版复算成立，但共存起点是 V540 不是 V534（V534..V539 只有旧句，两列不曾相反）；F23 的 18 / 4 两口径与 COVERAGE 全树失联闭世界复算（V553→V554）

**一 · 判据先行：同一句话里的数与量必须分成「算术差 / 值跨度 / 成员宽度」三个口径分别测.** F24 的 statement 与 limitations 里 16,711,118 共出现 **8** 次（statement 4 + limitations 4），其中「**恰为被剔的 bounds 段**」型 **1** 次（statement 内）。`r173a` **18 断言 0 FAIL**：现盘 `a2_sites.json` = **17,624,355 B**、sha256 前缀 **7a8447d1d816cdc3**；用「字符串转义感知 + 括号配平」的顶层 span 扫描器实测 **bounds 值跨度 16,711,104 B** = **1,392,592** 条 × **12 B**（每条为 8 位十六进制加引号逗号，恰 12 字节）、calls 值跨度 913,228 B（6,728 键）。三个宽度互不相同且两两相差 2 B：**值跨度 16,711,104 / 删整条成员 16,711,116 / 现盘减快照清单 16,711,118**。**可失败的部分**：在 ±32 B 窗口内以 16,711,118 为宽度试删 **65** 个起点，能得合法 JSON 的起点 **0 个**；而删 913,238 起 **16,711,116 B** 得合法 JSON（顶层键只剩 calls、删后 **913,239 B**），删 913,250 起 16,711,104 B（只删值）**不合法**（缺分隔符）、删 913,237 起 16,711,118 B 亦**不合法**。⇒ 正文那句「差额数对、『恰为 bounds 段』错」：14 B 缺口 = 键名 `"bounds"`（8）+ 冒号（1）+ 空白（1）+ 末尾方括号（1）+ 前置逗号与空格（实际分布见 `r173a` B4），不是段内数据。**这不改任何既有数字**：8 次 16,711,118 一字未动，只在 limitations 追加口径（`r173b` **10 断言 0 FAIL**，含「把 118 换成 104 后同一分类器仍判 BOUNDS_SPAN」与「空串分类 0 次」两条反控）。

**二 · F35 的两处版本范围声明：逐版复算成立，但「5 版共存」的起点要说清.** `r173c` **19 断言 0 FAIL**：版本目录 V530..V553 共 **24** 个连续无缺。① V540..V544 五版 statement 长度恒 **1054** 且「不是独立实现」各 **1** 次、limitations 里该半句恒 **0** 次（两列互斥）；② V545..V553 九版 limitations 里该半句恒 **3** 次，拆分为 **R139 段 1 + R165 段 2**（后者是追述引文），三处闭合；③ 原句「另有 3 个独立脚本含同一逐字判据」在 V534..V544 各 **1** 次、V545 起**不带引号 0 次 / 带引号 1 次** ⇒ 回收是真改文本。**但一条此前未写的边界**：V534..V539 六版 statement 长 **156**、不含该半句，原句只在 limitations —— 故「两列相反」只在 V540..V544 成立，V534..V539 是「只有旧句」。**第三条如实登记**：V553 的 limitations 里「不是独立实现」共 **3** 次（含本行自己的 2 次引文），引用该半句须说明「含引文」，否则与 statement 的 1 次对不上。

**三 · 一手权威与血缘四点逐字复核（不依赖任何已失输入）.** `r173e` **18 断言 0 FAIL**：`strict_panel.py` **6,481 B**、sha256 前缀 **731c98ea4910f5e9**；第 **78** 行逐字 `if "[未证]" not in sem:`、第 **76** 行逐字 `if grade == "[已证]":`，**缩进 8 vs 12 ⇒ 嵌套不是并列**；全文 `[未证]` 恰 **2** 次（行 14 散文 / 行 78 代码）、裸「未证」也恰 2 次、代码形态恰 1 次；`sem = r[3]` 在**第 67 行**（即 one_line_semantics 列），`d[s]["atlas_n"] += 1` 在**第 69 行**（在 `if e not in atlas: continue` 之后）。血缘四点矩阵：四个脚本（strict_panel / precheck / simulate / verify）**全部**满足「同一 PROJ + 同一对输入 + 同一判据串」；反控 `merge_panel.py` 有同一 PROJ 但**缺另两条**（三缺二），且全文「未证」**0** 次。**N2 反控最有判别力**：只用「同一 PROJ」会把 merge_panel 误纳得 **5** 个，加上另两条才是 **4** 个 ⇒ 正文「共用 PROJ 不是血缘充分条件」这句成立。

**四 · F23 的两口径与 COVERAGE 闭世界.** `r173d` **15 断言 0 FAIL**：11-22 快照清单 **4,417** 行 4 列；basename 精确 `coverage.tsv` 恰 **18** 条、字节值**两两不同（distinct 18）**、**存活 0**；rel 含 `/COVERAGE/` 恰 **28** 条、其中 basename 为 coverage.tsv 的 **4** 条、**28 条存活全为 0**（`COVERAGE/` 目录本身不存在）；`function_atlas.tsv` 清单里恰 **1** 条（**427,038 B**）、存活 0，全库 `os.walk` 命中 **0**、父目录 `next_re_20261112_r10` 不存在。**反控三条**：基准根换成仓库根存活仍 0、`a2_sites.json` 判存活为真（isfile 逻辑可用）、basename 改 contains 后条数 18→**41**（精确口径确实精确）。⇒ F23 的 458/291/293/1,196/1,654 与 F35 的 `n` 分母在**现盘无任何文件可重数**，这一条本轮再次闭世界确认。

**五 · 落盘与门禁（fail-closed，两处如实登记）.** V553→**V554**：**123,851 B** / sha256 **5de4084b76bbd0e786898beeefe9197bddb599f97bd122635afaee43b98c86b0** / 55 行 5 列 / CR 0；差分行**恰 2**（F24、F35），每行变化单元**恰 1** 且是第 5 列，SequenceMatcher 各 **1 个 insert 且落在末尾**（F24 位 16985、F35 位 3276），其余 **52 行 × 5 列逐字节相同**，母本 V553 一字未改；字节增量 **+2,841**。门禁：`facts_floors` 五点重钉（`EXPECT_CUR`→V554、`CUR_SHA256`→5de4084b…、`TOTAL_BYTES`→123,851、`MASTER_SHA256` `ce436f7a…`→**5f3ba93cb0f091e3**），**每步先用 ast 从源码取常量、用旧常量复算旧 MASTER 命中 `ce436f7a…` 作硬闸**；`gate_runner` 只改 `LEDGER` **1** 处（它本来就不持有 sha 字面量）。三段实跑：`check_disc` **exit 0**（C16 逐节 **171** 节 pinned 171、unpinned 0）、`facts_floors` **exit 0**（D0 5de4084b / D8 123851 / D9 5f3ba93c）、`gate_runner` **G1=G2=G3=ok**；`GATE_VER` 仍 **R166**。**如实登记两条**：① `r173g` 的 G2→C1 硬闸顺序有缺陷 —— 它在 4 条写前硬闸全过后写 `facts_floors`，但 `gate_runner` 的写盘**放在自己的 D2 断言之后而 D2 是一条方向写反的假 FAIL**（S-602），于是「写盘已发生、脚本 exit 1」；已由 `r173h` **14 断言 0 FAIL** 写后复验（H4 MASTER 自洽、H14 G3c/G3d 都是 PASS 而非 None 假通过）。② 三条自错 S-596/S-597/S-598 全由可失败断言当场抓出：S-596 把检索串写成「但不是独立实现」而正文里夹 Markdown 星号、S-597 把「limitations 也含该半句」当成应然而那正是矛盾本身、S-598 断言「恒 1 次」实测恒 3 次（引文也算）—— 三条都属「把结论写成断言」族，与 S-579/S-580/S-581 同族。脚本清单（`_r173/`）：`r173a_f24_bounds_bytes.py`（18）、`r173b_f24_wording_scope.py`（10）、`r173c_f35_version_range.py`（19）、`r173d_f23_layer.py`（15）、`r173e_strict_panel_authority.py`（18）、`r173f_write_v554.py`（21）、`r173g_repin.py`（28，含 1 条 S-602 订正前的假 FAIL）、`r173h_verify_after_repin.py`（14）、`r173i_r14_section.py`（本段）。
'''

new_txt = txt + '\n' + SEC
new_raw = new_txt.encode('utf-8')
ck('B1 追加后 CR 仍 1081', new_raw.count(b'\r') == OLD_CR, new_raw.count(b'\r'))
ck('B2 LF 增量 == 段内换行数', new_raw.count(b'\n') - raw.count(b'\n') == SEC.count('\n') + 1,
   new_raw.count(b'\n') - raw.count(b'\n'))
ck('B3 旧内容逐字节保留（新文件以旧文件为前缀）', new_raw.startswith(raw), True)
ck('B4 §2.178 出现恰 1 次', new_txt.count('## 2.178') == 1, new_txt.count('## 2.178'))

bak = os.path.join(BASE, 'R14_COMMON.md.before_r173_2_178_%s.bak' % stamp)
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(raw)
ck('C1 备份独占创建、sha256 == 旧 sha', hashlib.sha256(open(bak, 'rb').read()).hexdigest() == old_sha,
   os.path.basename(bak))

if fails:
    print('\n[FAIL-CLOSED] %d 条硬闸未过，不写盘。' % len(fails)); sys.exit(1)

with open(RC, 'w', encoding='utf-8', newline='') as f:
    f.write(new_txt)
back = open(RC, 'rb').read()
ck('D1 回读逐字节一致', back == new_raw, len(back))
ck('D2 回读 CR 仍 1081', back.count(b'\r') == OLD_CR, back.count(b'\r'))
ck('D3 回读 sha256 已变', hashlib.sha256(back).hexdigest() != old_sha, hashlib.sha256(back).hexdigest()[:16])

print()
print('SUMMARY: %d assertions, %d FAIL' % (n, len(fails)))
print('R14_COMMON: %d B / CR %d / LF %d / sha %s' % (len(back), back.count(b'\r'), back.count(b'\n'),
                                                     hashlib.sha256(back).hexdigest()[:16]))
json.dump(dict(fails=fails, asserts=n, bytes=len(back), cr=back.count(b'\r'), lf=back.count(b'\n'),
               sha=hashlib.sha256(back).hexdigest(), sec_bytes=len(SEC.encode()),
               backup=os.path.basename(bak)),
          open('/home/t628/projects/ra2-campaign-forge/_r173/r173i_r14_section.json', 'w'),
          ensure_ascii=False, indent=1)
sys.exit(1 if fails else 0)
