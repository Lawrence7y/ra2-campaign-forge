# S13-K9 · 裁定「11 行 exact 绑定」是否真的存在（审计 vs 执行员的硬矛盾）

## MODEL（派卡登记，Lead r14-s7 写入）
role=exec | provider=magpie-anthropic | model=work/cn:hy4flash-free | reasoning_effort=high | agent=agent-3 | dispatched_at=2026-11-18T12:45 | status=running
note=新派；只裁定 11+3 个入口

## 背景（盘上事实，**不要重新普查**）
- `a-S13-K6`（`S13_K6\_audit\VERDICT.md`，09:56）判 S13-K6 交的 45 行里**只有 11 行是 exact 绑定**：
  `0040B880` `0040B930` `0040F7C0` `0040FD90` `0040FE40` `0046B7E0` `0046B890` `0062B250` `0062B300` `0065C0D0` `0065C180`
  判据原文：**`mov ecx,<global>; mov edx,[global]; call [edx+slot]`**，且该全局对象 vptr 的写入须有实证（例：`mov dword[0x89C668],0x7E17CC` @ `0x43856D`）。
- `S13_K7`（12:09 派、12:29 随会话被中断）自扫结果**相反**：`EVIDENCE\exact_callsites.tsv` 只有表头（0 数据行），
  `EVIDENCE\core_numbers.json` 记 `exact11_entries_with_hit=0`、`exact_call_sites_total=0`，四环表**全是「待」**。

⇒ **两者必有一错。本卡只做一件事：判定这 11（含 3 条漏扫共 14）个入口到底有没有 exact 绑定，并把结论钉死。**

## 本卡唯一任务
对 14 个入口 `0040B880 0040B930 0040F7C0 0040FD90 0040FE40 0046B7E0 0046B890 0062B250 0062B300 0065C0D0 0065C180`（11 行）
+ `0048AD60`(slot6) `0054E8E0`(slot6) `0048AD70`(slot1)（3 条漏扫）逐个判四环：

1. **① 入口**：16 B 对齐 + 首字节非 `E8/E9/EB` + 前驱非 fall-through + 合法序言或叶函数形态；**若来源是 vftable 槽值，则槽值即函数**，不得再用「像不像函数」二次筛。
2. **② 类归属**：`[vt-4]=COL → [COL+0xC]=TD → 名在 TD+8 内联串`；读不到 **fail-closed 停下，不许猜**。
3. **③ exact 调用 + vptr 写实证**：见下「两条通道」。
4. **④ 语义合同**：slot6 合同 = `mov eax,[ecx+4]; mov ecx,[esp+4]; mov eax,[eax+ecx*4]; ret 4`（= `GetItem(int)`）；
   其余槽按体内字节合同 + 调用点传参互斥定名（查不到就**不命名**，只报合同）。

## 两条通道（必须互不依赖，并各自提供对方给不出的信息）
- **通道 A**：capstone 指令边界上的真 `call [reg+disp]` 扫描（`skipdata=True`），回溯 `reg` 是否由 `[global]` 载入、`ecx` 是否来自同一/相关 global；
  给出每个命中的 `(call_site, global, slot, owner)`。**分母必须是「指令边界上的真 call」**（不得用 .text 原始 `E8` 字节数——本项目实测 81,715 vs 真 call 68,253）。
- **通道 B**：**不依赖 atlas 的 entry+size**。例如：直接按 PE 节扫字节模式；或用 vftable 槽值 + 构造器 `push <size>` 双点闭合反查调用方；
  或按全局对象地址反查 `mov dword[global], <vt>` 写点再回溯谁在这条链上真调了该槽。
- **两条通道必须能互相证伪**：若 A 说「有 exact」而 B 找不到该全局，必须解释为什么，不许只报 A。

## 强制自证（审计会照这几条打回）
- **检出力基线（本卡成败关键）**：从全 `.text`/atlas 随机抽 11 个入口，用同一判据跑一遍，给出误命中数。
  `a-S13-K6` 就是栽在这：slot-baseline 判据只落在 5–6 个调用点，而全 .text 有 6,313 处同类虚派发 ⇒ **任意 45 个函数都会过，检出力 = 0**。
  ⇒ **凡「某 slot 在已证 owner 里存在」类判据一律禁用。**
- **⑰ 同源不算两条证据**：「体内形态」+「调用点模式」同属通道 A，只计一环。
- **⑭ 环④ 必须真被调用**：数一遍 direct call 目标（`S10-K13` 的幽灵被调就是漏了这一步）。
- **⑮ 环① 不得编造**：引用的地址必须在体内真出现。
- **升级硬规矩**：升 `[已证]` 必须 ①字节级证据（可独立复算）或 ②独立审计复算；「复用别人结论」「只有探针脚本」「只有恒 0 读数」都不够。
- **⑱ 命名冲突按 entry 地址查全库**（`docs\re\` + `re_atlas\kb\` + 台账 + `COVERAGE\`），不只查新名。

## 禁止
- 不许 `import` 或复制 `S13_K6\_audit\` 或 `S13_K7\work\` 下的代码（**可读其结论做对照**，复算必须自己写）。
- 不许改分母、不许改归属（D-37 未裁）、不许碰 `S13_K8` 正在处理的 164 行残行、不许碰 `S13_K2`/`S13_K5` 已并的 14 行。
- **不许创建 venv、不许 pip install**（系统 python 已有 capstone 5.0.7 / pefile）。

## 交付（绝对路径，只写这里）
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\`
`PROGRESS.md`（≤60 行：14 行四环表 + 给审计的 1–3 个核心数字）/ `UNKNOWNS.md` / `DISAGREE.md` / `EVIDENCE\` / `work\`
`coverage_delta.tsv`：8 列 `entry, subsystem(S13), name, one_line_semantics, grade, evidence_path, name_kind, 缺环说明`
**每完成 2–3 个入口就增量落盘 PROGRESS.md。**

## 核心数字（给审计员复算）
① exact 命中数（**按 call 站点 / 按入口** 两口径）② 随机 11 个入口的基线误命中数 ③ 11 行中四环齐全的行数
④ 与 `a-S13-K6` 的 11 行**逐行**是否一致（一致/不一致各几行，不一致的给地址与理由）
