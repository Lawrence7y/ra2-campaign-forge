# R-051 · **推翻 R-050/H-038**：TriggerClass 有专用注册表 `DynamicVectorClass<TriggerClass*>` @`0xA8EAE8`（ctor 向**三个**容器注册）

门禁 `tools/r051_trigger_three_registries.py`：**8/8 字节断言 PASS**（S1 结构性不入分母）；
变异 `tools/mutate_r051_gate.py`：**12/12 killed（精确集合；pre-run 现值断言前置）**。

## 1. ⚠ 推翻横幅（章程 §7）

- **被推翻的结论**：R-050 证据 §2 与 H-038 断言「TriggerClass 实例**不是**存在专用 trigger
  向量里 / 不存在专用 trigger 向量」。
- **推翻者**：R-051（本轮）。**方向相反**：存在专用向量
  `DynamicVectorClass<TriggerClass*>` @**`0xA8EAE8`**（vptr `0x7E9BE4`，降级
  `VectorClass<TriggerClass*>` @`0x7E9C04`）。
- **根因**：R-050 只从**一条**注册腿（`0xB0F670`）反推结论，把「这家容器装的是
  AbstractClass*」外推成「没有专用容器」。实际 ctor 注册**三条腿**，R-050 漏了两条。
  这与 G-62、「样本当总体」（[[gate-assert-values-not-existence]] 变种 F）同族：
  **一条链 ≠ 唯一的路**；也是「穷举未做到底就当定谳」的复发。
- **受影响条目（逐条列）**：

| 条目 | 旧（R-050） | 新（R-051） |
|:--|:--|:--|
| `evidence/r050_trigger_registry.md` §1 结论 | 「容器 = AbstractClass* 共享表，非专用」 | **不完整**：另有专用表 `0xA8EAE8`（勘误指针已挂） |
| `evidence/r050_trigger_registry.md` §2 | 「专用 trigger 链另有其头 `[owner+0xAC]`」 | 头仍在，但**专用注册表确实存在** |
| `kb/21` L-30 行 R-050 段 | 「引擎级共享注册表，非 `<TriggerClass*>`」 | 需补第三条腿（已改） |
| `STATUS` R-050 段 / 面板行 | 同上 | 已加 R-051 推翻注 |
| `HANDOFF` **H-038** | 「遍历全部 trigger 的静态入口 = 该向量筛 WhatAmI==0x26」 | **升级**：直接遍历 `0xA8EAE8` 即可，无需 WhatAmI 过滤（H-039 取代） |
| 契约 `class_contract.json` `instance_registry` | 单表 | 改为三表（已改） |
| `INDEX` C.16n | 单表结论 | 挂推翻指针 |

## 2. 新结论（全部字节级）

**TriggerClass ctor `0x725FA0..0x726131`（`ret 4`）向三个容器注册同一个 this**（X1/X2/X7）：

| 腿 | 地址 | 全局 | 容器类型（RTTI 定谳） | 引用量级 |
|:--|:--|:--|:--|--:|
| block1 | `0x725FE9` | `0xB0F670` | `DynamicVector<AbstractClass*>`（vptr `0x7E91EC`） | 116 站 |
| block2 | `0x72603A` | `0xB0F708` | `DynamicVector<AbstractClass*>`（**同** vptr `0x7E91EC`） | 12 站 |
| block3 | `0x72608D` | **`0xA8EAE8`** | **`DynamicVector<TriggerClass*>`**（vptr `0x7E9BE4`） | **8 站** |

三块结构逐字节同构：容量/计数/grow 旗标三查 → `b9 <global>` → `ff 52 08`（容器虚槽 2=Add）
→ count 自增回写 → `8b 0d <data>` + `89 34 81`（SIB 原始指针存 `esi`）。三容器全局布局一致：
`vptr[+0] data[+4] capacity[+8] grow[+0xC] flag[+0xD] count[+0x10]`。

- **X3 阳性控制**：ctor 全跨度内 `89 34 81` 恰 **3** 处 = `{0x726037, 0x72608A, 0x7260DD}`
  ⇒「恰三次注册」是可数断言，不是散文。
- **X5**：三容器的 vptr 安装/降级 pattern 全 `.text` 各**唯一**
  （`0xB0F670`: `0x72536D`/`0x725398`；`0xB0F708`: `0x72546D`/`0x725498`；
  `0xA8EAE8`: `0x4E65FD`/`0x4E6628`）⇒ 容器类型无第三方改写者。
- **X6**：dtor `0x726950` = vtable `0x7F5858` **slot8**，先退化四 vptr（写回
  `0x7F5858/0x7F583C/0x7F5834/0x7F582C`）+ `call 0x7258D0`，再**三路对称注销**
  （`A8EAE8`@`0x726976` / `B0F670`@`0x7269BF` / `B0F708`@`0x726A08`），每路
  Find(slot16) → count-- → SIB 压缩下移，三段逐字节同构。
- **X7**：ctor **body**（止于 epilogue 前 `0x72612A`）写 `esi` 的指令集 == `{0x725FA2}`
  （头部 `mov esi,ecx`）⇒ 三容器入册的是**同一个 this**
  （`0x72612E` 的 `pop esi` 是 epilogue 恢复，不计赋值）。
- **X8**：引用量纲明确分化（116 / 12 / 8）⇒ 专用表才是 trigger 遍历入口。

## 3. 对 GOAL-3T 的净收益（H-039 取代 H-038）

**遍历全部 TriggerClass 实例 = 直接遍历 `0xA8EAE8`**（读 `[+4]` data / `[+0x10]` count /
`[+8]` capacity），**不再需要** WhatAmI==0x26 过滤——表名与元素类型自洽（S1）。
比 H-038 的方案少一次逐元素虚调用，且不会被 AbstractClass 注册表里的非 trigger 对象干扰。

## 4. 诚实账

1. **R-050 的教训是「一条腿推总体」**：R-050 的 7/7 + 12/12 全绿并不假——它测的东西都真，
   但它把「本条腿的容器类型」外推成「没有专用容器」。**N/N PASS 只覆盖被测命题**；
   这是 [[gate-assert-values-not-existence]] 变种 F（样本当总体）在**结构发现**层的复现。
   本轮补的 X3（恰三处尾存）+ X8（三表引用量纲）就是防这类外推的可数控制。
2. **两处 FAIL 都是我的判据写错，不是事实错**：X6 头部窗长 0x18 装不下 0x1E 字节
   （改 0x1E）；X7 首版把 epilogue 的 `pop esi` 计入「写 esi」⇒ 命中集多出 `0x72612E`
   （改为只测 body，并把排除理由写进断言文案）。两处都是「先跑红、查清、再改判据」。
3. **M9 预期值实测后修正**：首稿预期 `{X1,X7}`，实测只 `{X1}`——X7 断言的是 esi 写入
   地址集合，把后一条 `call` 改成 `nop` 不移动也不新增该 `mov`，X7 本不该红。
   **改预期不改断言**（断言是对的），并在注释里留下这次修正。
4. 变异 M3 的偏移首稿算错（`0x72606B`），被 pre-run 现值前置当场拒（G-67 第三役）。

## 5. 复跑入口

```text
python re_atlas/tools/r051_trigger_three_registries.py   # 期望 8/8 + S1, exit 0
python re_atlas/tools/mutate_r051_gate.py                 # 期望 pre-run OK + 12/12, exit 0
```

## 6. 异族盲验（R-052 轮补做，**通过**）

两路 GLM 子代理（`new-provider-2/glm-5.3-flash$max`，与本线 DeepSeek 异族；工作流
`dwfrun-1af687ad`，前置 `dwfrun-56dd81cd`）在**不看**本证据件的前提下，按逐字固定规格
（PE 节元组顺序断言 → fileoff 必经节表 → 线性解码至首 ret → `ff5208`+`b9` 配对 →
`893481` 清单 → `c705` 安装点 + RTTI 链解名 → le32 find 计数）独立复算，八标签**逐值相等**
且三路可见性自检 3/3：

| 标签 | 两路一致值 | 与 R-051 门禁值 |
|:--|:--|:--|
| `BODY_RET` | `0x726130` | 一致（`ret 4` 位于 0x726130） |
| `LEG_SITES` | `0x72601B, 0x72606E, 0x7260C1` | 一致（三条 Add 槽站点） |
| `GLOBALS` | `0xB0F670, 0xB0F708, 0xA8EAE8` | 一致（三表） |
| `LEG_GLOBALS` | 1→B0F670 / 2→B0F708 / 3→A8EAE8 | 一致 |
| `TAIL_STORES` | `0x726037, 0x72608A, 0x7260DD` | 一致（恰 3 处） |
| `REF_COUNTS` | `116 / 12 / 8` | 一致（X8 量纲） |
| `INSTALL_NAMES` | 专用表 vptr `0x7E9BE4` = `DynamicVectorClass@PAVTriggerClass` | **一致（X4 命题本体）** |
| `SELFTEST` | `PASS/PASS/PASS` ×2 | — |

⇒ **R-051 的三注册表结论通过异族盲验**（章程 §5 对「推翻自研结论」的核验要求已满足）。
**首跑判据假红（G-70）**：`dwfrun-56dd81cd` 汇总判「未命中」，但两路原始八行已完全正确——
判据用子串 `PAVTriggerClass` 计数，而每张动态表 RTTI 链出**两行**（动态态 + 降级态），
专用表天然贡献 2 而非 1。改判据为「数 `DynamicVectorClass@PAVTriggerClass` 行=恰 1」后
`dwfrun-1af687ad` 判定通过（子代理提示词字节未变 ⇒ 缓存回放，零 token 重打分）。
**未覆盖**：X6（dtor 三路对称注销）与 X7（esi 保全）未纳入盲验范围——本轮只裁「三注册表」
命题本体；未做动态验证。
