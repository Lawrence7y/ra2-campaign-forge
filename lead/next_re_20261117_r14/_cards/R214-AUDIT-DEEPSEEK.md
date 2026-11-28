# R214-AUDIT · 只读复核（deepseek）· 虚槽 +0x48 面与 HouseClass adjustor 例外成因

## 角色
只读审计。禁止修改任何仓库文件，禁止写 lead/ 下四件套，禁止跑长扫描。允许在 _r214/ 下新建自己的临时脚本 a1.py / a1_out.txt 做复算，其它一律只读。
预算 8 分钟，回合上限 50；一次到位，不要逐条单点命令试探。

## 待复核的六组结论（全部为 R214 主会话与两个 exec 子代理的报数）
数据来源：_r214/m0_out.txt、_r214/ex1_out.txt、_r214/ex2_out.txt；二进制 ra2bench/gamemd.exe；PE 映射可复用 _r185/pe185.py（P.RAW / P.B / P.dw / P.where / P.cstr / P.r2o / P.sec_of）。

A 组（槽面普查，m0）
A1 全部 1214 张视图共 14044 槽，槽目标 100% 落 .text（14044/14044）。
A2 槽目标 distinct 个数 = 6692。
A3 主视图 distinct 目标 6345、次视图 348、交集仅 1、仅主视图独有 6344、仅次视图独有 347。
A4 单一索引全部类同目标（单值索引）个数 = 91，索引总数 344。
A5 反控：以 COL+4 当 vftable 口径取到 .text 指针为 0/954。

B 组（slot18 = 虚槽 +0x48，ex1）
B1 槽数 > 18 的视图 = 137（主 125 + 次 12），slot18 落点 distinct = 27，全部落 .text。
B2 slot18 落点 top3：0x4104c0 x56 / 0x5f65a0 x19 / 0x4e1960 x17。
B3 MouseClass 主视图起点 0x7e1964 槽数 55，slot18 = 0x5bda80；TabClass 与 ScrollClass 主视图 slot18 均 = 0x4c9150；三类 21784 次视图 slot0 均 = 0x6d1770 且该视图只有 1 槽。
B4 0x723ea0 / 0x723eb0 在 .text 内的直接 call 位点 19 处（e8 相对调用），且这两个地址不作为任何 vftable 槽值出现（0/14044）。
B5 控制组：slot17 落点 distinct 28、slot19 落点 distinct 27，三者不等 ⇒ slot18 非平凡。

C 组（HouseClass 例外，ex2）
C1 全体 adjustor 槽 305 个，imm==mdisp 通过 303，例外 2 条 = ?AVHouseClass@@ mdisp=40 次视图（起点 0x7ea80c）idx3/idx4，imm=4，jmp 目标 0x4f6e60 / 0x4f6950。
C2 这两条 jmp 目标不在该类的 mdisp=0 主视图（起点 0x7ea8a0，24 槽）里，而落在同一 HouseClass 的 mdisp=36 次视图（起点 0x7ea834）idx3/idx4 上，且 imm 恰等于 40-36=4。此条订正 R213 看板原话「两目标均在本类主视图槽内」。
C3 每类 mdisp 多元组只有 6 种：(4,8,12) x76、(4,) x7、(4,24) x6、(21784,) x3、(4,8,12,36,40,44) x1（HouseClass）、(4,8,12,1728) x1（AircraftClass）。
C4 adjustor 指令级模板只有 2 种（sub [esp+4],imm 5 字节版 x302 / 8 字节版 x3），R213 报的「7 种」是槽位字节通配串口径，两口径不同不可互换。
C5 每张次视图的 adjustor 数分布 {0:159, 3:100, 5:1}。

D 组（主会话自错声明，需你独立判断是否成立）
D1 m1 的「vftable 前缀一致 ⇒ 单继承父类」推导被判为无效方法：实测 93 类歧义、出现深度 75 的退化长链、根 861 个 ⇒ 前缀关系不足以定父，该方法 0 条进结论。

## 交付格式
按 A/B/C/D 分节，每项给 PASS / FAIL / CANNOT-VERIFY 三态之一，FAIL 必须给出你的实测值与我方报数并列。最后一节写「我方口径风险」，只写你认为会影响进结论的（最多 5 条），不要复述结论本身。
