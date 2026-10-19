# House/Team AI 残差深潜（R-TEAM-AI）

> **目标二进制**：`ra2youli\gamemd.exe` 1.001（ImageBase `0x400000`，FileOffset = VA − `0x400000`）
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **证据分级**：`[实证]` = VA + 机器码（`out/re_work/re_sprint/R_team_ai/scan_phase*.txt` 本轮反汇编）；`[推演]` = 相邻实证 + x86/MSVC 习惯；`[待实测]` = 需真机。
> **边界**：本专章收口 **AI 更新循环 ABI、确定性残差、限频/跳帧安全点、RNG 次数禁区、ra2forge 产品建议**。
> 前作：`docs/re/house_team_ai_update.md`（调用树/热点/优化插入点 S6）；交叉：`trigger_determinism_deep_dive.md`（T8）、`rng_residual_u3_deep_dive.md`、`net_sync_checksum.md`。
> **工作区**：`out/re_work/re_sprint/R_team_ai/`（claims.txt / risk_table.md / FINDINGS.md / scan_phase*.txt）

---

## 0. 结论速览

1. **TeamDelayTimer 是整型逻辑帧定时器**（`House+0x5798` Start / `+0x57A0` Duration），比较 `CurrentFrame@0xA8ED84 − Start ≥ Duration`；重装 `Duration = Rules+0x115C[House+0x184]`。**无浮点**。ctor 装填 `Duration=1`。[实证]
2. **AITrigger 评估序 = `AITriggerTypeClass::Array` 下标升序**，无排序/哈希；权重 `==5000` 特权清候选表；轮盘 `RandomRanged(1,Σw)`。[实证]
3. **RNG 次数陷阱**：`0x6F0AB0` 入口**先**烧 `RandomRanged(1,100)`（R1）**再**查 `AITriggersActive(+0x1F2)`——「关 AI 标志省 RNG」不成立。[实证]
4. **生产/招募决策全是 ScenarioRandom**：三兄弟各 1–2 次 + BaseCons 1 次 + SW 1 次 + 建队 1 次；与 Trigger 动作 RNG **串行同流**。[实证]
5. **可落地限频**：保持 Timer 节拍；Team dtor 反向索引（保序）；局外 `Randomizer::Global` 可短路。**禁止**跳帧不烧 R1、招募轮转、改遍历序。[实证+推演]
6. **ra2forge**：维持 `IgnoreGlobalAITriggers=yes`；战役出兵走 Trigger CreateTeam，不走全局 AITrigger。

---

## 1. 更新循环 ABI

### 1.1 时钟

| 量 | 地址 | 语义 |
|---|---|---|
| `CurrentFrame` | `0xA8ED84` | 32 位有符号逻辑帧；`MainLogicFrame` 尾部唯一 `inc` |
| 读点 | `0x4F8A11` 等 | TeamDelay / Timer / 招募节拍统一读此值 |

轮询器（Trigger）与 House/Team AI 都在 `inc` **之前**读同一帧号 ⇒ 同帧相位一致。[实证]

### 1.2 TeamDelayTimer 门控

```
0x4F8A00  edx = House+0x5798 (Start)     ; -1 = 未装填
0x4F8A06  eax = House+0x57A0 (Duration)
0x4F8A11  ecx = CurrentFrame
0x4F8A19  cmp (CurrentFrame-Start), Duration ; jge → 触发
          否则 remaining = Duration - elapsed ; remaining==0 亦触发
0x4F8A6A  call 0x6F0AB0                  ; AITrigger 评估
0x4F8AD9  Start = CurrentFrame           ; 重装
0x4F8AEB  Duration = Rules+0x115C[House+0x184]   ; 按 House 类型查表
```

ctor/lateinit（`0x4F5CD5`）：`Start=CurrentFrame`，`Duration=1` ⇒ 开局几乎立刻评估。[实证]
`House+0x565C`（Probability 阈值）ctor 写 `0x64`（100）；全镜像 8 处引用（含触发器动作写点 `0x6DF366/0x6E3310`）。[实证；写者语义 [待实测]]

触发前置（`0x4F8A27–0x4F8A5D`）：`GameMode`、`Defeated/IsLoser (+0x1EC/+0x1ED)`、`HouseType+0x1A6` 任一置位则跳过整段（**不重装 Timer**）。[实证]

### 1.3 脚本步进

- 入口 `TeamClass::AI 0x6E9050`，**33 个调用点**（含自递归 `0x6E93F4/0x6E942A` 与脚本动作簇 `0x6ECxxx/0x6EExxx`）。[实证]
- 动作跳转表 `0x6E9F74`，**action 0..55**；action **49**（`0x6E9CE1/0x6E9CE8`）写 `AchievedGreatSuccess(+0x84)=1`。[实证]
- 招兵主动通道 `TeamClass::Recruit 0x6EAA90`，唯一 caller `0x6E9281`。[实证]
- `ProcessAllTaskforces 0x6F2040` 按 TeamType 序驱动；单队脚本步进在 `0x6E9050`。[实证]

### 1.4 与 Trigger 交叉

| 面 | 结论 |
|---|---|
| 结构 | **零交叉**：AITrigger 不进 Tag 向量、不挂 Tag；`RaiseEvent 0x6E53A0` 的 73 调用点无 AITrigger |
| RNG | **共享** `ScenarioClass::Random = [0xA8B230]+0x218` |
| 节拍 | Trigger 轮询每帧；AITrigger 由 TeamDelayTimer 秒级门控 |
| 建队 | Trigger 动作 `CreateTeam` 与 AITrigger 轮盘建队都进 `TeamClass`，后续脚本步进同一套 |

---

## 2. 确定性残差

### 2.1 AITrigger 评估序

```
0x6F0AF7  RandomRanged(1,100)                    ; ★R1 必烧
0x6F0B06  cmp eax, House+0x565C ; jg early-out
0x6F0B12  if (!AITriggersActive +0x1F2) return   ; R1 已消费！
0x6F0B20  扫 TeamArray 计 BaseDefense (Type+0xF6)
0x6F0C3E  for i in 0..AITriggerCount-1:           ; 下标升序
            ConditionMet 0x41E720
            w = ftol(Weight_Current +0xB8)
            if w==0x1388: 清空候选表             ; 特权
            else: 候选表.push(trigger, w)
0x6F0CEE  if Σw>=1: RandomRanged(1,Σw)           ; ★R2 条件烧
            轮盘前缀和选中 → Team1+0xDC / Team2+0xE0 CreateTeam
```

**禁改**：数组遍历序、特权 5000 短路语义、轮盘前缀和累加顺序、R1/R2 次数与参数。[实证]

### 2.2 TeamDelayTimer 残差

- 多端对齐依赖：同一 `CurrentFrame` + 同一 `Rules+0x115C` 表 + 同一 House 遍历序。[推演]
- 帧号/房序不一致 ⇒ 评估帧错位 ⇒ R1/R2 抽数次数错位 ⇒ **帧 CRC 当帧打出**。[实证]
- `House+0x565C` 若由触发器动作写入，该写入本身进 Trigger 契约面（T8 族）。[待实测]

### 2.3 生产决策 RNG

| 站点 | 函数 | 消费 | 备注 |
|---|---|---|---|
| `0x4FEE54` | 招募-战车 `0x4FEA60` | 1×`RandomRanged(0,0x7FFFFFFE)` | 浮点门 `Rules+0x13F4[HT]*k` |
| `0x4FF17E`/`0x4FF1E3` | 招募-步兵 `0x4FEEE0` | 2× | 同款门 |
| `0x4FF4AE`/`0x4FF513` | 招募-战机 `0x4FF210` | 2× | 同款门 |
| `0x4FE59E` | `AI_BaseConstructionUpdate` | 1× | 8 帧节拍 |
| `0x4FD922` | `AI_TryFireSW` 驱动 | 1×`RandomRanged(1,7)+0x69` | 返回值进决策 |
| `0x6F3254` | `CreateTeam` 路径 | 1×`Random()` → `[Team+0x3C8]` | 建队次数=抽数次数 |
| `0x6EE85C`/`0x6EFADC` | Team 脚本辅助 | 0–1× | 随动作触发 |
| `0x4F8908` | House Update | 1×（条件） | **同块另有 Global 流** `0x4F8888/0x4F889A`（SAFE） |

浮点门 `fild(rand)*C1 ? fild(Rules[HT])*C2` 用 `fcompp`——**x87 舍入**跨端需一致。[实证+待实测]

### 2.4 残差清单

| ID | 残差 | 状态 |
|---|---|---|
| U8 | TeamDelayTimer 多端对齐 | 门控 [实证]；跨端 [待实测] |
| U-AI-1 | `House+0x565C` 全部写者确定性 | 8 xref [实证]；触发器写路径 [待实测] |
| U-AI-2 | 招募浮点门舍入 | [待实测] |
| U-AI-3 | `0x6EE85C/0x6EFADC` 动作号映射 | [推演] |
| U-AI-4 | 第二直呼点 `0x4FA220` 门控条件 | 已见 `Defeated/IsLoser` 前置 [实证]；完整语义 [推演] |

---

## 3. 限频 / 跳帧安全点

### 3.1 可落地

| 点 | 做法 | 风险 | 约束 |
|---|---|---|---|
| **S1** | TeamDelayTimer 保持原节拍 | SAFE | 勿缩 Duration、勿改 Rules 表 |
| **S3** | Team dtor 权重回写反向索引 | SAFE | **必须按原 AITrigger 下标序**调 RegisterSuccess/Failure |
| **S6** | `Randomizer::Global` 站点短路 | SAFE | 仅局外（`0x4F8888/0x4F889A`、Theme 选曲等） |
| **S5** | 8 帧建筑回调 `0x6E53A0` 降频 | RISK | 多端同规则 `CurrentFrame%K`；不碰 RNG |

### 3.2 禁止

| 点 | 原因 |
|---|---|
| 跳过 `0x6F0AB0` 而不烧 R1 | 入口必烧 `RandomRanged(1,100)`；短接即少抽 |
| 「AITriggersActive=0 省 RNG」 | 标志检查在 R1 **之后** |
| 招募三兄弟跨类轮转 | 改同帧优先级 + 抽数次数（战车→步兵→战机固定） |
| 改 AITrigger/TeamType/Team 遍历序 | 轮盘边界与建队序变 |
| 缓存跨帧复用 ConditionMet | 同帧多 House 共享须逐端同结果；默认只允许「跳整帧且 RNG 照烧」 |

**跳帧安全形态（若必须做）**：
```
if (should_skip && ai_eval_dirty_or_cache) {
    // 照烧本应发生的 RNG，保持序列
    ScenarioRandom.RandomRanged(1, 100);           // R1
    if (would_have_candidates) ScenarioRandom.RandomRanged(1, sum); // R2
    return; // 不建队
}
```
`would_have_candidates` 必须与原逻辑同序同权重；否则宁可不跳。[推演]

---

## 4. RNG 次数禁区清单

完整表见 `out/re_work/re_sprint/R_team_ai/risk_table.md`。摘要：

| 级 | 站点 |
|---|---|
| **绝对禁区** | R1 `0x6F0B01`、R2 `0x6F0CEE`、R3–R5 招募、R6 `0x4FE59E`、R7 `0x4FD922`、R8 `0x6F3254`、R9 `0x6EE85C/0x6EFADC`、R10 `0x4F8908` |
| **可短路** | `Randomizer::Global` 全部站点 |
| **计数公式** | `ΔRNG = AITrigger(0..2) + Σ招募 + BaseCons + SW + CreateTeam×N + 脚本条件` |

与 T8/U-3 交叉：Trigger 侧 Meteor×4 / PlaySndRnd / ResetTimers / 帧 CRC 与本清单**同一 ScenarioRandom 流**——任一侧改次数，全流错位。

---

## 5. ra2forge 战役 AI 产品建议（只读）

| # | 建议 | 位置/依据 |
|---|---|---|
| P1 | **维持** `IgnoreGlobalAITriggers=yes` | `maplib.py:230`；消除 AITrigger 双 RNG，战役确定性最稳 |
| P2 | 战役出兵用 Trigger `CreateTeam`/`Reinforcement`，不写 `[AITriggerTypes]` | 与 P1 配套 |
| P3 | 若开 AITrigger：文档化 Probability（默认 100）与 TeamDelay（Rules 按房型） | `House+0x565C` / `Rules+0x115C` |
| P4 | TeamType `Max=1`/`Priority=7`/`Reinforce=yes` 可保留；多波次用 repeating Tag | `maplib.py:375-413` |
| P5 | Script 默认 `[(0,0)]` 无害；攻击波次写显式脚本行，避免 Action 49 误置成功 | 脚本步进/权重回写 |
| P6 | 联机图禁本地输入事件；AI 面禁单端短路/轮转 | T8 + 本专章 §3 |

---

## 6. 证据与产物

- claims：`out/re_work/re_sprint/R_team_ai/claims.txt`（30+ 锚）
- 风险表：`risk_table.md`（R1–R10 + S1–S6）
- 反汇编：`scan_phase2/3/4.txt`、`out/re_work/house_team_ai/*`
- 复算脚本：`verify_residual_anchors.py`

### 6.1 残差

| ID | 内容 | 状态 |
|---|---|---|
| U8 | TeamDelayTimer 跨端对齐 | [待实测] |
| U-AI-1 | `+0x565C` 写者 | [待实测] |
| U-AI-2 | 招募浮点门 | [待实测] |
| U-AI-3 | 脚本 RNG 动作映射 | [推演] |
| U-AI-4 | `0x4FA220` 完整门控 | [推演] |
