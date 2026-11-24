# R112 执行员任务卡（只读分析，严禁改任何文件）

## 你的角色
你是独立执行员。任务**只读**：核对并报告，不要修改、创建或删除任何文件。
你的结论会由主会话用独立实现复算，所以请只报你能在文件里直接看到的东西。

## 可读文件（全部在 /home/t628/projects/ra2-campaign-forge/ 下）
1. _r112/r112a_rtti.json
2. _r112/r112b_qi_offset.json
3. _r112/r112c_subobj.json
4. _r111/r111d_full_iid.json
5. _r111/r111b_bidir.json

## 要你回答的 6 个问题（逐条给结论 + 你看到的具体数值）

Q1. r112b_qi_offset.json 的 sites 列表里，第 3 个元素（偏移 N）取值一共有哪几种（去重后列出）？
    其中 N 等于 0 的有多少个站点？N 是字符串 "NA" 的有多少个站点？

Q2. r112b_qi_offset.json 的 b4.resolved 里，哪些 IID 被唯一确定成了哪个接口名？
    逐条列出（IID 与接口名）。

Q3. 比较 _r111/r111d_full_iid.json 的 iids 里声称包含 "0x7f7c70" 的类集合，
    与声称包含 "0x7f7c80" 的类集合。这两个集合是否完全相同？（答 相同 或 不同，
    若不同请给出对称差里的类名）

Q4. r112c_subobj.json 的 trio 里，键 "0x7e9ae0" 的 N 是几？它的 n_distinct_subobj_vt 是几？
    并说明 subobj 字典里键 "0x7e9ae0" 的 resolved 值是多少。

Q5. r112a_rtti.json 的 rtti 里，键 "AircraftClass" 的 bases 字典中，
    "IFlyControl" 对应的值是什么？"IRTTITypeInfo" 对应的值是什么？

Q6. r112c_subobj.json 的 c1.n 与 c1.ok 分别是多少？两者是否相等？

## 输出格式
用 6 段，每段以 Q1. Q2. ... 开头，写出你的结论与具体数值。
最后追加一行：合计已答 X/6。

## 严禁
不得使用任何反引号字符。不得修改/创建/删除任何文件（包括临时文件）。
