# W59 · DISAGREE.md（与既有签发事实 / 前卡产物的差异）

> 说明：本文件只登记**差异、更正与待裁定项**，不推翻本卡未复核的内容。
> 与既有结论一致的部分在 `ENDOFGAME_CHAIN.md` 里标 `[转引]`，不在此重复。

## D0 · 二进制身份：无异议（先行门槛）

卡片给定 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`；
本卡 `[本次实测]` `Get-FileHash` + 脚本内 `hashlib.sha256` 双算：

```
PATH  : D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe
SIZE  : 4,825,360
SHA256: 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
MATCH : YES
```

⇒ **未触发「立即停手」条件**，本卡正常执行。与 W29 `OVERRIDE_ORDER.md:5`、
W50 `step1_scan.stdout.txt:1-3` 的哈希一致，无差异。

---

## D1 · W50 `step1_scan` 的「0 命中」是扫描未覆盖，不是「没有引用」

- `W50_endofgame_chain\EVIDENCE\step1_scan.stdout.txt:11`：`linear disasm instructions: 155215 (last VA 0x0046f59d)`。
- 同文件 `:13-45`：`0x34AC`/`0x34B0`/`0x1CD9`/`0x35A0`/`0x34CC` 全部 `0 sites`，
  12 个 `0x5xxxxx`/`0x6xxxxx` 函数全部 `0` call xref。
- `[本次实测]`（`w59_static.stdout.txt:10-35,41-116`）：`text_insns.pkl` 覆盖
  VA `0x401000..0x7E0FFD`、1,394,120 行；`0x685670` 有 1 个调用点 `0x0055D14A`，
  `0x5CEEF0` 有 2 个，`0x5CF810` 有 2 个，`0x5CF830` 有 2 个……

⇒ **差异**：W50 的 step1 线性反汇编在 `0x46F59D` 因遇不可解码字节而停止（Capstone
`disasm` 迭代器行为），目标函数全在其后，故扫描必然 0 命中。
**不得**把这 12 行「0」引用为「引擎不调用这些函数」或「字段无读写点」。
本卡与 W50 的 step2/3/4（它们用的是 pkl 全量缓存）不冲突；step1 只是覆盖不足。

## D2 · 阶段段数字子项键上限：W34 的 `0..255` vs 本卡 `[本次实测]` 的 `1..100`

- `[转引]` `REVIEW\LEAD_VERDICT_map_start_root_cause.md:111`：
  「阶段段候选子项是数字键 **0..255**、值为阶段名」；同处「阵营段键 **1..100** 连续、首个缺口即停」。
- `[本次实测]`（`w59_static.stdout.txt:5842-5844`、`w59_detail3.stdout.txt:65-122`）：
  `MAPSELMD_loader(0x5CEEF0)` 内 `imm∈[8,0x400]` 的 `cmp` 全扫描**只有两条**：
  ```
  VA 0x005CF04F  83 ff 64  cmp edi, 0x64   ; 阵营段键循环  (FOFF 0x1CF04F)
  VA 0x005CF367  83 fd 64  cmp ebp, 0x64   ; 阶段段数字键循环 (FOFF 0x1CF367)
  ```
  两条循环的计数器都从 `1` 起（`0x005CEF98 mov edi,1` / `0x005CF2B1 mov ebp,1`），
  都在 `>100` 时 `jg` 退出，且都在「首个键缺失」时提前退出
  （`0x005CEFD4 sete bl` / `0x005CF2EB sete bl`）。

⇒ **差异**：阵营段 `1..100` 一致；**阶段段数字键本卡实测是 `1..100`，不是 `0..255`**。
可能 W34 说的是 `atoi`/键名字符串转换函数的取值范围，或另一处解析层。
本卡不裁定谁对，**建议 Lead 复核 W34 原始证据**；本卡 Q4 只按自己实测的字节写。
关联 `UNKNOWNS.md U5`（`0x528C00` 返回语义未完整反编译）。

## D3 · W39 部署文件用 `2=`（无 `1=`）—— 与「子项键从 1 连续」的静态解读冲突，但因果未定谳

- `[转引]` `W39_mapselmd_live2\out\MAPSELMD.INI.w39_deployed` 尾部（本卡只读 40 行）：
  ```
  [RA2F_ECH01_2004FB14]
  Scenario=ECH01.MAP
  ...
  2=RA2F_ECH02_1E0DEBE8          ← 只有 2=，没有 1=
  ```
- `[转引]` `REVIEW\LEAD_VERDICT_Q2_CLOSED.md:32,84-87`：`skip_yes` 臂仍弹同一对话框，
  Lead 归因于「当前阶段候选子项 `Scenario=` 与 `NextScenario` 不匹配」。

⇒ **本卡的静态解读**：按 D2 的循环字节，键从 `1` 起、首个缺口即停 ⇒ 只有 `2=` 会得到
**0 个候选子项**，这比「键值不匹配」更前置。但**这只是 `[静态推断]`，不是定谳**：
W39 的 `skip_no` 臂用**同一份** `2=` 文件成功推进到 A2（`Q2_CLOSED.md:30,48-56` `[转引]`），
说明 `2=` 至少不阻塞 `SkipMapSelect=no` 路径；且 `0x528C00` 返回值语义未完整反编译（U5/U7）。
⇒ 不写「W39/Lead 判错了」，只登记为一处**待真机单变量对照**的结构性疑点；
  Q6 因此**不**把「把 `2=` 改成 `1=`」列为已定谳的必修项。

## D4 · 对 `scen_stage_idx=8` 的处理：无异议，且**支持** Lead 的降级

`REVIEW\LEAD_VERDICT_Q2_CLOSED.md:57-60` `[转引]` 已把该值从 `[本次实测]` 降回 `[转引]`，
并指出 0-based 下下标可能差一格。本卡**不复活**「引擎选中第 8 阶段」的宣称；
本卡新增的只是 `[本次实测]` 的**写入点与全局归属**（Q3），与该降级完全兼容。

## D5 · `BATTLEMD` 合并表全局地址：`0xA83CF8`（W29） vs `0xA83CFC`（本卡实测）

- `[转引]` `W29_override_order\OVERRIDE_ORDER.md:22`：「合并到全局表 `0xA83CF8`」。
- `[本次实测]` `Start_Scenario(0x683AB0)` 里读的是
  `VA 0x00683AF0  a1 fc 3c a8 00  mov eax, dword ptr [0xa83cfc]`（FOFF 0x283AF0），
  随后 `mov ebp,[eax+edx*4]` 取 battle 条目。

⇒ 相差 4 字节，可能是「容器对象基址 vs 其数据指针」的记账差异，但本卡未证明。
登记为待核，见 `UNKNOWNS.md U9`。**不影响** Q2 结论（`[Battles]` 不决定下一关）。

## D6 · 对「`NextScenario` 写法不是成因」的**细化**（不是反对）

`W28_nextscenario_form\NEXTSCENARIO_FORM.md:15-16` `[转引]` 结论正确，本卡复核一致。
但 W28 的表述容易读成「`NextScenario` 与推进无关」。本卡 `[本次实测]` 补一层：
`[Scen+4]`(NextScenario) / `[Scen+0x108]`(AltNextScenario) 在
`0x00685A59`/`0x00685A4C` 被取作 `edx` 传给 `0x5ADE20` → `0x5ADF20`，
是 `skip_path_match` 遍历候选子项时的**匹配过滤器**（`0x5AE025..0x5AE098`）。
⇒ 精确口径应为：**写法（形式）不是成因；值必须在 `SkipMapSelect=yes` 路径里能与
子阶段 `Scenario=` 匹配；但它本身不构成链，链由 `MAPSELMD.INI` 阶段表提供。**

## D7 · Q5 的两种候选顺序，本卡给出**第三种**答案

问题给的二选一是「EndOfGame→推进下一关」或「推进下一关→EndOfGame」。
`[本次实测]` `0x006859C7  74 47  je 0x685a10`（`EndOfGame==0` 才进推进分支）、
`0x006859C9..0x00685A0F`（`EndOfGame!=0` 直接 `ret`）表明：
**两者都不是** —— 引擎每关结束都先走推进分支，`EndOfGame` 是**在分支入口被读取的终止闸**，
`yes` 时从控制流上根本到不了 `0x685C54` 的 `Start_Scenario`。`EndOfGame` 也不是
「推进之后写的结果」，而是地图加载时 `0x68A11F` 从 INI 预设的静态字段。

## D8 · `0x49F7A0` 不是「victory predicate 函数体」，而是 3 字节恒 1 桩

`W50_endofgame_chain\EVIDENCE\step4_helpers.py:29` 把它标为
`"0x49F7A0 victory predicate?"`（带 `?`，属试探）。
`[本次实测]`（`w59_detail.stdout.txt:854-860`）：
```
VA 0x0049F7A0  b0 01   mov al, 1
VA 0x0049F7A2  c3      ret
VA 0x0049F7A3  68 98 f5 81 00  push 0x81f598   ; 另一个函数（copy-protection 校验）
```
⇒ 三处调用点（`0x68599E`、`0x685C1C`、`0x55CFE1`）在本镜像**恒真**。
不否定 W50 的试探标注，但下游不得据此推断「引擎在此做了胜负判定」。
该桩是否被工具 patch 未定谳 → `UNKNOWNS.md U12`。

## D9 · 方法学差异：未使用 REA MCP

会话技能表的 `reverse-engineer-anything` 要求经其 MCP/CLI 分析原生二进制；
**该 MCP 工具未在本会话注册**，而其 `npx rea-agents setup` 会写入
`W59_endofgame_chain\` 之外的配置并破坏「纯离线只读 / 只写本卡目录」纪律。
⇒ 本卡按卡片指定路线（消费 W50 的 pkl + 自写离线 Python/Capstone）执行，
这是**对卡片纪律的遵守**，不是对 REA 技能的否定。据 `w59_static.stdout.txt:10-15`
该 pkl 已是全 `.text` 覆盖的指令表，足以支撑本卡的静态 xref 结论。

---

## 汇总

| 编号 | 性质 | 是否影响六问主结论 |
|---|---|---|
| D0 | 无异议（哈希一致） | 否（放行） |
| D1 | 前卡扫描覆盖不足的更正 | **是**：不得引用 step1 的 0 命中 |
| D2 | 数字键范围 `1..100` vs `0..255` | 影响 Q4 的上限写法；待 Lead 裁定 |
| D3 | `2=` 与「键从 1 连续」的疑点 | 影响 Q6 建议强度；因果未定谳 |
| D4 | 支持 Lead 降级 | 否 |
| D5 | 全局地址 ±4 | 否 |
| D6 | 细化（非反对） | 影响 Q2 的精确口径 |
| D7 | 给出第三种顺序答案 | 影响 Q5 |
| D8 | 桩函数标注细化 | 轻微（Q1 B 层） |
| D9 | 工具路线差异 | 否 |
