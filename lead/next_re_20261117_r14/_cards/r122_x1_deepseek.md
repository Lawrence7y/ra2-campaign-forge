# R122 执行员任务卡（deepseek · work/cn:deepseek-v4.1-flash）

## 目标
对 gamemd.exe 的 c7 05 写 BSS 扫描，独立复算三套口径的全量数字，并判定 104 与 103 的差异对象归属。只写自己的产物到 _r122/exec2/，不改任何既有文件。

## 输入（只读）
- /home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe
  sha256 必须实测并打印，期望 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
- PE: ImageBase 0x400000; .text VA 0x401000 raw 0x3e0000; .data VA 0x812000 raw 0x6c000 VirtualSize 0x367be4
- BSS 区 = [0x87e000, 0xb79be4)
- 指令边界必须用 capstone CS_MODE_32 且 disasm_lite 且 md.skipdata=True 全段一次扫完（.byte 伪指令不计入边界）；禁止对整段开 detail=True

## 必须回答的 6 个数字（每个都要自己的代码算，不得抄任何现有 json）
1. Q1 raw 口径（纯字节扫 c7 05，不判边界）：BSS 目标数、站点数
2. Q2 clean 口径（站点必须落在 skipdata 边界集合上）：BSS 目标数、站点数、被丢弃目标数
3. Q3 指令边界总数与 .byte 伪指令条数
4. Q4 带 skipdata 的线性扫描总条数，以及扫描是否覆盖到 .text 末地址 0x7e1000
5. Q5 VectorClass 族 BSS 目标数（raw 与 clean 各一）
6. Q6 双形态对象数两种定义：
   - 严格：该对象全部写入中恰 2 次，且恰 1 个 DynamicVectorClass 名 + 恰 1 个 VectorClass 名，元素类型相同
   - 宽松：该对象全部写入中至少 1 个 DynamicVectorClass 名 + 至少 1 个 VectorClass 名，元素类型相同
   分别给出总数、35 内、35 外；并给出两种定义的集合差集（逐个地址 + 该地址的写入次数 + 全部类名）

## 35 个容器的定义（必须自己重算，不得复制）
扫全 .text 的 call rel32，目标落在 [0x67fdf0, 0x680f80] 的站点，排除 0x67d193 与 0x67e62b 两站，剩余 35 站；每站前 7 字节形如 ba imm32 8b ce，取 imm32 得容器地址；断言 35 个互不相同。

## 自测要求（必须写进脚本并打印 PASS/FAIL，宁可真 FAIL 不写恒真断言）
- 正控：手工构造一条 c7 05 字节流，扫描必须命中
- 负控 1：modrm 为 0x45 的 disp8 形态不得被当成 c7 05
- 负控 2：把边界集合换成空集，Q2 的 clean 目标数必须为 0
- 负控 3：把 skipdata 关掉后重扫，必须观察到扫描提前中断（记录中断地址），证明 skipdata 是必需的
- 口径自检：Q1 的目标集必须包含 Q2 的目标集

## 输出
- 脚本 _r122/exec2/q1.py 到 q6.py（可合并为 1 到 6 个文件，文件名自定但要能单独跑）
- 每个脚本必须带 timeout 900 之前跑完；结束时打印全部实测数字
- 结果 json 落 _r122/exec2/
- 最后追加写 _r122/exec2/REPORT.md，逐条列 6 个答案与自测结果，不要预测，只写实测

## 纪律
- 只读 exe，只写 _r122/exec2/ 下自己的文件
- 不改 R14_COMMON.md / LEAD_LOCK / STATUS_BOARD.md / BOARD_ARCHIVE.md / GOAL_THREE_TARGETS / check_disc.py
- 内存红线：不要对整段 .text 开 detail=True；分块时每块处理完释放对象
