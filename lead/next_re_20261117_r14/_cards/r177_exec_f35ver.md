# 执行卡 r177_exec_f35ver（role=exec，模型 work/cn:hy4flash-free）

## 任务（只读，禁止写任何文件）
在 /home/t628/projects/ra2-campaign-forge 下，对 FACT_INDEX 的 F35 行做一次逐版实测。

## 一次取证纪律
只允许一条命令完成全部取证（可写一个 python3 heredoc，内部完成所有统计），一次输出全部证据。不要拆成多次单点命令。

## 必须输出（表格形式）
1. 对目录 lead/next_re_20261117_r14/R17_R*_FACTINDEX_V5* 中版本号 553..559 的 7 个 FACT_INDEX.tsv，逐版给出 F35 行：
   - statement 的字符长度
   - limitations 的字符长度
   - statement 中串「同血缘克隆」出现次数
   - limitations 中串「同血缘克隆」出现次数
   - statement 中串「不是独立实现」出现次数
   - limitations 中串「不是独立实现」出现次数
2. 对 V559 单版：全表 54 个数据行中，「同血缘克隆」与「不是独立实现」每个串分别出现在哪些 fact_id 的哪一列、各几次。
3. 对 V559 的 F35.limitations：找出包含「R174-R2」的那一段（以【R174-R2 补 起到段尾/下一个【 为止），给出该段自身的两个串出现次数与字符长度。
4. V559 的 F35 statement 中是否包含串「缺一手权威」，出现几次；是否包含「已撤回」，几次。

## 禁止
- 不得修改、创建、删除任何文件；不得 mkdir。
- 不得使用 git 命令。
- 不得引用或补充任何你自己的推断，只报实测数字。

## 交付
在回件里给出：上面的 4 张表 + 一句结论（V559 的两串计数是否等于 limitations 侧 5 与 8）。若某项与预期不符，直接如实写出实测值。
