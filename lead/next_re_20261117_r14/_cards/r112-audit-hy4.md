# R112 跨家族审计任务卡（只读核对，严禁改任何文件）

## 你的角色
你是独立审计员。只用只读方式核对下面 8 条数值结论是否与给定 JSON 一致。
严禁修改任何文件、严禁运行任何会写盘的脚本、严禁创建或删除文件。
发现不一致就如实报「不一致 + 你在文件里看到的值」。不确定就写「无法判定」。

## 可读文件（全部在 /home/t628/projects/ra2-campaign-forge/ 下）
1. _r112/r112a_rtti.json
2. _r112/r112b_qi_offset.json
3. _r112/r112c_subobj.json
4. _r111/r111d_full_iid.json

## 待核对 8 条（逐条给 一致 / 不一致 / 无法判定 + 你看到的值）

A1. r112a_rtti.json 的 coloff_dist 是一个字典，键 "0" 的值 == 942，键 "4" 的值 == 12。
A2. r112a_rtti.json 的 rtti 字典条目数 == 954。
A3. r112a_rtti.json 的 negctl 里 text_hit == 0，且 img_hit 是一个大于 0 小于 100 的整数。
A4. r112a_rtti.json 的 rtti["HouseClass"]["bases"]["IHouse"] == [36]，
   且 rtti["HouseClass"]["bases"]["IPublicHouse"] == [40]。
A5. r112b_qi_offset.json 的 sites 是列表，长度 == 343。
A6. r112b_qi_offset.json 的 full_sets 里，键 "0x7e9ae0" 的 N == 4，
    且其 full == ["IRTTITypeInfo"]。
A7. r112b_qi_offset.json 的 b4.resolved 是列表，长度 == 6，且其中每一项的第 3 个元素
    都以 "EXACT-unique" 或 "AMBIG-unique" 结尾。
A8. r112c_subobj.json 的 same_70_80 == true，且 assembly 是列表，长度介于 2000 和 3000 之间。

## 输出格式
用 8 行，每行格式：编号 | 一致 或 不一致 或 无法判定 | 你看到的值
最后追加一行：合计一致 X/8。

## 严禁
不得使用任何反引号字符。不得运行 python 以外的写操作。不得 touch / mv / cp 任何文件。
