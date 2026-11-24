# residual · R17-R9

## 未取得
| # | 项 | 原因 |
|---|---|---|
| 1 | 子表精确起止 (T1/T2) | 0x7E3FE0 / 0x7E4068 均落在连续 350 槽全-text 指针串 [0x7E3E8C,0x7E4403] 内部, 串内无 0/非 text 值, 字节判据无法切分 |
| 2 | R8 的 slot 序号口径 | 0x7E3FE0 不是表头 (#85), 0x7E4068 是 #119; 两端均无边界 |
| 3 | 运行期取用点 | .text 全扫 12 个候选 VA 立即数 → 0 命中; 宽口径乐队 [0x7E3E00,0x7E4140) 仅 26 条且最高 0x7E3EBC |
| 4 | call [reg+off] 与槽偏移 | 前置 (取用点) 不存在 |
| 5 | 所属函数 | 无 site, 位置断言无对象; 拒绝用 forced_host / 形态匹配代替 |
| 6 | RTTI 类名 | .rdata 无 MSVC 装饰名, 无 pTD 形态 |

## 若要推进 (建议, 未执行)
1. 需要动态证据 (本卡禁止建进程): 在 0x7E3FE0 / 0x7E4068 下硬件读断点, 看是否被读; 若从不被读, 则两表是死数据, 0x43F180 / 0x449440 的派发入口在别处。
2. 静态可做的下一步: 对 0x43F180 / 0x449440 各自做函数体反汇编, 看它们是否被 `mov eax,[ecx+off]; call eax` 形式调用 (即从对象里取指针), 而不是从表里取 —— 这能把 "表" 假设改成 "对象内嵌指针" 假设。`work.py` 已给出二者的 E8/E9 直接引用为 0。
3. 该 350 槽串若确为 vtable 数组, 应能从构造函数 `mov dword ptr [this+off], 0x7E3Exx` 找到 —— 但 .text 中不存在任何 0x7E3E8C..0x7E4403 的立即数, 故构造函数装表假设**同样被否**。

## 边界遵守
- 只读打开 gamemd.exe 一次 (fs.readFile), 无进程、无调试、无写 exe。
- 数据扫描限 .rdata / .data (另做全节交叉引用仅为证伪, 未越界写)。
- 产物仅写本目录: REPORT.md / tables.tsv / consumers.tsv / consumers_extra.tsv / residual.md / work.py / _pe.json / _bounds.json / _imm_raw.json / _names.json。
- 未从任意地址线性反汇编 (无 site)。
