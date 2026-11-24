# W11 汇总 · D-22 执行步：`except_post` 新鲜性缺失核查 + 离线修复候选（四项回件 + 四道独立复核合并）

> 依据：`TASK.md`（D-22 裁决 A，`dwfrun-daa0cd3f`）四任务 T1–T4；回件四份
> （`T1_SEMANTICS.md` / `T2_CRITERIA.md` / `T3_CANDIDATE.md` / `T4_IMPACT.md`），
> 复核四份（`reviews/T1..T4_review.md`）。本汇总件由 W11 汇总员合并；标注「★亲验」的
> 数据为本汇总员本轮实跑所得（命令与输出随文标注），其余数字均可在上列八件溯源。

## 0 总判

**本次是否修改了任何正式 harness 文件：否**

- 四项回件 **CONFIRMED ×4**；四道独立复核 **CONFIRMED ×4**，均 `independentlyReproduced=true`、
  `modifiedForbiddenFile=false`。**无整项 PARTIAL/REFUTED**；仅 T2 一处子判断
  （「ERRATA_CARRIER_REBUILD.md 未找到⇒未验」）被复核 O1/mustFix-M1 **驳回改判**（见 §3、§6）。
  ⇒ **总判：CONFIRMED**（无 modifiedForbiddenFile=true 项，不触发降档条件）。
- ★亲验禁改件：`sha256sum`+`wc -c -l`+`stat`+`git check-ignore -v`+`git status --porcelain`
  于 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` →
  SHA256=`517889c6…5ba636`、399508 字节、7291 行，mtime `2026-10-20 00:08:02 +0800`（早于本 run
  17 天），`.gitignore:33` 忽略 `out/`、porcelain 空 ⇒ 未被修改。
- 核心结论一句话：`copy_post_except_evidence` 的**新鲜性语义属「实现缺陷」**（T1_SEMANTICS.md:210），
  全链零新鲜性检查（`:4420` 一处 mtime 仅日志记录用）；判据设计定为 **B 跑前基线哈希主判据 +
  A 加固版 mtime 旁证**（C 需新裁定、D 否决）；离线候选 `candidate/except_freshness.py` 14 测全绿
  （★亲验 PASS=14 FAIL=0、EXIT=0）；影响面 311 主命中仅 1 处正面崩溃证据使用且已被下游纠正，
  需实质降级 3 处 + 改口径 2 处（§5/§6）。
- 工具链副作用（非违规）：Mimosa 安全钩在 `out/re_work/.../qc151_u0400_trip/.mimosa/` 写入 2 件
  hook 状态件（03:19:19/03:23:54，实读 `touched:[]`、`bashMutation:false`），另 T4 探针初稿被误报
  「路径穿越」拦截 6 次后改写通过——均为插件自动行为，零趟件内容改动（四道复核独立核实）。

## 1 SHA256 绑定

被核对象 `qc151_trip.py`（路径 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py`）：

| 来源 | SHA256 | 字节数 | 行数 | 实算方式/出处 |
|---|---|---|---|---|
| T1 回件 | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 399508 | 7291 | `T1_SEMANTICS.md:5` 强制头部，回件时刻 03:31:04 |
| T2 回件 | 同上 | 399508 | 7291 | `T2_CRITERIA.md:3-9`，自注 sha256sum+wc，03:11:35 |
| T3 回件 | 同上 | 399508 | 7291 | `T3_CANDIDATE.md:5-8`，开头/收尾两次实算同值（03:36 起） |
| T4 回件 | 同上 | 399508 | 7291 | `T4_IMPACT.md:5-7`，sha256sum+wc 两轮一致（03:34） |
| 四道复核 | 同上 | 399508 | 7291 | 各自独立重算（T1/T2/T3/T4_review「检查1/①/〔检查1〕/①」），逐位一致 |
| ★W11 汇总员亲验 | 同上 | 399508 | 7291 | `sha256sum` + `wc -c -l` 本轮实跑（§0） |

- **与 Leader 实算值一致**：台账 `GOAL_THREE_TARGETS_20261018.md:338`（「母本零改动核验：
  `qc151_trip.py` 399,508 B / `517889c68f037ab6`」）、`:408`/`:462`（同前缀）、`:9179`（§595，
  `SHA256 = 517889c68f037ab63f9c38300e627d34...` 记录截断 + bytes=399,508 + porcelain 空）。
  Leader 记录为**截断指纹（16 位前缀）**，与四项回件全 64 位实算值**逐位前缀吻合 ⇒ 一致**。
- `gamemd.exe`：`TASK.md:112` Leader 给定 `73201cc021497c95…fcf67476`；T2 复核（sha256sum
  `ra2youli/gamemd.exe`）与 T4 复核（4,825,360 B）重算一致；T4 回件另与
  `ERRATA_EXCEPT_RESTORE.md:30` 互证。T1/T3 复核未重算（TASK 明定本任务不反汇编，零真机）。

## 2 T1 语义核查

三分类逐项（依据 `T1_SEMANTICS.md` §1–§7，行号经四道复核独立核验；**证据不足类：七项中无一项落入**）：

| # | 对象 | 三分类 | 关键证据（文件:行） |
|---|---|---|---|
| Q1 | 载体 `except.txt` 来源链 | **源码明确设计** | 母本只读 `:228`（sha `ca175a71…`/26,515B 与常量 `:229-230` 一致）；`except_reset` `:623-669` 死代码（零调用点）；交接复制 `:4946-4961` 逐字节继承（l3_20261031hb receipt 实证 sha `6694b75e`/26,405B = 2026-10-17 漂移留痕版 1046 行） |
| Q2 | 跑前基线 `pre_except_txt` 时点 | **源码明确设计**（附轻缺陷：基线 sha 未落盘） | 启动前唯一被动读取 `:6395-6402`（backup `:6385-6388` 后、launch 前），缺失则 None |
| Q3 | `copy_post_except_evidence` 调用时机 | **源码明确设计**（附轻缺陷：三处「跑后不存在」处理不一致） | def `:4561`，唯一调用 `:5939`（finalize 第 1 步 `:6043`），先于 restore `:6048`；不一致三处：copy_post 返 None `:4575-4578`、move_out 判必需件 `:5402-5406`、`_except_diff` 无 exists 直接 `read_text` `:5978` |
| Q4 | 全链新鲜性检查 | **实现缺陷（全链缺失）** | 全 7291 行 `st_mtime` 仅 `:4420`（`_render_log_probe` 记 `ra2render*.log` 元数据，非新鲜性检查）；`getmtime`/`新鲜`/`fresh` 均 0 处 |
| Q5 | `carrier_post_state.json` | **源码明确设计**（留痕）；**写了但没人比**（实查） | 写入 `:4591-4598`；仓内读者仅做路径长度/件数审计（`_audit_trips.py:17-18` 等 4 件），无一与跑前 bak 比对 |
| Q6 | `except_post_*` 归档/读取 | **源码明确设计**（writer-only 留痕） | harness 内唯一写点 `:4581`、零清理（rmtree `:5759` 只删载体）；数据面 112 副本/66 diff/63 state（口径见下） |
| ★ | **`copy_post_except_evidence` 的新鲜性语义** | **实现缺陷** | `T1_SEMANTICS.md:210` 明判：字面意图（还原前另存副本）与实现一致，但 U-5 移除覆盖写后（`:6406-6408`）「except_post ≡ 基线」成常态——实测 60/60 趟 `except_post` sha == receipt 继承 `sha256_dst`、0 趟不同 ⇒ 留档件在全部实跑记录中**不含本趟信息**，却以「本趟跑后原件/崩溃证据」名义呈现，且无任何字段标注「与跑前相同」（比对 `:4460` bak sha 即可标出）——意图与实现不符、缺少必要条件 |

**复核修正（已按复核意见采纳进本汇总）**：
- 计数口径（T1 复核 mustFix）：两棵趟树（chain + `lead/qc161_u0400_trip`）不设上限实为
  **diff=64 / post=112 / state=63**；66/113 是把 scope 扩到 `CONTINUE_20261003/lead` 父目录
  （`qc161_t13_verify_20261017/raw`、`qc161_t14_run_20261017/raw` 各 1 diff、`q161/` 1 post）；
  **真全仓 diff=68**（另含 `lead/l1_u0800_20261020`、`lead/t55k_20261020` 各 1）。4 个树外 diff
  复核逐一解析，全部 `(1046,0)` ⇒「全部 (1046,0)、『59 份』计数过期」实质结论成立。
- 实跑比对加固（T1 复核 E 段）：有 receipt+post 的趟=60，逐件 111 份 `except_post` sha ==
  receipt `sha256_dst`，**match=111 / differ=0**——不止首件，复现并加固 T1 的 60/60。
- 读者枚举补全（T1 复核 mustFix）：Q5/Q6「唯一/仅」表述不全，补
  `XVERIFY_TRIPS_20261030/_xv_s04_windows.py:76-78`（读 carrier_post_state，仅 dump）、
  `swarm_20261104/XVERIFY_S544_c1606d35/V3/v3_census.py:56,72-84`（112 份 except_post 全量普查，
  `:101` 清点 state）、`XVERIFY_S543_0a451d0b/V2/probe_e4_t42.py:25-27`——**均无跑后 vs 跑前比对**，
  「写了但没人比」「harness 内零读者」主结论不动摇。
- nitpick：探针 [C] 称 `except_reset` 非 def 出现 4 处，实为 5 处（漏 `:6391` 注释行；grep 全文件
  6 处 = def `:623` + `:643/:646/:663/:6391/:6408`），无一为调用，「死代码」结论不受影响。
- Leader §595 前置事实四条核对（`T1_SEMANTICS.md:195-208`）：①②③成立（行号偏差 2 行，非实质
  错误）；④「59 份」实质成立但计数过期（今日 66，全 `(1046,0)`）。

## 3 T2 判定口径

- **生成点**：`copy_post_except_evidence`（`:4561-4599`）只判 `src.exists()`（`:4574-4578`），
  `read_bytes` 原样复制（`:4579`），无任何新鲜性判断。
- **mtime 在本链路不可靠（探针 [0]–[7] 实测）**：载体每趟新建（`:4926` mkdir 排他）+ `write_bytes`
  复制（`:4958`）⇒ 载体 `except.txt` 的 mtime = harness 复制时刻而非游戏写入时刻；copy2 保留
  mtime、`os.utime` 可伪造、同内容重写 sha 失明而 mtime 可见、内容变更+utime 拉回则 mtime 失明
  而 sha 可见、同 tick 200 连写仅 122 个不同 mtime、时钟回拨假阴性（原理项未实测）。T2 复核重跑
  探针全复现（[6] 本轮 128 个，同量级）。
- **方案裁定**：**D 否决**——harness 自家口径 `:677` 明写「不得用 sha 变化判 crash（游戏自身会
  重写该文件）」，方案 D（游戏只在崩溃时写）与之直接矛盾；**C 需新裁定**——`:6390-6408` 被动基线
  是外部裁定 V5 §6.1.1（U-5）的产物，移走=再次主动干预载体，且游戏对文件缺席的行为反应未验；
  **推荐组合 = B 跑前基线哈希（主判据，回答 freshness）+ A 加固版 mtime 差分（旁证，专补 B 的
  同内容重写盲区）**，两者盲区经探针 [4][5] 证实互不重叠。
- **B 可零改动落地**：跑前/跑后哈希工件已全在盘——`RESTORE.backup_sha256:except.txt`（`:4461`）、
  receipt `sha256_dst`（`:4962-4980`）、`carrier_post_state.json`（`:4593-4596`）、
  `RESTORE.current_sha256`（`:4492`）；T2 复核以 `l1b_20261021` 真实趟只读复验成立（sha256_src==
  sha256_dst==`6694b75e…aac251`/26,405B，post 相同，setdiff 1046/1046/new=0）——「原样遗留」链路坐实。
- **旁证锚点**：`launch_pid_creation_time`（`:1107/:1109`）= Windows FILETIME 100-ns
  （`get_process_creation_time :766-786`，复核 O3：实体至 `:796`、100ns 换算在 `:790-792`），
  精度高于 `now_iso()` 秒级（`:432-434`）。
- **★复核驳回并改判（T2 复核 O1 = mustFix M1）**：T2_CRITERIA.md §7.1「ERRATA_CARRIER_REBUILD.md
  未找到 ⇒ 未验」被驳回——该件一直在盘：
  `out/re_work/work_chain/CONTINUE_20261003/lead/qc163_a5_prep_20261017/ERRATA_CARRIER_REBUILD.md`
  （birth=mtime 2026-10-18 00:46:14，2,552 字节；内容：A5 交接载体 86 件清空事故、按母本 82+变体
  3 件逐件 sha256 重建、归因 UNRESOLVED）。改判「**已找到并补读**」，并入 §3.C/§7.4 交接路径风险
  （重建可逐件 sha 验，但 **mtime 保留与否仍未验**）。T2 复核另更正：`CTRL1_SHA256` 实际在
  `:219`（回件自述 `:215` 有误）；「ct/ 已被删除链清理」措辞不准——l1b 版空目录 `ct/` 仍在
  （mtime 2026-10-21 18:45:22），被清理的是载体实例 `ct/c_184242594319_11992`。

## 4 T3 离线候选

- 三件交付物：`candidate/except_freshness.py`（纯函数 `classify_except_post` 等）、
  `candidate/test_except_freshness.py`（14 用例）、`candidate/PATCH_SUGGESTION.md`
  （**仅建议性 diff，未应用真文件**，三段均标「未应用」）。
- **★测试结果：PASS=14，FAIL=0，退出码 0**（`Ran 14 tests / OK`）。
  - 回件实跑：`python -I -X utf8 candidate/test_except_freshness.py` → 输出留档
    `_w11_t3_test_out.txt`（尾行 `PASS=14 FAIL=0 / EXIT=0`，★亲读确认）。
  - 独立重跑：T2 复核（`reviews/_t3check/`）、T3 复核（`reviews/_t3_review_rerun/`）、
    T1 复核（`reviews/_t3_recheck/`）、T4 复核各重跑一次，均 PASS=14 FAIL=0 / EXIT=0。
  - ★W11 汇总员第 5 次亲跑：同命令，输出 `OK / PASS=14 FAIL=0`，进程退出码 0；
    `ls -d _t3_sandbox_*` → 无残留。
- **TASK 四必备分支全覆盖**：源件缺失 `test_01` → `absent_both(is_new=False,low)`；
  原样遗留 `test_02` → `leftover_unchanged(is_new=False,high)`；内容变化 `test_03` →
  `new_write(is_new=True,high)`；复制失败 `test_04+4b+4c` → `ok=False` + stage
  （write_bytes/read_bytes/src_missing）+ traceback 非空、不静默。
- **判据实现 = T2 推荐组合**：B 主（跑前基线 sha256）+ A 加固版（mtime_pre 差分旁证）；
  `run_start_ts` 仅旁证回显（`test_10` 用荒谬锚点证明不参与定判）；C 仅 `hard_evidence_mode`
  标注（需新裁定）；D 否决未进判定链（与 `:677` 矛盾）。扩展覆盖：同内容重写 `test_06`
  （B 的盲区，判 `rewritten_same_content`）、`vanished`、`new_first_appearance`、`clock_rollback`、
  `post_read_error`、纯函数性 `test_11`（沙箱目录清单不变）。
- **零真机零污染**：候选全程不写盘不启动进程；测试沙箱建于本目录并清理（★本轮亲验零残留）；
  `qc151_trip.py` 未修改（回件开头/收尾两次实算同值，★本轮亲算同值）。
- 复核观察（不降级）：`test_04c`（`test_except_freshness.py:109`）`assertFalse(rec["ok"] is None)`
  偏弱，同用例 `stage=="src_missing"` 断言已覆盖本意；T3 JSON 自述实算时刻 03:36/03:52 与件内头部
  03:36/03:38 存在出入（复核现算同值，不构成实质问题）。补丁缺口有行号支撑：`backup_carrier`
  `:4460-4461` 只记 size+sha 无 mtime、`:4574-4582` 只判 exists、`import time` 已在 `:173`、
  `Recorder.add` 签名 `:446` 兼容。

## 5 T4 影响面

扫描底数：探针 `lead/` 41 文件 311 主命中（except_post 260 / new_exception_count 45 /
no_new_exception 6）+ 补充扫 345 条；`docs/` 全树零命中（实跑 grep 留档 `_w11_t4_out.txt` 3,363 行）。
T4 复核独立重扫：md=48 文件（差额含 W11 自产 11 件、W9 Q1/Q3/Q4_review 真实小缺口——已代过堂、
无新增降级）、md+txt=102 文件/2,312 行（`.txt` 工具输出层未过，TASK 本只令扫 md）。
逐条（文件:行 + 论证了什么 + 是否降级）：

| 位置 | 论证了什么 | 是否降级 |
|---|---|---|
| `GOAL_THREE_TARGETS:5466/:5473`（§555 标题） | 「37 个 archive 零趟游戏崩溃」 | **已降级、确认恰当**——§594:8875（D-22 落账）已停作已验证结论引用，状态改「逐趟归因未独立核验」；§555 八.3（`:5570-5571`）当时已自报「未独立验证，只验了必要条件」；另按 §3-4 加残件出身边注 |
| `GOAL_THREE_TARGETS:5475-5478`（§555 一） | 107 份同哈希 ⇒ 历史基线残件、非任何一趟崩溃证据 | **维持+边注**——W11 根因**坐实**（同哈希是 `:4576-4581` 逐趟逐字复制的结构性结果）；「残件」≠「内容从未对应真实异常」（见 §5 新发现行） |
| `GOAL_THREE_TARGETS:5531`（§555 五） | T5 归因：`new_exception_count=0` ⇒ error.txt 是更早失败残留 | **降级（佐证部分）**——载体陈旧期 `new_exception_count=0` 对本趟崩不崩无信息量；**正确语义 = 「载体 except.txt 跑前跑后内容相同」（经 `except_set_diff :672` 内容差分，不经 except_post 副本）**；主证据 mtime（早 3 小时）保留 |
| `GOAL_THREE_TARGETS:5539/:5565/:5578`（§555 六/八/九） | 目录计数（19 有/18 无）、107 份单一哈希亲验 | 维持（纯计数/亲验事实） |
| §545–§554（`:4489-5465`） | 「计分屏/零建筑判负」之争、§547 进程仍活等 | **零命中**（grep 实证）——未引用 except_post / new_exception_count，不在降级范围 |
| §556–§593 | — | 无关键词命中；崩溃相关表述集中在 §592/§594，已在 2.1 覆盖 |
| `GOAL_THREE_TARGETS:8543`（§594） | 「过去所有基于 except_post 的崩溃判断全部要重估」 | 本清单即重估结果：311 主命中中需实质降级仅 3 处、改口径 2 处，其余维持 |
| `GOAL_THREE_TARGETS:8875`（§594，D-22） | §555 标题级结论停止引用 | 确认降级恰当 |
| `GOAL_THREE_TARGETS:8902-9000`（§595） | 根因节四条前置事实 | 核对一致，无实质错误（计数 59→66/68 过期，见 §2） |
| `XVERIFY_S543_0a451d0b/VERDICT.md:165`、`V2/REPORT.md:157-168`、`V2/RECHECK.md:104-111` | **全仓唯一**把 except_post 当某趟崩溃正面证据（「死因确证」） | **降级成立**——已被下游 `T42E4_FORENSIC` 纠正为「107/107 基线残件不作孤证」；引用原文须带勘误 |
| `BASELINE_MEASURE_DESIGN.md:304/:407`（V7/C9 门禁） | 「无新异常」作门禁语义 | **需改口径**（设计文档，本轮未改）：改「载体内容未变」，判据换 T2 复合口径 |
| `E2_GATE_VERDICT.md:45`、`XVERIFY_TRIPS:285`、`ROUND_LOG:3297`、`c1606d35 REPORT:282`、`ae38d56c REPORT:108` | 「无新异常 = new_exception_count=0 ⇒ CONFIRMED」式表述（共 5 处） | **需加边注**「= 载体内容前后相同」，不改结论 |
| S544 三路（`7255362d`/`ae38d56c`/`c1606d35`） | 普查/REFUTED 记录 | 不需降级（本就不把 except_post 当崩溃孤证） |
| `T42E4_FORENSIC_085458ab`（10 条）+ `RULING_D16/AUDIT.md:498` | 下游纠正与取证 | 维持（即 §555 降级的执行者） |
| `EXIT_CENSUS_77a0d667 01:111`（正确行号；`GOAL:5592` 为 dispatch_table 行，回件引错、复核更正为 `:5492/:5555`） | 16 个目录缺 `qc151_run_log.json` | 维持（§555 取证基础不完整的旁证） |

- **★新发现（T4 §5-1）**：`…/qc164_a4_prep_20261017/ERRATA_EXCEPT_RESTORE.md`（2026-10-17 22:43）
  登记 `6694b75e` 残件内容源自 **qc124 期游戏整体重写 except.txt**（mtime 2026-10-16
  19:21:11+08:00，SINGLE_STEP@007CFC9F），登记链 `VERDICT_T11.md:149`（§9.4）核实 CONFIRMED
  ——**部分回答 W9-Q4 未验项「游戏是否会写 except.txt」**（至少一次，且为内容变化型）。
  复核更正转述：`VERDICT_T11.md:149` 原文是「最新 mtime=19:16:13…（except.txt mtime=19:21:11）」
  ——19:21:11 与 CONFIRMED 属实，「全树最新=except.txt」张冠李戴。
- 勘误件：`lead` 树 3 件（ERRATA_D18/D19/D20B）三关键词 0 命中；`ERRATA_CARRIER_REBUILD.md`
  为程序性勘误（见 §3 复核改判）。复核更正计数：out 树 ERRATA 实为 **15 件**（2 相关+13 其他），
  回件「19 件」应更正。

## 6 必须改项

**modifiedForbiddenFile=true 项：无**（四道复核均 false；`qc151_trip.py` 未被修改——★亲验见 §0；
不触发「总判不得为 CONFIRMED」条件）。须单独落实的修改项：

1. **【T1 复核 mustFix】`T1_SEMANTICS.md` §6/§7/§8 计数口径改写**：两棵趟树不设上限
   diff=64/post=112/state=63；66/113 对应父目录 scope（含 qc161_t13/t14、q161）；全仓 diff=68
   （`lead/l1_u0800_20261020`、`lead/t55k_20261020` 各 1，均 (1046,0)）。
2. **【T1 复核 mustFix】`T1_SEMANTICS.md` §5/§6 读者枚举补全**：补
   `_xv_s04_windows.py:76-78`、`v3_census.py:56,72-84`（含 `:101`）、`probe_e4_t42.py:25-27`，
   保留「均无跑后 vs 跑前比对」核心表述。
3. **【T2 复核 mustFix M1】`T2_CRITERIA.md` §7.1 更正**：ERRATA_CARRIER_REBUILD.md 已找到
   （qc163_a5_prep_20261017/，2026-10-18 00:46:14，2,552B）→「已找到并补读」，并入 §3.C/§7.4；
   同步修正 T1 Q1 证据链引用与本汇总未验清单（本汇总 §3 已按改判落稿）。
4. **【T4 复核意见，数字更正】`T4_IMPACT.md`**：§0 行1「33 个文件」与探针 41 对账（复核实扫
   md=48）、headline「全仓 311 处」限定为「43 件字面量清单上的 311 处」；ERRATA 计数 19→15；
   `GOAL:5592`→`:5492/:5555`；`VERDICT_T11.md:149` 转述删「全树最新」。
5. **【T4 §6-4/5，待后续授权轮】设计文档改口径**：`BASELINE_MEASURE_DESIGN.md:304/:407`
   （V7/C9）改「载体内容未变」+ T2 复合判据；5 处「无新异常⇒CONFIRMED」加边注。
6. **【T1 复核 nitpick】探针 [C] `except_reset` 非 def 出现 4→5 处更正**（漏 `:6391` 注释行）。
- 注：第 1–4、6 项是对**回件原文**的更正，本轮汇总未改回件原件（各回件作者/下一轮执行）；
  本汇总稿内相关数字已按复核口径呈现。

## 7 诚实账

- **未跑/未验项**：gamemd.exe 未反汇编（TASK 明定不需要）、零真机、零注入、零活进程内存
  （四回件四复核一致声明）；T1/T3 复核未重算 gamemd.exe SHA（T2/T4 复核重算一致）；T2 回件
  未全量复核「59 份 setdiff」（声明归 T4，只抽查 l1b）；`s4_module_table.txt`（2026-11-05
  19:44，先于 run）写入者未追查；Mimosa 对 T4 探针「6 次拦截/行号 107/125/…」**不可独立复算**
  （现存 `.mimosa/finding-ledger` 仅聚合记录，`finding_blocked` 为真但逐数不可枚举）；T4 未过
  `.txt` 工具输出层约 2,000 行命中（TASK 只令扫 md）；T1 交接载体 86 件 HANDOVER_SHA 未逐件
  复核（六问不需要）；「谁把漂移件放进 L3 模板」静态不可考，如实登记未验。
- **写域**：唯一写域=W11_EXCEPT_FRESHNESS/（TASK §5）；例外：T4 在 `.tmp/w11_t4_filelist.txt`
  （97,395B，03:45）**技术性越域**（新建草稿非禁改件，已自报 T4_IMPACT §7.4，实质无害）；
  各复核唯一写域 reviews/；本汇总件写入本目录。禁改件（qc151_trip.py、out/re_work/、台账、
  既有 W1–W10/D*_RULING）零修改——★亲验（§0）+ 四复核独立核验。
- **台账漂移**：`PENDING_DECISIONS.md`/`GOAL_THREE_TARGETS_20261018.md` 于 04:23 被领队订正轮
  重构（git diff 261 insertions），T4 所引 PENDING `:28-74` 等行号对不上现行文件——T4 复核改用
  `_w11_t4_out.txt` 03:49 探针快照逐字核实其引用当时为真，**非 T4 之过**。
- **工具链副作用**：Mimosa 钩子两轮写 `out/re_work/.../qc151_u0400_trip/.mimosa/` 2 件状态件
  （03:19:19/03:23:54，`touched:[]`、`bashMutation:false`，事件对象=T2 的 Edit）——判为插件
  自动化副产物（与该目录约 90 个同模式会话件对照），零内容改动，不计违规；本汇总目录亦有
  `.mimosa/` 记账件（同性质）。`lead/GOAL_*.md`、`PENDING_DECISIONS.md` 会话开始前即 MM，
  不归各回件。
- **口径账**：T1 探针深度≤3 的 112/64/63 为截断口径（回件双口径并列），复核细化为三口径
  （见 §2/§6-1）；T4「33 文件/41 文件/48 文件」三个口径已并列对账（§5）。
- **T3 流程透明**：实算时刻自述 03:36/03:52 vs 件内 03:36/03:38（可能第三次未留痕实算，
  复核现算同值）；`test_04c` 断言偏弱（同用例 stage 断言兜底）。
- **★本汇总员本轮实跑清单**：`sha256sum`+`wc -c -l`+`stat`+`git check-ignore -v`+`git status
  --porcelain`（qc151_trip.py 与 out/）；`head` 四回件头部；`grep -n` 台账指纹与 T4 §555/§545
  引用；Read `TASK.md`、`GOAL:9165-9195`、`T1_SEMANTICS.md:193-262`、`T4_IMPACT.md:205-304`；
  第 5 次重跑 T3 测试（PASS=14 FAIL=0 / EXIT=0）+ 沙箱零残留检查。其余数字均溯源八件原始材料。
