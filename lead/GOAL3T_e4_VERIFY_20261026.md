# GOAL-3T e4 独立核验判定书 · l1_20261023e4（① 环境门趟）

核验时间：2026-10-26 20:43 (+08:00)  模式：纯只读离线复核（零真机、零 git）
唯一写入=本文件。所有哈希/读数均由核验员独立重算，未采信申报值本身。

---

## 0. 身份（异族声明）

**核验员实际 model 身份：`new-provider-3/qoder-cn:qfmodel`（Qoder 会话内核 = qfmodel）。**
被核趟申报「执行者=DeepSeek dfmodel」。qfmodel ≠ dfmodel ⇒ **异族成立**。
本机 `ListModels`/运行时均无法读回子代理真实 model 字符串，故此处以本会话驱动内核署名；
无法进一步证伪「趟执行者= dfmodel」（申报侧身份不在盘内，UNVERIFIABLE，见 E-身份附注）。

---

## E1 原件逐项复算 —— **CONFIRMED**

独立 `sha256`/JSON 重算，全部逐字对上：

| 字段 | 申报 | 实测（重读原件） | 判定 |
|---|---|---|---|
| `_launch_result.json` rc | 0 | 0 | ✓ |
| duration_s | 275.4 | 275.4 | ✓ |
| 残留 / 载体删净 | 0 / 删净 | `leftover_procs=[]`；`ct/` 已空；`carrier_delete_result.json`: deleted=true, residual_exists=false, same_object=true | ✓ |
| gate pre_fps15 | 30.692 | 30.692 | ✓ |
| gate units0 | 702 | 702 | ✓ |
| gate ok | True | True | ✓ |
| W0 fps_avg | 29.44 | 29.441409419151583 | ✓ |
| W0 frame_ms_p50 | 32.62 | 32.62485000232118 | ✓ |
| W0 p90 | 43.14 | 43.14420000082464 | ✓ |
| W0 p99 | 60.96 | 60.9565249971638 | ✓ |
| W0 max | 69.58 | 69.58020000092802 | ✓ |
| W0 logic_frames | 736 | 736 | ✓ |
| W0 tick_miss | 43 | 43 | ✓ |
| W1 logic_frames | -3557 | -3557（note="frame not advancing"） | ✓ |
| W1 max_stall_s | 15.73 | 15.732883 | ✓ |
| W2 logic_frames | 0 | 0（samples=5949 全 f=0） | ✓ |
| W2 max_stall | 11.89 | 11.894575 | ✓ |
| NAV.verdict | OK | "OK"（qc151_fields.json group=NAV） | ✓ |
| MEASURE.verdict | degraded | "degraded"（注记 `w2:empty` 空窗降级） | ✓ |

> 附：申报「>80 ms 占比 0」亦独立复核为真——W0 frame_ms_max=69.58 ms < 80 ms，全窗无样本越 80 ms。

---

## E2 口径三查 —— ① CONFIRMED / ② CONFIRMED（产物，非损坏）/ ③ CONFIRMED

### ① pre_fps15 定义与阈值 25（V11-a 硬门）
读 `lead/goal1_v11_env_gate_20261021/V11_ENV_GATE_DESIGN.md`：
- `:142` 「V11-a（硬门禁）：当趟 `pre_fps15` 必须 **≥ 25**（即落在 31 档）」——口径核实。
- `:148-150` 该字段源自 `qc151_trip.harness3.py:4043-4063`，`MEASURE_GATE_FPS15_MIN = 3.0`（现值仅判「在局」，V11-a 把它提到 25 判「档位」）；31 档实测簇 = 31.397/31.401，10 档簇 = 8.023/9.354/10.012/10.023，25 为干净分界。
- e4 `pre_fps15=30.692 ≥ 25` ⇒ 落 31 档簇，**通过 V11-a**。定义与阈值申报属实。

### ② W1 负 logic_frames：产物 or 损坏？—— 读原始 samples 边缘 ⇒ **采样跨局尾的产物，非损坏**
逐点读 `measure_w1.json` samples（t/f 各 12501 点，无负值、无空洞）：
- f 从 3557 平滑推进到 **3668**（前 ~3.7 s，约 30 fps，节奏正常，112 次真实 +1 边沿）。
- 在相对 t=**9.265 s** 处出现**单次跳变 3668 → 0**，此后 f 恒 0（约 21 s 停帧）。
- `logic_frames = last − first = 0 − 3557 = −3557` ⇒ 负号纯粹是「帧钟在窗内归零（局终/回放重置）」的算术产物，**边沿计数 n_edges=113 正常、无损坏样本**。
- W1 末取证 `measure_forensics_w1`: current_frame=0、focus_ok=true、标题仍 "Yuri's Revenge"。
- W2 全 f=0、末取证 `empty_window=true`、fg="BuddySwitch 整合预览版"（游戏窗已消亡）⇒ W2 = 局已结束的后续窗，零帧合理。
⇒ 与申报「W1/W2 不作性能样本」一致。**注意**：此证据（帧钟→0 + W2 空窗）**强支持「W1 尾=局终」**，但「自然终局」的全盘归因仍属场景/会话线，单趟不足以定谳——见 E2③ 边界。

### ③ 「环境门绿 ≠ 基线已建」是否被遵守
全文扫描 `无卡顿已证明 / 基线已建 / 已建基线 / 证明无卡顿`：台账 §438/§439 与 handoff **均未出现**该表述。
- §438 line 716-718 措辞 = 「31 档可判、**未复现真实卡顿**、不作卡顿判据」——有限表述，未放大。
- §439 line 737 明确降级：「环境门绿**只**支持『本会话 31 档可判 + W0 受测窗 max<80 ms』的有限结论；W1/W2 剔除；自然终局归因**未闭合**」。
- `REVIEW_S438_AND_NEXT.md:9`：「pre_fps15 门绿不等于稳定基线已建，max<80 ms 也不是通用『无卡顿』判据」。
⇒ 边界声明被遵守。**CONFIRMED**。

---

## E3 装置身份 —— **CONFIRMED**

- **harness7 sha16 实测**：`sha256(qc151_trip.harness7.py)[:16] = d019e8beecfb5fd8` ✓（申报 harness-sha16 一致；`_launch_result.json` 记录同值）。文件 472,020 B，与 launcher `KNOWN_HARNESS["d019e8beecfb5fd8"]="harness7（+124−0）"` 注记吻合。
- **发射器未改·--extra-argv 走 argv 透传**：读 `_launch_l1_20261023.py:197-219` + `build_harness_argv:151-180`：
  - `extra_argv=[x for x in _a.extra_argv.split() if x]`，在 `argv += ["--evid-diff","--probe-frames",probe_frames]` **之后** `argv.extend(extra_argv)` ⇒ 尾置透传，不扰动既有段位序。
  - 缺省 `--extra-argv=""` ⇒ `[].split()`=空 ⇒ argv 与改前逐字一致（注释 `:153`「抽成纯函数便于离线实测缺省行为未变」、`:205`「缺省行为一字未变」）。
  - `harness-sha16` 经 `choices=sorted(KNOWN_HARNESS)` **哈希枚举选择**（非任意路径），集合外 argparse 硬停——门禁未放宽。
  - e4 实发 argv（`_launch_result.json`）末两项 = `...,"3900,...,6000","--h7-keep-rect-wait"` ⇒ extra-argv 正确落到探针阶梯之后。
- **载体源=母本 _src_L1_sf8**：argv `--carrier-create-from ..._src_L1_sf8_20261020`；`--target-sha256` = XMP29U2.MAP `0add791d...` = launcher VARIANTS["L1"] map_sha。
- **gamemd 母本 sha16**：`sha256(_src_L1_sf8_20261020/gamemd.exe)[:16] = 73201cc021497c95` ✓（只读断言，申报一致）。趟内 `scene_fixed.gamemd_sha256` 前缀 73201cc0… 一致。

---

## E4 一致性（keep-rect 对照臂预期）—— **CONFIRMED，等待真实发生**

e4 = keep-rect 对照臂 ⇒ 预期 rect 等待发生（polls>0，非短路）。实测：
- `META h7_fs_rect_wait_skipped = false`（ts 19:56:36）——**短路闸未生效**，符合对照臂语义。
  源码核对 `harness7:8072-8101`：仅当 `fs_rect_wait_skipped=true` 才把 `deadline` 重绑 0.0 令母本 `while` 立即跳出；e4=false ⇒ 母本 `while` 谓词 `(rwh)!=(800,600) and now<deadline` 在恒 [0,0,2560,1440] 全屏下每 0.5 s 一轮跑满。
- `FRAME pre_capture_wait_polls = 249`（ts 19:59:28），`pre_capture_rect=[0,0,2560,1440]`（非 800×600，符合全屏恒值）。
- `stage_seconds:frame = 124.781 s` ≈ 249 × 0.5 s = 124.5 s（一致，纯死等被实测计入 frame 阶段）。
- **对照 §423 hc 形态**：hc（keep-rect，10-24 会话）polls=244；10-23 三趟 polls=251/251/253；ha（短路臂）polls=0。e4=249 落在 keep-rect 簇（244–253）内、且**远离**短路臂 0 ⇒ 对照臂身份与「等待发生」双双成立。**无短路闸意外生效的偏差**。

---

## E5 作废账复认（l1_20261023e1）—— **CONFIRMED 作废成立**（gate 读数存在但不可用）

独立读 `l1_20261023e1/measure_w0.json`：
- `gate`: pre_fps15=**5.342**、units0=**0**、ok=**False**（trip ts 19:40:25，早于 e4）。
- `stats`: logic_frames=8、verdict=**no_advance**；fps_avg=2.0、frame_ms_max=3780.8 ms、p99=3520.5 ms（严重卡顿形态）。
- 作废判据复算：units0=0 < 协议 `w1_units0_min=150` ⇒ 场景未 fanout 到位；ok=False ⇒ 窗前在局闸未过；verdict=no_advance ⇒ 帧钟几乎不推进。
- 「是否有档位信息可用」的点名要求：pre_fps15=5.342 **读数存在**，但**不可用作档位**——5.342 既低于 10 档簇下沿（8.023）也远离 31 档簇，且 units0=0/no_advance ⇒ 非任一干净档位，属「未进局 + 掉档」混合退化。
⇒ **e1 作废成立**，不据其档位翻案。申报「短路臂 e1 units0=0/no_advance 作废」准确。

> 附注：§438 line 719 称 e1 为「**短路臂**」——经独立复核**命名正确**：e1 `_launch_result.json` argv **不含** `--h7-keep-rect-wait`（保持母本缺省），其 `qc151_fields` 实测 `h7_fs_rect_wait_skipped=true`（deadline 重绑 0.0）、`pre_capture_wait_polls=0`。对照 e4=keep-rect 臂（含旗标、skipped=false、polls=249）。⇒ 两趟恰成「短路 vs 保持」对照，标签与 E4 源码语义严格对应，无命名越界。e1 harness_sha16 同=d019e8beecfb5fd8。不影响作废结论。

---

## E6 边界声明审读 —— **REFUTED（开机会话身份）** / CONFIRMED（其余）

### (甲) 开机会话身份 —— **REFUTED，日期标签错误（实质偏差）**
申报「本开机会话（**10-25 08:36 起**）31 档可判」。只读实测 `Get-CimInstance Win32_OperatingSystem` + `Get-WinEvent Id=6005`：
- **当前** `LastBootUpTime = 2026-10-26 15:14:25`；事件 6005「日志服务启动」= 2026-10-26 15:14:42。`SystemUpTime` ≈ 19,587–19,720 s（≈5.45 h），与「15:14 开机、现 20:43」自洽。
- 10-25 08:37:14 确有一次 6005（历史开机），但**其后已被 10-26 15:14 的重启取代**。
- e4 趟 ts = 2026-10-26 **19:56–20:01**、e1 ts = 19:40 ⇒ 二者均落在 **10-26 15:14** 会话内，**不在 10-25 08:36 会话**。
⇒ 「本开机会话 = 10-25 08:36」**证伪**。当前有效会话 = **10-26 15:14**。
  - 影响面：**档位读数本身不受损**——pre_fps15=30.692 是在真实当前会话（10-26）内实测，「该会话 31 档可判」的**技术结论仍成立**；错的是**会话身份/日期署名**。
  - 风险：任何把「10-25 08:36 会话」当作跨趟可拼 A/B 锚点的下游主张，会因该会话**已于 10-26 15:14 重启**而**失效**（V11-c：跨会话不可拼）。下游须把 ① 证据锚点改署为「10-26 15:14 会话」。

### (乙) 「单趟读数说成稳定基线」—— **CONFIRMED 未越界**
§439 line 737 已明写「只支持…有限结论」「归因未闭合」，REVIEW:9 重申「门绿 ≠ 基线已建」。申报文本未把 e4 单趟说成稳定基线。边界遵守。

---

## 总判定

**PASS（带一处实质偏差须回登台账）**。
e4 原件 E1 全字段逐项复算**无一不符**；装置身份（harness7=gamemd 母本双 sha、extra-argv 尾置透传、缺省 argv 不变、哈希枚举门禁）E3 **确认**；keep-rect 对照臂语义（polls=249、stage:frame 124.8 s、短路闸未误触、落在 hc 簇 244–253）E4 **确认**；e1 作废（units0=0/5.342/ok=False/no_advance）E5 **确认**；口径三查 E2 **全绿**（W1 负帧差经原始 samples 边缘证实为「帧窗内归零」产物、非损坏；W2 局终空窗；无「无卡顿已证明/基线已建」越界语）。

**唯一须纠正项**：E6(甲) **开机会话身份 REFUTED**——申报「10-25 08:36 起」为**误标**，实为 **10-26 15:14** 会话（10-25 会话已于当日 15:14 被重启覆盖）。
- 这不推翻「当前会话 31 档可判 + W0 受测窗 max<80 ms」的有限结论（读数在当前会话内为真）；
- 但**禁止**把 ① 证据挂到「10-25 08:36」这一已灭会话上，且据 V11-c，10-23/10-24 各 keep-rect 趟（polls 251/251/253/244）**与 e4 非同一会话**，不得跨会话拼作同一档位的重复样本。
- 台账 §438 line 716「本开机会话（10-25 08:36）」**应勘误为「10-26 15:14」**。

### ① 下一步（负载方案）的证据前提清单
1. **先改锚**：① 会话身份统一改署 **10-26 15:14**；在此之前冻结任何「与 10-25/10-23/10-24 同会话可拼」的措辞。
2. **档位单趟**：31 档目前仅 e4 单趟确证（本会话）。若需「本会话 31 档稳健」，须在同会话（不重启）内再取 ≥1 趟 `pre_fps15≥25` 复现；否则按 V11-a 只作「该趟可判」。
3. **战斗覆盖**：申报 W0 受测窗未复现严重停顿，但 W0 仅覆盖 f≈2696→3668 段；真「无卡顿基线」需战斗负载全程覆盖档（台账已列「① 战斗覆盖档择机」为前提）。
4. **W1/W2 剔除**：继续按 §439 不作性能样本；「自然终局」归因须由场景/会话状态线另证，不得由本趟负帧差单独定谳。
5. **e1 不复用**：作废维持；其 5.342/units0=0 读数不进档位账。
6. **身份附注**：如需硬证「趟执行者=dfmodel」，须补盘内可校验的执行者签名件（当前不可读回，UNVERIFIABLE）。

---
摘要：e4 全字段复算与装置/对照臂/作废/口径四查均属实；唯一实质偏差=开机会话误标（实为 10-26 15:14，非 10-25 08:36），31 档读数仍真但锚点须改署，跨会话禁拼。总判定 PASS。
