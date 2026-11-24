# LEAD_VERDICT · 「無法啟始選取地圖！」根因（W31 + W33 双卡独立互证）

> **状态更新（18:58）**：本文件是**静态**判定。其结论已于同日由真机三臂 A/B **验证成立** —— 见 `REVIEW\LEAD_VERDICT_Q2_CLOSED.md`（W39：追加 `MAPSELMD.INI` 后 `run_outcome=A2_loaded`；同环境负对照用官方 5,573 B 则 `error_dialog_GUI_OK`）。
> 本文件中的 `[待运行验证]` 项，凡涉及「登记后能否推进」的，均已转为 `[本次实测]`；其余（`skip_yes` 失败成因、末关终止、交互选图）仍未闭合。

> ## ⚠️ 更正块（21:12，据 W51 独立复核 `W51_chain_equivalence_check\CHAIN_EQUIVALENCE.md` 31,717 B）
>
> W51 逐条核对了 W31/W33 两卡与本文件的中间步骤，**发现本文件有 5 处实质问题**，以下为更正，
> 与本文件正文冲突时**以本更正块为准**：
>
> **① 我把两条不同的失败出口合并成了一条（最严重）。**
> 正文 §1 的判定链写成单一路径，实际应拆为两条：
> - `SkipMapSelect=no`：`0x005AE320` 打印 `Invalid stage!` → `0x005ADDB5` / `0x005ADDCF` 弹窗（`MapSel.CPP:0x86`）
> - `SkipMapSelect=yes`：`0x005ADFF3` **或**「候选子项不匹配时经 `0x005AE0CD..0x005AE0F1` **靠空串静默返回 AL=0**」→ `0x005ADEE0` / `0x005ADEFA` 弹窗（`MapSel.CPP:0x98`）
> 正文还**跳过了 Wrapper2 `0x005ADE20`**。
>
> **② 新发现（W51，我此前没有）**：`=yes` 路径在候选子项不匹配时**不打印 `Invalid stage!`**，而是静默 `AL=0` 后弹同一个标签。
> ⇒ 这解释了 W39 `skip_yes` 臂"仍弹同一个对话框但内部路径不同"的观测——**两条路径共用弹窗标签，但一条有 debug 串、一条没有**。
>
> **③「转大写」这个错，W31 也犯了，我此前只点名 W33。**
> 正文 §5 只写「W33 采信 W34 的小写更正」，漏了 **W31 犯的是完全相同的错**（`WHY_MAP_FAILS.md:129,141`）。
> 且 §5 保留了过时的 `[转引·待核]` 注记，应删除。
>
> **④ 正文 §1 主图仍保留旧错**：`遍历候选子项(0x005CF6B0)` —— 正确是 `0x005CF6B0` 按**阶段名**（`[stage+0]`）查找，`0x005CF760` 才是按 `Scenario=`（`[stage+4]`）反查（W34 已证）。
> 另正文 §2 未补入 W34 证实的加载器会读 `[Anims]`/`[GDISFX]`/`[NODSFX]` 段。
>
> **⑤ 笔误**：正文 §3.1 里 SHA-256 缩写 `…6919d52` 应为 `…691d52`；§8 未回填容器名 `LOCALMD.MIX`。
>
> ### 「两卡互证」的正确成立范围（W51 结论，我采纳）
> - ✅ **成立**：「问题不在 `NextScenario` 写法与 MIX 寻址，而在 `MAPSELMD.INI` 未登记我方地图、`SkipMapSelect=no` 经 `0x005CF760` 反查失败」这层**顶层排错归因**与**骨干地址**
> - ❌ **不成立**：① 「中间判定链等价」② 「公共底层函数（`0x7B5B30`）无共误」③ 「静态已证明真机触发哪条具体失败分支」
> ⇒ 我此前写「两卡独立互证」过强，应改为「**两卡在顶层归因上互证；中间链不等价，且存在同向共误**」。


> 签发人：Lead（本会话）｜ 日期：2026-11-13 18:05
> 依据：**两张卡、两条不同技术路线、结论相同**，且两卡的前提均经 Lead 独立复算。
> - **W33**（Gemini 4 Hydrogen `high`）：从 `NextScenario` **数据流**正推 → `W33_nextscenario_dataflow\NEXTSCENARIO_FLOW.md`
> - **W31**（Hy4 `work/cn:hy4free`）：从 `MSG:UnableMapSelect` **错误消息**反推 → `W31_map_start_failure\WHY_MAP_FAILS.md`

---

## 1. 结论

**C 线阻塞②的成因：战役推进必须先过 `MAPSELMD.INI` 的阶段登记表校验；我方地图未登记在其中，于是查表失败并弹出该消息。**
`NextScenario` 写法不是成因；MIX/散装寻址也不是成因。

两卡独立得出同一判定链：

```
结算屏点 GUI:Continue
  → 0x00685A38 读 [Scen+0x34B0] (SkipMapSelect) 分派
      ├─ SkipMapSelect=no  → 0x005ADD10 → 0x005AE100 → 0x005AE220 载入 MAPSELMD.INI
      │                       → 0x005CF760 用「当前地图名」[Scen+0x125C] 反查 stage
      └─ SkipMapSelect=yes → 0x005ADF20 载入 MAPSELMD.INI
                              → 0x005CF810 取当前 stage → 遍历候选子项(0x005CF6B0)
                              → 用子项 Scenario= 与 NextScenario 做（归一化后）比较
  两条路径都要求 MAPSELMD.INI 认识我方地图
  → 未命中 → 0x005AE320 打印 "MapSelect: Invalid stage!" → MapSelect::Init 返回 AL=0
  → 0x005ADD95..0x005ADDCF 弹 CSF 标签 MSG:UnableMapSelect
```

而 `[SOV1] Scenario=` 直接指向能进，是因为走 `Start_Scenario(0x00683AB0)` → `CCFileClass`（磁盘优先），**完全不经过 MapSelect**。

---

## 2. Lead 独立验证过的事实（不是转引）

| # | 事实 | 方法 |
|---|---|---|
| 1 | 我方 `ECH01.MAP`：`SkipMapSelect=no`、`EndOfGame=no`、`NextScenario=ECH02.MAP`、`Official=no` | 直接读 `[Basic]` |
| 2 | 官方 14 张 MD 图：**全部** `SkipMapSelect=no`（仅 `ALL07SMD`/`SOV07TMD` 的 `EndOfGame=yes`） | 逐字节提取 14 份 |
| 3 | `MAPSELMD.INI` 真实内容：`[GDI] 1=ALL01..7=ALL07` / `[Nod] 1=Sov01..7=Sov07` + 每阶段段的 `Scenario=` 与 `N=下一阶段` | 从 MIX 提取全文 |
| 4 | 官方 14 张图**逐一登记**在表中；我方 `ECH01.MAP`/`ECH02.MAP` **不在表内** | 全文比对 |
| 5 | 两处游戏目录（`ra2bench`/`ra2youli`）**都没有散装** `MAPSELMD.INI` | 文件系统 |
| 6 | `MAPSELMD.INI` 在 `ra2md.mix` 内，**文件偏移 `0x71D050`**、5,573 B、CRLF、SHA-256 `074ccccd…6919d52` | 哈希反查起点 |
| 7 | CSF 标签真值 `MSG:UnableMapSelect` = 「無法啟始選取地圖！」（**啟始**，非「啟動」） | 我自己遍历 5,211 标签 |

---

## 3. 证据强度必须如实标注（W31 自我限制，我采纳）

`[本次读码]` `[静态推断]` **静态判定链完整，但运行时分支未直接观测。**

W31 明确列出：`MapSelect::Init` 内有**四条**失败分支（`Invalid side!` / `Unable to initialize choices!` / `Invalid stage!` / `Unable to create font!`），静态证据下 **`Invalid stage!` 最可能，但没有运行时断点/日志证明 W27 那一帧（frame=210）实际走的就是这一条**。

`[待运行验证]` 尤其这一条必须写明：**frame=210 时 `[Scen+0x125C]` 的实际内容未观测**。若引擎在胜利后已先清空/改写该字段，失败点可能前移到空串检查（`0x7B4710`）。W31 是按 `0x00686700` 的写入语义推断其为 `ECH01.MAP`。

⇒ **不得写「已定位根因」的绝对化措辞**。正确表述：
> 已把失败点收窄到 `MapSelect::Init` 的 `MAPSELMD.INI` 阶段登记表分支，给出完整静态判定链；仍缺一次运行时观测来区分具体是哪条分支。

---

## 4. 修法方向（已派 W34，尚未真机验证）

**包里附带一份完整的 `MAPSELMD.INI`（官方全部阶段 + 我方追加阶段），安装时散装投放。**

依据：
- `[签发]` 散装文件优先于 MIX 内同名条目（W29 字节级自证：`Get_File` 磁盘命中即跳过 MIX）
- `[本次实测]` 现文件在 `ra2md.mix` 内 ⇒ 必须**克隆后再追加**；生成「只含我方条目」的最小文件会让官方 14 关全挂（与 CSF 同构的"完整合法文件"硬前提）
- `[未定谳]` 我方该注册到哪个阵营段（`[GDI]`/`[Nod]`，YR 可能还有第三阵营）、阶段序号如何接续
- `[已定谳·本次实测]` `0xFBE0D09D = ts_crc_hash("LOCALMD.MIX")`（Westwood 填充规则：追加长度余数字节 + 重复末组首字节）。**我此前用简单零填充"证伪"过这条，是错的，已撤回** —— 见 `REVIEW\LEAD_VERIFY_W34.md` §3。`MAPSELMD.INI` 自身 id 是普通 `crc32=0x922B8CE7`、5,573 B。

---

## 5. 两卡的分歧点（我裁定）

| 项 | W33 | W34（更正） | 我的裁定 |
|---|---|---|---|
| 比较前归一化方向 | 转**大写** | 转**小写**（`0x7B5B30` 调 `0x7CAFF4` +0x20） | 采信 W34（**小写**）；"大小写不敏感"结论两卡一致，不受影响 |
| `0x005CF6B0` / `0x005CF760` | 未明确区分 | `0x005CF6B0` 按**阶段名**(stage+0)、`0x005CF760` 按 `Scenario=`(stage+4) | 采信 W34，待 W34 交完整指令字节 |
| 阵营段/阶段段键语义 | 部分未定 | 阵营段键 1..100 连续、首个缺口即停；阶段段候选子项是数字键 0..255、**值为阶段名** | 采信 W34，同上 |

`[纪律]` 上述三项在 W34 交付前标 `[转引·待核]`，不得单独外传。

---

## 6. 与其它卡的交叉

- **W28**：`NextScenario` **形式**与官方相同 ⇒ 不是成因。与本判定**不冲突**，互补。
- **W29**：散装优先 MIX；CSF 必须完整合法。**支持**本修法。
- **W32**（同期）：菜单徽章生成，属**另一条正交阻塞**（Q1：条目进不了 UI）。
- **W27**：D2 直接指向能进 / D3 链式失败的非对称，本判定可完整解释。

---

## 7. 交付物索引

- `W31_map_start_failure\WHY_MAP_FAILS.md`（18,420 B）+ `DISAGREE.md`（6 项）+ `UNKNOWNS.md` + 12 份 EVIDENCE（全部 exit 0，另含 `CORRECTION_s09.md`）
- `W33_nextscenario_dataflow\NEXTSCENARIO_FLOW.md`（19,779 B）+ `DISAGREE.md` + `UNKNOWNS.md` + 20 份 EVIDENCE
- 本文件 + `REVIEW\LEAD_W33_VERIFY.md` + `REVIEW\LEAD_FACT_map_error_label.md`

---

## 8. W31 收尾补入的事实（其自身消息，`[转引]` 未逐条复算）

`[转引]` `MAPSELMD.INI` 的容器路径已被 W31 展开到索引级：
`ra2md.mix` 顶层 **`entry[14] id=0xFBE0D09D`** 是一个**嵌套加密头 MIX**，展开 **187 条索引**后，其中 **`[20] id=0x922B8CE7 size=5573`** 即 `MAPSELMD.INI`。
`[本次实测]` 与我的独立结论不矛盾：我算出的内容起点 `0x71D050` 落在这个嵌套容器覆盖区间内（我按 0xFBE0D09D 的 off=6,237,216 / size=4,819,480 核对）。

`[转引]` W31 精确化了 xref 面：
- `MSG:UnableMapSelect` 串在 `.data` **FOFF `0x42C108` / VA `0x82C108`**，全文件**仅 2 个 xref**：`0x5ADDB5`、`0x5ADEE0`（均 `mov ecx,0x82c108`），分属 `MapSel.CPP` 的两个 wrapper `0x5ADD10` / `0x5ADE20`
- 这两个 wrapper 的 `rel32` 直接调用点**仅 3 处**：`0x685A52`、`0x685A5C`、`0x685A74`（`Scenario.CPP` 状态机）
- `[Scen+0x34B0]` 的读侧证据：`0x68A200 push 0x83e0e0` → `0x68A211 mov [esi+0x34b0],al`
- vtable `0x7E16B0`：`+0x04=0x401940`、`+0x14=0x473C50`、`+0x1C=0x473D10`

`[转引]` **W31 主动记录了一次自我推翻**：其 `s09` 曾误判「`MAPSELMD.INI` 缺失」（因只扫顶层 id），后被 `s10`/`s11` 推翻并留 `CORRECTION_s09.md`。
`[本次实测]` 我当时也独立判过这个「假冲突」（见 `REVIEW\LEAD_W33_VERIFY.md` §3.2）——两处结论一致：**顶层扫不到 ≠ 容器内没有**。

`[纪律]` 上面这些都还是**静态链**。W31 与我的口径一致：**未写「已定位根因」**，只写「已收窄到 `MapSelect::Init` 的 `MAPSELMD.INI` 阶段登记表分支，仍缺运行时证据」。

> ### ⑥ Lead 亲自验证 W51 的新发现（21:15，`[本次实测]`）
>
> 反汇编 `0x005AE0C0..0x005AE0F8`：
> ```
> 005AE0CD  8b cf                mov  ecx, edi
> 005AE0CF  e8 1c 15 02 00       call 0x5cf5f0
> 005AE0D4  8b 54 24 1c          mov  edx, [esp+0x1c]
> 005AE0DD  8d ba 5c 12 00 00    lea  edi, [edx+0x125c]     ; [Scen+0x125C] 文件名缓冲
> 005AE0E3  f2 ae                repne scasb al, es:[edi]   ; strlen
> 005AE0E5  f7 d1                not  ecx
> 005AE0E7  49                   dec  ecx
> 005AE0E9  3b c1                cmp  eax, ecx
> 005AE0EC  1b c0                sbb  eax, eax
> 005AE0EF  f7 d8                neg  eax
> 005AE0F5  c2 08 00             ret  8                     ; 直接返回，无打印
> ```
> ⇒ **确认：候选不匹配时走这里，静默返回布尔，不打印 `Invalid stage!`。**
>
> 并核 `0x005ADEE0`（`MapSel.CPP:0x98` 弹窗点）：
> ```
> 005ADEE0  b9 08 c1 82 00       mov  ecx, 0x82c108    ; = MSG:UnableMapSelect 串 VA
> 005ADEE6  68 98 00 00 00       push 0x98             ; 源行号 152
> 005ADEEB  68 1c c1 82 00       push 0x82c11c         ; = "D:\ra2mdpost\MapSel.CPP"
> 005ADEF0  e8 6b 6f 18 00       call 0x734e60
> 005ADEFA  e8 91 55 02 00       call 0x5d3490         ; 弹窗
> ```
> ⇒ 与 W51 所述结构一致。
