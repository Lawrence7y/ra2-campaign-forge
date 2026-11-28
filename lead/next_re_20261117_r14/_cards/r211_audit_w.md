R211 跨家族只读复核卡（deepseek-v4.1-flash，role=audit，预算 50 轮，一次到位）

工作目录 /home/t628/projects/ra2-campaign-forge
目标文件 ra2bench/gamemd.exe（PE32，ImageBase 0x400000）
只读复核，禁止写盘到除 _r211/audit_deepseek.json 以外的任何路径。

背景：R210 定稿「律 U：类的视图偏移集合 V(c) = (R 非空) ? ({4} ∪ R) : 空集，R 为主视图 slot0 QI
返回的 this 正偏移集合」，并把 HouseClass 记为「唯一不匹配反例」。R211 主会话新提出更强、更本质的
律 W，请你独立复算，不要采信我方结论。

BCD 实测口径（请自行验证后再用）：
  BCD 24 字节，依次为 +0 pTD、+4 numContainedBases、+8 mdisp、+12 pdisp、+16 vdisp、+20 attributes
  COL 记录：+0 signature(0/1/2)、+4 mdisp、+8 cdOffset(恒0)、+12 pTD、+16 pCHD，COL 地址 +16 处内嵌本类 own 记录
  CHD 16 字节：+0 signature、+4 attributes、+8 numBaseClasses、+12 pBCA；BCA 元素是 BCD 记录地址

待复核断言（逐条给 PASS/FAIL + 实测数字，禁止预估）：
G1  COL/CHD/BCA 口径：COL 记录 1214 条 / CHD 954 个 / BCA 记录合计 2615 条；
    其中 mdisp != 0 的记录 387 条。
G2  律 W（核心）：定义 INTERFACE = pTD 名字以 .?AU 开头的类型描述符；
    TD_OWN = 954 个 own COL 记录的 pTD 集合。
    V(c) 由「同 CHD 下全部 COL 记录的 mdisp，去掉 0」重建（不要用 vftable 扫描）。
    断言 V(c) == { mdisp(r) : r ∈ BCA(c), mdisp(r) != 0, pTD(r) ∈ INTERFACE ∪ TD_OWN } 对全部 954 类成立，失配 0。
G3  等价式：把条件换成「pTD 名字不以 .?AV 开头 ∨ pTD ∈ TD_OWN」，失配仍为 0。
G4  反控 C0：不加任何 pTD 过滤（全部非零 mdisp），失配类数应为 15。
G5  反控 C4：只用 pTD ∈ TD_OWN 过滤，失配类数应为 91。
G6  反控 C5：只用 .?AU 前缀过滤，失配类数应为 81。
G7  反控 C1：把全部 954 类 BCA 的非零 mdisp 并集套给每个类，成立类数应为 0。
G8  律 W 的排除集（G4 多出来的那些记录）涉及的 pTD 恰好 5 个，且全部满足
    「名字以 .?AV 开头 ∧ 不被任何 COL 记录引用（onlysec）」：
    0x817ab8 .?AVStageClass@@、0x817ad8 .?AVFlasherClass@@、0x845e30 .?AVBounceClass@@、
    0x84a838 .?AVCComObjectRootBase@ATL@@、0x84a860 .?AV?$CComObjectRootEx@VCComMultiThreadModel@ATL@@@ATL@@
G9  8 个「{4} 独立附加项」类的 COL 地址与 mdisp=4 记录的第二记录身份：
    HouseClass 0x802a18 与 AircraftClass 0x7fb4b0 的 mdisp=4 第二记录是 .?AUIRTTITypeInfo@@；
    6 个 Locomotion（0x7ffea0 Drive / 0x800098 DropPod / 0x804ce0 Jumpjet / 0x8093f8 Ship /
    0x80c1d0 Teleport / 0x80d298 Walk）的 mdisp=4 第二记录是 .?AUILocomotion@@；
    全部 8 类的 mdisp=4 记录里都另有一条 .?AUIUnknown@@（nc=0, attr=0x2）。
G10 mdisp=4 记录按 pTD 组合分组：.?AUIRTTITypeInfo@@+.?AUIUnknown@@ 78 类 /
    .?AUILocomotion@@+.?AUIUnknown@@ 12 类 / CComObjectRootEx+CComObjectRootBase 5 类 /
    .?AUILinkStream@@+.?AUIUnknown@@ 1 类，合计 96 类。
G11 4∈V 的类 91 个；4∈B 的类 96 个；差集 5 个恰为 G8 的 5 个 ATL EventSink 类
    （0x80e680 / 0x80e740 / 0x80e780 / 0x80e7c0 / 0x80e998），它们的 V 为空集。
G12 HouseClass 0x802a18 的 V = [4,8,12,36,40,44]；其主视图 slot0 函数是 0x4f6830。

产出：把每条断言的实测值写成 JSON 到
/home/t628/projects/ra2-campaign-forge/_r211/audit_deepseek.json
格式 {"G1":{"pass":bool,"values":{...}},...}。最后在回复正文给一张 PASS/FAIL 表 + 每个 FAIL 的原因。
纪律：一条命令输出一批证据，不要逐条试探；禁止对整段 .text 开 capstone detail=True 全量反汇编。
