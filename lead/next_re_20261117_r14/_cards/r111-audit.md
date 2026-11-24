# R111 跨家族审计任务卡（只读核对，不改任何文件）

## 你的角色
你是独立审计员。只用只读方式核对下面 8 条数值结论是否与给定 JSON 文件一致。
严禁修改任何文件、严禁运行任何会写盘的脚本。发现不一致就如实报"不一致 + 实测值"。

## 可读文件（全部在 /home/t628/projects/ra2-campaign-forge/ 下）
1. _r111/r111a_iidmap2.json
2. _r111/r111b_bidir.json
3. _r111/r111c_thunk.json
4. _r110/r110a_iidmap.json

## 待核对 8 条（逐条给 一致 / 不一致 + 你在 JSON 里看到的值）

A1. r111a_iidmap2.json 里 n_qi_classes == 172，且 n_qi_classes_r110 == 172。
A2. r111a_iidmap2.json 里 iid_n 的条目数 == 18；r110a_iidmap.json 里 iid_classes 的条目数 == 17。
A3. r111a_iidmap2.json 的 truncated 列表长度 == 1，且唯一元素的类名是 HouseClass，其三元组为 (HouseClass, 6, 3)。
A4. r111a_iidmap2.json 的 negctl.hit == 116，negctl.base_pct == 0.58。
A5. r111b_bidir.json 的 exact 列表长度 == 8，ambig 长度 == 5，nomatch 长度 == 5。
A6. r111b_bidir.json 的 negctl.hit == 99，negctl.trials == 20000。
A7. r111c_thunk.json 的 set_equality == true，且 thunks 字典条目数 == 12，全部 N 值都是 4。
A8. r111c_thunk.json 的 negctl.hit == 2，negctl.base_pct == 0.01。

## 输出格式
用 8 行，每行格式：编号 | 一致 或 不一致 | 你看到的值
最后追加一行：合计一致 X/8。
