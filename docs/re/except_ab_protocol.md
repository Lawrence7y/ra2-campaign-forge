# except A/B 真机对照协议（ZC-EXCEPT-AB）

> [META]
> 任务=except 注入相关性 A/B 真机协议 · 起草方=MiMo（M 轨）· 日期 2026-09-30
> 上游定谳：`docs/re/except_zc11_forensics.md`（崩溃在 `__sbh_alloc_block @ 0x007CFB13`，EIP `0x007CFC9F`，毒值 `EDX=FE00FFFF`）
> 机制背景：`docs/re/h1_fanout_mechanism.md`（进图指纹 / 误选签名 / 国家对耦合）
> 执行方：**ZCode（唯一真机执行方）** · 本文只写协议，不跑局
> 写作用域（执行时）：`out/re_work/zcode_live/except_ab/**` + `ra2bench` 内 ini 注入开关（须还原）
> 证据等级：`[实证]` / `[推演]` / `[待实测]`（禁止伪造）

---

## 0. 目的与假设

**目的**：把「崩溃在原版 CRT，与 ra2render **执行层**无关」与「**注入态才复现**」这两件事拆开收口。前者已有定谳；后者**未证伪**（forensics §[4] 环境层判定 = 不能排除）。

| 代号 | 假设 | 含义 | 若成立则 |
|---|---|---|---|
| **H0** | 注入**无关** | 原版 `gamemd.exe` 单独跑同场景也会以相近概率崩在同一 EIP | 根因在原版 SBH 生命周期（R1–R3），注入不是触发器；harness 可把 `except.txt` 当**通用**门禁，不单绑注入态 |
| **H1** | 注入**环境相关** | 注入 OFF 复现率显著更低 / 为 0，注入 ON 更高；或仅 ON 出现 | 升级排查 R4（LFH 堆布局）/ R5（钩子数据层），按钩子热路径二分 |

> 一句话背景（[实证]）：ZC-11 段 D U0200 对局 @2026-09-29 22:38:24 生成 `except.txt`，EIP `0x007CFC9F` = 原版 `.text` 内 `__sbh_alloc_block` 解引用毒指针 `FE00FFFF`；调用链全在 CRT，**无** `ra2render` / 跳板页返回点。但该局是**注入态**，缺 OFF 对照。

**本协议不回答**「根因是哪个对象 UAF」——那是 R 轨 SBH 深入的事。本协议只回答：**崩溃出现率与 EIP 是否随注入开关变化**。

---

## 1. 对照设计

### 1.1 固定项（两臂必须完全一致）

| 项 | 值 | 依据 |
|---|---|---|
| 游戏目录 | `ra2bench`（`--game-dir ra2bench`） | ZC-11 已分离基准环境 |
| 场景 | **U0200_H1**（`[2]0LoadBench_U0200_H1.yrm`） | 原崩溃窗在 segD U0200 |
| **国家对** | **Americans（P1）vs Russians（P2）**，全程锁定 | H1 机制已证 units_seen 由国家对主导；固定对去掉该混杂 |
| 对局时长 | 每局 ≥3 分钟有效对局，或直至一方主基地摧毁 / ESC 终局 | 覆盖对象 churn 累积 |
| 开局兵力 | 保持 `ra2md.ini [Skirmish]` 现状（`UnitCount=10`, `Credits=10000`），**两臂同一份** | 不引入额外变量；对照的是注入，不是兵力 |
| 机位/操作 | 固定走位脚本或人工近似剧本；禁止一臂手玩另一臂 AFK | 降低 churn 差异 |
| 分辨率/窗口 | 同 ZC-11（800×600 逻辑） | — |

### 1.2 自变量（唯一被操纵的）

| 臂 | 注入 | 启动 | 配置 |
|---|---|---|---|
| **A · OFF** | **无** ra2render | **直接**启动 `ra2bench\gamemd.exe`（不经 `ra2loader`） | 不读 `ra2render.ini`；`ra2render.dll` 不加载 |
| **B · ON** | 有 | `ra2bench\ra2loader.exe`（挂起启动并注入） | 部署态 ini（现网 `EnableLFH=1` 等） |
| **C · ON+LFH0**（加测臂，隔离 R4） | 有 | 同 B | **仅**把 `[System] EnableLFH=1→0`，其余不动；改前/改后副本 + sha256；**收尾必须还原** |

> 臂 C 为 forensics §[8] V3 要求；时间不够可降为「A/B 先行，C 见缝插针」，但**不得**用 B 冒充 C。

### 1.3 注入开关如何落地（执行细则）

- **OFF 判定（必须自证）**：进程列表无 `ra2render.dll` 加载；`ra2render.log` **无新会话行**；截图/进程留痕证明是原版路径。
- **ON 判定（必须自证）**：启动日志出现「配置加载完成: … EnableLFH=…」；末行遥测非零（或说明该局未触发钩子）。
- **禁止**用「改 ini 把功能关掉」冒充 OFF——OFF 的定义是 **DLL 未注入**。

---

## 2. 进图指纹（每局必采，缺一即该局作废）

沿用 `h1_fanout_mechanism.md` M5/A3/A5 口径，**先校验再计数**：

| 指纹 | 采集 | 合格判据 |
|---|---|---|
| F1 图文件哈希 | 安装后 `sha256` U0200_H1 | 与批次开工时记录一致；变化则停手 |
| F2 units_seen | `@f15` 与终局各一次 | 固定国家对预期 **≈22–30**（美蘇带）；**若 ≈713 ⇒ 误选/进错图，该局作废**（U0200 随机误选签名，见 `segD_run.py` 口径） |
| F3 对阵 | 截图或设置页 | 确为 Americans vs Russians，非随机 |
| F4 会话 | PID / 起止时间 | 每局独立进程（崩溃局不得续用） |
| F5 崩溃指纹 | 见 §4 | — |

> **注意**：固定国家对下 `units_seen` 仅 20–30，**低于**原崩溃局的 713。若 A/B 各 5 局均 0 崩溃，**不得**写「H0 成立」，只能写「该负载下未复现」，并启动 §5 高负载加测层。

---

## 3. 样本量与停止规则

### 3.1 样本量

| 项 | 值 |
|---|---|
| 主协议 N | **每臂 5 局**（A、B 各 5；C 若做 ≥3） |
| 下限 | 每臂 ≥3 局才允许出率；不足标 `[待实测]·弱` |
| 上限 | 单臂 ≤10；三臂合计 ≤20 局（硬顶） |
| 指标 | `except_rate = 崩溃局数 / 有效局数`（有效 = 过 §2 指纹） |

### 3.2 停止规则（按优先级）

1. **红线立即停**：出现 EIP ∈ `ra2render` 注入区（ImageBase `0x10000000` / 钩子 `0x54D3xxxx`）或 `0x01B00000` 跳板页 ⇒ **整批停手**，原样回报（判实施侧缺陷，不在本协议内修）。
2. **H0 收敛可早停**：A 臂已 ≥1 崩且 EIP 同为 `0x007CFC9F`，B 臂也 ≥1 同 EIP ⇒ 可在凑满 N=3/臂 后收口（两臂都有同型崩溃）。
3. **H1 倾向**：满 N=5 时 A=0 且 B≥1（EIP=`0x007CFC9F`）⇒ 判「注入态相关**倾向**」，可加跑至 10 局/臂压稳率；同时把臂 C 提为必做（隔离 LFH）。
4. **双零**：A、B 均 0/5 ⇒ **不判 H0**，转 §5 高负载加测；禁止用「没崩」写成「注入无关已证实」。
5. **其它崩溃**：非 `0x007CFC9F` 也非红线区 ⇒ 记入「其它崩溃」列，**不并入**主指标，继续跑完 N。

---

## 4. 判据表（交付必填）

| 判据 | 度量 | 读法 |
|---|---|---|
| **J1 except 出现率** | `rate_OFF` vs `rate_ON`（及 `rate_LFH0`） | OFF 显著>0 且与 ON 同量级 ⇒ 偏 H0；OFF=0 且 ON>0 ⇒ 偏 H1 |
| **J2 EIP 是否同为 `0x007CFC9F`** | 每份 `except.txt` 的 `Exception at` | 同 EIP ⇒ 同型崩溃可比；不同 EIP 另表 |
| **J3 其它崩溃** | 非目标 EIP 的异常码/EIP | 有则单独列，禁止混入 J1 |
| **J4 调用链形态** | 栈是否仍全在 CRT（`0x7C9489/0x7C9452/0x7C8E22` 帧） | 仍全 CRT ⇒ 维持「非执行层肇因」；出现 `0x54D3xxxx` ⇒ 红线 |
| **J5 毒值形态** | `EDX` / Access address | 仍为 `FE00FFFF` 或同族业务数据形态 ⇒ 同型；出现模块内立即数 ⇒ 另案 |
| **J6 指纹有效率** | 作废局数 | >20% ⇒ 先修测量再谈率 |

**统计口径（诚实约束）**：N≤10 只做**描述性**率比较（如 0/5 vs 2/5），**不做**显著性检验宣称；「倾向 / 不倾向」用词，禁止「证明/证伪」绝对化。

---

## 5. 高负载加测层（双零时的升级路径，非主协议）

原崩溃特征是 **U0200 + 随机敌国 + units_seen 713–716**（高 churn）。固定国家对只有 22–30。

- 触发条件：§3.2 规则 4（A/B 双零）或 J1 无法区分。
- 动作：同 A/B 开关，场景改为 **U0200 + 随机敌国**（复刻原崩溃条件），每臂 ≥3 局；此时进图指纹 F2 预期改为 **≈713**（且必须确认真是 U0200 而非误选）。
- 仍 0 崩 ⇒ 报告写「双层负载下均未复现」，升级 R 轨 SBH 深入 + 可选调试器断点（forensics V4），**仍禁止**写「已排除注入相关」。

---

## 6. 崩溃留证（强制，禁止伪造）

每局结束后**立刻**检查 `ra2bench\except.txt`：

1. **不存在**：记「本局无 except」，不得跳过检查。
2. **存在**：
   - 记录 `CreationTime`、字节数；
   - **SHA256**（与 ZC-11 参考件 `B42C7014C96CADCB2DA86327CA6A62E302A043283238531880325809D7D35870` 对照是否同型）；
   - **整文件复制** 为 `except_ab/evidence/arm{A|B|C}_game{NN}_except.txt`（原件随后可隔离出游戏目录，避免串局）；
   - 抽出 `Error code / Access address / Eip / EAX–EDI / Stack` 首帧到 `arm{X}_game{NN}_summary.txt`。
3. 截图唯一 MD5；进程留痕（PID、启动方式 OFF/ON）。
4. **禁止**：编辑/补写 `except.txt`；把旧崩溃挪进本批；用同一文件冒充多局；隐瞒崩溃继续报「零崩溃」（ZC-11 [7] 教训，见勘误）。

---

## 7. 写作用域与禁止

**允许写**：

- `out/re_work/zcode_live/except_ab/**`（协议副本、evidence、RESULT）
- `ra2bench\ra2render.ini` **仅**臂 C 的 `EnableLFH` 一键切换（改前/改后副本 + sha256，**收尾还原并贴 sha**）
- `ra2bench\except.txt` 的复制/隔离（不动其它游戏文件）

**禁止写**：

- `ra2render/**`（源码与 DLL）、`ra2youli/**`、`gamemd.exe`、任何 `.mix`/地图本体
- `tools/bench_replay.py` 等 harness（T13 在改）
- `RESULT_ZC11.md` / 台账 / 其它 docs
- 伪造证据（红线）

**自证门禁**（实跑贴原文）：

```text
python tools\verify_anchors.py          → 323/323
python tools\bench_map_install.py --verify --game-dir ra2bench   → 全 PASS
```

---

## 8. 交付与回报

**交付物**（均在 `out/re_work/zcode_live/except_ab/`）：

1. `RESULT_EXCEPT_AB.md` —— §9 卡内判据表 + J1–J6 + 率表
2. `evidence/**` —— 每局指纹、截图、except 副本与哈希、ini 前后副本
3. `claims.txt`（可选）—— 关键行断言

**回报格式**：严格按 `docs/re/AGENT_DELIVERY_FORMAT.md` **10 节骨架**（缺节=不合格）。特别地：

- **[5] 作用域合规** 必须声明 `EnableLFH` 是否已还原 + sha256；
- **[7] 风险红线** 必须回答是否触发崩溃 / 是否出现注入区 EIP；
- **[3] 勘误**：本批若证实「零崩溃」类表述需改，只交勘误清单，**不改** RESULT_ZC11 本体（Lead 合并）。

---

## 9. 可粘贴协议卡（交 ZCode 粘贴执行）

> 与 `out/re_work/dispatch_v30/prompt_zcode_except_ab.txt` 同文。以该 txt 为派发件。

```text
【任务卡 ZC-EXCEPT-AB】except A/B 真机对照：注入 ON/OFF 复现率与 EIP 收口（P0）

◆ 执行方：ZCode（唯一真机执行方）   ◆ 期望耗时：60–120 分钟（主协议 10 局 + 可选臂 C/高负载）
◆ 工作区：D:\Project\ra2-campaign-forge · 游戏目录 ra2bench（所有命令带 --game-dir ra2bench）
◆ 基线：ra2bench\gamemd.exe（MD5 4f37486e5b0dbe2ae5f45aeee0f98367）【只读】
       ra2bench\ra2render.dll（152,576 B / MD5 3C1077BD44F2B0DB9D30D55C5C9DA68C）【只读，不改】
◆ 上游定谳（只读引用）：docs/re/except_zc11_forensics.md
   —— 崩溃点 __sbh_alloc_block @ 0x007CFB13，EIP 0x007CFC9F，毒值 EDX=FE00FFFF，
      调用链全在原版 CRT；「注入态才复现」未证伪 ⇒ 本卡只做 A/B 率与 EIP 收口。

◆ 目的/假设
  H0 注入无关：OFF 臂同场景也会崩、EIP 同为 0x007CFC9F
  H1 注入环境相关：OFF 显著更少/为 0，或仅 ON 崩；必要时再分 LFH（臂 C）
  本卡不找根因对象，只回答「出现率与 EIP 是否随注入开关变」。

◆ 绝对禁止
  伪造证据（截图唯一 MD5 + 进程留痕 + ini/图哈希前后对照）｜改 except.txt 或挪旧崩溃冒充
  把「没崩」写成「H0 已证实」｜改 ra2render/** / ra2youli/** / gamemd.exe / .mix / 台账 / docs
  用「关 ini 功能」冒充注入 OFF（OFF = DLL 未加载）｜UI 失响应继续硬点

◆ 段 0（前置）【必做】
  0.1 哈希核对 ra2bench 游戏目录（对照 out\loadbench\RA2BENCH_MANIFEST.md）；
      python tools\verify_anchors.py → 323/323；bench_map_install --verify 全 PASS。
  0.2 安装 U0200_H1（bench_map_install.py），记录图文件 sha256（F1）。
  0.3 锁定国家对：P1=Americans，P2=Russians（禁止随机）。记录 ra2md.ini [Skirmish] 现状哈希（两臂共用，不改）。
  0.4 清点 ra2bench\except.txt：若已有旧文件，先哈希隔离到 evidence/pre_batch/，保证每局判新。

◆ 段 A（臂 A · 注入 OFF）【必做】N=5
  A1 直接启动 ra2bench\gamemd.exe（不经 ra2loader）。
  A2 自证 OFF：无 ra2render.dll 模块、ra2render.log 无新会话、进程留痕。
  A3 每局：进图指纹 F2 units_seen@f15 + 终局（预期 ≈22–30；≈713 ⇒ 误选，作废重跑）+ F3 对阵截图。
  A4 每局结束后立即检查 except.txt（§判据-留证）。

◆ 段 B（臂 B · 注入 ON 默认档）【必做】N=5
  B1 经 ra2bench\ra2loader.exe 启动（注入 ra2render.dll，部署态 ini，EnableLFH=1）。
  B2 自证 ON：启动日志「配置加载完成…EnableLFH=…」；遥测末行。
  B3 同 A3/A4 指纹与 except 检查。
  B4 与 A 臂同剧本/同时长；不得一臂手玩一臂挂机。

◆ 段 C（臂 C · ON + EnableLFH=0）【加测，隔离 R4】N≥3
  C1 仅改 ra2render.ini [System] EnableLFH=1→0；改前/改后副本 + sha256。
  C2 启动日志须显示 EnableLFH=false 且无「成功激活 LFH」行。
  C3 其余同 B。
  C4 ★收尾：EnableLFH 还原 1，贴还原后 sha256（与改前一致）。

◆ 判据（写进 RESULT，禁止只写结论）
  J1 except 出现率 rate_OFF / rate_ON / rate_LFH0（崩溃局数/有效局数）
  J2 每份 except 的 Eip 是否同为 0x007CFC9F
  J3 其它崩溃（非目标 EIP）单独列表，不并入 J1
  J4 调用链是否仍全在 CRT（0x7C9489 / 0x7C9452 / 0x7C8E22 帧）；出现 0x54D3xxxx / 0x01B00000 ⇒ 红线停
  J5 毒值形态（EDX / Access address）是否仍为 FE00FFFF 或同族
  J6 指纹作废率（>20% 先修测量）
  统计诚实：N≤10 只描述率，写「倾向/不倾向」，禁止「证明」绝对化。

◆ 样本量与停止规则
  每臂 N=5（下限 3 才出率；单臂≤10、三臂合计≤20）。
  ① 红线（注入区/跳板 EIP）⇒ 立即整批停手回报。
  ② A、B 均已有 ≥1 同 EIP 崩溃 ⇒ 可 3 局/臂 早收。
  ③ 满 5 局 A=0 且 B≥1（同 EIP）⇒ 判「注入相关倾向」，加跑至 10 并提臂 C 为必做。
  ④ A、B 双 0/5 ⇒ 禁止写 H0 成立；转高负载加测层。
  ⑤ 非目标 EIP 崩溃记 J3，继续跑完 N。

◆ 高负载加测层（双 0/5 时触发）
  同 A/B 开关，场景改 U0200 + 随机敌国（复刻原崩溃条件 units_seen≈713），每臂 ≥3 局。
  仍 0 ⇒ 写「双层负载下均未复现」，升级 R 轨 SBH + 调试器断点，仍不得写「已排除注入相关」。

◆ 崩溃留证（每局强制）
  except.txt 有无都要记；有则：CreationTime + 字节数 + SHA256 + 整文件复制到
  except_ab/evidence/arm{A|B|C}_game{NN}_except.txt + summary（Error code/Eip/Access/寄存器/栈首帧）。
  参考同型件：SHA256 B42C7014C96CADCB2DA86327CA6A62E302A043283238531880325809D7D35870（ZC-11）。
  禁止编辑 except.txt、挪旧件、一文件冒充多局。

◆ 失败判据（任一即 FAIL，原样回报不得掩盖）
  红线 EIP ｜伪造/复用 MD5 ｜未做指纹或指纹作废未重跑 ｜臂 C 未还原 ini ｜
  漏检 except 或隐瞒崩溃 ｜用关功能冒充 OFF ｜样本 <3/臂 却写成率结论 ｜把「没崩」写成 H0 证实

◆ 写作用域
  允许：out/re_work/zcode_live/except_ab/**、ra2bench\ra2render.ini（仅 EnableLFH，须还原）、
        ra2bench\except.txt 的复制/隔离
  禁止：ra2render/**、ra2youli/**、gamemd.exe、.mix/地图本体、tools/bench_replay.py（T13 在改）、
        RESULT_ZC11.md、台账、其他 docs

◆ 交付
  out/re_work/zcode_live/except_ab/RESULT_EXCEPT_AB.md（判据 J1–J6 + 率表 + 每局指纹）
  out/re_work/zcode_live/except_ab/evidence/**
  自证门禁原文：verify_anchors 323/323；bench_map_install --verify 全 PASS

◆ 回报：docs/re/AGENT_DELIVERY_FORMAT.md 10 节骨架。
  [5] 必须声明 EnableLFH 是否还原 + sha256；
  [7] 必须回答是否触发崩溃、是否出现注入区 EIP；
  [3] 勘误只交清单，不改 RESULT 本体。

◆ 参考（只读）
  docs/re/except_zc11_forensics.md（归因定谳 + §8 V1–V5）
  docs/re/h1_fanout_mechanism.md（进图指纹 / 误选签名 / 国家对）
  docs/re/zc11_closeout_report.md（「零崩溃」误报教训）
  out/re_work/zcode_live/RESULT_ZC11.md（段 D U0200 记录，只读）
```

---

## 10. 与既有结论的关系

| 既有 | 本协议动作 |
|---|---|
| forensics 执行层「与 ra2render 无关」[实证] | **不推翻**；本协议补的是环境层 |
| RESULT_ZC11 [7]「零崩溃」 | 已定错误；本协议任何结果都不得回退成「零崩溃」叙事 |
| H1 性能 ROI 冻结 | **不变**；本协议不产出 ROI 数字 |
| harness `except_watch` 门禁（勘误建议 [9]⑨） | 本协议人工版先跑通；自动化仍归 M 轨 harness，**不改** `bench_replay.py` |
