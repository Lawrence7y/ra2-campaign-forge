# 任务 B′：六探针合流成一份可入账的因果链报告（含复现门）

仓库：D:\Project\ra2-campaign-forge（Windows / PowerShell）。你是受限执行方，只按本任务书写盘。

## 铁律
1) 零真机：不启动 gamemd.exe / ra2loader / YURI.exe，不 attach、不读活进程内存，不写 hook / 采样 / MiniDump 代码。
2) 除写域外一律只读；禁止 git commit / push / reset；不得改既有件。
3) python 一律 python -I -X utf8 <绝对路径>；指纹用 hashlib 实算。
4) **最重要的一条**：只写「探针输出直接支持」的话。凡属运行期机制、跨图普适性、因果推断，一律标【未证】并说明缺什么证据。**禁止把读数升格成机制结论**。
   反例（前一位执行方犯了，你必须避开）：
   - ✗「证得 0x0084F2BA 为 DEP 取指违规」——实际它只是 2026-10-20 真机崩溃对话框里出现的地址（见 lead/stale_pass_20261109/_sp_report.txt:37），性质未定谳。
   - ✗「证得 House 实例由 [Houses] 严格决定」——单个地图只证明该图 [Houses]↔house 节一一对应（re_orphan_owners/_oo_map_out.txt），推不出引擎机制。
   - ✗「PercentBuilt 引擎零读取」——需全镜像读点普查，未做即为未验。

## 输入（只读）
lead\re_crashwriter_static_20261110\ · lead\slot2_fullscan_20261111\ · lead\playerctrl_semantics_20261111\ · lead\re_orphan_owners_20261110\ · lead\re_map_preset_decode_20261110\ · lead\re_loadbench_diff_20261110\
靶件：ra2bench\gamemd.exe，期望 sha256=73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476（先自核，不符即停）。

## 写域
只允许新建 lead\re_chain_synthesis_20261111\。

## 步骤
1) 核 sha256 与字节数。
2) **复现门**（第一道硬门）：把 6 个目录里的探针脚本逐个 python -I -X utf8 重跑，stdout 落写域，与既有 _out.txt/_out.json 逐项比对，产出 MATCH / MISMATCH 表；MISMATCH 必须给出差异字段与两边的值。**任何一条 MISMATCH 都要在报告最前面点名**。
3) **合流**，每环给 VA + 关键字节 + 证据文件:行，并且明确区分「读数」与「推断」：
   ① slot2 调用面：0x54A4F0 / 0x54A630 的调用点确切计数与分块覆盖方式（如何处理 capstone 在 file offset 0x6F59D 截断）；
   ② 0x0054A56E：静态可达性如何（哪些边能到、哪些不能），**只报静态图结论**；
   ③ House 归属：把「地图文件里 [Houses]↔house 节一一对应」与「引擎建几个 House」分开写，后者标【未证】；
   ④ 地图预置槽位：三份地图（XMP29U2.MAP 311,822 B / 大版 yrm 92,332 B / 小版 yrm 25,604 B）的预置单位真实计数，逐槽位；
   ⑤ PlayerControl / PercentBuilt：只写静态字面语义与读点计数（若做了读点普查才写计数，否则标未验）。
4) 口径引用（不必再研究，直接引用）：XMP29U2.MAP=311,822 B(sha 0add791d) 与载体 [2]0LoadBench_U0400.yrm=222,799 B(sha 93c2974b) 是**不同文件**；ra2youli 同名件 92,332 B 又是另一个。

## 交付（写域内）
- CHAIN_SYNTHESIS.md：①复现门结果表（置顶）②逐环证据表（VA→读数→证据文件:行→【已证】/【未证】）③边界与未验清单。
- _repro_*.txt 六份重跑输出 + 比对脚本与输出。
- LEDGER_SECTION_DRAFT.md：一段可入账的 §节草案（≤80 行，标 §6xx 待编号），**只收【已证】项**，未证项单列「待证」。