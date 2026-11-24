# 卡 R17-AUDIT-R13 · 异族审计「vtable 反查类名」（执行方 hy4，本卡须跨家族）

审计对象：`lead\next_re_20261117_r14\R17_R13_NAME_TABLE\`（REPORT.md / names.tsv / vtable_owner.tsv / work.py）。
**禁止 import 或复用执行方 work.py**，自写独立实现。
**镜像钉死**：`ra2youli\gamemd.exe` sha256 `73201CC0…F67476`；**报告第一行写实际路径与 sha256**。

## 〇、为什么这张卡是关键
执行方给出了一条**会把类名写进事实底座**的结论：
 - `0x7E3EBC` / `0x7E3EA0` / `0x7E3E98` / `0x7E3E90` = **`.?AVBuildingClass@@`**
 - `0x7F4960` / `0x7F4944` / `0x7F493C` / `0x7F4934` = **`.?AVTechnoClass@@`**
 - `0x7E4E78` = `.?AV?$DynamicVectorClass@H@@`
其方法是 `vtable[-4]` → COL → TypeDescriptor → 名字。
若该链条有一步错（例如把 `vtable[-4]` 当成别的东西、或 COL 解错、或 TD 偏移错），**类名就会全错**，
而类名会被下游当作事实引用。所以必须独立重解。

## 一、必须裁定
**A1 · 链条本身是否成立**：独立复算 `0x7E3EBC[-4]` 的值 → 该值指向什么 → 是否真是 COL（Complete Object Locator）→
  COL 内的 pTD 字段偏移是否正确 → TD+8 是否真是内联名字串。给逐跳字节。

**A2 · 四个 BuildingClass vtable 是否都成立**：对 `0x7E3EBC`/`0x7E3EA0`/`0x7E3E98`/`0x7E3E90` 各自独立走一遍链条，
  报出各自拿到的名字原串（**逐字抄，含 `.?AV` 与 `@@`**）。若某个拿不到，写未取得。

**A3 · TechnoClass 组**：对 `0x7F4960`/`0x7F4944`/`0x7F493C`/`0x7F4934` 各自走一遍，报名字。
  这条同时是对 `R14_COMMON §2.6`「`0x6F2B40` = TechnoClass 构造器」的**独立第二源检验** ——
  请明确回答：**支持 §2.6 / 与 §2.6 冲突 / 无法判定**。

**A4 · 交叉验证（防止链条"处处都返回同一个名字"这种假成功）**：
  请再取 **3 个执行方没有列过的 vtable**（你自己在 `.rdata` 里找，须有合法 COL→TD），用同一方法定名，
  并对其中至少 1 个用**第二种方法**（例如从 TD 的 `.?AV` 名字反查哪些 vtable 的 COL 指向它）交叉确认。
  这一步是为了证明链条**有分辨力**，不是无论如何都吐 BuildingClass。

**A5 · 「988 个名字 / 未找到单一 988 项总表」是否成立**：独立复算名字总数与前缀分布；
  并复核「`.data`/`.rdata` 中对九个 vtable 的直接 VA 引用均为 0」这一负面结论（须给正控/反控，见 `§2.8` 规则 A）。

## 二、铁律
1. 报告第一行写实际镜像路径与 sha256；不符即作废。
2. 禁止复用执行方脚本。反汇编若需要，锚点对齐。
3. 数据扫描限 `.rdata`/`.data`，**声明字节数**。
4. 只读；不建进程、不调试、不启动 gamemd；产物只写本卡目录；**不得修改 `R17_R13_NAME_TABLE` 下任何文件**。
5. 中间结果先落盘，严格 **7 分钟**预算。
6. 取不到写「未取得」，严禁编造。**不得因为名字"看起来合理"就放行。**

## 三、产物（只写本目录）
`lead\next_re_20261117_r14\R17_AUDIT_R13\`
- `VERDICT.md` —— 第一行镜像+sha256；A1–A5 逐项 AGREE/DISAGREE/无法判定 + 必改项
- `chain.tsv` —— 逐 vtable 的链条：vtable \t [-4] 值 \t COL \t pTD \t TD+8 名字
- `controls.tsv` —— A4 的 3 个自选 vtable 与第二种方法交叉结果
- `audit.py` —— 独立实现