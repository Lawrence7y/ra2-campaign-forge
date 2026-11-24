# P04 · tick 字段数据检验：A02 焦点旗标假说 **不能**被既有真机数据判定——判定 = DATA_INSUFFICIENT（事件缺失型：全批 15,229 个有效 tick 采样无一为 0，且 0 个非设计停帧事件）

## 0. 现场自证

- **引擎自证**（`P04/P04_probe2_out.txt:2-3`，本会话实跑）：
  `eng.coverage = 100.00% / 1394120 insns / 66 resync`，`sha256 = 73201cc0…f67476`（与冻结母本一致）。
- **零真机自证**（本会话实跑）：`tasklist | grep -i -E "gamemd|ra2loader|yuri"` → 无匹配（grep 退出码 1），无游戏进程。全程未启动任何游戏/加载器，未 taskkill，母本只读。
- **数据枚举自证**（`P04/P04_probe1_out.txt:4`）：`lead/qc161_u0400_trip/c2ab_x/*/timeline.json` 共 **23 份**（9 份 schema-A `{battle_tl,pre5,close_rows}`，14 份 schema-B `{hold_tl,close_rows,_e2}`），总行数 **15,237**；tick 可读 int 采样 **15,229**，读失败件 8（全部是 8 个自然退出趟的末行，进程已死后 `tri_read_u32` 产 `{"state":"read_fail"}`）。
- 逐份时间跨度与中位采样间隔（`P04_probe1_out.txt:6-149`，全表见输出件）：battle 段 2.00s、hold 段 1.00s、pre5 段 1.00s、close 段 0.100s（全批 p10/p90=0.100/0.101，`P04_probe1_out.txt:4177-4181`）。趟跨度最小 21.5s（自然退出），最大 186.4s（watch 120s 的挂死趟）。

## 1. 结论（带证据级别）

1. **[字节/推导] 判定 = DATA_INSUFFICIENT**。四选一明确落入：CAN_CONFIRM ✗、CAN_REFUTE ✗、CANNOT_DECIDE（不取——它指"事件在但被混杂堵死"，本案是事件本身缺席）、**DATA_INSUFFICIENT ✓**。且属**事件缺失型**不足，不是采样分辨率不足（close 段 0.1s 已比 A02 两个环粒度 500ms/10ms 细）。
2. **[字节] 全批 tick==0 出现 0 次**。15,229 个有效采样全部 ==1（独立于脚本的直查：原始 JSON 值分布 `{1: 15229, read_fail: 8}`）。趟件全程从未失焦——**A02 的前提事件（焦点旗标=0）在这 23 趟里一次都没发生**。
3. **[字节/推导] 全批 0 个 A02 相关停帧事件**。11,279 个 Δf==0 相邻对（主口径剔除 16 个跨 singleton 变界对后 11,263）**全部** tick==(1,1)，且 100% 属两类混杂：菜单设计停帧 8,983 对 + 战斗趟拆除清零尾段 2,280 对（RELEVANT=0）。战斗趟 frame 全速 31fps 推进（含 WM_CLOSE 后整个 watch 段）。
4. **[推导·与任务规则冲突，必须指出] 任务给的原始判定规则在本批会产生假证伪**。"Δf==0 却 tick==1 ⇒ 证伪"若照搬，将用 11,279 对"证伪"A02——但这些对全部是：①菜单趟 frame==0：`0x55D360` 头部 `mov al,[0xA8E9A0]; je 0x55DECF`（`a0a0e9a800` / `0f84580b0000`）在进战斗前就早退，frame 不前进与焦点无关，tick==1 恰是同一字节机制预测的稳态；②战斗趟清零尾段：frame/hwnd/singleton 被拆除路径清 0（跌落瞬间 min Δf=−3613/−3798/−4019/−5700 各 1 对），tick 残读 1 是死字节（唯一写者 `0x7778CE` 在已销毁窗口的 WndProc 里，且该写是沿触发：`0x7778BF` 旧值==新值则跳写）。拿它们证伪 A02 是逻辑错误。
5. **[推导·弱信号] 全批 3,923 个 Δf>0 对全部 tick==(1,1)**——与 A02 逆否命题（frame 前进 ⇒ 未失焦）一致，但在"从未失焦"的世界里恒真，**无鉴别力**，不构成支持。
6. **[推导] 采样功率对照（任务第 4 条陷阱的正面回答）**：可捕捉停帧时长下限≈各段中位采样间隔：close 0.1s、pre5/hold 1.0s、battle 2.0s。close 段功率充足；battle/hold/pre5 段只能捕捉 ≥1–2s 的冻结。**但功率不是本案瓶颈**——即使 100Hz 采样，也无法从"零失焦 + 零非设计停帧"的数据判出任何方向。
7. **[推测] 若 A02 为真，本批的兼容解释**：这批趟件从不夺焦（tick 恒 1）⇒ A02 机制的触发条件从未满足 ⇒ 数据与 A02 相容但零检验力。A02 只能用"制造失焦"的趟件判定（方案见 §4 末与 §5）。

## 2. 证据（逐条 VA + 字节 + 推导链）

### 2.1 tick 字段确为焦点旗标采样（数据链）

- [字节] `_drive_c2_x_probe_v2.py:70`：`G_TICK = 0x00A8ED80`；schema-A 9 趟由它直产（battle `sleep(2.0)`:641、pre5 `sleep(1.0)`:673、close `sleep(0.1)`:718）。
- [字节] schema-B 14 趟由 `_drive_c2_x_e12.py` 产，close 采样器同源：`_drive_c2_x_e12.py:467` `("tick", V2.G_TICK)`。
- [字节] 本会话复核 `0xA8ED80`：全镜像 **46 引用 / 唯一写者 `0x7778CE`**（`P04_probe2_out.txt:5-7`：`W 007778CE mov byte ptr [0xa8ed80], al`），与台账 §3689 吻合。

### 2.2 A02 机制字节（为何菜单停帧/清零尾段不构成证据）

`P04_probe2_out.txt:9-37`（本会话逐字节重读）：

```
0055D360  a0a0e9a800    mov al, [0xa8e9a0]     ; in-tactical 门
0055D371  0f84580b0000  je   0x55decf          ; ==0 → 早退，frame 不推进（菜单设计停帧）
0055D377  a080eda800    mov al, [0xa8ed80]     ; 焦点门
0055D385  7534          jne  0x55d3bb          ; ==1 → 正常帧体
0055D39B  68f4010000    push 0x1f4             ; GameMode 0/5 → Sleep(500ms)
0055D3A2  e8a9790700    call 0x5d4d50          ; +泵
0055D3AE  74dd          je   0x55d38d          ; 仍失焦 → 环
0055D3B2  6a0a          push 0xa               ; 其余 GameMode → Sleep(10ms)
0055D3BB  a184eda800    mov eax, [0xa8ed84]    ; 帧体才碰 CurrentFrame
```

- [字节] IAT：`[0x7E11F0]→KERNEL32!Sleep`、`[0x7E1530]→WINMM!timeGetTime`（`P04_probe2_out.txt:40-42`）。
- [字节] frame 推进点：`0055DE7E 42 inc edx` + `0055DE81 891584eda800 mov [0xa8ed84], edx`（`P04_probe2_out.txt:64-70`）。
- [字节] 写者沿触发：`007778B9 mov dl,[0xa8ed80]` → `007778BF cmp edx,ecx; je 0x777949`（旧==新跳过写）→ `007778CE mov [0xa8ed80], al`（`P04_probe2_out.txt:44-55`）。
- **推导链（结论 4）**：菜单趟 tick==1 ∧ frame==0 ⇒ 走 `0x55D371` 早退路径（焦点门 `0x55D377` 根本没执行）⇒ 与 A02（焦点门控帧）无交涉 ⇒ 该类 Δf==0 对不能进判定。清零尾段同理：读数是死字节残值。

### 2.3 数据面（全量 23 份，`P04_probe1_out.txt`）

| 量 | 值 | 出处 |
|---|---|---|
| 文件数 / 总行 / tick 可读 | 23 / 15,237 / 15,229 | :4, :177 |
| tick==0 / tick==1 / 其它 int | **0 / 15,229 / 0** | :177（独立直查复核同值） |
| Δf==0 对（含跨段） | 11,279，全部 tick=(1,1) | :180-189 + 本会话补算 |
| └ 菜单设计停帧 | 8,983（close 8,804 + hold 149 + pre5 8 + battle 4 + 跨界 18） | :182-188 |
| └ 清零尾段（战斗趟） | 2,280 | :189 |
| Δf>0 对 | 3,923，全部 tick=(1,1) | 本会话补算 |
| Δf<0 对 | 4（−3613/−3798/−4019/−5700，各 1） | 本会话补算；清零跌落 |
| RELEVANT（非设计停帧）对 | **0** | :190 |
| 最长 Δf==0 链 | 菜单 hang 趟 close 段 ≥119.87s（frame==0, tick 全 1） | :193 |
| 战斗趟 close 帧率 | P0 两趟 31.25/31.08 fps 贯穿 40s watch，每对 Δf min=2 | :4151, :4156 |

- [字节] 清零点原貌（`20261028T085640_0001_P1_G1B0exp` close[470..473]，本会话直读）：`hwnd=0, singleton=0` 先行，100ms 后 `frame 3798→0`，`wait=258`（进程仍活），`tick=1` 残读——是拆除清全局，不是活游戏停帧。
- [字节] 战斗趟 `G_HWND(0xB73550)` 在 close 进入后即刻归 0（各趟 hwnd 存活行仅 1），但 frame 继续以 31fps 推进——"hwnd=0"≠"游戏停"，仅作观察记录。

## 3. 与本仓既有记载的对账

- ✅ `GOAL_THREE_TARGETS_20261018.md:3689`：G_FOCUS 0xA8ED80 = 46 引用 / 1 写——本会话重扫逐位吻合。
- ✅ `XVERIFY_E5_20261030.md:233`：`G_TICK` 系列名误标（一址三名 AppHasFocus/tick/闩互斥），tick 列读的就是焦点旗标、恒 1=有焦点——与本任务口径及本次全批测量一致；本报告沿用该定谳（列名 `tick` 语义=focus）。
- ✅ `XVERIFY_E5_20261030.md:136`：hold_tl tick 恒 {1}——本次扩展到全部 23 份×4 段（15,229/15,229）。
- ✅ `DISCIPLINE.md` §4 基线（写者 0x7778CE、Sleep/timeGetTime IAT、inc 0x55DE7E+写回 0x55DE81）——本会话全部重验吻合；MainLogicFrame 3-ret 基线本报告不依赖、未重验（见 §4）。
- ⚠️ **冲突（对任务给定规则，非对台账）**：任务的操作化规则"Δf==0 却 tick==1 ⇒ 证伪"在本批数据上会产生**假证伪**（见结论 4）。这不是数据问题，是规则未排除两个字节级可证的混杂态。按纪律指出，不沉默迁就。
- 无与既有台账冲突的新事实。顺带观察（未入账建议）：战斗臂 hang 的形态是"全速跑不退"（P0）或"拆完全局不退"（P1/P2/P3），菜单臂 hang 是"设计停帧挂着不退"——三种形态 tick 全程 1。

## 4. 诚实账

**没做的**：
- 未重验 MainLogicFrame 3-ret 基线（0x55D877/0x55DEC7/0x55DEDB）——本报告结论不依赖它。
- 未读 `_e2` 段（slow_sample_rows/latch/summary）与 25 份 `_rec.json` 之外的趟件字段——属其它子任务面。
- 未做退出时刻毫秒级归因、未对 8 个自然退出趟做退出时长分布——超出本任务四选一所需。

**样本薄的**：
- P0 臂仅 2 趟；frame 清零事件仅 4 次；"Δf<0"形态只有战斗臂 4 趟出现。
- 全批 0 个失焦样本 ⇒ 关于"tick==0 时行为"的任何统计都是零样本。

**可能出错的**：
- menu_idle 归类依赖 `_rec.json` 的 `mode` 字段；若 mode 标错则分类错。但 frame==0 与 `0x55D371` 早退机制自洽，误标可由数据本身检出行（战斗趟不会 frame==0）。
- Δf==0 对的 tick 双端读数在 0.1s 窗内无法排除窗内毫秒级翻转——对本案结论无影响（RELEVANT=0，没有对可逃逸）。
- probe1 的运行段切分按 singleton 变化，导致全批对数出现 11,279（不剔除）vs 11,263（主口径）两个数，差 16 对跨界对；两数都已在报告中给出。

**最小补充采样方案（第 7 条要求，不执行）**——核心是**制造失焦事件**，否则永远 DATA_INSUFFICIENT：
- 趟件设计：战斗稳态（frame>0）后由外部窗口主动夺焦 ≥10s 再还原，×5 次；菜单态同做一组；另保留全程不夺焦对照趟。
- 采样 VA（6 个）：`0xA8ED84`(CurrentFrame)、`0xA8ED80`(focus)、`0xA8E9A0`(in-tactical 门，剔除设计停帧)、`0xA8B238`(GameMode，区分 500ms/10ms 环)、`0xA8EDD8`(exitstate)、`0xB73550`(hwnd)。
- 频率：**≥20Hz**（50ms——in-battle 10ms 环 5 个迭代/样本、菜单 500ms 环 1/10 周期；≥100Hz 更稳）。
- 时长：每趟 ≥180s（30s 稳态 + 5×(10s 失焦+10s 还原) + WM_CLOSE 后 120s watch）。
- 真机判别量表：出现 `[0xA8E9A0]==1 ∧ tick==0 ∧ Δf==0` 连续 ≥2 采样 → CAN_CONFIRM 方向；出现 `[0xA8E9A0]==1 ∧ tick==0` 持续 ≥0.5s 而 frame 前进 ≥1 → CAN_REFUTE 方向。

## 5. 复算入口

```bash
cd D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/P04
# 数据主检验（纯离线，~3s）
python -I -X utf8 P04_probe1.py > P04_probe1_out.txt 2>&1
# 引擎自证 + 机制字节复核（只读 gamemd.exe，~2min）
python -I -X utf8 P04_probe2.py > P04_probe2_out.txt 2>&1
# 零真机自证
tasklist | grep -i -E "gamemd|ra2loader|yuri"   # 期望无匹配
```

- `P04_probe1.py`：23 份 timeline.json 全量枚举、tick 分布、Δf==0 对三分类（RELEVANT/menu_idle/zeroed）、停帧链、功率对照。
- `P04_probe2.py`：`ra2tool.Engine` coverage 自证、0xA8ED80 普查、0x55D360 门控字节、IAT、写者上下文、frame 推进点。
- 独立直查（本会话实跑原样命令，绕开脚本逻辑；输出 `{'1': 15229, "{'state': 'read_fail'}": 8}`）：

```bash
python -I -X utf8 -c "
import json, glob
c = {}
for p in glob.glob(r'D:/Project/ra2-campaign-forge/lead/qc161_u0400_trip/c2ab_x/*/timeline.json'):
    d = json.load(open(p, encoding='utf-8'))
    for key in ('battle_tl','hold_tl','pre5','close_rows'):
        for r in d.get(key) or []:
            rows = [r.get('sent', r)] if key == 'pre5' else [r]
            for rr in rows:
                k = repr(rr.get('tick')); c[k] = c.get(k, 0) + 1
print(c)
"
```
