# S16-N1 · 补 S16 的**真实语义名**（超级武器；缺口 8）

## MODEL（派卡登记，Lead r14-s7 写入）
role=exec | provider=magpie-anthropic | model=work/cn:hy4flash-free | reasoning_effort=high | agent=agent-1 | dispatched_at=2026-11-18T12:45 | status=running
note=重派；禁 venv/pip

## 盘上现值（Lead 实测，若与你自己复算不一致按纪律 9 停下报告）
S16：atlas ∩ coverage `n = 90`，`sub_` 残行 **17**，named（PANEL 字面口径）**73**，DoD 门槛 **81** ⇒ 差 **8**。
proved **46/90 = 51.11%** 已过线（门槛 45）⇒ **本卡只补名字，不动 grade。**

## 🔴 硬禁令（本卡成败全在这条）
1. **禁止**产出 `Class::sub_XXXXXXXX` 形式的「类前缀 + 占位」名。审计 a-S16-K2 原话：**该形式全表先例 = 0，不是名字，不得计入 named**。
   上一张卡（S16-K2/K3）就是把 7 条这种占位名当成绩报上去，被判 PARTIAL 的。
2. **禁止**把 `sub_00539EB0` 原样保留却声称「已命名」。
3. **禁止**编名。查不到就交 0 条并列出已试通道（`S15-K5` 先例：交 0 条、如实交差，被记为合格交付）。
4. 每条名字必须 **两条独立通道**，且**各自提供对方给不出的信息**（R14-R17 / 错源 ⑰）：
   - 「镜像内串 + 函数体行为」同属通道 A（同一二进制同一反汇编）⇒ **只算一环**。
   - 合格的异源例：**镜像内 `Msg:`/EVA 键串 + 推动点**（二进制）+ **YRpp 符号或 `Ion.cpp`/`Beacon.CPP` 源文件语义**（源码）；
     或 **RTTI 类名 + vtable 槽号**（二进制）+ **`ArrayClasses.h`/`Ion.CPP` 合同互斥**（源码）。
5. **必须做基线/正负对照**：给出「随便挑同样多条目、用同一判据会误命中的数量」。

## 17 条 sub_ 残行（盘上现值）
`00430BA0` `00539EB0` `0053A0E0` `0053A6C0` `0053AE00` `0053AE50` `0053B410`
`0053D8E0` `0053DDA0` `0065E660` `006CE240` `006CE270` `006CE280` `006CE2C0`
`006CE2D0` `006CE320` `0071AB60`

### 其中 3 条**已被审计认证**，可直接复用（但你必须自己复核字节，不得只引用结论）
- `00539EB0` = `LightningStorm::Start`（审计已确认 `0xA9F9F8/FA` 两读、两次 `call 0x65C7E0`、写 `0xA9F9CC/0xA9FACC`）
- `0053AE00` = `LightningStorm::AnnounceActive`（`mov ecx,0x82809C` = `'Msg:LightningStormActive'` @`0x53AE0C`，体内；→ `call 0x734E60` → `0x5D3BA0`）
- `0053B410` = `PsychicDominator::AnnounceActive`（`'Msg:DominatorActive'@0x8280B8` @`0x53B41C`，体内）
⇒ 这 3 条仍算进本卡 KPI（它们至今**未并入**盘上），但**不得**把它们重复报成 8 条里的新发现；请标 `reused_audited`。

## 剩下 5 条从这 14 条里找（优先级按可证性）
1. `0053A6C0` `0053AE50` `0053A0E0`（`Ion.cpp` 邻域，K2/K3 已给出行为描述但**名不成立**，须换通道）
2. `006CE280` `006CE2C0` `006CE2D0` `006CE240` `006CE270` `006CE320`（`SuperClass` 时间/计时器族；
   注意 `0xA8ED84 = CurrentFrame`，且 `MissionClass::TimeLeft` 在 `+0xD0` 且**不递减**（见 R14_COMMON §8.2））
3. `0065E660` `0071AB60` `0053D8E0` `0053DDA0`（`EVA`/`Msg:` 串推动点优先）
4. `00430BA0`（`Beacon.CPP` 邻域；**注意**：审计已确认它**不在任何 vtable**，`BeaconClass` 无 RTTI 支撑，只有源串提示）

## 可复用通道（R14_COMMON §8 与本项目已验证打法）
① RTTI 数组元素类型反证 + `new size` 与 `GetSize` 双点闭合；② 契约互斥法；③ 镜像内串（INI 键 / EVA / `Msg:` / `%s`）；
④ 标量删除析构形态（带配对基线，全 `.text` 真 dtor 站点基线 = 169）；⑤ YRpp 符号 + 地址注释。
⚠️ `docs\re\*` 只能当线索，结论须本卡重新取证；进结论前先查 `R14_COMMON §1` 作废索引（42+ 条）。

## 交付（绝对路径，只写这里）
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16_N1\`
`PROGRESS.md`(+四列表) / `UNKNOWNS.md` / `DISAGREE.md` / `EVIDENCE\` / `work\`
`coverage_delta.tsv`：8 列 entry, subsystem(S16), name, one_line_semantics, grade, evidence_path, **name_kind**, **reused_audited(Y/N)**
**每完成 2–3 条就增量落盘 PROGRESS.md。**

## 核心数字（给审计员复算）
① 真实语义名新增条数（不含占位、不含 reused）② 每条的两条通道名称与各自提供的信息 ③ 正/负对照误命中数

---
## 🔁 续跑补记（Lead r14-s7，2026-11-18 12:45）
- **上一轮本卡（12:09 派、同卡号）零产出**：只在 `work\venv\` 建了个空 venv（12:10）就停了 ⇒ 判静默失败。
  ⇒ **严禁创建 venv、严禁 pip install**。系统 python 里已有 capstone 5.0.7 + pefile，直接用。
  ⇒ 沿用本卡目录已有的 `work\venv\` **不要管它、也不要往里写**。
- **每完成 2–3 条就增量落盘 PROGRESS.md**；25 分钟内 PROGRESS 无实质内容即判失败。
- 若最终只能交 3 条 `reused_audited`（`00539EB0` / `0053AE00` / `0053B410`）而无新名 ⇒ **如实交 3 条 + 写清已试通道**，仍算合格交付（`S15-K5` 先例）。
