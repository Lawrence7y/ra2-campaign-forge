# C08 · DISAGREE（口径差异 / 无事实冲突）

## 1. 与 C05/C06 口径的差异：通用模板包装器优先归 S22（有意修正，非事实冲突）
- C05/C06 的 `classify.py` 把 `T_VectorClass_<T>` / `T_DynamicVectorClass_<T>` / `TClassFactory<T>` 等泛型模板类按「字符串包含元素/实例类型名」判为对应子系统的 core（计入 high）。C06 `UNKNOWNS.md` §4 已明确标注这是「固有偏差」并建议 P1 统一修正为「前缀优先归 S22」。
- 本卡（C08）实现该修正：`work/classify.py` 的 `GENERIC_WRAPPERS = [TClassFactory, VectorClass, DynamicVectorClass, DiscreteDistributionClass, DistributionObject]` 先于 core 规则识别，一律归 S22 core=False（grade `[未证]`、conf `med`）。实证依据：`TClassFactory<V*>` 的 slot0 在 T=Tactical/Cell/EMPulse 下**MD5 完全相同**（generic 工厂基础设施），按嵌入 T 判 core high 属分级虚高，违反本卡纪律「分级不得虚高」。
- 后果：本片 284 个 TClassFactory 工厂方法 + 若干模板容器从 core high 改判 S22 med；S06/S13/S19 的 high 归 0（这三族在本片仅有泛型工厂虚表，无 core 类直接命中）。high 总数 = 408（self_known 101 + vtable-core 307），与 C05(563)/C06(382) 的差异由本片类族结构 + 此修正共同所致。
- **这不是数据矛盾**：C05/C06 交付产物不改，本卡只在自己的写域内采用更严格（且被 C06 建议）的口径；审计按本卡 `classification_trace.tsv` 的 conf 列复算即可自洽。

## 2. 与 C04 旧口径的差异：atlas 空洞三通道（按 Lead R14-R1 统一裁定执行）
- C04 的 `atlas_gaps.tsv` 只收 rel32（E8+E9）；本卡按 Lead R14-R1 三通道分列 call32(E8)/jmp32(E9)/jmp8(EB)，每行格式 `address TAB chan TAB first_insn TAB referencing_sites TAB note`。
- 本片三数 call32=2 / jmp32=2 / jmp8=37（41 行 / 41 独立地址 / 疑似真入口 3）。若按 C04「仅 rel32」旧口径会得 4（call32 2 + jmp32 2）；按 C05/C06「call32 + 非分支 jmp32」亦得 4。本卡以 **R14-R1 严格判据**（align16 + prev∈{nop,ret,jmp} + 首指令非分支标签）取 **3**，排除 `0x6CA204`（align16=0、prev=other、洞内分支标签）。这是口径统一 + 判据从严，不是数据矛盾。
- 三通道均满足纪律 #1：通道 B（`sweep_independent.py`）自写 struct PE + capstone `skipdata=True` 按操作码字节分目标，不依赖 function_atlas.tsv 的 entry+size；站点归属用「函数区间包含」`owner()`，已抽检 `owner(0x482854)=None`。

## 3. 虚表槽数不用 vtables_v2.json 的 slots（按坑 (a) 独立定界）
- `vtables_v2.json` 全镜像槽数和 13,351；本卡自写 RTTI 通道 `rtti_independent.py`（COL→TypeDescriptor→vftable，槽数=从 slot0 起连续 .text 代码指针数）实测 **14,044**，差 +693；delta 分布 `{1:794, 0:327, -1:85, -2:8}` 与 C03 审计 `a3_out.json` 完全一致。
- 后果：本片 683 个函数有 vtable 命中（真实槽），比盲信 v2.json 多覆盖被丢的末槽函数。未直接引用 v2.json 的 `slots` 作判定。

## 4. 与既有事实底座无冲突
- 本片地址 0x6BF750–0x719F29 覆盖的类族（S16 超级武器 SuperClass、S05/S10/S12 对象模型、S15 TAction/Tag、S14 Team/TaskForce、S17 Swizzle、S07 Tactical/DirtyArea、S11 TeleportLocomotion）与 `R14_COMMON.md` §1–§7、台账 §911–§928 无口径冲突。
- 写卡前已 grep 台账 `GOAL_THREE_TARGETS_20261018.md`：台账 §923–§928 的具名地址（矿石价值 0x485020、Blitter/绘制链 0x5F4B10/0x5F4D30/0x5F5F40、DLC 0x52CB90 等）均落在 C05/C06 片，本卡未触碰、未推翻任何 `[已证]`。本片内台账唯一直接命中的是 `0x006E8000`（§877-2/§877-6 记为「不在函数图谱内、未验」的 AbstractClass 数组零引用候选），本卡独立扫到它是 call32 洞目标（align16 + prev=nop + 序言形态），仅列入「疑似真入口」，**与台账「未验」一致，不新增 [已证]**。其余本片地址未见台账落点。
- 本卡未写任何新 `[已证]` 发现，未改 `R14_COMMON.md` / 台账 / `COVERAGE\coverage.tsv`。

## 5. 未与 Lead 裁决口径 disagreement 的项目
- capstone `skipdata=True`（全 .text 解出 1,394,120 条，与 C05/C06 一致）；`boundary_check` 超 max_bytes 的「未判定」保留 None 不当 False（R14 §6-3），已落实。
- 双通道不独立源：通道 A=atlas entry+size（切片/owner），通道 B=自写 struct PE 的 RTTI + 字节扫；第三通道 `verify_core.py` 用 pefile + `op_str` 解析独立复核，核心数字全 match。
- 未用 Ghidra（并发 ≤4 留给别卡）；未改 gamemd.exe / ddraw.dll / ra2youli\；未 git commit/push。
