# 任务 B：把 11-10/11-11 的六个静态探针收成一条因果链报告

仓库：D:\Project\ra2-campaign-forge（Windows / PowerShell）。你是受限执行方，只按本任务书写盘。

铁律：
1) 零真机：不启动 gamemd.exe / ra2loader / YURI.exe，不 attach、不读活进程内存，不写 hook / 采样 / MiniDump / SuspendThread / StackWalk 代码。
2) 只读边界：除写域外一律只读；禁止 git commit / push / reset / checkout；不得覆盖或删除既有件（要备份就备份到写域内）。
3) python 一律：python -I -X utf8 <绝对路径>；指纹用 hashlib 实算，禁止手写估计。
4) 每个数字追到「实跑命令+输出」或「文件:行」；拿不到就写「未验」，不补造。
5) 报告必须含「边界与未验」一节。
6) 收尾回执：改了哪些文件、跑了哪些命令、结论一句话、遗留未验项。

## 背景
上一批静态逆向留下 6~7 个只读探针与 _out.txt/_out.json，但**没有任何 md 结论**，也没入账。它们指向同一族对象，需要收敛成一条可引用的链。

## 输入（只读）
lead\esi_caller_trace_20261111\ · lead\slot2_fullscan_20261111\ · lead\re_crashwriter_static_20261110\ · lead\re_orphan_owners_20261110\ · lead\re_map_preset_decode_20261110\ · lead\re_loadbench_diff_20261110\ · lead\playerctrl_semantics_20261111\
靶件：ra2bench\gamemd.exe，期望 sha256=73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476（先自己核，不符就停）。

## 写域
只允许新建 lead\re_chain_synthesis_20261111\；不得改上述目录任何文件。

## 步骤
1) 核 sha256 与字节数。
2) 复现门：6 个探针逐个 python -I -X utf8 重跑，输出落写域，与既有 _out.txt/_out.json 逐项比对，出 MATCH/MISMATCH 表（MISMATCH 必须点名差异字段与数值）。这是第一道硬门，不许静默。
3) 合流成链，每环给 VA + 关键字节 + 证据文件:行：
   ① 虚表 slot2 → 0x54A4F0 / 0x54A630 调用面（谁调、多少处、100% 分块覆盖下的确切计数、capstone 在 file offset 0x6F59D 截断如何处理）；
   ② 0x0054A56E 数据依赖链（写什么、值从哪来、谁消费）；
   ③ HouseClass 数量与 owner 归属（哪张表/哪个结构决定，怎么与 ①② 接上）；
   ④ 地图预置单位表槽位语义（XMP29U2.MAP 311,822 B / 大版 .yrm 92,332 B / 小版 25,604 B）；
   ⑤ PlayerControl / PercentBuilt 静态语义定名及其在链上的位置。
   接不上的环写「未接上」，不要硬凑。
4) 口径已定案（不必再研究，只需在报告里引用一句）：XMP29U2.MAP=311,822 B(sha 0add791d) 与载体 [2]0LoadBench_U0400.yrm=222,799 B(sha 93c2974b) 是**不同文件**；ra2youli 同名文件 92,332 B 也是另一个文件。

## 交付（写域内）
- CHAIN_SYNTHESIS.md：结论 / 证据表（VA→含义→证据文件:行）/ 文字版因果链 / 复现门 MATCH-MISMATCH 全表 / 边界与未验。
- _repro_*.txt（6 份重跑输出）与比对脚本输出。
- 一段可入账的 §节草案（≤80 行，标 §6xx 待编号），只写亲验成立的部分。