D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe
sha256=73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# R17-R25-SLOT107 · slot #107 (0x449440 / vtable+0x1AC) caller intersection

## 第一步：交集筛

- 输入 hits.tsv：call & disp=0x1AC 共 86 条；call & disp=0x124 共 181 条。
- 输入 ctor_sites.tsv：15 个直接构造点，host 集合 14 个：0X44F820 0X453E20 0X45E800 0X45E880 0X4737F0 0X5904B0 0X595400 0X5A652D 0X5A82E0 0X5A8F00 0X5A95B0 0X5CA800 0X6C3590 0X7393F2。
- 按 host 精确相等求交集：0x1AC=0 条，0x124=0 条；逐条结果见 intersect.tsv。
- 计数复现：hits 侧 0x1AC host 集合与 ctor host 集合无公共元素；hits 侧 0x124 host 集合与 ctor host 集合亦无公共元素。
- 注：ctor_sites.tsv 中上一轮 #73 对应构造点 site=0x5A66D4 的 host 为 0x5A652D；本卡没有把 host 地址放宽到邻近值。

## 第二步：字节链验证

- 因 0x1AC 交集为空，没有可执行逐指令验证的候选；本步反汇编函数数=0，字节链扫描字节数=0，chain_1ac.tsv 仅表头。
- 因此未产生寄存器写点统计，也未形成 site -> host -> fn_end 的 0x449440 调用链。

## 第三步：空集结论与覆盖边界

- 结论：在这 15 个构造点的 host 函数体内，没有 R17_R12 已枚举到的 [reg+0x1AC] 派发 call；0x449440 的调用方本轮未取得。
- 计算依据：两侧条数与 host 集合见上；求交以 host 地址为键，未使用地址邻近、模块基址猜测或跨函数传播放宽。
- 未覆盖：对象经全局/成员字段长距离传递、跨函数传入、或非 0x43B740/0x43B680 直接调用构造；R17_R12 的非标准间接形态（先算目标地址、跳板、索引型、disp8、段覆盖、跨节代码）也可能漏网。

## 结论边界

- 本轮只证明：在给定静态枚举口径下未发现 0x449440 调用方；不证明不存在，不证明唯一，也不证明运行期是否真的执行到。
- 不改变 ②-b 的 [静态推断] 收口（D-53(A)）。

## 产物

- REPORT.md、intersect.tsv、chain_1ac.tsv（表头）、work.py。
