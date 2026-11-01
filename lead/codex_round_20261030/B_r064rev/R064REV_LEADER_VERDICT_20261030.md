# R-064 独立验收判定书（Leader 续办 B 线中间证据 · 2026-10-30）

- **性质**：B 线工作流（`dwfrun-be5d1896`）被用户主动停止于「汇总」阶段之前，**未产出其判定书**；
  但其 6 支**自写全新实现**探针 + R-062 门禁/变异复跑的**原始证据已全部落盘**。
  本书 = Leader 依该盘面证据**独立逐字节复算后**对 R-064 裁定的验收，**非**采信 B 线转录。
- **身份自验**：Leader 亲跑 gamemd.exe sha256=`73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`（命中）；
  `brev_a` 自报同值，[decode] 全 .text 反汇编 insns=1,394,120、E8 头 6,719。
- **B 线「非空 stderr」定性**：brev_a/b/c/d/e、probe2–7 的 `.err` **仅为 `/usr/bin/time` 的 real/user/sys 计时行**，非错误栈 ⇒ 六支探针全部真跑成（a=1m22s 全表扫描、e=46s、mutate=64m46s 全量）。

---

## 逐条判定（Leader 亲读字节，capstone 独立反汇编）

### 问题 2a — 盘上字节：**CONFIRMED**
Leader 独立读 8 字节窗（与 B 线 `brev_a` 逐位相同，10/10 MATCH）：
- 0x5256F0 复位体三 stamp：`5256F8 c706 f4a57e00`=mov[esi],0x7EA5F4 ✓ /
  `52571E c7460c 041b7e00`=mov[esi+0xC],0x7E1B04 ✓ /
  `525760`&`52578D c700 0c1b7e00`=mov[eax],0x7E1B0C ✓（lea eax 分别 = [esi+0x1C]@52575B、[esi+0x10]@525788）。
- 帧 A/B/F 的 witness 落格：A-GL@0x7787C0、A-List@0x7787D1、A-INI@W@0x7787F7 … 全部逐位吻合。
⇒ R-062 三窗字节、R-064 补 stamp、R-063b 三处 c7 直写、T16@0x5D761D **均为真**（与 R-064 一致，无新字节红项）。

### 问题 2b — 物理槽配对「错位恒 0xC」：**CONFIRMED，且 B 线给出更强的机制解释（对 R-064 措辞的一处精化）**
- B 线 F1/E1（Leader 亲验 9 处 witness 落格字节复算 D/P/W）：witness 传参 lea 的物理槽 W（帧 A/B/C=−0x98、D/E/T16=−0xac、F=−0xb8）落 **INIClass vptr stamp**（rel=this+0x0）；
  0x7E1B04(GenericList)/0x7E1AFC(List<INISection*>) 落格 **rel(this)=+0xC**。
- **第三种读法（B 线独立发现，我判定成立）**：`+0xC` 不是「杂散错位」——它正是 `0x5256F0` 体内 `mov [esi+0xC],0x7E1B04` 的 **INIClass 内嵌 GenericList 成员偏移**。
  即帧 A 把「INIClass 主对象(this)」与「this+0xC(其内嵌子对象)」两个 vptr 都写进栈，witness 传的是主对象。
- **⇒ 对 R-064 的影响**：R-064「配对命题 REFUTED / witness 格实为 INIClass 栈件」**维持成立**（witness≠GenericList，见问题 4）；
  但 R-064 §裁定 里「GL stamp 与 witness 槽错位恒 0xC ⇒ 配对判据不成立」这句的**「无配对/杂散」语气过强**：0xC 错位本身 = 被传对象的合法内嵌成员偏移，是**有结构的构造序列**。
  记为**精化（refinement）**，非推翻 R-064 主判；不改 R-062 冻结字节断言。

### 问题 1 — esp-D 归一化 + HYPV 依赖性：**CONFIRMED（归一化稳健，不依赖假设）**
- B 线 E2 网格（帧 D 承重假设=两处间接 call 的 ret-imm，扫 c1∈{0,4,8,C}×u∈{None,0,4,8}）：
  **仅** (c1=4,u∈{None,8}) 时「7/7 闭合 ∧ W 命中 INIClass=7」；其余 14 组 **W 命中 INIClass=0**（要么剪枝、要么错格）。
  ⇒ 归一化结论「帧 D 7 行 = INIClass」对 c1 **敏感**（须 c1=4），B 线如实标注承重假设——与 R-064「含 HYPV 依赖性实验」自认一致；
  **未翻转** R-064 的 17/17，但把它**降级为**「14 行无间接假设恒等（E2b：A3/B1/C1/E1/F3/T16-1 全 STRICT 闭合、GenericList 命中 0）+ 帧 D 7 行条件成立(c1=4)」。
  这是 HYPV 真翻转风险的实证——**支持 R-064 把 HYPV 单列的谨慎**，非红项。

### 问题 3 — RTTI 双链 + 组合非继承：**CONFIRMED**
- B 线 F2 + Leader 亲读 CHD numBases（dword@+8）：`List<INISection*>` CHD@0x7FAC10 **numBases=2**，基类数组含 TD 0x817508 '.?AVGenericList@@'（mdisp=1）；
  `GenericList` CHD@0x7FAD08 **numBases=1**（R-064 §38 一致）。
  ⇒ **修正一处**：R-064 §38 写 GenericList 家族 CHD `numBases=1（基类数组仅 GenericList 自身）`——此为 GenericList 本身 ✓；
  B 线另算的 `List<INISection*>` numBases=2（含 GenericList 基）与 R-064 §160「+0x1C/+0x10 = List<INISection*> 节点头」自洽 ⇒ 组合关系（INIClass ⊃ GenericList 成员 + List<INISection*> 派生自 GenericList）**各自为真、非互斥**，无红项。

### 问题 4 — 勘误链 E1–E6 是否越界：**CONFIRMED（零字节改动属实）**
- B 线复跑 R-062 **门禁 126/126 PASS**（`gate_r062_126.txt`，30.8s）+ **变异 112/112 exact-killed**（`mutate_r062_112.txt`，64m46s 全量非抽样，phantom/uncovered=0）。
  ⇒ R-062 冻结口径（126 门禁/112 断言/字节断言）**确实未被动摇**；R-064 被推翻的只是「GenericList 栈件」**定名与配对解释**，非字节本体——与 §R-064「影响与不变」逐字相符。
- E3「门禁不触码保 611ca4d4 冻结哈希」：Leader 本轮未重算该门禁件哈希（他线写域），但 B 线以**同门禁跑出 126/126** 间接证其未改 ⇒ **登记为已复核（间接）**，直接哈希复算留 RE-ATLAS 线自证。

---

## 红项 / 精化清单（供 Leader 入账）
1. **[精化·非推翻]** R-064 裁定句「GL stamp 与 witness 槽错位恒 0xC ⇒ 配对判据不成立」中**「无配对/杂散」语气过强**：
   0xC = 被传 INIClass 对象**自身内嵌 GenericList 成员偏移**（0x52571E `mov[esi+0xC],0x7E1B04` 为字节铁证）。
   witness≠GenericList（R-062 §2 五行配对仍 REFUTED），但落格**有结构**、非噪声。→ 建议 R-064 §裁定 追加此注，不改冻结件。
2. **[降级·加严]** R-064「17/17 witness=INIClass」应分层：**14 行 STRICT 恒等闭合 + 帧 D 7 行依赖 c1=4 假设**（E2 网格实证翻转风险）。
   当前写法把两者并计 17/17，掩盖了帧 D 的 HYPV 承重——与 R-064 自设的 HYPV 实验**方向一致但计数表述可再精确**。
3. **[待议·不采信]** brev_g–k（见证宿主偏移、帧 A −0x8C 取址者、帧 F 线外块 0x778B40 解码错位）为 B 线**未收口的中间探针**；
   brev_k 显示帧 F 边界处 capstone 线性解码错位（`mov ebx,0x4c8d0003` 明显为字节流错位）——与 R-064 E6「帧 F 0x778A20 线外块」同一难点，**B 线未据此下结论**，Leader 判 UNVERIFIED，不作红项。

## 未验项（如实）
- 611ca4d4 门禁件本身 sha256 未由 Leader 本轮重算（他线写域，间接证）。
- `brev_a` 的 (c) 判据可互换性「17 行里同字面 disp 的 store 恰也在同物理槽=0」——Leader 抽验帧 A/B/F 三行的 W 落格字节复算**与 0 计数相符**，未逐行扩验其余 14 行（B 线全 17 行已列，未见反例）。
- 本书是 Leader 单上下文验收；异族（不同模型家族）复算 R-064 仍**未派**（§R-064 诚实账自认「单甄别员同族」）。→ 列下一动作。

## 总判
R-064 定名仲裁 **验收 PASS（定谳·静态范围）**：esp 归一化可独立复现、物理槽配对 0xC 为真、RTTI 双链组合非继承为真、E1–E6 零字节越界属实；
附 1 项精化（0xC=内嵌成员偏移，非杂散）、1 项计数加严（17/17 应分层为 14 恒等 + 帧 D 依赖 c1=4）、1 项待议（帧 F 解码）。
**不改 R-062 冻结口径、不动 R-064 冻结件**；「实例归属 UNKNOWN」保持。异族复算仍缺，登记下一动作。
