# R209 A1 · 只读复核：额外视图 vftable 的 IUnknown 三方法 thunk 三元组

你是审计员，只读。**禁止修改任何文件**。可以用 python3 读文件与跑自己的核对脚本。

## 待复核的主张（主会话本轮产出）
产物目录 /home/t628/projects/ra2-campaign-forge/_r209/（q1..q9 的 py/json）。
被测对象 /home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe。

主张清单：
- M1 .text 段全域 this 调整 thunk 锚点：83 6C 24 04 形态 67 处、81 6C 24 04 形态 3 处，合计 70；
  .rdata/.data/.rsrc 同判据 0 处。
- M2 81 形态三处地址 0x41c670 / 0x41c680 / 0x41c690，imm 均 1728；
  E9 落点分别 0x414290 / 0x4142f0 / 0x414300（记住 81 编码 E9 在 +8、rel 在 +9、落点 = va+13+rel）。
- M3 COL 记录 1214 条（+8 cdOffset 恒 0、+12 pTD 落 .data、+16 pCHD 落 .rdata），按 +16 分组 954 组，
  vftable 1214 张，总槽 14044。
- M4 含 thunk 的 vftable 恰 101 张；这 101 张的 slot0/slot1/slot2 三槽**全部**是 thunk（不是只有 slot0）；
  thunk 立即数 == 该表 mdisp，303/303。去重后 (slot0,slot1,slot2) 三元组 23 个，每个三元组 mdisp 唯一。
- M5 70 个 thunk 全部被引用，未引用 0 个（即不存在"孤儿 thunk"）。
- M6 三槽随 thunk 跳到上级后：slot0 落点全部 ret 0xc（12）、slot1 全部 ret 4、slot2 全部 ret 4（各 101/101），
  判为 QueryInterface / AddRef / Release 的 this 调整 thunk。
- M7 101 张表的 slot_k thunk 的 E9 落点 == 同一类主视图（mdisp==0 的那张）的 slot_k，k=0/1/2，各 101/101。
- M8 唯一越界：COL 0x8028b8 .?AVHouseClass@@ mdisp=40 的 9 槽表，slot3/slot4 也是 thunk
  （0x510ab0 imm=4 jmp 0x4f6e60；0x510ac0 imm=4 jmp 0x4f6950），其 imm 与表 mdisp 40 不等。
- M9 三形态互斥：T（101 张含 thunk 表）/ S（156 张单槽表，共享 0x410590 / 0x410580 / 0x6d1770 三个静态函数）/
  I（3 张表，slot0 为 0x41bc30 / 0x522a60 / 0x746100 真函数体）三者承载表集合两两不交。
- M10 S 表 0x6d1770 的三张承载表是 MouseClass / TabClass / ScrollClass，mdisp 全 21784，均单槽；
  该函数体里比较的 0x11c7 / 0x11c8 不是类 pTD 地址（pTD 全落 .data），且 0x6d1770 自身被直接 call/jmp 各 0 次。

## 你要做的
1. 逐条独立验证 M1–M10。**不要读 _r209 的 py 脚本照抄其判据**，自己写判据（可以用 json 做交叉但不作为唯一依据）。
2. 特别攻击这几处：
   - M4 的 303/303 是不是把 101 张表数错？换一种口径（按 COL 计、按槽计）分子分母各是多少？
   - M6 的 ret 分布：如果函数内第一个 ret 不在前 900 字节怎么办？换更宽松窗口重测，结论会变吗？
   - M7 的"主视图"定义：若某组 mdisp==0 的记录不止 1 条怎么办？实测有几组异常？
   - M8 的 slot3/slot4：是否有其他表也出现 idx>=3 的 thunk 而主会话漏了？换扫描口径（不依赖已缓存的 json）重测。
   - M10 的 0x11c7：会不会其实是某个立即数被误读？给出你的独立取值。
3. 指出主会话**表述过强或口径含混**的地方（这是本次审计最有价值的部分）。

## 输出纪律
- 每项给 PASS / FAIL / 存疑 + 你的实测数字。
- 最后一行写 断言 N 项 / FAIL M 项。
- 严禁修改任何文件，严禁在输出里用反引号。
