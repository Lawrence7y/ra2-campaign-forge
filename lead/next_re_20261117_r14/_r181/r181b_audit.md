# r181b 只读复核：C19「事实层联动」盲区盘点（deepseek / audit，R181）

**重要状态变更**：我复核期间（15:51:32）主会话已把 C19 **落盘**到 check_disc.py（62955 B / 1141 L / `8de20d8e`，GATE_VER 仍 R166，:`1039-1119`），且**落地版与卡面四条判据不同**：卡面 (c) 是「check_disc 内嵌 facts_floors.py 的 sha」，落地版**明确否决**该方案（`:1045-1046`「本脚本内不存任何事实层文件的 sha 常量 … 实测该面在 R181 是被明确否决的方案」），改为 (a) facts CUR_SHA256、(b) facts TOTAL_BYTES、(c) 指针 sha、(d) 指针字节、(e) 指针版本目录。以下按落地版判定，并标注与卡面的差异。

**最小复算（一条，只读）**：`cd /home/t628/projects/ra2-campaign-forge && sha256sum lead/next_re_20261117_r14/check_disc.py _r160/facts_floors.py _r161/gate_runner.py lead/next_re_20261117_r14/R17_R131_FACTINDEX_V563/FACT_INDEX.tsv | cut -c1-16 && sed -n '1039,1119p' lead/next_re_20261117_r14/check_disc.py && rg -n '^EXPECT_CUR|^LEDGER|^C19_LEDGER|_c19_dir = ' _r160/facts_floors.py _r161/gate_runner.py lead/next_re_20261117_r14/check_disc.py && (rg -c '\| 行数 \||\| 相对路径 \|' lead/next_re_20261117_r14/check_disc.py || echo 'pointer-path-fields-read=0')`

**前置（卡面路径错）**：`R14/_r160`、`R14/_r161` 不存在，实物在项目根 `_r160/facts_floors.py`（26147 B/478 L/`ed717d13`）、`_r161/gate_runner.py`（20268 B/398 L/`5fe108f5`）。另：`check_disc.py:31` 的 `LED` 在 `:1121` 仍被叫作 `'LEDGER'`，实为 `GOAL_THREE_TARGETS`——这是「主门禁零接触台账」长期未被察觉的命名原因。

**Q1 与 G3 重复：部分成立。** 落地 (a)(b) 与 `gate_runner.py:187` G3c、`:192` G3d 同义（卡面把 (b) 对到 G3e 有误，G3e 是 C16_FLOORS 的 sha），并已被 `facts_floors.py:340` D0、`:418` D8 覆盖 ⇒ 三重复。独立价值不在判据而在**执行面**：crontab/systemd 实测 0 条门禁接线、gate_runner 无自动调用者，G3c/d 仅人手跑 `_r1xx` 时生效；进 check_disc 才每轮必跑。

**Q2 卡面 (c) 的假 FAIL 面：若按卡面实现则成立（我反对），落地版已规避。** 卡面 (c) 的代价不是「V-bump 时改」（facts_floors.py 内容不变则其 sha 不变），而是「每次重生成 facts_floors.py 必回填 **1 处**、连锁 4 处」：`check_disc.py:33` GATE_VER↑、`DISC_RECHECK.tsv:21` col6、`DISC_UNVERIFIABLE.tsv:20` col4、`check_disc.py:34` FREEZE_SHA256（末步自指环）；r160c 不认识 check_disc，回填必靠人（`R17_LEAD_BASELINE/facts_floors.py*.bak` 实测 **33** 份 = 历史重生成 ≥33 次）。落地版改取**目标文件事实**而非「门禁文件自身 sha」，无此面 —— 这个否决是对的。落地版的真代价另算：**V-bump 后 check_disc 的 `C19_LEDGER:1055` 也必须改**，否则与 (a) 同吉（见 Q4）。

**Q3 (d) 覆盖面：部分成立。** 落地 (c)(d) ≡ D10 的 (A)(B) 两条独立事实，且因 D0 保证 sha(CUR)==CUR_SHA256，(A) 与冗余项 (C) 同真同假（`facts_floors.py:441-442` 自述）⇒ 落地版**把 D10 的两条独立项都覆盖了**，比卡面 (d) 更完整。卡面 (d) 只等价于 (A)，漏掉 (B)。「指针 133310 / 现盘 133311」：D0 与 D8 都会红（`:418` 是 `<` 下界），**不是盲区**；真盲区是反向——台账未动、只把指针字节写成 133311，D0/D8/(A)/(C) 全绿，只有 (B) 抓，落地 (d) 已补。

**Q4 恒真项：部分成立，且落地版新增一格恒真。** 反控实测（/tmp 副本 + `ROOT` 重定向，7 例全部 exit 1 且有 C19 专属 FAIL）：台账+1B、facts 加注释、facts CUR_SHA256 改值、facts TOTAL_BYTES 改值、指针字节 133311、指针版本目录 V564、指针 sha 改值 ⇒ 均被抓，**无恒真**。但两条结构性缺口：
1. **V-bump 僵尸链**：`facts_floors.py:46 EXPECT_CUR`、`gate_runner.py:51 LEDGER`、`check_disc.py:1055 C19_LEDGER` 三处硬编码 V563，而「历史版本保留不删不改」是纪律 ⇒ 升 V564 而漏改任一，那个门就成天检查旧快照、永绿（与 C7b/C11b/C18 同型）。**(e) 只比「指针字段 vs C19_LEDGER 目录名」，两边都硬编码 ⇒ 同源不独立。**
2. **事实层可被摘除而 C19 全绿**：把 `facts_floors.py:340/418/427` 的判据改成 `if False`（或直接加 `sys.exit(0)`），字面量 CUR_SHA256/TOTAL_BYTES 都不变，落地 (a)(b) 仍绿；三门均不断言「这些判据仍在执行」（rg 计数 0）。卡面 (c) 恰好是唯一能抓这一类的判据 —— 它被否决后，这个盲区**没有替代品**。建议补一条低成本断言：facts 源码必须含 `sha != CUR_SHA256` 与 `_master != MASTER_SHA256` 两个子串，且不得出现 `IGNORE_PIN = True`。
3. 指针 `行数`（`FACT_INDEX_CURRENT.md:13`）与 `相对路径`（`:10`）字段被三门读取 **0** 次；实测把行数改成 999、相对路径改成 `lead/nowhere/…` 后 check_disc 仍 exit 0。

**Q5 更该进主门且更便宜的两条**：① **三处当前版本路径互等**：`facts_floors.py:46` == `gate_runner.py:51` == `check_disc.py:1055`；一条断言抓「升版漏改其一，两门各查各的版本各报绿」（R164/R171 正文反复记录这种靠人记的同步），零常量、不产生重钉面。② **指针派生而非旁证**：C19 的台账路径从指针「相对路径」解析（现盘该字段读 0 次），并校验「行数」== 现盘行数；一条断言同抓「指针指向不存在路径」「行数字段单独漂移」，零新常量。

**附加（顺手发现的独立缺陷）**：`check_disc.py:22` 是 `import io, os, re, sys, hashlib, hashlib, json, ast` —— `hashlib` 重复导入（无害，但同族于本门反复抓的「复制粘贴未清理」）。

**裁定**：落地版比卡面方案好（无自指 sha 重钉面、多覆盖指针目录与字节），可保留；但请补 Q4-2 的「判据仍在执行」断言与 Q5-① 的三路径互等，否则 V-bump 一发生，C19 的 (a)(b)(e) 会同时退化为对着旧快照永绿的恒真项。
