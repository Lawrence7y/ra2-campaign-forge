# R219-A 高槽 67 个「与父类不同」目标的语义归类

## 环境
工作目录 /home/t628/projects/ra2-campaign-forge 。python3 + capstone 可用。
只读模块 _r185/pe185.py：P.B[段名] 给 lo/rawptr/rawsize；P.RAW 全文件字节；P.dw(va)；P.where(va)；P.cstr(va)。
防 OOM 硬红线：严禁对整段 .text 一次性 md.disasm() 且 detail=True。目标只有几十个地址，
逐个用 md.disasm(字节切片) 即可；不要做全段扫描。

## 背景（主会话已实测，作为正控必须复现）
- 虚表重建律：COL 记录 5 dword 组 (n1, mdisp, 0, pTD 落 .data, pCHD 落 .rdata)，pTD+8 是 ".?AV...@@"
  名字；虚表 = .rdata/.data 里 dword 等于 COL 地址的位置 +4。全库 1218 张，其中 dw(V) 落 .text 的 1214 张为真表。
- 六张大表：UnitClass 0x7f5c70 = 344 槽；InfantryClass 0x7eb058 = 343；AircraftClass 0x7e22a4 = 341；
  FootClass 0x7e8c94 = 341；BuildingClass 0x7e3ebc = 322；TechnoClass 0x7f4960 = 309。
- 槽数判定：从 V 起逐 dword 前进，直到该 dword 不落 .text 为止。
- R218 已算出：六张大表 slot>=256 区间合计 464 槽；与父类同槽比对 same=294 / diff=67 / oob=103；
  R218 只给出 67 个 diff 目标的字节前缀粗分布：other 58 / jmp_rel 4 / mov_eax_arg 4 / push_ebp_std 1。

## 目标 A1（唯一目标）
把 67 个 diff 目标逐个定性，产出逐目标一行表：目标地址 | 前 12 字节 hex | 前 3 条指令 | 前缀类别。
前缀类别定义（必须用同一套判据，逐条给）：
  - jmp_rel  : 首条指令是 jmp rel8/rel32，且跳转落在 .text
  - push_ebp : 首条 0x55 push ebp（标准 prologue）
  - mov_eax_arg : 首条是 mov eax, dword ptr [esp+...] 或 mov eax, dword ptr [ebp+8]（取第一个参数）
  - ret_stub : 首条即 ret / ret imm16
  - cc_pad   : 目标处是 0xCC int3 填充
  - other    : 以上都不是
最后按类别汇总计数，并核对合计必须等于 67。

## 目标 A2（必须做的交叉检查）
对这 67 个地址，逐个报它们的「反查命中数」：全 .rdata + .data 里有多少个 dword 等于该地址（即被多少张虚表引用）。
给出：被引用 1 次的个数、被引用多次的个数（>1 的逐个列出地址与次数）。
判据：若某个 diff 目标只被本表引用 1 次，它是本表专属新增槽；若被多表共用，要列出所有宿主虚表地址。

## 目标 A3（反控）
随机取 20 个 same（与父类相同）目标做对照，报它们的前缀类别分布，
用来证明「diff 目标的前缀分布」不是全表通性。

## 输出格式
一条命令输出全部证据，不要分多次试探。
最后单列「异常与不确定」：特别说明有多少目标的首条指令无法用线性解码确定（例如落在数据里），
以及是否存在目标地址互相重叠（两个槽指向同一地址）。
所有数字必须实跑，禁止预估。产物写到 /home/t628/projects/ra2-campaign-forge/_r219/ ，文件名前缀 cardA_。
