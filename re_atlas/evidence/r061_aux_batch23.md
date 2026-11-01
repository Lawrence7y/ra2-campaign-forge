# R-061 · 辅任务批次 2/3（G-79 推广 → R-050/051/052 + R-047/048/049）

批次纪律：每批 ≤3 套件（C26-05）。批 1（R-053/054/055）见 `r061_witness_this.md` §6；
本件=批 2+批 3。全部改动仅动**本线现役件**（五套件加 G-79 尾段、r051/r052 补 killer、
r052 门修 attestation 时序）；R-047..R-052 的**旧证据件**（`r047_l20_triggersave.md` 等）
未动。

## 批 2：R-050 / R-051 / R-052

- **R-050**（三套件基线本就全杀）：零 killer=无。W1..W7 实测红集全非空
  （M1..M12 并集覆盖 W1-W7；S1 结构性不入分母、M12 杀之照旧）。加机器 G-79
  尾段 → **12/12 + 覆盖 7/7**（`evidence/r050_mutate_r061.txt`）。
- **R-051**：零 killer=**X7、X8**。X7（esi-writer 集=={0x725FA2}）的根因=
  M1..M12 没有一个动 0x725FA3 的 modrm；X8（imm32 census 8 站）的根因=M3/M4 翻的是
  b9 **opcode**（census 数的是 imm32 字节，opcode 不入账）。补：
  - M13 `{0x725FA3:F9}`（head modrm esi→edi）→ 实测红 {X1,X7}（字节同时落在 X1 的
    5B 头窗内，跨断言足迹照 G-65 实测写死）；
  - M14 `{0x7260BD:E0}`（block3 b9-imm 低字节 e8→e0）→ 实测红 {X2,X8}。
  → **14/14 + 覆盖 8/8**（`evidence/r051_mutate_r061.txt`；before 态
  `out/_r061_r051_mutate_before.txt`）。
- **R-052**：零 killer=**Y2、Y4**；外加**根因级发现**——门的 `fp_ok =
  sha256(bytes(RAW))` 在注入**之后**算，变异跑必 exit 2，rc 通道报废（精确集合计分
  未失真：仍看 stderr FAIL 行，但批 2 首跑 15 例 rc 全 2 才暴露）。修
  `PRISTINE = bytes(RAW)`（加载即冻结），attestation 回到 pristine——修后
  15 例 rc 全 1，与 r047/50/51 同轨。G-84 变体入册。补 killer：
  - M14 `{0x6E53A2:6C}`（head 窗内 `mov al,[0xA8ED6B]` 位移低字节）→ 实测红 {Y2}；
  - M15 `{0x725FC4:C6}`（TriggerClass ctor +0x34 store 89→c6：钉读 894e34 破、
    census c6463400/c6463500 因 modrm 4e≠46/47 保持 []）→ 实测红 {Y4}。
  → 门 **10/10 GREEN**（rc 0）+ **15/15 + 覆盖 10/10**
  （`evidence/r052_gate_r061.txt`、`r052_mutate_r061.txt`）。

## 批 3：R-047 / R-048 /（R-049 判 N/A）

- **R-047**：零 killer=无（M1..M12 红并集已覆盖 T1..T5；S1=RTTI JSON 不可杀、
  结构性档）。加 G-79 尾段 → **12/12 + 覆盖 5/5**（`evidence/r047_mutate_r061.txt`）。
- **R-048**：零 killer=无（V1..V10 全被覆盖；V0=指纹/S1=JSON 双结构性档）。加尾段
  → **13/13 + 覆盖 10/10**（`evidence/r048_mutate_r061.txt`）。
- **R-049**：**N/A——无断言套件可收**（本轮 D-06 异族盲验三回合工作流实录，无
  byte-level gate；G-79 断言→killer 双向对账不适用）。如实登记，不硬造套件。

## 控制（每步实测，非叙述）

- **阳性**：五套件尾段全绿（uncovered=[]），批 2/3 十件 gate/suite 输出落
  `evidence/r0{47,48,50,51,52}_{gate,mutate}_r061.txt`。
- **阴性 1（整件幻影注入，实测红）**：R-047 套件 out/ 副本 COUNTED 扩到 T1..T6 ⇒
  尾段 `COVERAGE RED: ['T6']`、rc=1（`out/_negctl_r047_tail.py` /
  `out/_r061_negctl_r047.txt`）。三件同形尝试被 Mimosa 钩子按已知假阳性类拦下
  （cp 组合+exec 动态编译），未强行绕钩。
- **阴性 2（决策单元隔离验证）**：`out/_negctl_r061_taildecision.py` 把尾段的判定式
  `bool([x for x in COUNTED if x not in killed_union])` 抽出，对五套件的**真实
  counted/killed 集**跑 11 例（5 正+6 负含幻影与缺杀两形态）→ **11/11 OK**。
  与阴性 1 合并 ⇒ 每个尾段都有「能红」证明。
- **attestation 时序全仓分档**：见 CONFLICTS G-84 变体段（r052 修、r053 同序但 rc
  未报废登记、域外 5 件移交）。

## 诚实账

- 批 2/3 的改动面=五个 mutate 套件 + r052 门一处时序；**逆向结论零改动**（各门
  字节断言原样）。12/12、13/13、14/14、15/15、7/7、8/8、10/10、5/5、10/10 全是
  覆盖性数字，不等于 RE 结论成立。
- r051 M13/M14、r052 M14/M15 的红集=实测转录（首稿按字节代数预测 {X1,X7} 与
  {X2,X8} 恰好全中；Y 两例首稿即对——预测对了也要跑，G-82）。
- R-049 N/A 是口径边界，不是「已核验」。
