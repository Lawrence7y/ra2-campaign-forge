# R210-A 主视图 954 表 slot>=3 的槽族普查（执行员卡）

## 任务
在 t628 本机对 gamemd.exe 做纯静态统计，产出主视图（mdisp==0 的 COL）vftable 的 slot>=3 槽落点族分布。禁止动态、禁止改任何既有文件，只读 + 写 _r210/ 下新文件。

## 环境
- python3 + capstone + 已有工具 /home/t628/projects/ra2-campaign-forge/_r185/pe185.py（只 import，不要改）。它提供 P.B[段名]、P.RAW、P.dw(va)、P.where(va)、P.r2o(va)、P.cstr(va,max)。
- 上一轮成果 /home/t628/projects/ra2-campaign-forge/_r209/q3.json 已经存好：keys = vt（COL 地址 -> 槽地址列表，hex 字符串）、vt_of（COL -> vftable 起址）、thunk、hit、mdisp、names。
- 直接读 q3.json 复用，不要重扫全段。

## 必须一次命令输出的证据（写 _r210/a1.py，一条命令跑完，输出 JSON + 人读表）
1. 主视图表 = q3.json 里 mdisp==0 的 954 张。逐表给 slot>=3 的落点地址。
2. 对每个落点，只用 capstone 反汇编前 <=256 字节，取**第一条 ret 的机器码**（形如 ret 4 / ret 0x10 / ret 0xc / ret / 无 ret 前 256B）。注意：不得对整段 .text 开 detail=True 一次性 disasm；只对命中的槽地址单独反汇编 <=256 B。
3. 统计表：按 (slot 号, ret 立即数) 二维桶计数，slot 号只统计 3..8，把 slot>=9 合并为 9+ 桶。
4. 统计：954 张表里，slot3 落点属于「本类自己实现」还是「与其他表复用同一地址」——给「slot3 地址被 N 张表共用」的 N 分布（N=1,2,3..10,>10 分桶）。
5. 判据反控：随机取 20 张表，人工核对输出里的前 3 条（脚本里打印，不要人工改数）。
6. 正控：构造一个已知槽地址（例如 0x401950）必须出现在结果里且 ret 读取不报错。

## 断言（脚本内必须 ck 打印 PASS/FAIL）
- A1：mdisp==0 表数 == 954
- A2：slot>=3 的槽总数 == (all slots of 954) - 954*min(3, len) 之实际值，脚本自算并打印，不要预设。
- A3：slot3 的 ret 立即数 top1 与 R209 q5 报的主视图三槽 ret 分布不冲突（打印对比即可，不硬判）。
- A4：随机 20 张表输出完备（每张至少打印 vt 起址、槽数、slot3 地址、slot3 ret）。

## 纪律
- 卡面与本卡回复中禁止使用反引号。
- 一条命令跑完，禁止逐条试探命令。总耗时控制在 8 分钟内。
- 结果写 /home/t628/projects/ra2-campaign-forge/_r210/a1.json 与 a1.txt，并在最终回复里贴出断言 PASS/FAIL 汇总和 5 行核心数字。
- 如果某项实测与预期不符，如实报告实测值，不要凑数。
