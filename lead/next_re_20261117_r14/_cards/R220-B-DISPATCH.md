# R220-B 取证：0x87c484 12 B 派发表 + 0x77c/0x780/0x784/0x788 四字段宿主（执行员 hy4）

## 角色
执行员。只做实测取证，产物写 _r220/ 子目录，文件名统一前缀 B_ 。
工作目录 /home/t628/projects/ra2-campaign-forge 。禁止修改四件套（R14_COMMON.md / LEAD_LOCK / STATUS_BOARD.md / GOAL_THREE_TARGETS_20261018.md）。

## 环境与硬性口径
- PE 映射：sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge'); import _r185.pe185 as P
  P.RAW 全文件字节；P.r2o(va) 文件偏移（None = virt-only）；P.dw(va) dword；P.cstr(va) 字符串；P.B['.text'] 段信息。
- capstone：CS_ARCH_X86 + CS_MODE_32，md.skipdata = True，逐字节 resync：
  while 循环 raw[pos:pos+16] 调 md.disasm_lite 取第一条，pos += 长度；解不出 pos += 1。
  禁止整段 .text 一次性 md.detail=True。后台命令带 timeout 900。

## 待取证
T1. 派发表本体：从 0x87c484 起读 8 条 × 12 B = 96 B，按 3 个 dword 每条打印；
    用 0x7cdd08 的 cmp edi, 0x87c4c0 作为上界，说明 (0x87c4c0-0x87c484)/12 的商与余数，
    并说明每条记录的三个 dword 各自是否落在 .text（用 P.r2o 判断）。
T2. 每条记录的 dword0 / dword1 / dword2 对应的代码：对每个落在 .text 的目标，输出前 6 条指令（disasm_lite）。
    特别给出 dword1=0x7ce046 处的前 6 条指令并判定它是否为 xor eax,eax / ret 桩。
T3. 调用点 0x7cde2b 上下文：把 0x7cdd80..0x7cde60 逐条列出（disasm_lite），
    标出 esi 的构造链（0x7cddac lea esi,[edi+edi*2] / 0x7cddb6 shl esi,2）、
    edi 的来源与取值上界、以及调用后对 eax 的用法（返回值语义）。
    再找 0x7cdd80 所属函数入口（0xCC 填充判界：向前找最近 >=2 连续 0xCC，其后第一个字节为 start），
    给出 start 与 E8 调用该 start 的站点数与地址清单（最多 20 个）。
T4. 四字段宿主：对 +0x77c / +0x780 / +0x784 / +0x788 四个 offset，全 .text 逐字节 resync 扫一遍，
    统计每个 offset 的：读次数、写次数、写入端指令地址清单（最多列 20）、
    写入端是否把 .text 地址作为 imm32 写入（条数）。
    汇总每个 offset 的写入端所属函数入口（start，按 0xCC 判界），按函数聚合计数。
T5. 已知写入端集中在 0x7be66a 与 0x7c2f6b 两个地址附近。核实：
    从 0x7be600..0x7be700 与 0x7c2f00..0x7c3040 两段逐条列出（disasm_lite），
    指出把 .text 函数地址写入 [reg+0x77c..0x788] 的精确指令地址与 imm32 值，逐个列出（应为 12 条，给地址+offset+imm）。
T6. 宿主类定位：用 RTTI COL/vftable 表（可用已存在的扫描思路：.rdata 内 dw(V-4)==COL 形态）；
    若难定位则改为给出：这 4 个 offset 在哪些虚表槽目标函数的体内出现（把写入端 start 与 1218 张虚表槽目标地址做交集），
    给出交集中的虚表地址+槽号清单（最多 20 条）。不要硬编造 RTTI 结论，找不到就写 0 条。
T7. 正反控：
    正控 —— 0x7bea07 必须被 T4 扫描识别为 [esi+0x784] 的 call；
    反控 —— 把 offset 换成 0x778 与 0x78c 各扫一次，报告两条计数（应与四字段明显不同）。
    另给一条负控：扫描一个不存在的 offset 0x7a4，报告计数（预期 0）。

## 输出
- _r220/B_report.md：T1..T7 实测值 + 判据脚本名。
- _r220/B_result.json：结构化数字（派发表条目数与目标分类、四 offset 读写次数、12 条写入端清单、E8 站点数、正反控计数）。
