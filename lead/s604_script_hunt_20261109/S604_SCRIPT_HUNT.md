# S604_SCRIPT_HUNT.md —— S604 生成脚本残迹穷搜·报告撰写轮（2026-11-09）

角色：穷搜报告撰写员（汇总轮）。链路：编排方（六件指纹 + 六路框架回件）→ 穷搜轮（R6–R10 扩面 + 会话库定向挖掘，回件 `_sh_findings.md`）→ 复核轮（verdict = confirmed，在盘工件 `_shv_*` 19 件）→ 本轮（撰写本报告 + 最小抽查复验）。
写域：`lead/s604_script_hunt_20261109/`。证据分级约定：【本轮实跑】= 本会话执行的命令与输出（输出件 `_sph_*` 前缀）；【实读】= 本会话打开的文件与行号；【转述】= 编排方/穷搜/复核回件内容，本轮未重跑。

---

## 1 目的与边界

1. **目的**：汇总 S604（台账 §604「同一窗内慢 1/3 vs 快 1/3 帧」对照，`lead/GOAL_THREE_TARGETS_20261018.md:9687-9757`【实读】）生成脚本残迹的穷搜全程：逐路覆盖面数字、逐候选真伪、完备性与置信度、复核回件与替代路径。上一轮（`lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md`，下称 GAP 件）结论是「不在盘且从未落盘、码形不可定谳」；穷搜轮在文件系统之外找到生成器本体并定谳码形，复核轮 confirmed；本轮如实成文。
2. **本轮动作边界**：报告撰写 + 抽查复验，不做新的全盘搜索；不重建台账数字、不判台账该不该改（处置留编排方）。
3. **纪律（全程遵守）**：零真机（未启动 gamemd.exe/ra2loader/YURI.exe，未 taskkill，未读活进程内存）；零采样代码（未写 hook/MiniDump/SuspendThread/StackWalk/探针注入/动态内存解析）；全部被搜件只读（会话库用 `mode=ro&immutable=1` 打开，零写入零锁文件）；唯一写域 = `lead/s604_script_hunt_20261109/`；未 commit、未 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 hashlib。
4. **本轮实跑命令清单**（全部只读或仅写本写域）：`_sph_fp.py`（六件指纹+台账 CR 统计+写域有界清点）、`_sph_db_probe.py` 与 `_sph_db_probe2.py`（db.sqlite 行级点查，rowid=512655/512667，immutable=1）、`_sh_gen512655_payload.py` 原样重跑 ×2（输出重定向至写域）、`_sph_cmp.py`（重跑件逐字节比对）、`_sph_ledger_cmp.py`（台账 §604 尾块 vs sec 文本字节比对）。

---

## 2 上游指纹（六件）与上轮四证据链复核

### 2.1 编排方六件指纹（本轮 hashlib 自算，6/6 MATCH）

【本轮实跑】`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/s604_script_hunt_20261109/_sph_fp.py` → `_sph_fp_run_out.txt:2-7`，与编排方指纹块逐一比对：

| 件 | 字节数 | SHA256（本轮自算=编排方基线） | mtime | MATCH |
|---|---:|---|---|---|
| lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md（被核对象） | 20271 | 593c7a3ed3b1d1d47d6da5d8277f76c9323499aa04084a86e376ab5f9d2ab740 | 2026-11-09 02:49:31 | True |
| lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md | 30536 | 823476680c4c7aab7ead279a3f47724dbd1b2fed977087ae86c35a4eef36258c | 2026-11-09 04:53:03 | True |
| lead/s604_attribution_20261108/S604_ATTRIBUTION.md | 27182 | 8e9a606752ce2fd4c3d279ba5bb4a54eba99bc83f8974921f3f5601aa1008237 | 2026-11-09 00:56:15 | True |
| lead/slowframe_r3_20261108/S604_GAP_RECHECK.md | 19291 | 5d1b0ecc9f0e21ddecc38584c363afa0c758f40089ccc57749f237aeffbdf726 | 2026-11-08 13:28:53 | True |
| lead/GOAL_THREE_TARGETS_20261018.md | 759518 | 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede | 2026-11-06 06:53:04 | True |
| lead/PENDING_DECISIONS.md | 52419 | 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 | 2026-11-08 22:26:42 | True |

台账附加指纹【本轮实跑，`_sph_fp_run_out.txt:9`】：总换行数 9757、CR 总数 72、CR 所在行 9686..9757——72 个 CR 恰好全部落在 §604 追加块（9687-9757 及其前导空行），与复核轮「文本模式追加独有指纹」的判定一致（`io.open(p,'a')` 默认 newline 翻译把 sec 文本的 LF 写成 CRLF；512667 落盘命令原文见 `_sh_generator_512655.txt:142-143`【实读】）。

### 2.2 上轮四证据链复核（GAP 件 §3.1–3.5）

【实读】GAP 件 `lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md:32-71`。四条链的性质与覆盖面（穷搜轮复核表 `_sh_findings.md:15-22` 一致，本轮不重跑其搜索，只复核判定）：

| 链 | 性质 | 覆盖面 | 本轮判定 |
|---|---|---|---|
| 路线一 文件名搜索（GAP 件 §3.1，`find lead out/re_work -name '*.py'` + 名针） | 实跑 | lead/ + out/re_work 两棵树 .py 11790 件——仅文件系统 | 成立，但只覆盖两棵树 |
| 路线二 内容搜索（GAP 件 §3.2，5 针 grep） | 实跑 | lead/ + .tmp 的 .py | 成立，同上 |
| 路线三 产物反查（GAP 件 §3.3，三处引文） | 产物自述 | S604_GAP_RECHECK.md:101/:153、SLOW_WINDOW_LIMITS.md:91 | 「未落盘」是上游自述，非独立搜索 |
| 路线四 台账实读（GAP 件 §3.4） | 实读+围栏扫描 | §604 区无代码块、:9751 自述内联、ROUND_SUBAGENT_LOG 零 S604 | 证明「未写入台账」，非对会话存档的搜索 |

判定：四链在**文件系统**范围内方向一致，「未以文件形式落盘」成立；但**均未触及 CLI 会话存档**——而 GAP 件 §4.6-1（`:130`【实读】）自己已把「会话记录/终端历史/编辑器临时文件/系统 TEMP」列为首要可疑来源。穷搜轮正是补上这一路并推翻「语料不存在」（见 §3.11、§4.2）。

---

## 3 九路搜索逐路结果

**路线编号说明**：任务书按「九路」交付；穷搜全程实得路线标签为 R1–R10（R6 含 a–k 子路），外加 DB 定向扫描与复核轮复跑。为不丢任何覆盖面数字，本节按实跑逐条列全、不归并：R1–R5 为编排方实跑（转述），R6–R10 与 DB 为穷搜轮自跑（数字转述自 `_sh_findings.md:24-43`，谓词【实读】自其脚本 `_sh_r678_search.py`），另列复核轮复跑与本轮抽查。

### 3.1 R1 py 文件名含 604/slowframe/gapdiff【转述：编排方回件】
- 范围/谓词：lead/ + out/re_work 等树，.py 文件名正则含 604/slowframe/gapdiff；dirsVisited=2493，耗时 1.56s；命中 5：
  - lead/slowframe_r3_20261108/_r3_recompute_gapdiff.py（12659B）
  - lead/slowframe_r3_20261108/_s604_delta_check.py（2076B）
  - lead/slowframe_r3_20261108/_s604_fp_check.py（2636B）
  - lead/slowframe_r3_20261108/_verify_r3_gapdiff.py（9811B）
  - out/re_work/qc/W2_20261001/forge/scripts/echgap_diff.py（14176B）

### 3.2 R2 全类型名含 604【转述：编排方回件】
- dirsVisited=1291，0.92s，命中 8（=R3 六件 + R1 的 _s604_delta_check.py/_s604_fp_check.py）：lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md（7703B）、lead/s604_attribution_20261108/S604_ATTRIBUTION.md（27182B）、lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md（17272B）、lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md（30536B）、lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md（20271B）、lead/slowframe_r3_20261108/S604_GAP_RECHECK.md（19291B）及上述两 py。

### 3.3 R3 md/txt/json 名含 604【转述：编排方回件】
- dirsVisited=615，0.15s，命中 6（3.2 表中六件文档，清单同上）。

### 3.4 R4 历史/备份目录【转述：编排方回件】
- dirsVisited=615，0.15s，命中 13：lead/c07_gate_fix_20261109/_f3v_orig_transcript.txt（52813B）、_f3_orig_transcript.txt（53005B）、_g1g5_orig_transcript.txt（53005B）、lead/gate_validate_20261108/_gv_replay_original.py（2374B）及其输出（1332B）、lead/goal3t_nightwatch_20261102/swarm_20261104/P01/F_hold_funcs.txt（61904B）、…/XVERIFY_S544_c1606d35/V1/RECHECK_orig_recompute_out.txt（18852B）、lead/qc161_u0400_trip/_audit_threshold_support.py（8069B）、_preview_h7_forms.py（10932B）、_preview_h7_fullpath.py（8903B）、_verify_threshold_audit.py（4395B）、codex_e12_e5_20261030/evidence_hold10_offline.txt（90B）、evidence_hold_invalid.txt（271B）。

### 3.5 R5 无扩展名或异常扩展【转述：编排方回件】
- dirsVisited=600，0.2s，命中 2：lead/o1prime_reach_20261109/_o1v_tmp/_o1v_out_is_file（39B）、lead/w2_samecause_20261109/_w2v_case/outfile_as_outdir（0B）。

### 3.6 R6 仓库外位置扩面（a–k 子路）【穷搜轮自跑；数字转述 `_sh_findings.md:28-36`，谓词【实读】`_sh_r678_search.py:107-129`】
- 谓词通则：每路带深度上限/目录上限/时间预算（`_sh_r678_search.py:54-93` walk 实现），跳过 .git/node_modules，命中=文件名正则（s604|slowframe|gapdiff|gap_?diff|(^|[^0-9])604，:23）或内容 6 针（空档差/快1/3/慢1/3/s604/gapdiff/gap_diff/gap-diff/slowframe，utf-8+gbk 双编码，:15-19）；另收集 11-04..11-08 mtime 窗内 .py 清单（pyInWindow，:27-28,:143）。
- R6a 用户 TEMP（depth6，.py/.txt/.log/.md/.json/.out ≤1MB）：dirs=2076，files=18115，39.1s，未截断；79 命中全为 11-08/09 会话回声与 dsh 对象哈希噪声；**pyInWindow(11-04..08)=0**。
- R6b C:\Windows\Temp（depth4）：dirs=1，files=7，0.01s；0。
- R6c C:\$Recycle.Bin（depth4，.py）：dirs=3，files=3，0.00s；0。
- R6d 仓库 .tmp 深层（depth6）：dirs=12，files=129，0.39s；内容 0 命中；窗内 .py 48 件全列、无一相关。
- R6e/f/g C:\Temp、D:\Temp、D:\tmp（各 depth4）：dirs 合计 828，files 4898，4.5s；6 命中=cargo 哈希噪声。
- R6h C:\Users\Administrator\.zcode 遍历（depth5，.jsonl/.json/.txt/.md/.log ≤30MB，跳 plugins/cache）：dirs=2387，files=5453，90.5s **预算截断**；51 命中=UUID 哈希噪声+10 月 rc4_gap_diff 日志+今日日志；由此转定向 DB 挖掘（§3.11）。
- R6i C:\Users\Administrator\.agents（depth4）：dirs=119，files=696，5.3s；0。
- R6j VSCode Code\Backups（scan_all）：dirs=1，files=0，0.00s；空。
- R6k Recent .lnk（仅名，窗内）：dirs=3，files=907，0.25s；1 哈希噪声；窗内 .lnk=0。

### 3.7 R7 git 历史/悬空对象【穷搜轮自跑；转述 `_sh_findings.md:40`】
- 只读列举（未用会写盘的 --lost-found）：stash 空；.git/lost-found 不存在；`git fsck --full --dangling --no-reflogs` = 213 悬空 blob + 25 commit + 20 tree；逐 blob `git cat-file` 内容扫描 52.3s：64 个含 measure_w|frame_edges（goal1 时代 10-18 旧结果），**0 个含 空档差/快1/3/慢1/3/s604/gapdiff**；历史删除路径 grep 空。

### 3.8 R8 编辑器残迹【穷搜轮自跑；转述 `_sh_findings.md:37`，谓词【实读】`_sh_r678_search.py:25,:180-219`】
- 范围=仓库 depth5；谓词=编辑器备份名正则（.swp/.swo/.kate-swp/~/.bak/.orig/.rej/.autosave/.sav/.#）+ .vscode/.idea/.history 目录探存；dirs=2315，files=434850，29.6s，未截断；21 件命中全为 .sav/.bak/.orig 游戏与 RE 旧件；存在性检查：VSCode Backups/Notepad++ backup/JetBrains LocalHistory/OneDrive 存在，仓库 .vscode/.idea 不存在。

### 3.9 R9 仓库日志内嵌 Python【穷搜轮自跑；转述 `_sh_findings.md:38`，谓词【实读】`_sh_r678_search.py:222-249`】
- 范围=仓库 depth8；扩展名=.log/.txt/.out/.md/.json/.jsonl，1B–5MB；谓词=9 针（R10 名针集）**且**同文件含 `def `/`import `（require_py）；dirs=5288，files=64378，120.1s **预算截断**；209 命中全部为「604」数字噪声（十六进制地址/字节数/行号），逐条摘句核实无脚本块。全量清单在盘 `_sh_r678_out.txt`。

### 3.10 R10 仓库名复核【穷搜轮自跑；转述 `_sh_findings.md:39`】
- 范围=仓库 depth8，文件与目录名正则（604|slowframe|gapdiff|gap_?diff）；dirs=8522，files=533992，7.4s，未截断；7588 命中=哈希/日期碰撞 + rc4_gap_diff_fix 时代（2026-10-12）旧件；**复现 R1/R2 全部 8 件，无遗漏件**。

### 3.11 DB 定向扫描（决定性一路）【穷搜轮自跑；转述 `_sh_findings.md:41,:63-75`】
- 范围=C:\Users\Administrator\.zcode\cli\db\db.sqlite（3.1GB），`immutable=1` 只读，全 99 对象全 TEXT 列 7 针，139.6s：10224 命中行；CN 针（空档差/快1/3/慢1/3/最大空档）仅 2 行 → 顺会话 sess_4fc16d67-74ac-4000-b9e9-9fd1257930aa（「每25分钟驱动逆向线」，1714 消息/5933 parts/1008 个 Bash 调用）时间线锁定：512645（06:52:26 帧方差探针）→ 512650（06:52:33 两窗三分对照=「标签写反」现场）→ **512655（06:52:40 生成器本体）** → 512660 → 512664（前缀闸）→ 512667（06:53:03 §604 落盘）→ 512670（06:53:11 节拍锚账）。
- 复核轮补扫【实读 `_shv_dbscan3_out.txt`】：db.sqlite 主库 raw 扫描 SHARP 96/FULL 46/ISPREFIX 74/CN_lit 3523 处（:1-7）；**WAL** SHARP 6/CN_lit 24 全为今日会话回声（:8-14）；**db.sqlite.bak-2026-11-05T14-37-34（2.7GB）全针 0**（:15-21）——穷搜轮申报的 bak 未扫项由复核轮闭合。行归因：part 表 SHARP 行 35 个中属 11-06 时代的**仅 512650 与 512655**，其余 33 个 rowid≥601200 全为今日 dwf 会话回声（:23-54）。

### 3.12 复核轮复跑与本轮抽查（覆盖面背书）
- 复核轮 R1′/R2′ 等价复跑【转述：复核回件 + 实读输出件】：文件名路 5669 目录/493585 文件/7114 命中全为哈希碰撞+旧件；内容锐针全量不截断（仓库 dirs=16575 files=116980 65.6s + .zcode dirs=6253 files=40165 25.1s = 157245 文件）**写域外零命中**，命中 19 处全为写域自镜像与今日会话工件（`_shv_r2full_out.txt:1-31`【实读】）；TEMP 窗内 py=1439/pyInWindow=0/内容 0【转述】；git 213 悬空 blob 零命中【转述】。
- 本轮抽查【本轮实跑】：写域有界清点 dirs=1/files=38/0.002s（`_sph_fp_run_out.txt:11-49`；17 件 `_sh_*`=穷搜轮产出、19 件 `_shv_*`=复核轮产出、2 件 `_sph_*`=本轮在写）；DB 点查 open+两行 rowid 查找 0.003s（`_sph_db_probe_out.txt:4-22`）、嵌套 JSON 解析 0.002s（`_sph_db_probe2_out.txt:10`）；生成器重跑 0.473s（`time` 实测）。

---

## 4 候选真伪鉴别与完备性评估

### 4.1 逐候选真伪鉴别

**(a) 文件系统候选 9 件**（R1/R2/R5 并集去上游基线件；指纹+mtime=`_sh_fp_out.txt:10-18`【实读】，三问判定转述自 `_sh_findings.md:49-61`，本轮逐件核对其 mtime 与字节一致）：

| 候选 | 字节 | mtime | 完整脚本? | 11-06 产物? | 能否定谳码形? |
|---|---:|---|---|---|---|
| slowframe_r3/_r3_recompute_gapdiff.py | 12659 | 11-08 12:43 | 是（第三方复算） | 否 | 否——正确口径自实现，非原脚本 |
| slowframe_r3/_s604_delta_check.py | 2076 | 11-08 13:25 | 是（核对件） | 否 | 否 |
| slowframe_r3/_s604_fp_check.py | 2636 | 11-08 13:23 | 是（指纹件） | 否 | 否 |
| slowframe_r3/_verify_r3_gapdiff.py | 9811 | 11-08 13:05 | 是（第三重实现） | 否 | 否 |
| out/re_work/.../echgap_diff.py | 14176 | **2026-10-01** | 是（RE 时代旧件） | 否 | 否 |
| ledger_appendix/_la_draft3_s604_gapdiff.md | 7703 | 11-08 23:14 | 文档 | 否 | 否 |
| s604_attribution/_sa_ATTRIBUTION_S604.md | 17272 | 11-09 00:04 | 文档 | 否 | 否 |
| o1prime/_o1v_out_is_file | 39 | 11-09 04:00 | 探针残渣 | 否 | 否 |
| w2_samecause/outfile_as_outdir | 0 | 11-09 04:11 | 空件 | 否 | 否 |

**9 件全非生成器**：无一既是完整脚本又是 11-06 撰写轮产物，故无一能定谳码形。文件系统上确无 11-06 脚本残迹。

**(b) 会话库行（决定性命中）**：part rowid=512655。本轮证据链【本轮实跑】：
1. `_sph_db_probe_out.txt:6-13`：rowid=512655 存在于 part 表（列 [id, message_id, session_id, time_created, time_updated, data, sequence]），session_id=sess_4fc16d67-74ac-4000-b9e9-9fd1257930aa，time_created=1793919160503（epoch ms）= 2026-11-06 06:52:40.503（本地 UTC+8）——与台账落盘（512667 tc=1793919183419 = 06:53:03.419，`:14-21`）相差 23 秒，与「落盘前 23 秒」一致。
2. `_sph_db_probe2_out.txt:2`：直读 `data.state.input.command` = **1633 字符 / 1729 UTF-8 字节，sha256=f4f6aa516a76ea8a5e8557e01925223a31361a97282cefe67792f1479b3cb459**——与复核轮提取件 `_shv_row512655_command.txt`（1729B，`_sph_db_probe_out.txt:2` 同哈希）逐字节一致；command sha 来自 DB 本体，链路闭合。穷搜回件所写「input.command 1245B」为误（1245 = 该行 **output** 的 metadata originalBytes，`_sh_generator_512655.txt:62`【实读】），复核轮已勘误，本轮实证。
3. 码形原文【实读 `_sh_generator_512655.txt:14`，即 command 体内】：`dur={fe[i][0]:(fe[i][1]-fe[i-1][1])*1000.0 for i in range(1,len(fe))}`——键取第 i 帧，值取 fe[i−1]→fe[i] 区间长（=前一帧时长）；配对行 `rec.append((fi,dur[fi],max(gaps)*1000.0))`（:22）、排序 `rec.sort(key=lambda r:r[1])`（:24）。maxgap 计算本身正确（:21）。
4. 原样重跑【本轮实跑】`python -I -X utf8 …\_sh_gen512655_payload.py`（纯计算：只读 `lead/**/measure_w*.json`，仅 print——源码 `_sh_gen512655_payload.py:1-33`【实读】）：`_sph_cmp_out.txt:1-4` = 与穷搜轮捕获 `_sh_gen512655_out.txt` **bytes_equal=True**（同 1247B，sha256=cf74264071463777e55a10111b6768ff528328bb43d203da001886be6fda9256）；15/15 行与台账 §604 表 :9706-9720【实读】逐位一致，汇总行「中位 -114.820 ms，范围 -153.822 .. -32.233」「2.19 倍」一致（`_sph_gen512655_rerun_out.txt:1-19`；第二次重跑 `_sph_gen512655_rerun2_out.txt` 同内容）。
5. 落盘同源【本轮实跑】`_sph_ledger_cmp_out.txt:1-4`：台账 9687..9757 行（去 CR，含末换行）= **3022 字符，sha256=6a893fb8b9942b5bc7e23cee0bd07ae1bbe0f252d7403832f90793c628059788**，与 DB 512667 command 内嵌 `sec` 文本 `sec[1:]`（`_sph_db_probe2_out.txt:7`，同哈希）**MATCH=True**；边界变体 `sec[1:-1]`（3021 字符，e0365b2b…）亦 MATCH。512667 输出原文 `APPENDED 3023 / IS_PREFIX_EXT True LINES 9757`（`_sh_generator_512655.txt:156-157`【实读】）与本轮台账实况（总换行 9757、被核对象哈希未变）吻合。
6. 穷搜回件所称「CN 针仅 2 行」系首版扫描归类窗口伪影，复核轮实测 part 表含「空档差」字面 645 行（在盘件 `_shv_dbscan3_out.txt:93` 实测值 **647**，回件转述 645，差 2 不影响归因）；11-06 时代含码行仍仅 512650/512655 两行（:24-26）。

**(c) 其余非候选**：DB 同族行 512550（06:02:36 两窗最大空档诊断）、512645、512660、512664、512670（探针/找节号/前缀闸/锚账）均非生成器；512650 的 command 亦含同款 dur 错位行（复核轮发现，`_shv_row512650_command.txt` 1223B）——「标签写反」现场与台账 :9752【实读】自白对应；仓库根异常未跟踪件 GLM/Qwen/`Step。`（0 字节，`_sh_fp_out.txt:21-28`）与今日回声行 rowid≥601200（`_shv_dbscan3_out.txt:27-54`）均与本议题无关。

**码形定谳**：错误行 = `dur` 字典推导错位（键 fe[i][0]、值 fe[i−1]→fe[i] 区间长）⇒ 三分排序时每帧挂接其**时间后继**帧的 maxgap，机制类 = C8a「时长-maxgap 错一帧对齐·时间后继挂接」（GAP 件 §4.3 筛入 75/75【实读 `S604_SCRIPT_GAP.md:109-111`】）；zip 截断 / wrap 回绕 / C13c bisect 三种候选码形全部证伪（显示精度下数值等价但原文只支持字典错位一种）。台账 :9754 的 −114.8 汇总行 = 512655 输出里 `diffs=[x[4]-x[3]]` 原样留痕【实读 ledger :9754、`_sh_generator_512655.txt:34`】。

### 4.2 完备性评估（覆盖了什么、不可能覆盖什么、置信度三档）

**已覆盖（数字汇总）**：仓库文件名两轮复核（R10 8522 目录/533992 文件 + R8 434850 文件名）、内容锐针全量不截断 157245 文件（复核轮）、R9 日志内容 64378 件、用户/系统 TEMP、回收站、C:\Temp、D:\Temp、D:\tmp、.agents、VSCode Backups、Recent、仓库 .tmp、git 全历史 + 213 悬空 blob、3.1GB 会话库主库 + WAL + 2.7GB bak 三件全针扫描。生成器本体经「DB 直读 command sha → 提取件同哈希 → 重跑逐位 → sec↔台账字节等 → CR 指纹 → mtime 链」六重独立验证（穷搜轮三重 + 复核轮复现 + 本轮四项抽查全部复现）。

**不可能/未覆盖（如实申报，穷搜轮 §5 :105-110 申报 + 复核轮确认）**：已删除文件的磁盘未分配残块 carving 未做（本体已得，无必要）；JetBrains LocalHistory 为专有二进制未解析；OneDrive 仅确认存在、云端内容未审计；R6h（90.5s）/R9（120.1s）两路预算截断后的残余未补扫（穷搜判定已由 CLI 日志逐件清点 + DB 全列扫描覆盖，属转述判断）；WAL 为活文件，读的是扫描时点快照。

**置信度三档**：
- **高**：①文件系统上无 11-06 生成器 .py（R1–R10 六方向 + 复核轮 157245 文件锐针复跑，独立一致）；②生成器本体 = part rowid=512655（本轮 DB 直读 command 1633c/1729B sha f4f6aa 实证 + 复跑逐位复现 + sec↔台账字节等 + 时间线自洽）；③码形 = dur 字典错位（原文在案 + 重跑复现 + 三候选证伪）。
- **中**：④「从未在 CLI 存档之外存在过」——依赖 TEMP/回收站/编辑器残迹等位置覆盖的完备性，属强推断而非可穷尽证明；⑤编排方 R1–R5 逐路数字（转述未重跑；复核轮复跑等价路 R1′/R2′ 一致，部分背书）。
- **低/未覆盖**：⑥carving、LocalHistory、OneDrive 云端、R6h/R9 截断残余——未审计；对本任务结论无影响（本体已得），但作为完备性边界如实计入。

---

## 5 复核回件、替代路径、未改文件声明与未验项

### 5.1 复核回件（如实转录）

- **verdict = confirmed**（复核回件原判；非 refuted/partial，故不标 unconfirmed）。复核员实跑 28 条命令，穷搜回件核心主张全部独立复现：六件指纹 6/6 MATCH、五路复现文件系统否定结论、512655 定谳链复现（command 实测 1729B、payload 为 -c 体去 1 前导换行、15/15 逐位、sec 文本 3022 字符 sha 双算、全件 72 个 CR 恰全部落在 9686-9757、台账 mtime 2026-11-06 06:53:04.100 未被触碰）、并补扫 bak（全针零命中）与 WAL（今日回声）闭合两项申报缺口。上述关键项本轮已再抽查复现（§4.1(b)）。【转述：复核回件；其中 command 1729B/sec 3022 字符/CR 指纹/行归因四项本轮已按在盘件与自跑复核】
- 复核轮记账 6 处小误差（复核自报，均不动摇定谳）：①「input.command 1245B」应为 1729B（本轮实证 `_sph_db_probe2_out.txt:2`）；②「原样重跑」实为 -c 体去 1 前导换行的 payload 形式；③「CN 针仅 2 行」是归类窗口伪影（实测 645/在盘 647 行含字面，11-06 含码行仍 2 行）；④512550 时间 06:4x 实为 06:02:36；⑤「产出 16 件」实为 17 件（本轮清点 `_sh_*` 17 件，`_sph_fp_run_out.txt:12-28`）；⑥「WAL 未读」实为已读且全为今日回声。
- 本轮另记一处：复核回件转述「645 行」与在盘 `_shv_dbscan3_out.txt:93` 的 647 差 2，以在盘件为准。
- 复核轮可证伪性裁决（转录）：若台账只记「机理=C8a 等价类」而丢工件链则不可证伪；现原脚本已钉死（rowid + 1729B 原文 + 复跑逐位 + sec↔台账字节等 + CR 指纹 + mtime 链），主命题「码形已定谳：dur 字典错位一行」+ C8a（75/75）作次级注记的写法**完全可证伪**。
- 被核对象绑定行（对象 = lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md；上值本轮 `python -I -X utf8 …\_sph_fp.py` + hashlib 自算，`_sph_fp_run_out.txt:2`，与编排方指纹 MATCH=True）：

被核对象 SHA256 = 593c7a3ed3b1d1d47d6da5d8277f76c9323499aa04084a86e376ab5f9d2ab740，字节数 = 20271

### 5.2 替代路径

- **缺码形定谳影响什么（反事实）**：若无 512655 本体，C8a 只能以「75/75 数值等价类」存在——它是对「错一帧挂接」的充分性证明，但 zip 截断/wrap/bisect 等码形在显示精度下数值不可分（GAP 件 §4.4【实读 :115-116】），任何复现同数字的实现都可事后归入同一等价类 ⇒ 「确切错误行」不可定谳，台账处置与回件可证伪性都只能停在机理类层面。
- **不依赖原脚本的推进方案**：①正确口径复算已有四重独立实现与 R3 [D] 真值（+0.0065..+0.1080，GAP 件 §4.5【实读 :124】），语料 15 件指纹锁定未漂移（GAP 件 §4.2）；②免授权即可复跑 GAP 写域 `_sg_probe_compression.py`/`_sg_probe_shift.py` 核对 75/75 与 −114.8 两指纹（GAP 件 §4.6-2【实读 :131】）；③台账 §604 是否改写、如何改写 = 编排方裁决事项，本轮不判。
- **未来拿到（新的）脚本/存档时的验证方案**（本轮已按此执行，可作模板）：①先报路径与字节数，hashlib 记指纹，不动原件；②`python -I -X utf8` + 绝对路径在只读输入上重跑，与历史输出逐字节比对；③与台账落盘文本做去 CR 字节级比对（注意边界约定：含/不含首尾换行会导致 sha 不同——本轮实证 6a893fb8=sec[1:]↔台账 9687..9757+末换行）；④时刻链核对（会话时间戳 vs 文件 mtime vs 台账落盘命令输出）；⑤静态定位确切错误行并与候选码形逐一证伪/证实。

### 5.3 未改任何文件声明

1. 本轮写入仅限写域 `lead/s604_script_hunt_20261109/` 内 13 件：`_sph_fp.py`、`_sph_fp_run_out.txt`、`_sph_cmp.py`、`_sph_cmp_out.txt`、`_sph_db_probe.py`、`_sph_db_probe_out.txt`、`_sph_db_probe2.py`、`_sph_db_probe2_out.txt`、`_sph_gen512655_rerun_out.txt`、`_sph_gen512655_rerun2_out.txt`、`_sph_ledger_cmp.py`、`_sph_ledger_cmp_out.txt`、本报告 `S604_SCRIPT_HUNT.md`。写域外**零写入**（含台账、语料、会话库——DB 以 `mode=ro&immutable=1` 打开，未产生 -wal/-shm 写入）。
2. 六件上游指纹本轮复算 6/6 MATCH（§2.1）——内容未变；台账 mtime 2026-11-06 06:53:04【本轮实跑】——未被触碰。
3. 生成器重跑只读语料、只 print（源码已核）；未 commit、未 push；本轮未运行任何 git 写命令（本轮未运行 git）。

### 5.4 未验项（不补造）

1. 编排方 R1–R5 逐路数字本轮未重跑（转述）；复核轮复跑 R1′/R2′ 等价路一致，属部分背书而非全量重放。
2. 复核回件 28 条命令未逐条重放；本轮只实读其在盘输出件 `_shv_r2full_out.txt`、`_shv_dbscan3_out.txt` 并自跑四项关键抽查（command sha、sec↔台账、重跑比对、六件指纹）。
3. R6h/R9 截断残余未补扫；磁盘 carving、JetBrains LocalHistory、OneDrive 云端未审计（§4.2）。
4. 穷搜轮大体积原始输出 `_sh_gen_out.txt`（1588260B）、`_sh_s407_out.txt`（1233911B）、`_sh_r678_out.txt`（121159B）、`_sh_r7_*` 本轮未逐行复读，仅实读其汇总件 `_sh_findings.md` 全件与关键证据件。
5. `_shv_dbscan3.py` 各针的确切字面定义本轮未逐针核对（CN_lit 按其输出标签转述）。
6. 台账 :9752「标签写反」的 512650 两窗版现场未由本轮直读 DB 行（转述：复核回件 + 在盘 `_shv_row512650_command.txt` 1223B 未复读内容）。
