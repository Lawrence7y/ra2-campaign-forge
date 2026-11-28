# R210-B 70 个 this 调整 thunk 与 23 个 jmp 三元组的完整复用映射（执行员卡）

## 任务
对 gamemd.exe 做纯静态统计，产出「同一 jmp 三元组被哪些 mdisp 复用」的完整映射，并给 mdisp=4 与 mdisp=24 成对规律。只读 + 只写 _r210/ 新文件。

## 环境与复用材料
- python3 + capstone。工具 /home/t628/projects/ra2-campaign-forge/_r185/pe185.py（只 import 不改）。
- /home/t628/projects/ra2-campaign-forge/_r209/q3.json 已存：thunk（70 条，value 含 va/kind/imm/jmp）、hit（101 张额外视图表 -> [[slot, thunkva],...]）、vt（COL->槽列表）、mdisp、names、vt_of。
- 上一轮已得数（请独立复算，不要抄）：thunk 70 个、slot0 口径 thunk 22 个、三元组去重 23 组、jmp 三元组 13 个、mdisp 分布 {4:91,24:6,1728:1,44:1,40:1,36:1}。

## 必须一条命令输出的证据（写 _r210/b1.py）
1. 从 q3.json 读出 101 张表的 slot0/slot1/slot2 的 thunk 地址，组成三元组 (s0,s1,s2)；按三元组去重，打印每组：
   - 组 id、s0/s1/s2 三个 thunk 地址与各自 imm
   - 该组覆盖的 COL 数与 mdisp 列表（排序去重）
   - 三个 thunk 的 E9 落点 (j0,j1,j2)
2. 按 jmp 三元组 (j0,j1,j2) 去重，打印每个 jmp 三元组覆盖哪些 thunk 三元组、哪些 mdisp。
3. 成对规律检验：在所有 mdisp 取值里，找出「mdisp=4 与 mdisp=24 是否成对出现在同一 jmp 三元组」的完整名单（例如同一 jmp 三元组下既有 mdisp=4 又有 mdisp=24 的族），给名单与计数。若无此规律，如实说不成立。
4. 70 个 thunk 全表：地址 / kind(A83|B81) / imm / E9 落点 / 被哪些表在哪些 slot 引用 / 引用次数。谁都没引用的必须单独列出（预期 0 个，需实测）。
5. 反控：断言 q3.json 里 thunk 键数 == 70；断言 101 张表每张前三槽都在 thunk 集合内。

## 断言（脚本内 ck 打印 PASS/FAIL）
- B1：thunk 总数 == 70
- B2：101 张表前三槽全为 thunk（303 槽）
- B3：三元组去重 == 23 组
- B4：jmp 三元组去重 == 13
- B5：70 个 thunk 孤儿数 == 0
- B6：每组内 mdisp 唯一（同组不出现重复 mdisp）
若任一断言实测不等，打印实测值并 FAIL，不要改断言凑数。

## 纪律
- 卡与回复禁止出现反引号。
- 一条命令跑完，8 分钟内。结果写 _r210/b1.json + b1.txt，回复里贴断言汇总与 5 行核心数字。
