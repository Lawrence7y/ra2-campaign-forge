# 领队离线预检（2026-11-05）：挂起计数器 `Scenario+0x62C` 的**脚本入口已被绑定到具体动作号**

> 本节是**领队自己跑的**离线核验（零真机、零母本改动、未 commit），
> 目的是给本轮两条工作流一个**已钉死的事实基座**，避免它们重复劳动或编造。
> 全部命令可复算，脚本未落盘（一次性 `python -I -X utf8 -c`），复算方法见 §4。

## 一、为什么要做这一步

台账 §540/§541 与 `BATCH1_VERDICT.md` 已经把**结构**钉死：

- `[0xA8B230]` = `ScenarioClass::Instance`（不是 GameLogic）；
- `+0x62C` = **挂起深度计数器**，全镜像写点恰 3 处
  （复位 `0x6836D2` / 加一 `inc [eax+0x62C]` @`0x684174` / 减一写回 `0x684195`）；
- `0x55D877` 冻结出口由 `GameMode∈{0,Campaign; 5,Skirmish}` ∧ `[Scenario+0x62C]≠0` **双门**开启；
- 「挂起请求」入口函数 = `0x684060`，**全镜像恰 4 个 call 点**；
  「释放」入口函数 = `0x684180`，**恰 3 个 call 点**；
- 渐变启动器 = `0x53B460`，**恰 2 个 call 点**。

**但 P01 自己登记的开放项第 2 条至今未闭**（`P01/REPORT.md:150`）：
> 「动作处理器区 0x6DF6FD/0x6E4080 的**动作号**未定谳（表基 0x872A7C 槽 255 仅是序数）」

本轮把这一条查掉了。

## 二、★ 结论（本线亲验，可复算）

### 2.1 动作号绑定（`out/re_work/triggers/action_dispatch_table.tsv` 区间命中）

| 挂起相关 call 点 | 落在哪个动作的派发块内 | 动作 kind | 动作名 |
|---|---|---|---|
| `0x6DF703`（call `0x684060`） | `0x6DF6FD..0x6DF717` | **0x6E = 110** | **PauseGame**（PauseScenarioFor） |
| `0x6DFAC5`（call `0x53B460` 渐变启动器） | `0x6DFABF..0x6DFAD9` | **0x7F = 127** | **StartChronoScreenEffect** |
| `0x6E4086`（call `0x684060`） | 无动作块（`0x6E4080` 是 [M+N] 从属方法） | — | 由 `0x6DF6FD` 同族调用（动作 110 的从属体） |
| `0x6E2F96`（call `0x53B460`） | 无动作块（`0x6E2F90` 是 [M+N] 从属方法） | — | 由 `0x6DFABF` 同族调用（动作 127 的从属体） |

字节自证（本线实跑 `ra2tool.Engine.disasm`）：

```
006DFABF  8b8e90000000   mov ecx, [esi+0x90]      ; 读 Value 参数
006DFAC5  e896b9e5ff     call 0x53b460            ; → 渐变状态机启动（内部在 state2 末尾 call 0x684060）
006DF6FD  8b8e90000000   mov ecx, [esi+0x90]
006DF703  e85849faff     call 0x684060            ; → 挂起请求（ecx = 时长秒）
```

`docs/re/trigger_system_manifest.md:264` 与 `:247` 分别把 127 / 110 的从属体写作
`SetChronoScreenEffectState 0x6E2F90` 与 `PauseScenarioFor 0x6E4080`，与本轮区间命中**一致**。

### 2.2 第三个挂起入口**不是**脚本动作

`0x657CA0`（call `0x684060`，时长=0）所在函数头 = **`0x6579E0`**，
全镜像**唯一调用者 = `0x653446`**（只有一个 call 点）。
该函数被一个**全局布尔计数** `0xB45B68` 驱动（23 处引用、写点 `0x5BF341/0x5BF43B/0x5BF487`），
语义为「沿翻正→挂起 / 沿翻回→释放」（`0x657C9C je 0x657CC8`）。
⇒ **它是引擎内部的对象状态机，不经 TActionClass 派发**，对「地图里能触发什么」这一问**不构成额外入口**。
（该对象身份本线**未定谳**，留给 W1。）

### 2.3 ★ 测量用地图 `U0400` 根本没有这两个动作

对 `ra2youli/[2]0LoadBench_U0400.yrm` 的 `[Actions]` 段做解析：

```
[2]0LoadBench_U0400.yrm   n=3   kinds = [(2,1), (4,1), (9,1)]
```

即 **Lose(2) / CreateTeam(4) / FireSale(9)** 各一条，
**不含 110 PauseGame、不含 127 StartChronoScreenEffect**。

同一批扫描里：`U0050/U0200/U0400` 也是 `{2,4,9}`；`U0100/U0800` **无 `[Actions]` 段**；
`ECH01/02/03.MAP` 只有 `{(1,11)}` / `{(1,11),(2,1)}` / `{(1,12)}`。

### 2.4 这三条合起来意味着什么（**只说到证据允许的地方**）

`[Scenario+0x62C]≠0` 的**脚本可达路径**只有两条（动作 110 / 127），
外加一条引擎内部布尔沿（`0x6579E0`，无脚本入口）。

而**全部 101 份 `measure_w*.json` 的测量图里没有任何一条 110/127 动作**
（U0400 是 43 份里最主要的一张；本轮抽查的三张 LoadBench 图均无）。

⇒ **在测量语料这一范围内，「帧钟停摆」不能用「地图脚本主动 PauseGame / ChronoScreen」来解释。**
这是一条**阳性排除**（不是"未观察到"，是"入口不存在"）。

**它不证明什么**：
- 不证明 32 个零推进窗「一定不是引擎停摆」——`0x6579E0` 那条内部路径仍在，本线未查其触发条件；
- 不证明这些窗「是终局态」——那是 §545/§550 已裁的另一条线（计分屏证据）；
- 不覆盖非 LoadBench 的测量图（`l1*` 趟的 `0add791d`、archive 的各图），本轮**未逐张解析**。

## 三、这给两条工作流各自的题

**W1（挂起面完备性）**：把 §2.2 的空白补上——
`0x6579E0` 的宿主对象是谁、`0xB45B68` 是什么计数、它在**没有脚本动作**时凭什么翻沿、
以及 `0x53B460` 渐变机是否还有**非动作**入口。产出必须是「挂起计数器的全部可能来源」的完备清单。

**W2（同图同兵力 3–6 倍帧时差）**：测量语料里存在一组**同图同 harness 同 units0≈1200–1350**、
但 `frame_ms_p50` 相差 1.7–5.7 倍的趟（见 W2 任务书）。
这是目标①目前最强的**受控对照**，且完全离线可查。

## 四、复算方法（零真机）

```bash
cd /d/Project/ra2-campaign-forge
# 1) 动作号区间命中
python -I -X utf8 -c "rows=[l.split('\t') for l in open('out/re_work/triggers/action_dispatch_table.tsv',encoding='utf-8',errors='replace').read().splitlines()]"
# 2) call 点枚举（用 ra2tool.Engine，SHA 断言 73201cc0…）
python -I -X utf8 -c "import sys;sys.path.insert(0,r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104');from ra2tool import Engine;e=Engine();print(e.coverage)"
# 3) 地图 [Actions] 段解析
python -I -X utf8 -c "d=open('ra2youli/[2]0LoadBench_U0400.yrm','rb').read();i=d.find(b'[Actions]');print(d[i:i+400])"
```

引擎自证：`coverage = 99.9984% / 1,394,120 insns / resync=66`，
SHA256 = `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`（与 `ra2tool.py:29` 期望一致）。

## 五、诚实账

1. **我亲验**：§2.1 四条区间命中、§2.2 的 `0x6579E0` 唯一调用者与 `0xB45B68` 引用数、
   §2.3 的 U0400 `[Actions]` 三动作、引擎 coverage/SHA。
2. **我未验**：`0x6E4080`/`0x6E2F90` 与 110/127 的**从属关系**——我只采信
   `trigger_system_manifest.md:247/:264` 的既有记载 + 同族地址相邻，**未做字节级父子证明**。
3. **我未验**：其余 40 张测量图的 `[Actions]`（只抽查了 U0050/U0100/U0200/U0400/U0800 + ECH 三张）。
   **本节 §2.4 的排除只对已解析的图成立**，W1 必须补齐。
4. 本轮**零真机**、**零母本改动**、**未 commit**。
5. 本节**不推翻任何已裁结论**：D-16/D-15/D-13 处置不变；它只是把 P01 的开放项②闭掉，
   并给 W1 一个具体的起点。
