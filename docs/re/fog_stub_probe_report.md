# FOG-PROBE · 混色桩「读取值」遥测探针交付报告（只加仪表 / 零行为改动）

[META]
- task=FOG-PROBE  executor=DSH 子代理（parent session-852a2193-…）  mode=accept-edits  elapsed≈2h
- scope=ra2render/**、ra2youli/ra2render.{dll,ini}、docs/re/fog_stub_probe_report.md、out/re_work/fog_probe/**
- 基线（只读）：ra2youli/gamemd.exe MD5 4F37486E5B0DBE2AE5F45AEEE0F98367（自始至终未变）
- 旧件：ra2render.dll 145,408 B / D2629BC5E0361624573C7550F69B58AB（备份见 [5]）
- 新件：ra2render.dll 148,992 B / **EAAA1BE95BE88BCC67F58A2AFD1A42C9**（ra2render/ 与 ra2youli/ 两份一致）
- ★未启动游戏、未注入、未改 exe/任何 .mix/.map/.sav、未改任何 ini 键与默认值。

[0] 结论摘要
1. F1 探针已装且**只读**：B1/B2 桩内取「桩实际读到的 16 位强度值」，写环形缓冲（8 槽）+ 8 桶计数 + 失配计数
   + 窗口内变化计数 + 窗口外读取计数；C 侧另记【本格强度】/【store 写入值】/【期望桩读值】/渐变相分布。
2. F3 零行为改动**已机器证明**（四路证据，见附录 B）：桩体旧指令 53/53 按序全匹配 + 穷举 786,432 组失配 0
   + 热路径切片 2,000 组合失配 0 + 探针全局非干扰扫描通过 + 既有挂钩常量多重集完全一致。
3. F2 遥测：新增 3 行（fogprobe 主行 / fogprobe 分桶行 / fogprobe-ramp 行），既有行字段与顺序零变化；
   行长最大 762 字节（< LogMessage 1024 缓冲，无截断风险）。
4. F4 已构建 + 部署；旧 DLL 已备份；两份 ini 逐字节一致且未改动任何键。
5. ★静态复算已**缩小并指向唯一判据**：数值档 scale=156 下，读到 39 ⇔ 本格强度=64（渐变相 (5−ramp)×64）——
   即 F5 只需真机确认【桩读取强度值】与【本格强度】两列；最大风险 = 真机一轮未跑前不得宣称 H-渐变相已定谳。

[1] 逐条必答项结论表
| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|---|
| F1 | 桩内读取值探针（环形缓冲/分桶/失配/相状态） | **已装**：B1/B2 桩内首读采样；缓冲 8 槽；8 桶；失配 = 【store 写入值】≠【桩读取强度值】；相状态 = 渐变相分布 + 【本格强度】精确值命中 | [实证] | 产物 0x40281A / 0x4029AA〔**勘误 2026-09-29**：原记 `0x40299A` 系笔误（MiMo 独立复核 + Lead 二进制复算）〕；源码 blitter_hooks.cpp:1924-2016（B1 探针块）/ 2069+（B2 探针块）；C 侧探针语句 1793-1846；遥测行 761/770/789 |
| F1 | 是否改变算术/时序/写入顺序/像素 | **否**（机器可证） | [实证] | 附录 B-1/B-2/B-3/B-4 |
| F2 | 遥测字段与口径 | 新增 3 行；字段名显式区分【桩读取强度值】与【store 写入值】；既有行零变化 | [实证] | 附录 A 字段表；源码 2 处 LogMessage |
| F3 | 穷举等价 ≥65,536×6 | **786,432 组失配 0**（更强：像素+8 寄存器+出口全等） | [实证] | stub_equiv_786432.txt |
| F3 | 桩算术指令序列一致 | 旧 53 条**符号归一化后按序 53/53 全匹配**；新增 54 条全为探针 | [实证] | prod_diff_run.txt §[2] |
| F3 | auto 直跳 / 共用 store / 恢复语句 | **语义未变**：单站点、同址、写值与顺序一致（指令编码因寄存器分配不同，见 [3]-2） | [实证] | 附录 B-2；hotpath_equiv_out.txt |
| F3 | 既有挂钩点未变 | **全未变**：65 个引擎地址常量多重集一致（含 0x4801F0/0x6F8DF0/0x655D38/0x655D87/0x65719A） | [实证] | prod_diff_run.txt §[5] |
| F4 | 构建/部署/备份/ini | 已构建 148,992 B 新件、部署 ra2youli/、旧件备份、两份 ini 逐字节一致 | [实证] | [5] 哈希表 |
| F5 | 真机判据 | 见附录 C（一轮单局、两档） | [待实测] | 附录 C |

[2] 关键证据块（VA = 0x400000 + RVA；完整 60 条见 out/re_work/fog_probe/claims_fog_probe.txt，audit 全 OK）
1. **探针读取点（B1/B2 同址）**：0x40281A = 0F B7 1D 6C 40 02 10（movzx ebx,[0x1002406C]）；0x4029AA 同〔**勘误 2026-09-29**：原记 `0x40299A` 系笔误 —— 实测 RVA `0x29AA` 处才是该 7 字节模式，全 DLL 恰 **2 处**（= B1/B2 两桩）；Lead 复算确认〕。
2. **共用 store**：0x4026F8 = 66 89 15 6C 40 02 10（mov [0x1002406C], dx）；**恢复**：0x402740 = 66 89 1D 6C 40 02 10（bx=0x100）。
3. **auto 直跳**：0x4026CC = 66 3B FB（cmp di,bx=256）→ 0x4026CF = 75 05（jne 数值档）→ 0x4026D1 = 0F B7 C2（movzx eax,dx）→ 0x4026D4 = EB 22（jmp store）。
4. **数值档算式**：0x4026D6 = 0F B7 C7（movzx eax,di=scale）→ 0x4026D9 = 0F AF C2（imul eax,edx=本格强度）→ 0x4026DC = C1 E8 08 → 0x4026EC = 0F 47 C1（cmova eax,ecx=511 护栏）。
5. **探针热路径**：0x402823 = 66 3B 1D 70 40 02 10（cmp bx,[s_probeWindowValue]）→ 0x40282A = 0F 84 CD 00 00 00（je 探针出口）⇒ 每像素仅多 2 条指令、零寄存器改动。
6. **失配计数比较点**：B1 内 cmp bx,[s_probeWriteValue]（0x1002406C 的 store 值）→ 不等则 inc [s_probeMismatch]。
7. **环形缓冲写入**：B1 0x402887 = 66 89 1C 4D 10 4B 2E 10（mov [ecx*2 + s_probeRing], bx）。
8. **桩算术（探针之后的原指令，逐字节同旧件）**：D1 E9（shr ecx,1）/ 81 E1 EF 7B 00 00（and ecx,0x7BEF）/ 66 2B D1（sub dx,cx）/ 0F AF C3（imul eax,ebx）/ C1 E8 08 / 66 89 08（mov [eax],cx）/ B9 40 F4 47 00（mov ecx,0x47F440）/ FF E1。
9. **.data 位移（勘误相关）**：s_fogBlendStrength 旧 0x1002306C → 新 **0x1002406C**；s_fogMasterGate 0x1002403B；scale 0x10024058。

[3] 勘误（逐条：改前 → 改后）
1. docs/re/fog_cal3_rootcause.md §[2] 第 1/3/5 条与 §附录 A：地址 0x1002306C 等**只对旧件成立**；本卡改动使 .data 整体位移
   （旧 0x1002306C → 新 0x1002406C）。性质：**仪器引入的布局位移**，不是语义改动。影响面：仅新件地址标注；结论不变。
2. 同上 §[1]-F1「共用 store」措辞：旧件 store 编码 66 A3 6C 30 02 10（mov [moffs],ax），新件为 66 89 15 6C 40 02 10（mov [moffs],dx）；
   恢复旧件 66 89 35（si）→ 新件 66 89 1D（bx）。**语义等价（同址、同值、同序），字节不同**；属编译器寄存器分配差异。
3. 热路径「逐指令一致」这一严格口径在新件上**不成立**：MSVC 对本函数做了整体寄存器重排（esi/edx/ebx/edi/ecx 互换）。
   本卡以**切片级状态等价**（2,000 组合，store/恢复/写点数/esp/Token 写全等）替代该口径，见附录 B-2。
4. docs/re/fog_strength_calibration.md 附录 D-① 判据状态：仍为「已测、未达成」（0.68 vs 0.50），本卡不改设计值，只补探针。

[4] 未闭环清单
| # | 缺口 | 为何无法静态闭环 | 下一步取证 | 级别 |
|---|---|---|---|---|
| 1 | 数值档「桩读取强度值」实测值（156 vs ≈39） | 需真机运行期取值 | 附录 C P1（一轮单局读 [ra2render-telemetry-fogprobe] 行） | **P0** |
| 2 | auto 档像素「逐位置不变」的真机对拍 | 静态只到「等价论证 + 穷举/切片等价」 | 附录 C P2（auto 档截图 vs 旧件基线逐像素比值） | P1 |
| 3 | 探针的常数成本（每像素 +2 条指令）对帧率的影响 | 需真机 perflog | 与本探针同轮顺手跑 U200/U800（非本卡范围） | P2 |

[5] 写作用域合规声明
- 改动文件：ra2render/blitter_hooks.cpp（177,420 B / D6524A701E43FABA624B5D2260F7E966，2,771 行，20:09:04）；
  ra2render/ra2render.dll 与 ra2youli/ra2render.dll（148,992 B / EAAA1BE95BE88BCC67F58A2AFD1A42C9，20:09:06，两份一致）；
  新建 docs/re/fog_stub_probe_report.md、out/re_work/fog_probe/**（脚本 6 + 证据 9 + 备份 3 + mapbuild/）。
- 未触碰：gamemd.exe（MD5 4F37486E5B0DBE2AE5F45AEEE0F98367 全程未变）、任何 .mix/.map/.sav、ra2forge/**、mcp/**、ra2opt/**、
  台账 REVERSE_ENGINEERING_AND_PATCHES.md、docs/RE_COORDINATION.md、其他 docs（含 fog_cal3/fog_strength_calibration 等——勘误只写在本报告 [3]）。
- 两份 ra2render.ini 逐字节一致且与改动前一致：4E086B357488DC95FA264B5ECCF0B6D7（ra2render/ 与 ra2youli/ 各一份）。
- build.bat 的 loader 部署保持可选（未设 RA2RENDER_DEPLOY_LOADER ⇒ 未部署 ra2loader.exe）。

[6] 门禁实跑输出（原文，全文见 out/re_work/fog_probe/gate_*.txt）
    C:\> python -X utf8 tools\verify_anchors.py
      回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
      ★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
    C:\> python -X utf8 tools\audit_bytes.py out\re_work\fog_probe\claims_fog_probe.txt --exe ra2youli\ra2render.dll
      合计 60 条：OK=60  MISMATCH/NOREAD=0

[7] 风险与红线提示
- ①同步语义/命令序：**未触及**（探针只读内存 + 自增我方计数；不写任何引擎状态）。②随机数消费序：**未触及**。③存档结构：**未触及**。
- ④渲染像素等价性：**触及（分析层面成立，真机未验）**——本卡未改任何算术/时序，且已穷举 786,432 组 + 切片 2,000 组证明等价；
  但按纪律**不得**在真机对拍前宣称「零风险/零 Desync」。本件为**常开诊断件**，定谳后应撤除或转键控。
- 联机：探针不改命令序与随机数；但常开仪表的每像素 +2 指令成本在联机大厅无影响（渲染侧）。仍未做 MP 门控矩阵。

[8] 交付物清单
- 新文档：docs/re/fog_stub_probe_report.md（本文件，≤150 行）；out/re_work/fog_probe/FINDINGS.md（42 行）
- 脚本 6：stub_emu.py（x86 迷你解释器）、stub_equiv.py（穷举等价）、prod_diff.py（产物级对照 + 非干扰扫描）、
  hotpath_equiv.py（热路径切片状态等价）、probe_dryrun.py（探针干跑自检）、mkclaims.py（claims 生成）
- 断言 60 条：out/re_work/fog_probe/claims_fog_probe.txt（audit 60/60 OK）
- 证据：stub_equiv_786432.txt、prod_diff_run.txt / prod_diff_out.txt、hotpath_equiv_out.txt、probe_dryrun_out.txt、
  gate_verify_anchors.txt、gate_audit_dll.txt；备份：ra2render.dll.before、blitter_hooks.cpp.before、ra2render.ini.before（×2）
- 符号基准：out/re_work/fog_probe/mapbuild/ra2render.map（/MAP 构建产物与部署件仅差 2 字节时间戳 ⇒ 可作符号真源）

[9] 待裁决项（需 Lead/人决定）
1. **是否批准真机 P1（附附录 C）**：建议在下一轮 ZCode 单局中顺带执行（零额外成本，只需读一行日志）。不批则 F3 根因永久停在 [推演]。
2. **探针去留**：本件常开。建议 P1 有结论后再决定 A) 撤除 B) 转 FogProbe=1 键控（需新增键，故本卡未做）。
3. **数值档语义**：若 P1 判为 H-渐变相，方案 A2（强度相依赖解耦）会改动渐变档像素 ⇒ 需 Lead 决定是否接受渐变形状变化。

## 附录 A · 探针字段口径（防反向歧义；遥测行原文格式）
| 字段 | 口径（严格定义） |
|---|---|
| 采样窗口(store->call->restore) | 格绘制窗口数 = 「写 s_fogBlendStrength」→「call 0x47F250 逐像素」→「恢复 256」整段被执行次数 |
| 有桩读取的窗口 | 上述窗口中桩至少读到 1 次的窗口数（覆盖率；两者之差 = 无读取窗口） |
| 窗口外桩读取 | 桩在**非**我方窗口内被读取的次数（证明是否存在引擎自身的调用者；本卡真机前未知） |
| 最近窗口样本: 本格强度 / store写入值 / 期望桩读值 / 桩读取强度值 | 最近一个窗口的四个量：本格强度 = 写入前的原始 strength；store 写入值 = store 后回读同一全局；期望桩读值 = (本格强度×scale)>>8 钳 511（C 侧模型）；桩读取强度值 = 桩内 movzx ebx,[全局] 的首读 |
| 桩读取强度值==期望桩读值 / != | 窗口首读值与模型期望值相等/不等的窗口数（判定 A 的两面） |
| 失配(store写入值!=桩读取强度值)窗口数 | **本卡要求的失配计数**：同窗口内「我方向全局写入的值」与「桩读到的值」不一致的窗口数 |
| 窗口内桩读取值变化次数 | 同一窗口内，桩的后续读取与**本窗口首读**不一致的读取次数（=0 ⇒ 窗口内全局恒定） |
| 分桶三列 | 桶界 0 / 1-8 / 9-48 / 49-128 / 129-200 / 201-255 / 256 / >256，分别统计【期望桩读值】/【store 写入值】/【桩读取强度值】(窗口口径) |
| 环形缓冲 | 最近 8 个窗口的【桩读取强度值】；**槽位序** i ↔ 窗口 k≡i (mod 8)，同时打印写指针 idx，最新窗口 = 槽 (idx-1) mod 8 |
| 【本格强度】命中 | 精确值 0/48/64/96/128/144/192/256/其它 的窗口数（渐变档 = ramp×48 或 (5−ramp)×64） |
| 渐变相 s_fogRampFrame 分布 | 非渐变 / ramp=1..4 的窗口数 |

## 附录 B · 零行为改动证明（四路）
**B-1 桩体结构等价（产物级）**：以「命中点符号归类」把两版指令归一化（GATE/STRENGTH/HITS/PROBE/引擎常量/分支目标）后，
  旧件 B1/B2 各 53 条指令在新件中**按序逐条全匹配 53/53**；新增片段各 54 条，内容全部为：(a) 探针全局的 cmp/inc/mov、
  (b) 探针本地跳转、(c) push/pop ecx（成对保护）。⇒ 桩的算术/落像素/出口**一位未改**（prod_diff_run.txt §[2]）。
**B-2 热路径切片状态等价**：对 2,000 组输入状态（cellIdx × inVision × ramp × fade × gate × scale × token 命中）逐条执行
  两版真实机器码（切片 = 强度选择 → store → call 0x47F250 → 恢复 256），比较【store 写入值】/恢复值/写点数/出口类型/esp/
  去重 Token 写：**失配 0**；且实测 store 值 = 本格强度（auto）或 (本格强度×scale)>>8（数值档）逐档吻合（hotpath_equiv_out.txt）。
**B-3 穷举等价**：2 桩 × 6 强度档（0/39/64/156/256/511）× 全色域 65,536 = **786,432 组**，逐条执行真实机器码，比较落像素值、
  8 个通用寄存器终态、出口目标：**失配 0**（stub_equiv_786432.txt）。旧件侧 53 条指令源 = out/re_work/fog_probe/ra2render.dll.before。
**B-4 非干扰 + 挂钩零改动**：19 个 s_probe* 全局的全部 .text 引用点只位于 3 个探针区（B1/B2 桩、Hook_CellClass_Draw 热路径、
  CheckTelemetry 打印）⇒ 既有代码路径**看不见**探针状态；s_fogBlendStrength 写点在两版均为 **2 处**（store + 恢复，无新增写者）；
  引擎地址常量多重集 65/65 一致（prod_diff_run.txt §[3][4][5]）。

## 附录 C · 给 ZCode 的真机判据（一轮单局即可定谳）
前置：本件已部署（ra2youli/ra2render.dll EAAA1BE9…）；日志 ra2render.log。战役进局玩 1–2 分钟，分别取两档，各读一次行：
    [ra2render-telemetry-fogprobe] FogStrengthPct=… | 采样窗口… | 最近窗口样本: 本格强度=…, store写入值=…, 期望桩读值=…, 桩读取强度值=… | …
    [ra2render-telemetry-fogprobe-ramp] 【本格强度】命中: 0=…, 48=…, 64=…, …, 256=… | 渐变相 s_fogRampFrame 分布: …
- 档位 1：FogOfWar/FogStrengthPct=50（期望桩读值应为 156）
  · P1-a【判 H-渐变相成立】桩读取强度值 ≈ 39（桶落 9-48）且【本格强度】以 64 为主 ⇒ 数值档进了渐变相 ⇒ 修法走 A2
    （让数值档不进渐变相 / 或相内也按 store 值读；两者都会改渐变档像素，需 Lead 批准）。
  · P1-b【判矛盾在桩之外】store 写入值 = 桩读取强度值 = 156（且 ==期望桩读值 数 ≈ 采样窗口数）⇒ 回传整行字段再定。
  · P1-c【判写后读前被改】store 写入值 = 156 且 桩读取强度值 ≈ 39 且【本格强度】= 256 且 失配 > 0 ⇒ 走 A1（写后回读校验）。
- 档位 2（对照）：FogStrengthPct=auto ⇒ 应为【本格强度】=256、【桩读取强度值】=256、预测净保留 ≈0.359375。
  若 auto 档出现 桩读取强度值 ≠ 期望桩读值 ⇒ 仪器/装载有问题，请连同 采样窗口 / 窗口外桩读取 两栏一并回传。
- 判据自检（无需真机即可复核）：out/re_work/fog_probe/probe_dryrun_out.txt 给出 A–G 七种场景下该行将打印的字段值，
  与本附录三类结论一一对应（场景 C ↔ P1-a、场景 B ↔ P1-b、场景 D ↔ P1-c）。
