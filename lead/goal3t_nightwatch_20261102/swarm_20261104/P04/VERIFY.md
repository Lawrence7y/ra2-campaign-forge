# P04 核验 · A02 焦点旗标假说判定=DATA_INSUFFICIENT 的事实基座全部从原始字节/JSON 独立复现成立（CONFIRMED），仅发现 3 处引用行号/下标漂移，无实质错误

- 核验人：核验员-P04（独立核验，目标是推翻）
- 原报告：`lead/goal3t_nightwatch_20261102/swarm_20261104/P04/REPORT.md`
- 复算件：`P04/VERIFY_data.py`（数据侧，不复用 probe1 逻辑）→ `VERIFY_data_out.txt`；`P04/VERIFY_mech.py`（机制侧）→ `VERIFY_mech_out.txt`
- 铁律遵守：全程未启动 gamemd.exe/ra2loader.exe/YURI，未 taskkill，未读运行中进程内存；gamemd.exe 只读（Engine 仅 open+read）；未 commit/push；写域仅 `P04/`。

## 0. 现场自证

- **引擎自证**（本会话 `VERIFY_mech.py` 实跑，`VERIFY_mech_out.txt:2-3`）：
  `eng.coverage = 100.00% / 1394120 insns / 66 resync`，`sha256 = 73201cc0…f67476`——与冻结母本一致，与原报告自报同值。
- **零真机自证**（本会话实跑）：`tasklist | grep -i -E "gamemd|ra2loader|yuri"` → 无匹配，`grep exit=1`。
- **数据枚举自证**（本会话 `VERIFY_data.py` 实跑，`VERIFY_data_out.txt:1-2`）：23 份 timeline.json（schema-A 9 / schema-B 14）；c2ab_x 下 24 个趟目录中仅 `20261029T222840_9001_P3e_E12_T2` 与 `_preflight` 无 timeline.json（T2 趟无数据文件，非 P04 遗漏）。

## 1. 结论（逐 keyFact，带证据级别）

| # | keyFact | 判定 | 依据 |
|---|---|---|---|
| 1 | 23 份（9A+14B）、15,237 行、tick 有效 15,229 全==1、tick==0 共 0 次、8 个 read_fail 全是自然退出趟末行 | **CONFIRMED** | [数据] 本会话独立重实现：`{1: 15229}`，0 值 0 次；8 个 read_fail 逐一定位=close 段**末行**且趟趟 exit=natural（`VERIFY_data_out.txt:3-13`）。并补查原报告自认未读的 `_e2` 块（14 份 schema-B 的 slow_sample_rows/latch/summary）——**0 个 tick 字段**，"全批无一为 0" 不受未读数据威胁 |
| 2 | Δf==0 对 11,279（剔除 16 跨 singleton → 11,263）全部 tick==(1,1)；menu_idle 8,983（close 8,804+hold 149+pre5 8+battle 4+跨界 18）+ zeroed 2,280；RELEVANT=0；Δf>0 3,923 全 (1,1) | **CONFIRMED** | [数据] `VERIFY_data_out.txt:16-20,44-54` 逐数命中；内部自洽：可读对 15,206 = 15,237−23 文件−8 跳过（read_fail 全末行的推论） |
| 2b | （我方加严）RELEVANT=0 不是分类规则的人造物 | **CONFIRMED** | [数据] 独立严格口径：Δf==0 ∧ frame>0 双端 ∧ hwnd>0 双端 ∧ singleton≠0 双端 ∧ tick==(1,1) 的"活游戏停帧候选"对 = **0**（`VERIFY_data_out.txt:56`）；zeroed 类 2,280 对逐一含 hwnd==0 或 singleton==0（`:54`） |
| 3 | 机制字节：0xA8ED80=46 引用/唯一写 0x7778CE；焦点门 0x55D377+0x55D385 jne 0x55D3BB；菜单早退 0x55D371 je 0x55DECF；Sleep(500ms)/Sleep(10ms) 环 | **CONFIRMED** | [字节] `VERIFY_mech_out.txt:5-7,10-42`：46/1 命中；`0f84580b0000` 手工重解码 rel32=+2904 → 0x55DECF（我第一次解码偏移错 1 字节得 0x612BFB，已修正重跑，capstone 窗口与我方重解码一致）；`7534`→0x55D3BB；`push 0x1f4`/`push 0xa`；环回 `74dd`→0x55D38D；0x55DECF 处=epilogue+`ret 0x55DEDB`，早退路径不含 inc——"菜单早退⇒frame 不推进且与焦点无关"机制成立 |
| 4 | 清零跌落 4 次（−3613/−3798/−4019/−5700 各 1）；teardown 序列 hwnd/singleton 先 0、约 100ms 后 frame 3798→0、wait=258 存活、tick 残 1（写者沿触发 0x7778BF 旧==新跳写） | **CONFIRMED**（1 处下标漂移） | [数据] 4 个 Δf<0 对逐一对值命中、全部 tick (1,1)、singleton/hwnd 0→0（`VERIFY_data_out.txt:38-42`）；[数据] 085640 实际跌落点 **close[504..507]**（非报告所写 close[470..473]）：close[506] frame=3798@…192.99 → close[507] frame=0@…193.09（100ms），wait=258，tick=1（`:58-64`）；[字节] 写者沿触发 `0x7778BF cmp edx,ecx; je 0x777949` 实读确认（`VERIFY_mech_out.txt:69-70`）。补充：192830 形态不同（hwnd 在 close[1] 即 0，frame 以 31fps 推进至 ~113s 才 5700→0）——与报告 §2.3"hwnd=0≠游戏停"自洽，不构成反例 |
| 5 | 采样间隔中位 battle 2.00s / hold 1.00s / pre5 1.00s / close 0.100s（close p10/p90=0.100/0.101） | **CONFIRMED** | [数据] `VERIFY_data_out.txt:66-70`：2.001/1.002/1.002/0.100；n_int=207/149/36/14790 与行数自洽（各段行数−文件数） |
| 6 | P0 两趟 close 31.25/31.08 fps 贯穿 40s watch、每对 Δf min=2；tick 列=焦点旗标（probe_v2.py:70、e12:467） | **CONFIRMED**（2 处行号漂移） | [数据] 084855=31.25fps minΔf=2、192013=31.08fps minΔf=2（`VERIFY_data_out.txt:73,78`；P0N_INJ_OFF 31.26 为同臂第 3 趟）；[字节] `_drive_c2_x_probe_v2.py:70` `G_TICK = 0x00A8ED80` 实读确认；**但 `_drive_c2_x_e12.py` 的 `("tick", V2.G_TICK)` 实际在 ：377，:467 是 `if stop:`**；probe_v2 的 sleep(2.0)/sleep(1.0) 实际在 ：649/:675（报告写 641/673），:718 sleep(0.1) 正确 |
| 7 | 四选一判定=DATA_INSUFFICIENT（事件缺失型）；任务规则"Δf==0∧tick==1⇒证伪"在本批=假证伪 | **CONFIRMED**（判定标签本身属判断，事实前提全验） | [数据/字节] 前提全部复现：失焦事件 0 次（keyFact 1）、活游戏停帧 0 对（keyFact 2b）、两类混杂的字节级解释成立（keyFact 3/4）。若照搬任务规则，11,263 对全部"证伪"命中，而其中 0 对是活游戏停帧——假证伪成立。DATA_INSUFFICIENT vs CANNOT_DECIDE 之辨（事件缺失 vs 事件被混杂）是定义之争，P04 已明写取舍理由，我方无字节反证 |
| 8 | 最小补采方案（自报未执行）：6 地址、≥20Hz、≥180s | **CONFIRMED**（作为设计；未执行无法数据验证） | [推导] 6 地址（0xA8ED84/0xA8ED80/0xA8E9A0/0xA8B238/0xA8EDD8/0xB73550）全部在册（ra2tool.py:33-38 + GOAL 台账表）；≥20Hz 依据（500ms/10ms 环粒度）与实读字节 `push 0x1f4`/`push 0xa` 一致。方案明确标注"未执行"，原报告未把它当结论 |

**总裁决：CONFIRMED**——headline、8 条 keyFact、conflicts 自述均与原始字节/数据独立复算一致；发现的问题全部是**引用行号/下标漂移**（3 处，见 §4），不影响任何数值、分类或判定。

## 2. 证据（复算命令与输出）

- 数据侧（纯离线，~3s）：
  `cd …/P04 && python -I -X utf8 VERIFY_data.py > VERIFY_data_out.txt 2>&1`（exit=0）
  - F1: 23 份 / A9 B14；F2: 15,237 行（battle 216/pre5 45/close 14,813/hold 163）；F3: `{1:15229}`、0 值 0 次
  - F4: 8 个 read_fail 全部 close 段**末行**、exit 全部 natural
  - F5: 可读对 15,206=15,237−23−8（自洽）；Δf==0=11,279 全 (1,1)；Δf>0=3,923 全 (1,1)；Δf<0=4 全 (1,1)；跨 singleton Δf==0=16 全 (1,1) → 11,263
  - F6: 4 个负对 = −3798(085640)/−3613(090813)/−4019(091330)/−5700(192830)
  - F7: 段内 11,263 = menu_idle 8,983 + zeroed 2,280 + RELEVANT **0**；分段明细与报告表逐格一致
  - F8: 严格"活游戏停帧候选" = **0**（我方加严口径）
  - F9: 085640 跌落上下文 close[504..507]（wait=258、hwnd=0、singleton=0、frame 3798→0、tick=1）
  - F10: 各段间隔中位/p10/p90；F11: 7 战斗趟 close 帧率（P0 两趟 31.25/31.08）；F12: 16 菜单趟各段 frame 值集全 [0]、tick 值集全 [1]
- 机制侧（只读 gamemd.exe，~2min）：
  `python -I -X utf8 VERIFY_mech.py > VERIFY_mech_out.txt 2>&1`（exit=0）
  - M1 coverage/sha；M2 0xA8ED80=46 引用/唯一 W 0x7778CE；M3 门控原始字节 `raw[0x55D360:0x55D3A0]=a0a0e9a800…0f84580b0000…a080eda800…7534…68f4010000` + je/jne/环回目标三重重解码；M4 0x55DECF=epilogue（pop×4+`add esp,0x1b4`+ret@0x55DEDB）无 inc；M5 IAT=KERNEL32!Sleep/WINMM!timeGetTime；M6 写者上下文含 `8a1580eda800`(读旧)/`3bd1…0f8482000000`(旧==新跳写)/`a280eda800`(写)；M7 `42`(inc edx)@0x55DE7E + `891584eda800`@0x55DE81；M8 0xA8E9A0=123 引用（头部 1 处）、0xA8B238=570 引用（环内 1 处）
- 补充直查（inline `python -I -X utf8 -c`）：`_e2` 块 14 份扫描→0 个 tick 字段；战斗趟 close 段 hwnd 存活行=7 趟各 1；趟跨度 min 21.5s/max 186.4s；`je` rel32 重解码=+2904→0x55DECF
- 引用核对：`_drive_c2_x_probe_v2.py:70`（G_TICK）、`:649/:675/:718`（sleep 2.0/1.0/0.1）；`_drive_c2_x_e12.py:375-377`（close 采样器 tick 元组）

## 3. 与本仓既有记载的对账

- ✅ `GOAL_THREE_TARGETS_20261018.md:3689`（行号实查无误）：G_FOCUS 0xA8ED80 = 46 引用 / W 1 / R 45、唯一写者 0x7778CE——本会话重扫 46/1 逐位吻合。
- ✅ `XVERIFY_E5_20261030.md:233`（行号实查无误）：0xA8ED80 三重命名混乱定谳、"tick 列读的是焦点旗标，恒值 1=有焦点，不是帧计数器"——P04 沿用该口径正确。
- ✅ `XVERIFY_E5_20261030.md:136`（行号实查无误）：hold_tl tick `{1}` 恒 1——本次扩到全批 15,229/15,229。
- ✅ `DISCIPLINE.md:60-63`：CurrentFrame 唯一定常 inc 0x55DE7E+写回 0x55DE81、焦点旗标唯一写者 0x7778CE、IAT Sleep/timeGetTime——实读吻合。
- ✅ 台账附合：GOAL 同表 G_INGAME=123 引用、G_GAMEMODE=570 引用——我方 M8 实测 123/570 同值。
- ⚠️ P04 自报对**任务给定规则**的冲突（"Δf==0∧tick==1⇒证伪"=假证伪）：我方独立确认 11,263 对中活游戏停帧=0，冲突真实存在且 P04 处理（改判 DATA_INSUFFICIENT 并写明）符合纪律。
- 未发现 P04 与任何台账记载冲突的新事实。

## 4. 诚实账（核验方）

**发现的问题（全部为引用级漂移，不改任何结论）**：
1. `_drive_c2_x_e12.py:467` → 实际 `("tick", V2.G_TICK)` 在 **:377**（:467 是 `if stop:`）。
2. `_drive_c2_x_probe_v2.py` sleep 引用 641/673 → 实际 **649/675**（718 正确）。
3. 清零点 "close[470..473]" → 实际 **close[504..507]**（内容：hwnd=0、singleton=0、frame 3798→0、wait=258、tick=1，与报告描述逐项相同）。
4. 措辞级：结论 3"战斗趟 frame 全速 31fps 推进（含 WM_CLOSE 后整个 watch 段）"对 P0 三趟成立；P1/P2/P3 在 watch 中段被拆除清零后 frame 停 0——P04 在 keyFact 4/§2.3 已如实分开描述，仅该句以偏概全。
5. "P0 臂仅 2 趟"指 P0_ORIG×2；P0N_INJ_OFF（31.26fps）为同族第 3 趟，未计入"P0 臂"——口径可辩，数值无误。

**核验方没做的**：
- 未重验 MainLogicFrame 3-ret 基线的分支图闭包（0x55D877/0x55DEC7 两个冻结出口未逐一溯源）—— incidental 证实了 0x55DEDB ret 存在于早退 epilogue（`VERIFY_mech_out.txt:51`）。P04 同样声明不依赖它。
- 未重验写者 0x7778CE 所在函数=主窗口过程的函数身份定谳（R-063a 基线，我方仅验证了写点字节与沿触发逻辑）。
- 未复核 `_rec.json` mode 字段的产生过程（menu_idle 分类依赖它）；但用 frame 值集自洽性（菜单趟全段 frame==0，战斗趟 battle 段 frame>0）交叉约束了误标风险，且我方 F8 严格口径不依赖 mode。
- P3e_E12_T2 趟无 timeline.json 一事未深究（无数据文件，不影响 23 份口径）。

**可能出错的**：我方第一次手工解码 `je` rel32 时偏移错 1 字节（读 0x55D372 应为 0x55D373）得出 0x612BFB——已当场发现、修正重跑为 +2904→0x55DECF，记录在此以示复算过程的自我纠错。

## 5. 复算入口

```bash
cd D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/P04
python -I -X utf8 VERIFY_data.py > VERIFY_data_out.txt 2>&1   # 数据侧 ~3s
python -I -X utf8 VERIFY_mech.py  > VERIFY_mech_out.txt 2>&1  # 机制侧 ~2min（只读 gamemd.exe）
tasklist | grep -i -E "gamemd|ra2loader|yuri"                  # 期望无匹配
```
