# S03-K2 · PROGRESS（文件系统 / MIX / CCFile / 压缩加密 · K2）

> 卡号 S03-K2｜目标 `ra2youli\gamemd.exe` SHA256 `73201CC0…F67476`（本卡复核一致）｜全部只读。
> 双通道：A=capstone(skipdata=True)+pefile+RTTI/字节扫描；B=磁盘真实 MIX 文件（langmd/theme 等）头+索引反查。两条均不依赖 function_atlas 做「函数/入口」判定（atlas 仅用于 T1 集合筛）。

## 结论表

| # | 结论 | 级 | 证据 |
|---|---|---|---|
| 1 | **MIX 头结构定出**：旧式 `u16 num+u32 body`(6B)；新式 `u16 0+u16 flags+u16 num+u32 body`(10B)；索引 `num×12B {id,offset,size}`，无文件名表；flags.bit0=尾 20B SHA1、bit1=加密 | 已证 | `E_T2_hash_mix.txt`/`E_T2_findorder_header.txt`/`E_T2_bootstrap_sha1.txt` |
| 2 | **hash 算法定出**：`0x4A1DE0` = 反射 CRC32(poly `0xEDB88320`,表 `0x81F7B4`,init/final `NOT`) + `len%4` 尾填充 `buf[r]=r, buf[r+1..3]=buf[0]`；名字先 `strupr 0x7DCFC4` | 已证 | `E_T2_hash_mix.txt`（langmd 8/8 命中，zlib 0/8） |
| 3 | 查找链：`Get_File 0x473D10`→磁盘 `0x431F10`(0x473D2D,失败才)→`Find 0x5B4430`(strupr 5B4470/hash 5B449C/链表头 `[0xABEFE0]`@5B44A1/12B 二分 5B44D5) | 已证 | `E_T2_lookup_chain.txt` |
| 4 | **散装优先于 MIX**：Get_File 先试磁盘 `0x431F10`，成功即返回；MIX 间链表 `[ebp+4]` 从头向尾 FIFO，先注册先查 | 已证 | `E_T2_lookup_chain.txt`/`E_T2_findorder_header.txt` |
| 5 | 5 类 vtable RTTI 定界（FileClass←RawFile←BufferIO←CDFile←CCFile；MixFile 独立）。Raw `0x7F0904`/BufIO `0x7E3A2C`/CD `0x7E1668`/CC `0x7E16B0`(17槽)/Mix `0x7EDF50`(1槽) | 已证 | `E_T3_rtti_discovery.txt`/`E_T3_vtables.txt` |
| 6 | **GetSize 闭合 2/5**：五类全无 `B8 imm32 C3` 槽(v[12]均普通函数)；分配点对账仅 CCFile `0x6C`(ctor 0x4739F0)/MixFile `0x28`(ctor 0x5B3C20) 唯一 size；3 内嵌基类无独立堆分配 | 已证 | `E_T3_vtables.txt`/`E_T3_allocsize.txt` |
| 7 | 字段双支撑：BufferIO `+0x29`(7W/3R)、`+0x30`buffer 指针(3W/2R,dtor free)；RawFile `+0x14`句柄(3W/7R)/`+0x18`名(3W/14R)/`+0x20`标志(3W/3R) | 已证 | `E_T3_fieldscan.txt` |
| 8 | 压缩/加密：LZO RTTI `LZOPipe@@`/`LZOStraw@@`@`0x82A00C`、`PKStraw@@`@`0x836874`(已证存在)；RSA e=`0x10001`@`0x52A6AF`、blowfish.dll@`0x840A78`、flag bit1 旁路 `0x5B3D11`(常量已证,分组未 dump) | 混合 | `E_T4_crypto.txt` |
| 9 | 4 条 S03 入口由 [静态推断]/[未证] 提 [已证]（3 个 dtor + 0x65CA00）：字节级 vptr 写 + 基类 dtor/delete 链 | 已证 | `coverage_delta.tsv`/`E_T3_ctors_alloc.txt` |

## 核心数字（给审计，含复算）

| 数字 | 本卡值 | 复算 |
|---|---|---|
| S03∩atlas（大小写归一后） | **194** | `python work/t1_targets.py`；coverage S03 196 行，2 行非 atlas |
| named_L / named_S | **125 / 125**（均 64.43%） | 同上；S03 无 `Class::sub_` 占位 ⇒ L=S |
| proved 基线 | **18（9.28%）**，非派卡 11 | `PANEL.md:35` + t1 自算一致；派卡 11 系旧截面（D1，未凑数） |
| 到 50% 闸门（97/194）差 | **79 个 proved** | 97−18=79；加本卡 4 条后为 75 |
| hash 命中 | **8/8**（zlib 0/8） | `python work/t2_hash_verify.py`，读 langmd.mix 官方索引 |
| GetSize 闭合 | **2/5** | `python work/t3_allocsize.py`：new(size)↔ctor 紧邻，CC=0x6C/Mix=0x28 唯一 |
| 本卡 delta | **+4 proved** | `coverage_delta.tsv` 4 行 |

## 复跑命令
```
cd D:\Project\ra2-campaign-forge
python lead\next_re_20261117_r14\S03-K2\work\t1_targets.py
python lead\next_re_20261117_r14\S03-K2\work\t2_hash_verify.py
python lead\next_re_20261117_r14\S03-K2\work\t2_lookup_chain.py
python lead\next_re_20261117_r14\S03-K2\work\t3_rtti.py
python lead\next_re_20261117_r14\S03-K2\work\t3_vtables.py
python lead\next_re_20261117_r14\S03-K2\work\t3_fieldscan.py
python lead\next_re_20261117_r14\S03-K2\work\t4_crypto.py
```

## 停机核验
自算 194/125/18 与 `PANEL.md:35` 一致；**派卡 proved=11 与盘面 18 不符**（纪律 9 停机项，已写 D1/U5，未凑数）。「先测基线」：hash 8/8 配 zlib 0/8 阴性对照、GetSize 纯字节 666/837 基线已在 `MIX.md`/`LAYOUT.md` 标注，不靠形态计数下结论。
