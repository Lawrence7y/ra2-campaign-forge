# S03-K1 · PROGRESS（文件系统 / MIX / CCFile）

> 卡号 S03-K1｜Δ目标 `ra2youli\gamemd.exe` SHA256 `73201CC0…F67476`（本卡复核一致）。
> 双通道：A=capstone(skipdata=True)+pefile+RTTI/字节扫描；B=Ghidra SLEIGH（E08，-noanalysis，副本用完已删）。两条均不依赖 function_atlas。

## 结论表

| # | 结论 | 级 | 证据 |
|---|---|---|---|
| 1 | CCFileClass vft=`0x7E16B0` ctor=`0x4739F0`(ret4)；MixFileClass vft=`0x7EDF50` ctor=`0x5B3C20`(ret8)，均 RTTI 实证 | 已证 | E01_rtti.txt / E02_vtables_getsize.txt |
| 2 | CCFileClass **12 字段**，max=`+0x68+4=0x6C`；文件名是指针(+0x18,strdup)非内联；**无持久化 MIX 指针字段** | 已证 | E03/E09_basefields.txt |
| 3 | MixFileClass **12 字段**，max=`+0x24+4=0x28` | 已证 | E04_mixfile_methods.txt |
| 4 | MIX 索引项 **12 字节** `{u32 id;u32 offset;u32 size}`：ctor `numFiles*12` 分配 + Find 12B 步长二分，两处独立 | 已证 | E04 / E08(Ghidra) |
| 5 | 哈希函数 **`0x4A1DE0`** = CRC32：init=`0xFFFFFFFF`(NOT@4A1E79)、poly=`0xEDB88320`(表`0x81F7B4` u32[1]=77073096)、final xor=`0xFFFFFFFF`(NOT@4A1E9E)；名字先 `strupr 0x7DCFC4` | 已证 | E05_hash_chain_alloc.txt / E08 |
| 6 | MIX 查找链：Get_File`0x473D10` 磁盘`0x473D2D`→Find`0x473D68`；Find 内 strupr`5B4470`/hash`5B4499`/链表头`5B44A1`/二分`5B44D5`；散装优先、MIX 内 FIFO | 已证 | E05 / E04 |
| 7 | 加密 MIX：flags bit1@`5B3D0E` 控密钥块；PKStraw`0x633050`+RSA(e=0x10001@52A6AF)+Blowfish(blowfish.dll)；bit1=0 明文旁路`5B3D11` | 静态推断 | E04（入口/常量实证，分组层未逐条 dump） |
| 8 | 散装与 MIX 内 INI **汇合于 `INIClass::Load 0x4741F0`**(→内层`0x525A60`)：BATTLE`52CB90`/RULE`52CD70` 通配枚举→ctor`4739F0`→Load`4741F0`；回退字面量名同路，MIX 回落由`473D68`决定 | 已证 | E07_ini_convergence.txt |
| 9 | 越界写 **0 处**：CC ctor 10 写点、Mix ctor 21 写点，disp+width≤size 全成立 | 已证 | E06_newsize_oob.txt |
| 10 | **GetSize 修正**：两类非 AbstractClass 派生，无 `v[12]=B8 imm C3` GetSize（CC v[12]=`473AE0` 是 `ret8` 方法；Mix vft 仅 1 槽）；改用 new(size)↔字段max 两处对账 | 已证 | E02 / E05 / E06 |

## 核心数字（给审计，含复算方法）

| 数字 | 本卡值 | 复算 |
|---|---|---|
| 两类字段数 | CC=**12** / Mix=**12** | LAYOUT §1/§2 行数；Mix ctor 写点 E06 数 12 个不同 disp |
| 对象大小（等价 GetSize） | CC=**0x6C** / Mix=**0x28** | 复跑 `s05_oob.py`：ctor 调用点前 `push imm;call 7C8E17` 统计 + 字段 max 对账 |
| 越界写数 | **0** | `python work/s05_oob.py` 末段 OOB 列表为空 |
| MIX 索引项 | **12 B** | E04 `5B3D81 lea edx,[eax+eax*2]`+`5B3D87 shl edx,2`；Ghidra E08 复核 |
| 哈希函数地址 | **`0x4A1DE0`** | E05 `5B4499 call 4A1DE0`；表 `0x81F7B4` 首项 77073096=反射 CRC32 多项式 |

## 复跑命令

```
cd D:\Project\ra2-campaign-forge
python lead\next_re_20261117_r14\S03-K1\work\s01_rtti.py        # E01
python lead\next_re_20261117_r14\S03-K1\work\s02_getsize.py     # E02
python lead\next_re_20261117_r14\S03-K1\work\s03_dump.py        # E03 E04
python lead\next_re_20261117_r14\S03-K1\work\s04_hash_chain.py  # E05
python lead\next_re_20261117_r14\S03-K1\work\s05_oob.py         # E06
python lead\next_re_20261117_r14\S03-K1\work\s06_ini.py         # E07
python lead\next_re_20261117_r14\S03-K1\work\s07_basefields.py  # E09
```

## 停机核验

自算 12/12、0x6C/0x28、0 越界、12B、0x4A1DE0 与派卡预期（索引12B/越界0）一致；GetSize 项与模板措辞不符（见 DISAGREE），已按纪律停机记录并改用等价核对，未编造值。
