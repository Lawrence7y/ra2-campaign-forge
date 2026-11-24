# PROGRESS — NAMED-PUSH S12 B2

每 5 行追加一次。落盘节奏：每核完一行立刻写 `EVIDENCE/ROW_<entry>.txt`。

## 起点
- 读卡 `_cards\NAMED-PUSH.md`（80 行全文）
- 建目录 `NAMED_PUSH_S12_B2\{EVIDENCE,_work}`，先写 `REPORT.md` 骨架
- 筛选：S12 `p3b2_named=True` 共 **33** 行，`fn_`/`sub_` 伪名 **0** 行；第 19..36 个实际只有 **15** 行 ⇒ 本批 15 行（`0044EFB0 … 00705CA0`）
- 材料自校验：SHA-256 逐字一致 `73201CC0…F67476`；`.text=[0x401000,0x7E038D)`；capstone 5.0.7 skipdata=True；pefile 2024.8.26
- 陷阱③ 前置：4 个类的主虚表全部钉死（slot0 均 = `00410260`），小成员表 12 张逐张排除

## 1–5 行（`0044EFB0` `00453E20` `00454190` `00456750` `0045E800`）
- ①② 5/5 PASS；④ 5/5 PASS（构造安装点，atexit 全空）
- ③ 仅 `00453E20` 成立：`0x453EB3 call 0x70BF50` → `cmp eax,ebx`(ebx=0) → `jl 0x45417E`（落点不碰 eax ⇒ 负 HRESULT 上抛），被调 `0x70BF50` 尾部 `0x70C246 mov eax,ebx(=0)` ⇒ 成功 0
- `00454190` 关键负结果：直接被调 `0x70C250` 25 B 尾 `xor eax,eax; ret 0xc`，**恒返 0** ⇒ `test ebp,ebp; jl` 是死分支（与对偶行 `00453E20` 的唯一差别）
- `0044EFB0` 的两处 `cmp eax,-1; jl` 判的是表项计数（同函数 `cmp ebp,eax; jle` 自证是循环上界）
- `0045E800` / `00456750`：分配判空 / 数值 getter + `jle` 范围判定

## 6–10 行（`0045E880` `0045EBD0` `0045F040` `0045FE50` `00465300`）
- ①② 5/5 PASS；④ 5/5 PASS
- ③ 仅 `00465300` 成立：`0x465313 call 0x716DC0` → `test eax,eax` → `jl 0x46536A`（落点不碰 eax），成功侧 `0x465368 xor eax,eax`
- `0045E880`（43 B new+construct 薄壳）/ `0045E800`（分配→构造→放置）都是 NULL 判空
- `0045EBD0`（slot39 取值 + 16 B 复制）/ `0045F040`（`call 0x4A3890` 返回指针或 0）都是指针非空 + 零默认
- `0045FE50`（19475 B，28 站点）三类全否：`call 0x528A10` 返「0 或正长度」的空串判定、`call 0x7514D0` Find(-1) 后**只差一条 `mov eax,edi` 默认值回填**、`call 0x5276D0` 配置量数值范围判定

## 11–15 行（`004728E0` `004729C0` `004CA3C0` `004CA770` `00705CA0`）
- ①② 5/5 PASS；④ 5/5 PASS
- ③ 4 行成立：`004728E0` / `004CA3C0`（`call 0x410320` 具名 HRESULT E_POINTER=0x80004003，`test eax,eax; jl` 或落点跳过 `xor eax,eax` ⇒ 负值原样上抛）；`004729C0` / `004CA770`（全局 `DynamicVectorClass` Find 未命中=-1 + count-- 压缩移除，`or eax,0xFFFFFFFF; ret 4` 字节铁证）
- `00705CA0` 不成立：`cmp eax,1` 是建筑状态常量比较 + `[esi+0x2B4]` 指针判空
- ㉓ 关键：`004729C0` / `004CA770` **本身就是删除式析构器**（`test byte [esp+0xc],1` + `call 0x7C8B3D` free + 基类析构），故其自身 vptr 重装点 **不作 ④**，改锚同类的构造安装点

## 收尾
- `delta.tsv` 6 行 / 6 列，reason 全互异，evidence_path 全部存在
- `base_rate.tsv`：`S12_B2  15  15  6  15  6  0.4000`
- `EVIDENCE/ROW_*.txt` × 15 全部落盘
- `_work/selfcheck.py` 回算：15 行 ② 槽值/COL/TD/RTTI/槽0、8 个构造安装点（含 atexit 与析构签名排查）、6 个成立行的站点字节与被调落点不写 eax、产物一致性与列数/格式 ⇒ **全绿 0 失败**
