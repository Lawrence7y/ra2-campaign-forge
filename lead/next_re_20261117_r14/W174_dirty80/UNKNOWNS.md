# W174 · UNKNOWNS / 未解决项

1. **[未证] 16 个写点（11 函数）的类属**：`0x438BF0`, `0x581F90`, `0x65E010`, `0x6ECE60`, `0x6EDE40`, `0x6EDE60`, `0x6EE0A0`, `0x6EE0E0`, `0x6EE1B0`, `0x6EE1D0`, `0x778A20`。它们多为无 RTTI vfunc 的静态辅助函数；后 8 个地址落在 TeamClass 代码段 `0x6E8000..0x6F1000` 但无 `[this+0x54]` 特征，未判为 TEAM；`0x438BF0` 基址 eax 来自 `[ebx+0x2c]`（非直接 this）。证据：`EVIDENCE/w174_class_decision.txt`, `w174_site_origin_backward.tsv`。

2. **[未证] 四类 b/c 精确边界**：写 1 站点（147 处）的「前面有新旧值比较」判据无唯一形式化定义。CFG 口径 b=104/c=43，邻近比较口径 b=112/c=35，字面窗口 4/6/8/10/16 得 b=73/83/103/106/116（c 相应 74/64/44/41/31）。两种极端口径均已在 `EVIDENCE/w174_classify_cfg.tsv` 与 `w174_classify_results.tsv` 全量落盘，审计可按任一复算。推荐 CFG 口径（语义最严）。

3. **[静态推断] TEAM 区 30 函数的精确 TeamClass 归属**：除 `0x6E9140`（原始 vtable 实证 slot23）外，其余 30 个 `0x6E8xxx..0x6F0xxx` 函数无单独 RTTI 实证，依据为「地址段内 + `[this+0x54]`=FirstUnit 特征 + YRpp TeamClass 方法地址簇（ctor 0x6E8A90 / LiberateMember 0x6EA870 / GetTaskForceMissingMemberTypes 0x6EF4D0）」。若需 [已证]，须逐函数查其唯一 vtable 引用（本卡未做，工作量大且非核心数字所需）。

4. **[未证] 18 处寄存器写值（d 类）的运行时值**：`al`×8/`bl`×7/`dl`×2/`cl`×1 的来源已逐条回溯（`EVIDENCE/w174_site_origin_backward.tsv`），但多数为栈槽/上层传参，静态无法确定运行期是 0/1/其他。其中 `0x6E937A` 的 `cl` 上文 `006E9378 mov bl,1` 提示可能为 0/1，未证。

5. **[未证] ObjectClass 侧「每帧谁把 +0x80 置 1」的集中点**（台账 §924-3 悬置项）：本卡证实 52 处 OBJ 写点中 b 类 34 处（有门控）、d 类 5、a 类 13、c 类 0 ⇒ ObjectClass 确有「状态变才置 1」特征；但未定位到单一「每帧重置」点，倾向不存在（与 §925-2 一致）。

6. **[未证] `0x778A20` 的类属**：写 `al` 到 `[reg+0x80]`，strings `wolinfoMD.ini|Server|Locale`，疑为网络/Info 类，非 ObjectClass；地址段 `0x770000+` 不在 OBJ/TEAM 已知簇。
