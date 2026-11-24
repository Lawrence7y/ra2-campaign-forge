# C 组 · 跨文件一致性独立复核（W7 复核员 C）

```
被核对象 = W4_FIELD_SPEC/sections/ 七份（C 组核其相互一致性）：
           card_0087E8E0.md / card_00A8EC34.md / card_00B0CE88.md / card_00A8ED50.md /
           Q2_ALPHA.md / Q3_FRAME_EDGE_SPEC.md / Q4_REDLINE.md
被核对象 SHA256 = 七份逐份实测（本人 python -I -X utf8 二进制读流实算，未照抄 TASK.md:13-21 参照值）：
           card_0087E8E0.md      = e3afe2abb9bcac4be6f7e9666a836c6dff3499e4be9796ab568c6347bd1534b8  (44403 B)
           card_00A8EC34.md      = 6cde19c881ab09f6f7b1246fe75dbc41d7538d0dbba59c9b528db9b35d821b46  (31647 B)
           card_00B0CE88.md      = c16cf1f3a3e5c254f8c232534a738ca24ced23803051f0fdb1e6145fc33ea578  (32262 B)
           card_00A8ED50.md      = a5926b6398879f880c7fe0c1726fec4a29306c9670bfcc67dad67aca36f3325e  (37864 B)
           Q2_ALPHA.md           = 27055e6b94f892c6a53facc07adf908688c151eca82cfe56da8133cee8507663  (31712 B)
           Q3_FRAME_EDGE_SPEC.md = 0d3e13875855ea4b5d36f22e6f622916ac15b479944767fe4d067aaee5639c5d  (38799 B)
           Q4_REDLINE.md         = 2189d17a115249e20d9f31465d7ec38535b10c10904db5c32212a5ecc886c329  (23037 B)
           七份按上表顺序拼接实测 = f323f77dd0f64fc9c1a2edfb138ece70667418ed11bac0987ef1918e7ac0b579 (239724 B)
           结构化回件 sha256Measured/sizeMeasured 绑定本组三条判定共同依赖的枢纽件 Q4_REDLINE.md。
字节数 = 七份合计 239724；枢纽件 Q4_REDLINE.md 实测 23037
复核时刻 = 2026-11-05 22:17:31（探针 _w7_c.py 起跑时刻，_w7_c_out.txt:1；逐份 Read 于同一会话完成）
实测命令 = cd /d/Project/ra2-campaign-forge && python -I -X utf8 -c "import hashlib, os;
           base=r'D:\Project\ra2-campaign-forge\lead\re_line_20261105\W4_FIELD_SPEC\sections';
           [print(f, len(open(os.path.join(base,f),'rb').read()),
           hashlib.sha256(open(os.path.join(base,f),'rb').read()).hexdigest()) for f in FILES]"
           （退出码 0，逐字输出见 _w7_c_out.txt:7-15 与下表）
```

## 0. SHA256 绑定（自己实算，二进制 `open(...,'rb').read()`；未照抄任务书参照值）

| # | 文件 | 实测字节数 | 实测 SHA256 | 与 `W7_W4_REVIEW/TASK.md:13-21` 对照 |
|---|---|---:|---|---|
| 1 | `card_0087E8E0.md` | 44,403 | `e3afe2abb9bcac4be6f7e9666a836c6dff3499e4be9796ab568c6347bd1534b8` | 一致 |
| 2 | `card_00A8EC34.md` | 31,647 | `6cde19c881ab09f6f7b1246fe75dbc41d7538d0dbba59c9b528db9b35d821b46` | 一致 |
| 3 | `card_00B0CE88.md` | 32,262 | `c16cf1f3a3e5c254f8c232534a738ca24ced23803051f0fdb1e6145fc33ea578` | 一致 |
| 4 | `card_00A8ED50.md` | 37,864 | `a5926b6398879f880c7fe0c1726fec4a29306c9670bfcc67dad67aca36f3325e` | 一致 |
| 5 | `Q2_ALPHA.md` | 31,712 | `27055e6b94f892c6a53facc07adf908688c151eca82cfe56da8133cee8507663` | 一致 |
| 6 | `Q3_FRAME_EDGE_SPEC.md` | 38,799 | `0d3e13875855ea4b5d36f22e6f622916ac15b479944767fe4d067aaee5639c5d` | 一致 |
| 7 | `Q4_REDLINE.md` | 23,037 | `2189d17a115249e20d9f31465d7ec38535b10c10904db5c32212a5ecc886c329` | 一致 |

**⇒ 七份全部逐字相符，无 `OBJECT_CHANGED`。** 合计 239,724 B；七份按上表顺序拼接的实测 SHA256 =
`f323f77dd0f64fc9c1a2edfb138ece70667418ed11bac0987ef1918e7ac0b579`（探针 `_w7_c_out.txt:7-15`）。
结构化回件 `sha256Measured`/`sizeMeasured` 绑定本组三条判定共同依赖的枢纽件 `Q4_REDLINE.md`
（`2189d17a…886c329` / 23,037 B）；七份单文件实测值全列于上，不冒充单文件覆盖全组。

目标镜像（`ra2tool.Engine` 实测，探针 `_w7_c_out.txt:20-25`）：
`EXE_SHA256 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`，`EXE_SHA_MATCH True`，
`IMAGE_BASE 0x400000`，`COVERAGE (99.99837567729335, 1394120, 66)`。故下列字节核证适用于七份正文共同声明的同一份 `gamemd.exe`。

---

## 1. 一句话总判

**五对逐对检查全部相容，字节底座经本次真反汇编复核成立；七份的「未验/未核实」标记均有诚实账落点，未发现把未验写成已验的强断言。C 组判 CONFIRMED，实质缺陷 0。**
仅记录 1 处**非实质**的措辞松散（`Q4_REDLINE.md:143` 把「读序/时间戳/…」整体称作「未来规格要求」，而同批 `Q3_FRAME_EDGE_SPEC.md` 已产出待审设计卡；不影响三条红线判定，见 §4）。

---

## 2. 本次实跑（精确命令 + 逐字输出要点）

| # | 精确命令 | 退出码 / 输出 |
|---|---|---|
| ① | `cd /d/Project/ra2-campaign-forge && python -I -X utf8 -c "import hashlib, os; base=r'D:\Project\ra2-campaign-forge\lead\re_line_20261105\W4_FIELD_SPEC\sections'; ... print(f, len(data), hashlib.sha256(data).hexdigest())"` | 退出码 0；7 行 `文件名 字节数 sha256`，逐字见 `_w7_c_out.txt:7-13`；与 `TASK.md:13-21` 全同 |
| ② | `cd "D:/Project/ra2-campaign-forge/lead/re_line_20261105/W7_W4_REVIEW" && python -I -X utf8 _w7_c.py > _w7_c_out.txt 2>&1` | `EXIT=0`，694 行；`W7_C_PROBE_START 2026-11-05T22:17:31` … `W7_C_PROBE_END 2026-11-05T22:19:41`（`_w7_c_out.txt:1,694`） |
| ③ | `python -I -X utf8 -c "... e.disasm(0x42CBFA,0x18) ... callers(0x429A90) ... callers(0x42A690) ..."`（补核 `Q4_REDLINE.md:95`） | 退出码 0；`0x42cc02 e889ceffff call 0x429a90`；`callers of 0x429A90 count 1 ['0x42cc02']`；`0x42A690 xrefs count 0`；`0x42c290 55 8bec 83e4f8 83ec5c` |
| ④ | `python -I -X utf8 -c "... 强断言正则逐文件扫描 ..."`（C2 项） | 退出码 0；逐文件 `strong_claim_lines` 9/8/13/11/9/7/5，逐行输出见 §5 讨论 |
| ⑤ | `python -I -X utf8 -c "... RULING_D21 / V6 / Q3 字面核对 ..."` | 退出码 0；`RULING_D21 '每个触发沿新增 5 次跨进程读' -> True`、`'20 B' -> True`、`'复用该拍外层轮询值' -> True`；`V6 'CONFIRMED' -> True`、`'每沿新增读为 5 次' -> True`；`Q3 '20λ B/s'/'5λ 次'/'名义操作数' -> True` |

探针 `_w7_c.py` 按 `TASK.md:120` 用 `sys.path.insert(0, r'...\swarm_20261104')` + `from ra2tool import Engine`，
全程只读磁盘 PE、零真机、零注入、未改任何既有文件；唯一写域 `W7_W4_REVIEW/`。

---

## 3. C1 · 五对逐对一致性（含真反汇编字节核）

### 对① `card_0087E8E0.md` ↔ `Q4_REDLINE.md`（C1 判定）—— **相容**

- 两份的判词同口径：`Q4_REDLINE.md:16`、`:74`、`:108`、`:152` 判 **C1 = 部分能**，理由「只能说发生了会推进代际的**入口/重试尝试**，不能说 Dijkstra 真被调用/完成/成功，更不能说展开了很多节点」；
  `card_0087E8E0.md:329-334`（能说第 3 条「受限尝试代理」）、`:341-344`（不能说 1–3 条）、`:258`（G5 递增早于可能失败的检查）与之逐条同义。
- **字节底座本次真反汇编复核成立**（`_w7_c_out.txt:37-121`）：
  - `0x42A5FB 8b4128` / `0x42A5FE 40` / `0x42A5FF 894128` 读/增/写回 `[ecx+0x28]`；`0x42A602 0f8580000000 jne 0x42a688`（非零早退）；
  - 回绕分支 `0x42A67F 8b4128` / `0x42A683 40` / `0x42A685 894128` 再增一次 ⇒ `0xFFFFFFFF → 0 → 1`（+2 跳 0）；
  - 构造体 `0x42A6DC 83c9ff`（ecx=−1）+ `0x42A701 894e28`（本字段=−1）⇒ 按字节链首次调用即回绕；
  - `0x42CC80 e82bd9ffff call 0x42a5b0` 同步重试再次推进；`0x42CC02 e889ceffff call 0x429a90` 是全镜像 **唯一** `SearchCore` 调用点（命令③），与 `Q4_REDLINE.md:95`「`0x42CC02` 才调用 `SearchCore`」相符；
  - `0x42D17D` 是另一入口 `0x42D170` 内的调用（prologue `83ec08` / `c6433801`），`0x42D229 0f8423020000 je 0x42d452` 是写回之后的失败检查；
  - `0x429AB6 c744242800000000 mov [esp+0x28],0` —— 节点轮数是**栈局部**，不是 `[this+0x28]` 代际戳，支撑两份共同的「不能说展开很多节点」；
  - 全流 census：`CALLERS 0x42A5B0 count=3 ['0x42c90d','0x42cc80','0x42d17d']`、`0x42C900 count=2`、`0x42D170 count=18`、`IMM mov ecx,0x87E8B8 count=28`（`_w7_c_out.txt:27-29,119-120`），与 `card_0087E8E0.md:29-33,270-308`、`Q4_REDLINE.md:76` 的数字一致。
- **判**：无矛盾。Q4 的三档判词没有把 `card_0087E8E0.md` 的「尝试代理」升级成「完成/工作量」，也没有把卡标「未验」的运行期频率当作已测。

### 对② `card_00B0CE88.md` ↔ `Q4_REDLINE.md`（C2 判定）—— **相容**

- `Q4_REDLINE.md:15`、`:37`、`:56-68` 判 **C2 = 不能**：`0x00B0CE88` 是脏矩形队列瞬时 Count，与屏内可见单位数无恒等/单射/单调/已校准映射；`card_00B0CE88.md:11`、`:175-194`、`:206-210` 同判，且 `:208` 明列「不能换算为屏内可见单位数」。两者共用同一组 W3 阈值否定（`Q4_REDLINE.md:68` ↔ `card_00B0CE88.md:155,210`）。
- **订正点本次逐址复核**（`_w7_c_out.txt:126-134,185-186`）：
  `0x6D3DE8 8a857c0d0000` → `0x6D3DEE 84c0` → `0x6D3DF0 a188ceb000`（读 Count）→
  **`0x6D3DF5 756e jne 0x6d3e65`**（不是 `test eax,eax`）→ `0x6D3DF7 84c9 test cl,cl` →
  `0x6D3DF9 0f859c000000` → **`0x6D3DFF 85c0 test eax,eax`**（真正的判零）→ `0x6D3E01 7566 jne`。
  原始字节 `RAW_0x6D3DF5_8B 756e84c90f859c00`、`RAW_0x6D3DFF_8B 85c075668a8d7d0d`。
  `Q4_REDLINE.md:53`「真实 `test eax,eax` 在 `0x6D3DFF`，不是 W3 抄录的 `0x6D3DF5`」与 `card_00B0CE88.md:141,153-155` 的 `0x6D3DF5=756e jne` / `0x6D3DFF=85c0` 完全一致。
- **「不是 TacticalClass 成员」/「零 call」**（`_w7_c_out.txt:137-184`）：
  `0x6D2790 83ec58` 紧接 `0x6D2793 8b0d88ceb000 mov ecx,[0xb0ce88]`（传入 `this` 立即被绝对地址覆盖）；构造 `0x6D1A7D c70578ceb0009c427f00` 写绝对 vptr、`0x6D1A91 a388ceb000` 置 Count=0；
  `DISP_HITS_0xB0CE88` 共 27 处（6 W / 21 R），与卡 §3.1/§4.1 数字一致；
  `RDA_callers_in_[0x5F4B10,0x5F4D30) count=0 []`、`RDA_callers_total count=58`，与 `card_00B0CE88.md:189`、`Q4_REDLINE.md:51` 的「函数体内零处 `call 0x6D2790`」「58 个直接调用点」一致。
- **判**：无矛盾。两份对「Count=0/小 ≠ 不渲染」的多路旁路（`Q4_REDLINE.md:53` ↔ `card_00B0CE88.md:130-155`）指向同一段字节。

### 对③ `card_00A8EC34.md` ↔ `Q4_REDLINE.md`（C4 判定）—— **相容**

- `Q4_REDLINE.md:17`、`:114-136` 判 **C4 = 不能**：只有 `Greatest_Threat` 入口累计，无每次扫描格数/候选数/早退分布/耗时，不足以判主犯；`card_00A8EC34.md:15-23`、`:233-265`（`不能说` 1/3/4/5、`:264-265` 一句话边界）同判。
- **字节复核**（`_w7_c_out.txt:191-230`）：`0x6F8DF3 8b1534eca800` → `0x6F8E04 42 inc edx` → `0x6F8E09 891534eca800` 写回；
  `DISP_HITS_0xA8EC34` = 2（1 R / 1 W）、`RAW_LE_DWORD_0xA8EC34_whole_file_count 2`；
  `JCC_CMP_TEST_CALL_between_0x6F8DF0_and_0x6F8E09 count=0`（入口到写回无条件）；
  `RET_in_[0x6F8DF0,0x6F9DB0) ['0x6f8e41','0x6f9b52','0x6f9b6b','0x6f9dac']` 全在写回之后，`0x6F8E41 c20c00 ret 0xc` 早退亦已计数；
  `CALLERS_0x6F8DF0 count=2 ['0x445f68','0x4d9942']`。
  这些正是两份共同援引的「入口累计 ≠ 工作量」（`Q4_REDLINE.md:116,120` ↔ `card_00A8EC34.md:98-109,217-245`）。
- **Hook 披露一致性**：`card_00A8EC34.md:170-197` 披露 `ra2render.dll` 9 字节 Inline Hook 节流到 1/8；`Q4_REDLINE.md:122,133` 把「Hook 节流」列入「未验/排除项」而非当作已测。本次核对源码行号（`_w7_c_out.txt:231-261`）：
  `ra2render/dllmain.cpp:27 DLL_PROCESS_ATTACH`、`:31 InstallVTableHooks()`；
  `blitter_hooks.cpp:1342` 原 9 字节注释、`:1363-1365` `interval > 1 && currentFrame > 0` 与 `throttledTargetScans++`、`:1394-1399` trampoline、`:1406-1408` `E9 <rel32>` 补丁、`:3782 InstallGreatestThreatHook()`；
  `ra2render.ini:22,25 TargetScanInterval=8`。**卡的行号引用对得上**（A2 项同源，此处只作跨文件一致性佐证）。
- **判**：无矛盾。Q4 未把卡标「未穷尽」的运行期写、`--allow-loader` 趟件状态写成已闭合。

### 对④ `card_00A8ED50.md` ↔ `Q2_ALPHA.md`（Bullet 的量纲归类）—— **相容**

- `Q2_ALPHA.md:32` 把 `y_3 = BulletCount (0x00A8ED50)` 归为 **瞬时水位 / 状态**（C3），`:199` 定义「水位型 = 某一采样瞬间的队列/容器长度，与窗口积分 `T_Ci` 不是同一泛函」，`:246-254` 判 `alpha_3 ∈ [0,+∞]` 平凡界且该行方程本身是误设。
- `card_00A8ED50.md` 未用「水位」二字（探针 §8：`PAT '水位' count=0`），但语义逐条等价：`:12`「已注册 Bullet 对象指针的**条目数**」、`:125`「**不每帧归零**…随开火/命中/移除**双向变化**」、`:191`「**双向变化的瞬时容器长度**」、`:211`「`实际更新数 ≤ … ≤ Count`」、`:222-223`「不能说的：本帧实际活跃更新数…动画/伤害结算次数、物理层耗时」、`:232` 重申瞬时容器长度。
  **术语差异不是量纲矛盾**：两份都把该字段放「瞬时状态/容器长度」一侧、都否认它是流量、工作量或耗时。`Q3_FRAME_EDGE_SPEC.md:185` 亦把 `S3/S4`（脏矩形、Bullet）并列为「两个**瞬时水位型**字段」，构成三方一致的第三种表述。
- **字节复核**（`_w7_c_out.txt:266-345`）：`0x55B93F a150eda800` 读 Count 作倒序边界；`0x55B954 8a8198000000 mov al,[ecx+0x98]` / `0x55B95A 84c0` / `0x55B95C 7405 je 0x55b963` 跳过 `0x55B960 ff525c`；`0x4666F7 8a8590000000` / `0x4666FF 0f84e9180000 je 0x467fee`（`0x467FEE..0x467FF5` 为 pop/ret 早退）——支撑 `Q2_ALPHA.md:248`「`L_3>0` 而 `T_C3→0` 是静态可见的可实现状态」与 `card_00A8ED50.md:12,158`；
  `0x4664AA 41 inc ecx`（+1）/ `0x46662D 49 dec ecx`（−1）、`DISP_HITS_0xA8ED50` 15 处（3 W / 12 R）与 `card_00A8ED50.md:56` 一致。
- `Q2_ALPHA.md:66` 援引 `card_00A8ED50.md:205,239,261,266` 佐证「无已校准映射/alpha 未校准/需补证」，本次 Read 核对这四行确为 §8.1 结论、不能说第 3 条、可采性表 alpha 行、需补证结论，**引用落点准确**。
- **判**：无矛盾。

### 对⑤ `Q3_FRAME_EDGE_SPEC.md` ↔ `Q2_ALPHA.md`（5 读口径与 alpha 不可解是否相容）—— **相容**

- `Q2_ALPHA.md:10,285,306` 结论「**不可解**」：不采帧内数据时 `alpha_i` 只有平凡界，四方程对 `T_Ci` 分解零约束。
  `Q3_FRAME_EDGE_SPEC.md` **从不声称解决 alpha**：`:44`「是否达成根因/成本分解 | **否**。alpha 未校准、充分性未证，只能报告关联与代理变化」；`:47,483` 强制每条记录带 `alpha_uncalibrated` 与 `sampling_sufficiency_unproven`；`:29,301-302,368` 反复声明「**名义操作数算账，不是耗时、CPU% 或扰动实测**」；`:478-483`「不是频率建议，不是充分性证明…不宣称根因或成本分解」。
  ⇒ Q3 是**读取规格/读数算账**，Q2 是**可辨识性判定**；两者作用域不同，Q3 显式把 Q2 的结论作为边界保留，无冲突。Q3:392 亦自述「`Q2_ALPHA.md`、`Q4_REDLINE.md` 仅作结论一致性核对（本次 `rg` 命中，未逐行全文复核）」，是诚实披露而非相反断言。
- **5 读口径外部锚点核对**（命令⑤）：`RULING_D21.md:5` 原文「采用 W4 的**每个触发沿新增 5 次跨进程读、20 B**，…复用该拍外层轮询值和其原始读前时间戳作为 **S0**」；`V6_V3_REVIEW.md:16-18`「**CONFIRMED** … 每沿新增读为 5 次（四 VA + f_post）」。与 `Q3_FRAME_EDGE_SPEC.md:157-162`（S0 复用、S1–S4 四 VA、S5 独立后读）、`:318-325`（合计 5 次/20 B，6 次/24 B 变体不采纳）一致，**且不是碰巧**：`:177-180,189-192` 逐条给了 S0 复用与 S5 括弧的理由。
- **算术本次重跑**（`_w7_c_out.txt:350-368`，与 `Q3_FRAME_EDGE_SPEC.md:434-454` 逐字相同）：
  四 VA 升序 `0x87E8E0, 0xA8EC34, 0xA8ED50, 0xB0CE88`；跨度 `2 680 232 B = 0x28E5A8`；
  间隔 `0x210354 / 0x11C / 0x34 / 0x7E104`；`payload 16 B`；基线 `508 calls/s, 2032 B/s`；
  七档 λ 与 B/s、调用/s 全部吻合（5.9952→119.90/29.98；6.0→120.00/30.00；19.8112→396.22/99.06；30.2016→604.03/151.01；30.8426→616.85/154.21；31.25→625.00/156.25；500→10000.00/2500.00）。
- **判**：无矛盾。Q3 未在任何处偷偷给百分比/耗时实测（B2 项关注的自我约束在此亦未被跨文件破坏）。

---

## 4. 唯一一处非实质措辞松散（记录在案，不翻转判定）

`Q4_REDLINE.md:143`：「读序、时间戳、跨帧/`df>1`、冻结、重置/回绕、`null`、附加读取与扰动验收**仍属未来规格要求**（`RULING_D19.md:58-60,68-70`；`TASK.md:73`）」。
同批 `Q3_FRAME_EDGE_SPEC.md:5,151-245,478-483` 已就其中前七项产出**待审设计卡**（§5 读序/时间戳、§6 跨帧与 null、§7 冻结/停止），只是明确「设计、非实现、未验收、须授权」。
`Q4_REDLINE.md:7,161` 也自述本次只亲读「四张字段规格卡」、未列 Q3/Q2。
⇒ 该句是对 D-19 执行要求的转述，**严格说略滞后于同批产出**，须理解为「尚未实现/验收/授权」而非「连设计卡都没有」。
它不改变 C2/C1/C4 任一判词、不改变 Q2/Q3 任一结论，故**不构成实质缺陷**；建议后续文书把该句改为「设计卡已产出但未实现、未验收」。

---

## 5. C2 项 · 「未验/未核实」标记 vs 诚实账 / 是否存在相反强断言

### 5.1 逐文件落点（探针 §7，`_w7_c_out.txt:380-638`；行号为探针输出内的 `M_L`/`LEDGER_HEADS`）

| 文件 | 含标记行数 | 诚实账标题行（本次 Read 与探针一致） | 标记是否真落在账里 |
|---|---:|---|---|
| `card_0087E8E0.md` | 39 | §13 诚实账 `L444`；`L450-452` 本次未验；`L413-417` 本次未运行/§11 末 | **是**（分类汇总，非逐条编号） |
| `card_00A8EC34.md` | 35 | §10 未验/诚实账 `L288`，`L290-300` 九项编号表；`L302-305` 已验/未验分栏；`L435-437` 未运行 | **是**（唯一有 1:1 编号表的文件） |
| `card_00B0CE88.md` | 29 | §10 合规与诚实账 `L238`，`L255-264` 八项编号；`L76-81` §3.3 不宣称穷尽 | **是** |
| `card_00A8ED50.md` | 35 | §10 合规与诚实账 `L270`，`L288-297` 八项编号；`L79-84` §3.3 | **是** |
| `Q2_ALPHA.md` | 18 | §7 诚实账 `L331`，`L339-345` 本次未跑/未独立复验；`L333-337` 本次已跑 | **是** |
| `Q3_FRAME_EDGE_SPEC.md` | 38 | §9 诚实账 `L373`，`L460-472` §9.3 本次未做；`L9,17,44-47` 边界声明 | **是** |
| `Q4_REDLINE.md` | 16 | §7 诚实账/本次未验 `L159`，`L163-164` 未运行的检查 / 未定位未验；`L7` 合规口径 | **是** |

核对方式：探针以正则 `未验|未核实|未独立复验|未复验|未穷尽|未闭合|未定位|未定名|未做|未重跑|未验证|未测|未量化|未证|未授|未获|未通过|未检查|采信|不宣称|不冒称|未运行|未启动|…` 逐行扫七份（§7 输出全部命中行），再逐条对照各文件诚实账的编号/汇总清单。
**结论**：所有类别的未验项都在诚实账中有对应条目（例如 `card_0087E8E0.md:143` 的 `0x42A690` 调用链、`L190-191` 的 CRT 初始化时机、`L208` 的首次回绕运行期、`L244` 的实际发生次数，分别落到 `L450-452` 的「间接调用与别名写 / CRT 初始化时机 / 重试·回绕实际触发频率 / 运行期真值」）；
但**并非逐条逐字 1:1 枚举**——四卡与 Q3/Q4 的诚实账是「按类别汇总」，只有 `card_00A8EC34.md:290-300` 是编号表。这是文体差异，不是漏账：本次未找到任何一项「正文标未验、诚实账却漏掉其类别」的情形。

### 5.2 是否存在「把未验写成已验」的强断言 —— **未发现**

- 探针 §7 的 `marker+strong_cooccur` 共 16 行，逐行 Read 复核后全属以下几类，**无一类构成相反断言**：
  引用他件时的引号内容（如 `card_0087E8E0.md:10` 引 `TASK.md` 的「已定谳/非实测」、`Q2_ALPHA.md:38` 引 D-19 的「不等于已校准」）、
  否定式清单（`card_00B0CE88.md:212`、`card_00A8ED50.md:241` 的「**不能**称『1 Hz 已完全充分』…」）、
  同一句内自带未验限定（`card_00A8EC34.md:314`「本次只穷尽 `E8/E9` rel32，**未验**」、`card_0087E8E0.md:374`「运行期有效性**未验**」）。
- 命令④ 的独立强断言正则扫描（`已验/已核实/已确认/已复验/已定位/已闭合/已穷尽/已校准/实测/通过/定谳` 等）逐文件 9/8/13/11/9/7/5 行，逐行核对后：
  - 「已定谳」全部指 `TASK.md:20-34` / D-19 的**既有裁决**（如 `card_0087E8E0.md:9,60`、`Q4_REDLINE.md:25`），不是本组新验；
  - 「独立二进制复验」（`card_00B0CE88.md:4,224`、`card_00A8ED50.md:4,255`）针对的是**字段静态语义**，其诚实账未验的是**写点全集/CRT 闭包/运行期有效性**（`card_00B0CE88.md:258-262`、`card_00A8ED50.md:290-295`）——作用域不同，不构成自相矛盾；本次 §3 的 `disp_hits` 27/15 处与卡的 6 W/3 W 数字一致，佐证该「复验」措辞有字节支撑；
  - `Q2_ALPHA.md:146`「由此本次独立确证」只覆盖其 §2.2 实跑的四段反汇编（`0x42A5F0/0x42CC70/0x55B93F/0x6F8DF0`），本次 §3 全部重跑相符；其诚实账 `L340` 未验的是「`0x00B0CE88` 初始化/插入/删除/合并与 `0x00A8ED50` RTTI/写点全集」，不冲突；
  - `Q3_FRAME_EDGE_SPEC.md:63` 的「源码自记**实测** 284–347 Hz」明确归属源码自记并同句写「未验证实际达到 500 Hz」，且 `L465-467` 记未重算/未复验；
  - `Q4_REDLINE.md:7,76,163` 三处自述「未重跑 PE / 不作为本撰写员独立二进制复验」，全文没有把底稿/卡的输出转记为自己的实跑。
- **⇒ 七份中未发现与诚实账相反的强断言，未发现把未验写成已验。**

---

## 6. 判定

| 检查项 | 判定 |
|---|---|
| 五对跨文件一致性（①–⑤） | **全部相容**，且关键字节经本次 `ra2tool.Engine` 真反汇编复核 |
| 5 读口径与 D-21 裁 A / V6 CONFIRMED 的外部一致性 | 相符（命令⑤） |
| C2 诚实账完整性 | 七份均有诚实账；标记按类别落账（仅 `card_00A8EC34.md` 为编号表） |
| C2 是否存在相反强断言 | **未发现** |
| SHA256 绑定 | 七份实测全与 `TASK.md:13-21` 一致，无 `OBJECT_CHANGED` |
| 实质缺陷（`substantiveDefect`） | **0**（`Q4_REDLINE.md:143` 措辞松散不改变任何结论） |

**C 组终判：CONFIRMED。**

---

## 7. 未验（诚实账）

1. **未验**：七份正文互相引用的**外部**文件行号（`Q1_C1_PATHFIND.md`、`Q1_C2_RENDER.md`、`Q1_C3C4_PHYS_TARGET.md`、`W3_COSTBOUND.md`、`PENDING_DECISIONS.md`、`GOAL_THREE_TARGETS_20261018.md`、`docs/re/*`、`A1_SAMPLER_CANDIDATE/*` 等）本次未逐份全文亲读；只核了本组七份之间的引用落点与 `D20_B_VISIBILITY_GAP.md`、`RULING_D21.md`、`V6_V3_REVIEW.md`、`EXECUTION_D21.md`、`RULING_D19.md`、`W4_FIELD_SPEC/TASK.md`（均在本次 Read 内）。
2. **未验**：七份自述的「本次实跑 PE 探针输出」是否与其声称的命令逐字一致——本次只**独立重跑**了与五对判定相关的字节段（`_w7_c.py` 所列），未重跑各卡 §11/§10 的 A1–A13、A1–A8、_probe_00A8ED50_a–g 全套探针，也未重跑 Q2 §2.3/§2.4 的两条 `rg`。**不把它们的自述输出转记为本次实跑。**
3. **未验**：`ra2render.dll` Hook 在具体真机趟件中是否在场、节流实际生效比例（七份均标未验；本次只核源码行号存在，零真机）。
4. **未验**：四个 VA 的运行期真值、字段有效性、扰动、实达 500 Hz、跨帧归属、读失败率、alpha 数值——七份均标未验/未校准，本次零真机，不补造。
5. **未验**：`Q3_FRAME_EDGE_SPEC.md` 的 λ 七档来源（`FACTBASE_D19.md:165-167`、`Q2_FRAME_EDGES.md:52`、`Q3_SAMPLE_PLAN.md:237`）本次只复算了 `1000/p50` 与 `20λ/5λ` 算术，未重算三窗 p50、未普查 87 窗/22 慢窗。
6. **未验**：`card_0087E8E0.md` 的 pefile `RSDS/NB10/.pdb` 全 0、`*.MAP` 非 linker map 的符号名依据（A1 项范围）；本次 C 组未重跑 pefile，只核了与五对判定相关的调用/立即数普查。
7. **未验**：`Q4_REDLINE.md:143` 措辞松散是否已由后续文书修订（不在本组只读范围内，不修改任何既有件）。

**合规**：零真机（未启动 `gamemd.exe`/`ra2loader`/`YURI.exe`，未读活进程内存）、零注入、未写任何 hook/RPM/dump/挂线程实现；
只读 `ra2youli/gamemd.exe` 做静态反汇编；唯一写域 `W7_W4_REVIEW/`（`_w7_c.py`、`_w7_c_out.txt`、`parts/C.md`）；未 commit、未 push。
