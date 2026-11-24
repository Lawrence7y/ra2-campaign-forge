# AUDIT110（hy4 · 跨家族审计员）

审计对象：_r110/r110a_iidmap.json、_r110/r110b_seh.json。仅做纯文本/数值核对，未运行反汇编脚本，未做字节级判断。

## A1 一致 | 实测 n_qi_classes=172 pct=18.0
json 顶层 n_qi_classes=172。S2 的 detail 为字符串 "{'qi_classes': 172, 'pct': 18.0}"。S1 的 detail 为 "954"，即本轮 vtable 总数 954。复算 172/954*100 = 18.029...，四舍五入 18.0。三项与调度卡叙述吻合。

## A2 一致 | S3 ok=true，detail=空列表 []，无 .text 项
S3 check 名称声称「落在 .text 的 0 个」；json 中该 check 的 ok=true、detail=[]。iid_classes 的 17 个键为 0x7e36c0 至 0x7f7cf0，最小 0x7e36c0、最大 0x7f7cf0，全部位于 S0b 给出的 .text 终点 0x7e038d 之后（.text = [0x401000, 0x7e038d)），逐点比对落入 .text 的指针数 = 0。S3 通过，不存在「把 RVA 当 VA 导致假失败」的迹象。

## A3 一致 | 四项之和 = 172
per_class_n = [[1,1],[2,92],[3,3],[4,76]]。亲手相加：1+92+3+76 = 172，等于 n_qi_classes=172。与调度卡叙述一致。

## A4 一致 | iid_classes 键数 17，guid_of_ptr 键数 17，值去重后仍 17
两个映射的键集合相同（17 个指针）。guid_of_ptr 的 17 个值彼此不同：len(values)=17，len(set(values))=17，无重复 GUID 内容。因此「按指针 17 = 按内容 17，无不同指针指向同一 GUID 内容」的数值前提成立。S6 detail 为 "{'by_ptr': 17, 'by_content': 17}"。

## A5 一致 | with_iunk=171，without_iunk=['AircraftClass']（顶层无 iunk_share 字段，见下说明）
顶层没有名为 iunk_share 的字段；等价数值在两处可直接读出：S7 的 detail = {'with_iunk': 171, 'total': 172, 'without_iunk': ['AircraftClass']}；顶层 without_iunk = ['AircraftClass']。另外对 172 条 rows 逐条检查 iids 数组是否含指针 0x7f7c90，得到含该 IID 的 171 条、不含的 1 条，不含者的 cls 为 AircraftClass。结论与调度卡叙述吻合。说明：若严格要求字段名 iunk_share，则该字段缺失；但所需数值已由 S7.detail.with_iunk 给出并可由 rows 独立复算，故本条判一致而非无法判定。

## A6 一致 | seh_funcs 长度 6，hb=17766
seh_funcs 实测列表为 ["0x6bb990","0x7ca650","0x7cc0dc","0x7cd790","0x7d0d3c","0x7d7ee0"]，长度 6；顶层 hb=17766。复算 6/17766*100 = 0.0338%，取两位小数为 0.03%。E1e detail = {'seh_funcs': 6, 'hb': 17766, 'pct': 0.03}。一致。

## A7 一致 | funcinfo 列表唯一一项节名为 .data，.text 项 0 个
funcinfo = [["0x87c1d0", ".data", "0x19930520", "0x87c1e8", "0x0", "0x7f9788"]]，节名字段为 .data，不是 .text；逐项统计节名等于 .text 的数量 = 0。E2b detail = [('0x87c1d0', '.data')]，ok=true。一致。

## A8 一致 | E4 三个支撑数字与结论不矛盾
E4 detail = {'seh_pct': 0.03, 'funcinfo': 1, 'refs': 3}。独立复算：seh_funcs/hb = 6/17766 = 0.03%（E1e）；funcinfo 列表长度 1（E2a 完整形态 1 条）；text_refs 列表长度 3（E3）。三个数字均极小，与「第二套函数边界不存在」结论方向一致，未发现任一数字与结论矛盾。注意 E2a 另有 1 条不满足形态的巧合命中（funcinfo_coincid = [['0x7f993c','.rdata','0x19930520']]），在 .rdata 且非完整形态，不影响 E4。

## 总判定
- 一致 8 条 / 不一致 0 条 / 无法判定 0 条

## 我认为主会话错了的地方（若无写 none）
none

补充说明（非纠错）：A5 所述的 iunk_share 字段名在 json 中不存在，实际使用的字段名是 S7.detail.with_iunk；若要求脚本严格按字段名取数，应调整键名。此外 A1 的 pct=18.0 是 18.029... 的一位小数表示，非精确商。
