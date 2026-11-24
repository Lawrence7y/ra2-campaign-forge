镜像 D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe  sha256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

结论摘要：988 个装饰名全部是 .data 内 MSVC TypeDescriptor 的内嵌 name 字段；未在 .data/.rdata 找到单一 988 项指针数组，但找到 stride=0x18 的 RTTI base-class 指针数组；九个 vtable 均可用 vtable[-4] 的 RTTI COL 链自证类名。

## 扫描范围（只读）
- 镜像大小 4825360 B；PE image base 0x400000。
- 扫描 1：.rdata，VA 0x3E2000..0x412000，raw 0x3E2000，长度 0x30000 = 196608 B（截到 .data 起点，避开文件重叠）。
- 扫描 2：.data，VA 0x412000..0x478000，raw 0x412000，长度 0x6C000 = 442368 B（rawSize；VirtualSize 0x367464 尾部无文件字节）。
- 合计 638976 B。未扫描 .text 等节；未建进程、未调试。

## Q1 .data 名字表结构
- 前缀分布：总计 988；.?AV 962，.?AU 26，.?AW 0，??_7 0，其它 0。全部在 .data。
- 连续性：无 NUL 紧邻的连续段；988 个名字各自独立成段（run=988）。首名 0x815DE8 ".?AVFileClass@@"，末名 0x87DA18。
- 结构字节依据：对每个名字取 name-8，988/988 处均为 `94 95 7F 00 00 00 00 00`，即 TypeDescriptor 的 type_info vftable 指针 0x7F9594 + 0 spare；name 恒在 TD+8。例：0x815DE0 处 `94 95 7F 00 00 00 00 00 2E 3F 41 56 ...`，0x815DE8 = ".?AVFileClass@@"。
- 数据引用：.data/.rdata 内精确 name 指针命中 1 处：0x87C5F8 -> 0x840010 ".?AVSmudgeTypeClass@@"。对 TD base（name-8）命中 2221 处，均在 .rdata，绝大多数为 RTTI COL / hierarchy 结构字段；这不是“代码逐个引用名字”，而是 RTTI 结构间接持有。
- 等距指针数组：有，但不是一张 988 项总表。命中 3 段长度≥4 的 stride 0x18 数组，共 17 项：
  - 0x7FA4F0，5 项，索引 0..4：FileClass / RawFileClass / BufferIOFileClass / CDFileClass / CCFileClass；
  - 0x7FA8C8，4 项，索引 0..3；
  - 0x7FA9C8，8 项，索引 0..7。
  元素 24 B，逐字观察为 `[DWORD pTypeDescriptor, DWORD idx, DWORD 00000000, DWORD FFFFFFFF, DWORD 00000000, DWORD 00000000]`，下一元素在 +0x18。字节例：0x7FA4F0 `e0 5d 81 00 00 00 00 00 00 00 00 00 ff ff ff ff 00 00 00 00 00 00 00 00`；0x7FA508 `f8 5d 81 00 01 00 00 00 00 00 00 00 ff ff ff ff 00 00 00 00 00 00 00 00`。未据形态替字段编名。

## Q2 九个 vtable 定主人
- .data/.rdata 内对九个 vtable VA 的 4 字节小端直接引用：全部 0 处（未取得直接数据引用）。
- 但 vtable[-4] 全部指向 .rdata 内合法 RTTI COL；COL+12 指向 TypeDescriptor，TD 头 0x7F9594/0 且 TD+8 为装饰名。COL 的 offset 字段依次为 0/4/8/12，符合同一多重继承类的多个 vtable 子对象。
  - 0x7E3EBC：COL 0x7FC360 -> TD 0x818D60 -> ".?AVBuildingClass@@"（offset 0）
  - 0x7E3EA0：COL 0x7FC2E0 -> TD 0x818D60 -> ".?AVBuildingClass@@"（offset 4）
  - 0x7E3E98：COL 0x7FC2C8 -> TD 0x818D60 -> ".?AVBuildingClass@@"（offset 8）
  - 0x7E3E90：COL 0x7FC2B0 -> TD 0x818D60 -> ".?AVBuildingClass@@"（offset 12）
  - 0x7F4960：COL 0x80C058 -> TD 0x817B58 -> ".?AVTechnoClass@@"（offset 0）
  - 0x7F4944：COL 0x80BFF0 -> TD 0x817B58 -> ".?AVTechnoClass@@"（offset 4）
  - 0x7F493C：COL 0x80BFD8 -> TD 0x817B58 -> ".?AVTechnoClass@@"（offset 8）
  - 0x7F4934：COL 0x80BFC0 -> TD 0x817B58 -> ".?AVTechnoClass@@"（offset 12）
  - 0x7E4E78：COL 0x7FCFC8 -> TD 0x81C058 -> ".?AV?$DynamicVectorClass@H@@"（offset 0）
- 字节例：0x7FC2B0 `00 00 00 00 0c 00 00 00 00 00 00 00 60 8d 81 00 50 c3 7f 00`；0x818D60 `94 95 7f 00 00 00 00 00 2e 3f 41 56 42 75 69 6c 64 69 6e 67 43 6c 61 73 73 40 40 00`。
- 判定：九个均可定类名，依据为二进制内 RTTI 自证；未使用 YRpp 或相似形态猜测。

## Q3 交叉检验 R14_COMMON §2.6
- 0x6F2B40 的 primary vtable 组 0x7F4960/0x7F4944/0x7F493C/0x7F4934 经上述 RTTI 链全部指向 ".?AVTechnoClass@@"。
- 结论：与 §2.6「0x6F2B40 = TechnoClass 构造器」的记录一致。
- 旁证：0x7E4E78 另属 ".?AV?$DynamicVectorClass@H@@"，不能当作 primary class 名；本结论只取 0x7F4960 组。

## 产物
- names.tsv：988 行，含名字、地址、段、数据精确引用数、TD base 引用数。
- vtable_owner.tsv：九个 vtable 的 RTTI 链与判定。
- work.py：可复跑脚本。
