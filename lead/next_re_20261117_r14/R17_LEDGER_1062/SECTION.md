## §1062 · 书记员覆盖 R17 第 10 轮（首次拿到 0x43F180 调用方 + 对账第三版定谳 + 三审）：事项 1–7 全落、三根红线全写

本草只写 `R17_LEDGER_1062\SECTION.md` / `numbers.tsv` / `SELFCHECK.md`；未改台账、未改控制文件、未改 `COVERAGE\coverage.tsv`、未执行逆向、未启动 gamemd。所有数字复算见 `numbers.tsv`。

### 1. 🔴🔴 首次拿到 `0x43F180` 的调用方（R23 + 审计 R23，字节证实）

- 链：`0x5A66D4 E8 67 50 E9 FF`（call `0x43B740`，rel32 解出目标）→ `0x5A66D9 8B E8`（mov ebp,eax）→ `0x5A684D 8B 55 00`（mov edx,[ebp]）→ **`0x5A6860 FF 92 24 01 00 00`**（call [edx+0x124]）→ `[0x7E3EBC+0x124]=0x43F180`。复算 slot #72=`0x70ADC0`、#74=`0x5F4730`。
- 构造点：`.text` 内直接 `call 0x43B740` **14** 处 + `call 0x43B680` **1** 处 = **15**（复算扫描窗口 4,060,041 B；E9/0F8x 补扫 0）。ctor `0x43B740` 内唯一 vptr 写点 `0x43B9FA C7 06 BC 3E 7E 00`；全 `.text` 立即数 `0x7E3EBC` 复算 3 处，全在该 ctor 内。
- host 必写 **`0x5A6510`**（`83 EC 70` 正常序言），fn_end `0x5A691C`，复算指令 308 条。执行方原报 `0x5A652D` 落在 `0x5A652A C1 E8 1F` 指令内部，不是函数入口；该纠正已按审计必改 1 落位。
- 寄存器：`ebp` 审计写点表 6 条（含 `0x5A651D push ebp` 分类项）；`0x5A66D9` 至 `0x5A6860` 前唯一写点 `0x5A66E6 33 ED`，由 `0x5A66E4 EB 16 jmp 0x5A66FC` 保证在 live-in 路径不可达；`edx` 在 `0x5A684D..0x5A6860` 之间零写点。
- 🔴 **覆盖边界（必须与结论同引）**：只证「**存在至少一个**动态派发点会到达 `0x43F180`」，**不证唯一**、**不证运行期真的执行到**。
- 🔴 **这【不改变】②-b 的 `[静态推断]` 收口（D-53(A)）**：那收的是「行为层可区分性」，本处是「指令层调用关系」，两者不同层；**不得据此声称 ②-b 升格**。
- 理由（事项 1）：用入口前缀、ret/填充边界与 rel32/disp32 四类独立字节锚把“找到调用方”钉在指令层，而不是从派发目标反推调用方。
- 证据：`R17_R23_CALLER_PATH\REPORT.md`、`ctor_sites.tsv`、`dispatch_hits.tsv`；`R17_AUDIT_R23\VERDICT.md`、`chain_bytes.tsv`、`reg_writes.tsv`、`_audit_result.json`；`numbers.tsv` N001–N024。

### 2. R21（`R17_R21_6F4A70_SEM`）· `0x6F4A70` 语义仍未取得，但结构与副作用位置清楚

- 函数体 **51 字节**（`0x33`），尾界 `0x6F4AA3`（最后 `ret 4` 在 `0x6F4AA0`），其后 13×`90`，下一锚点 `0x6F4AB0`；复算 2 条 call、2 个 ret 出口、0 条回边。
- 两条 call：`0x6F4A78` 直接 `call 0x5F5850`（**定名未取得**：字节证实为 thiscall(this,arg) 布尔返回；`.rdata` 复算 8 处代码指针引用，`vtable[-4]→COL→TD` 未取得可核验类名）；`0x6F4A91` 间接 `call [vptr+0x274]`（虚调用，槽 #157，目标不唯一）。
- 语义候选 2 条：候选 A 结构层**高**（字节直接证实）/ 语义层**中**；候选 B **低**。另有「确切游戏语义名无法推断」。
- Q4：`0x6F4A70` 在拒绝块 `0x43F5DB` 被调用，其 `al` 随后被 `0x43F5E3 xor al,al` 覆盖丢弃 ⇒ 属拒绝之后的副作用动作，不提供行为层新区分证据，②-b 收口不翻案。
- 理由（事项 2）：把“结构可证”和“游戏语义可命名”拆开记账，避免把布尔门控形态误写成具名方法。
- 证据：`R17_R21_6F4A70_SEM\REPORT.md`、`calls.tsv`、`disasm.txt`；`numbers.tsv` N025–N036。

### 3. 🔴 RTTI×coverage 对账已错两版，第三版定谳（双口径）

- 第 1 版（R19）**220** → 大量 `.?AV` 切分残片，作废。第 2 版（R20）**26** → 审计判 22 条抽查中 6 条为「过度消解」：下划线取段规则 6/6 全错，因为 `丢弃段@保留段` 形式的复合 TD 确实存在，R20 却记成「只等于基名」，把派生类并进基类。
- 第 3 版（R24）**双口径并列**：口径 S（严格基名）= BOTH **397** / COVERAGE_ONLY **32** / RTTI_ONLY **383**；口径 C（显式复合名 `X_Y`↔`X@Y` 匹配）= BOTH **403** / COVERAGE_ONLY **26** / RTTI_ONLY **377**。复合名共 **660** 条（模板 634 + 非模板 26）。
- ⇒ **「26 还是 32」不是谁对谁错，是两个口径。引用必须写明口径，不写口径不可引用。**
- 审计另判：R19/R20 的 (a) 无独立 vtable 6 条全缺证据（`RulesClass`/`ScenarioClass` 在全镜像 ASCII 复算均 0 次）；(d) 疑似命名差异 5 条全部不成立（4 条 coverage 自身语义已写死 IID 且解码对上；`MPGameModeClass` 是「1 基类 + 4 派生」被计 5 次）；(c) 模板类 9 条中 ≥7 条错。
- 审计判「93.94% 可在 in-binary 定位」会误导：分母 403/429 是 token 数不是出现次数；其中 186 条剥前缀后命中别的 token 早已命中的类，不新增定位；且未声明 in-binary 只覆盖有 RTTI 的类。
- 理由（事项 3）：按 token、TD 条目与匹配强度三条轴拆成 S/C 两套闭合账，既不沿用 R19 的残片，也不让 R20 的“取段=基名”偷换复合 TD。
- 证据：`R17_R20_RECON\REPORT.md`；`R17_AUDIT_R20\VERDICT.md`、`norm_spotcheck.tsv`；`R17_R24_RECON_FINAL\REPORT.md`、`compound_names.tsv`、`reconcile_final.tsv`、`_stage3_buckets.json`；`COVERAGE\coverage.tsv`（只读）；`numbers.tsv` N037–N058。

### 4. R22 + 审计 R22 · 「② 独立佐证」测量（只测量，无 grade 变更）

- 主口径复算：`[已证]` **1654** / 类名可定位 **1094** / entry 与类身份在同一 vtable 闭合 **433** / 跨类出现（原称“矛盾信号”）**141**；审计 A1 独立复现四数，另给敏感性口径 **1085 / 397 / 168 / 91**。
- 审计 A2 判执行方未做继承判断：按槽位单调性重分类后 `141 = 继承可解释 81 + 同址复用（TClassFactory 模板码）56 + 真正可疑 4`；4 条中 3 条属行名类抽取口径错位，仅 `004A88C0` 需人工决定 MapClass vs LayerClass 归属。
- 审计 A4 判「仅 YRpp 代理 40」名不副实：是兜底桶，显式 `YRPP_PROXY_RE` 命中 0 条，40 条全走兜底；抽查 8 条中 4/8 错标（`0041FB10` / `00471500` / `004DF320` / `005656D0` 实带独立链语义）。
- 🔴 表述边界：**433 只是地址锚定，不支持任何改判**。它只说明该 entry 数值等于某 RTTI vtable 的槽值，不说明 entry 属于该类的成员；不构成 ② 支持。`coverage.tsv` 未被改动（复算 mtime `2026-11-21T04:56:21Z`，sha `C2EE063F…C744A`）。
- 理由（事项 4）：坚持 measurement ≠ verdict，把“地址相等”“继承同址”“成员归属”“既有审计链”四种不同证据强度分层记账。
- 证据：`R17_R22_RING2_CORROB\REPORT.md`、`corroborated.tsv`、`_stage3_measure.json`；`R17_AUDIT_R22\VERDICT.md`、`inherit_vs_mismatch.tsv`、`_a4_evidence.json`、`_measure.json`；`COVERAGE\coverage.tsv`（只读）；`numbers.tsv` N059–N070。

### 5. §1061 勘误（单列）

- `§1061` 里 R19 小节记的 COVERAGE_ONLY **220** 已被本节点事项 3 取代；`§1060` 记的 `0x4264C0` 在 17 个类实为 **15**（`reverse_map.tsv` 中 condition 为 function_value=`0x004264C0`、slot=107 的不同类行数复算为 15；`§1061` 已明写「15（不是 17）」）。
- **引用这两处旧值必须同引本节点 3/5。**
- 理由（事项 5）：旧值是历史账页，脱离本节点双口径与勘误说明会被误当现行结论，故绑定引用。
- 证据：`_cards\R17-LEDGER-1060.md:30`；`_cards\R17-LEDGER-1061.md:21`；`R17_R17_SLOT73_MAP\reverse_map.tsv`；`R17_R19_RTTI_XCHECK\reconcile.tsv`；`numbers.tsv` N071–N074。

### 6. GLM 第四卡（`zcode/GLM-5.3-Flash`，自报 `bigmodel-api/GLM-5.3-Flash`）

- 8 项中 **7 AGREE + 1 DISAGREE**。DISAGREE 为 **#7**：`R17_R18_EDI_GAP\edi_writes.tsv` 实际 **11 行**数据（1 initial + 窗口内 4 + 窗口外 6），而派发卡面问「是否恰为 4」——报告说的 4 是「窗口内」的限定，卡面问法不严。
- 另附确认：`COVERAGE_ONLY` 里 AV 前缀 **107** 条（去 AV 后 **106** 条与 BOTH 同名，唯一未命中 `AVRTacticalClass`）、PAV 前缀 **26** 条。
- 自报身份与请求前缀 `zcode/` 不一致，**引用须注明**。
- 理由（事项 6）：第二意见只在纯文本/表内算术有效，身份字段与问题措辞本身须保留原始差异，不能替它改名或替卡面圆场。
- 证据：`R17_GLM_TXT_4\VERDICT.md`、`quotes.md`；`R17_R18_EDI_GAP\edi_writes.tsv`；`R17_R19_RTTI_XCHECK\reconcile.tsv`；`numbers.tsv` N075–N085。

### 7. Lead 独立复核（本节点作为对子代理主张的核对）

- 调用方链 5 个子节点（链上 4 条字节记录 + slot 值 1 项）、slot 值 `0x43F180`、邻槽 #72=`0x70ADC0` / #74=`0x5F4730`、host 入口 `0x5A6510`=`83 EC 70` 与 `0x5A652A=C1 E8 1F`（证明 `0x5A652D` 在指令内部）——全部亲核通过。
- 未取得项：无；本节点未发现与卡面不一致的数字，`numbers.tsv` 88 行 match 列为 MATCH。
- 理由（事项 7）：对子代理结论不是终局，必须把“链、槽、边界字节”三组可复算对象亲核后才写入本节。
- 证据：`R17_AUDIT_R23\chain_bytes.tsv`、`VERDICT.md`、`_audit_result.json`；`numbers.tsv` N001–N024、N086–N088。

本草为 §1062 草稿，由 Lead 逐字追加；书记员未自行改动台账。
