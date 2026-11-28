# R220-B 取证报告（执行员 hy4）

- 判据脚本：`_r220/B_forensics.py`（本脚本，单命令 one-shot）。
- 目标文件：`ra2bench/gamemd.exe`，SHA256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`，大小 4825360 B。
- `.text` VA `0x401000..0x7e1000`，文件 `0x1000 + 0x3e0000`；PE 映射 `_r185.pe185`，ImageBase `0x400000`。
- 扫描口径：`disasm_lite` 64KB 分块 + `skipdata=True` 逐字节 resync；仅对含 `[` 的指令用 `detail=True` 单条重解码；全段指令数见下。

## T1 派发表本体（0x87c484）

| # | 地址 | dword0 | dword1 | dword2 | 三个 dword 是否落 .text |
|---:|---|---|---|---|---|
| 0 | 0x87c484 | 0x0 | 0x7ce046 | 0x7f97d0 | N,Y,N |
| 1 | 0x87c490 | 0x87c370 | 0x7d6ce7 | 0x7f97c4 | N,Y,N |
| 2 | 0x87c49c | 0x87c370 | 0x7d6aa2 | 0x7f97b8 | N,Y,N |
| 3 | 0x87c4a8 | 0x87c370 | 0x7d6830 | 0x7f97ac | N,Y,N |
| 4 | 0x87c4b4 | 0x87c370 | 0x7d6624 | 0x7f97a4 | N,Y,N |
| 5 | 0x87c4c0 | 0x87c370 | 0x7d60b5 | 0x7f9858 | N,Y,N |
| 6 | 0x87c4cc | 0x7f9848 | 0x7d7ed2 | 0x7d7ed2 | N,Y,Y |
| 7 | 0x87c4d8 | 0x7d7ed2 | 0x7d7ed2 | 0x7d7ed2 | Y,Y,Y |

- 上界 `cmp edi, 0x87c4c0`（0x7cdd08）：`0x87c4c0-0x87c484 = 0x3c = 60`，除以 12 = 商 **5** 余 **0**。
- 结论：上界 `0x87c4c0` 恰为起始算起第 5 个完整 12B 记录的终点（`0x87c484+5*12`），故循环覆盖条目 0..4（共 5 条），条目 5（起点即 0x87c4c0）及以后不计入；表实际可读 8 条，但按上界语义有效 5 条。
- dword0：0（空）或 `0x87c370`/`0x87c4?` 段表内数据指针（非 .text）；dword1：全部 8/8 在 .text；dword2：前 6 条在 .data 派生区（非 .text），后 2 条在 .text。

## T2 各目标代码（前 6 条 disasm_lite）

### 0x7ce046

```asm
0x7ce046  xor      eax, eax
0x7ce048  ret      
0x7ce049  push     edi
0x7ce04a  mov      edi, dword ptr [esp + 0xc]
0x7ce04e  test     edi, edi
0x7ce050  jle      0x7ce06c
```

### 0x7d6ce7

```asm
0x7d6ce7  xor      eax, eax
0x7d6ce9  ret      
0x7d6cea  int3     
0x7d6ceb  int3     
0x7d6cec  int3     
0x7d6ced  int3     
```

### 0x7d6aa2

```asm
0x7d6aa2  push     ebp
0x7d6aa3  mov      ebp, esp
0x7d6aa5  sub      esp, 0x24
0x7d6aa8  push     ebx
0x7d6aa9  xor      ebx, ebx
0x7d6aab  cmp      dword ptr [0xb782a0], ebx
```

### 0x7d6830

```asm
0x7d6830  cmp      dword ptr [0xb782a4], 0
0x7d6837  push     esi
0x7d6838  je       0x7d68b0
0x7d683a  push     0x30
0x7d683c  push     1
0x7d683e  call     0x7d3374
```

### 0x7d6624

```asm
0x7d6624  push     ebx
0x7d6625  xor      ebx, ebx
0x7d6627  cmp      dword ptr [0xb782a8], ebx
0x7d662d  push     ebp
0x7d662e  push     edi
0x7d662f  movzx    edi, word ptr [0xb7853a]
```

### 0x7d60b5

```asm
0x7d60b5  cmp      dword ptr [0xb782ac], 0
0x7d60bc  push     esi
0x7d60bd  je       0x7d6119
0x7d60bf  push     0xac
0x7d60c4  push     1
0x7d60c6  call     0x7d3374
```

### 0x7d7ed2

```asm
0x7d7ed2  push     2
0x7d7ed4  call     0x7cd917
0x7d7ed9  pop      ecx
0x7d7eda  ret      
0x7d7edb  int3     
0x7d7edc  int3     
```

### 0x7ce046 桩判定

```asm
0x7ce046  xor      eax, eax
0x7ce048  ret      
0x7ce049  push     edi
0x7ce04a  mov      edi, dword ptr [esp + 0xc]
0x7ce04e  test     edi, edi
0x7ce050  jle      0x7ce06c
```

- 判定：**True**（前两条 `xor eax,eax` / `ret`，是 2 字节返回 0 的桩；后续字节属下一函数）。
- 语义：dword1=0x7ce046 的条目为 NULL/Object 返回值桩，调用方 `test eax,eax` 会判为失败/空。

## T3 调用点 0x7cde2b 上下文（0x7cdd80..0x7cde60）

```asm
0x7cdd80  add      byte ptr [ebx - 0x3f7aeb3c], al
0x7cdd86  je       0x7cde54
0x7cdd8c  lea      eax, [ebp - 0xa4]
0x7cdd92  push     eax
0x7cdd93  call     0x7d15a0
0x7cdd98  inc      eax
0x7cdd99  push     eax
0x7cdd9a  call     0x7c9430
0x7cdd9f  pop      ecx
0x7cdda0  mov      dword ptr [ebp + 0xc], eax
0x7cdda3  test     eax, eax
0x7cdda5  pop      ecx
0x7cdda6  je       0x7cde54
0x7cddac  lea      esi, [edi + edi*2]   ; <== 关键
0x7cddaf  lea      ebx, [edi*4 + 0xb78298]
0x7cddb6  shl      esi, 2   ; <== 关键
0x7cddb9  push     6
0x7cddbb  mov      eax, dword ptr [esi + 0x87c484]
0x7cddc1  mov      dword ptr [ebp + 8], eax
0x7cddc4  mov      eax, dword ptr [ebx]
0x7cddc6  mov      dword ptr [ebp - 0x14], eax
0x7cddc9  lea      eax, [edi + edi*2]
0x7cddcc  lea      eax, [eax*2 + 0xb78520]
0x7cddd3  mov      dword ptr [ebp - 8], eax
0x7cddd6  push     eax
0x7cddd7  lea      eax, [ebp - 0x20]
0x7cddda  push     eax
0x7cdddb  call     0x7d0a20
0x7cdde0  mov      eax, dword ptr [0xb782b0]
0x7cdde5  mov      dword ptr [ebp - 4], eax
0x7cdde8  lea      eax, [ebp - 0xa4]
0x7cddee  push     eax
0x7cddef  push     dword ptr [ebp + 0xc]
0x7cddf2  call     0x7d4bf0
0x7cddf7  mov      dword ptr [esi + 0x87c484], eax
0x7cddfd  push     6
0x7cddff  movzx    eax, word ptr [ebp - 0x10]
0x7cde03  mov      dword ptr [ebx], eax
0x7cde05  lea      eax, [ebp - 0x10]
0x7cde08  push     eax
0x7cde09  push     dword ptr [ebp - 8]
0x7cde0c  call     0x7d0a20
0x7cde11  mov      eax, dword ptr [ebp - 0x18]
0x7cde14  add      esp, 0x20
0x7cde17  cmp      edi, 2
0x7cde1a  jne      0x7cde21
0x7cde1c  mov      dword ptr [0xb782b0], eax
0x7cde21  cmp      edi, 1
0x7cde24  jne      0x7cde2b
0x7cde26  mov      dword ptr [0xb782b4], eax
0x7cde2b  call     dword ptr [esi + 0x87c488]   ; <== 关键
0x7cde31  test     eax, eax
0x7cde33  je       0x7cde58
0x7cde35  mov      eax, dword ptr [ebp + 8]
0x7cde38  push     dword ptr [ebp + 0xc]
0x7cde3b  mov      dword ptr [esi + 0x87c484], eax
0x7cde41  call     0x7c93e8
0x7cde46  mov      eax, dword ptr [ebp - 0x14]
0x7cde49  pop      ecx
0x7cde4a  mov      dword ptr [ebx], eax
0x7cde4c  mov      eax, dword ptr [ebp - 4]
0x7cde4f  mov      dword ptr [0xb782b0], eax
0x7cde54  xor      eax, eax
0x7cde56  jmp      0x7cde70
0x7cde58  cmp      dword ptr [ebp + 8], 0x87c370
0x7cde5f  je       0x7cde6a
```

- **esi 构造链**：`0x7cddac lea esi,[edi+edi*2]` → `esi=3*edi`；`0x7cddb6 shl esi,2` → `esi=12*edi`（12 字节/记录步长）；随后 `mov eax,[esi+0x87c484]`、`mov edx,[esi+0x87c48c]`、`mov ecx,[esi+0x87c488]` 取记录三个 dword。
- **edi 来源与取值上界**：`esi` 的构造基于 `edi`（`0x7cddac/0x7cddb6`），此 `edi` 是 0..5 的小整数索引（由 `cmp esi,5 / jg` @0x7cdb2c 限定）。另有独立循环变量 `edi`（`0x7cdccf mov edi,esi` 起，遍历派发表字节指针），`0x7cdd04 add edi,0xc` 每轮前进 12 字节，`0x7cdd08 cmp edi,0x87c4c0` + `jle` 把上界限制在表尾 `0x87c484+5*12`，即有效条目 0..4（5 条）。`cmp edi,0x87c4c0` 与 `esi=12*index` 是同一 12 字节步长的两种表现。
- **调用与返回值语义**：`0x7cde2b call dword ptr [esi+0x87c488]`（即 dword1，记录在 12B 内偏移 +4）；`test eax,eax; je 0x7cde58` 判空；非空则 `dword [esi+0x87c484]=eax`（回写 dword0），`call 0x7c93e8` 做后续处理。故 dword1 是「工厂/查询函数指针」，eax=对象指针或 NULL（0x7ce046 桩即返回 NULL），dword0 承载对象状态。
- **函数入口**（0xCC 判界）：`start(0x7cdd80) = 0x7cda90`。
- **E8 调用站点数**：扫描全 .text 的 E8 rel32 指向该 start，命中 **17** 处（最多 20）：0x7c8adf, 0x7c8afa, 0x7c8b16, 0x7cac93, 0x7cacf3, 0x7cad24, 0x7cad8c, 0x7cadef, 0x7cae24, 0x7caec4, 0x7cdcde, 0x7cded9, 0x7cdf85, 0x7cdf97, 0x7d4e76, 0x7d738c, 0x7d739d。

## T4 四字段读写统计（全 .text 逐字节 resync）

| offset | 读次数 | 写次数 | 合计 | 写站点（<=20） | .text imm32 写入数 |
|---:|---:|---:|---:|---|---:|
| 0x77c | 6 | 3 | 9 | 0x6660e1 0x7be6e9 0x7be6ff | 2 |
| 0x780 | 5 | 4 | 9 | 0x6660e7 0x7be6dd 0x7be6f3 0x7be709 | 3 |
| 0x784 | 2 | 10 | 12 | 0x6660ed 0x7be6c9 0x7be741 0x7be75a 0x7be773 0x7be7c1 0x7be7df 0x7be7f8 0x7c3234 0x7c323c | 7 |
| 0x788 | 16 | 14 | 30 | 0x6660f3 0x671762 0x7112b4 0x7be6cf 0x7be74b 0x7be764 0x7be78c 0x7be79f 0x7be7ae 0x7be7e9 0x7be811 0x7be820 0x7c324e 0x7c325a | 9 |

- 0x77c 写入端按函数聚合：0x665e5c:1, 0x7bc640:2。
- 0x77c 写入 .text imm32 明细：0x7be6e9→0x7bea40, 0x7be6ff→0x7bf140。
- 0x780 写入端按函数聚合：0x665e5c:1, 0x7bc640:3。
- 0x780 写入 .text imm32 明细：0x7be6dd→0x7bf230, 0x7be6f3→0x7bf0b0, 0x7be709→0x7bf190。
- 0x784 写入端按函数聚合：0x665e5c:1, 0x7bc640:9。
- 0x784 写入 .text imm32 明细：0x7be741→0x7c3d60, 0x7be75a→0x7c6fc8, 0x7be773→0x7c6dd6, 0x7be7c1→0x7c6e94, 0x7be7df→0x7c4260, 0x7be7f8→0x7c6d40, 0x7c323c→0x7bf220。
- 0x788 写入端按函数聚合：0x665e5c:1, 0x667970:1, 0x6dc83a:1, 0x7bc640:11。
- 0x788 写入 .text imm32 明细：0x7be74b→0x7c3eb0, 0x7be764→0x7c39c0, 0x7be78c→0x7c4b80, 0x7be79f→0x7c4f90, 0x7be7ae→0x7c4730, 0x7be7e9→0x7c43a0, 0x7be811→0x7c57d0, 0x7be820→0x7c53a0, 0x7c325a→0x7bf220。

## T5 两段逐条反汇编 + 12 条 .text 函数地址写入

### 0x7be600..0x7be700

```asm
0x7be600  add      byte ptr [ebx - 0x3974fb3c], al          0083c4048bc6
0x7be606  pop      esi                                      5e
0x7be607  ret                                               c3
0x7be608  mov      esi, dword ptr [esp + 0x10]              8b742410
0x7be60c  mov      eax, esi                                 8bc6
0x7be60e  pop      esi                                      5e
0x7be60f  ret                                               c3
0x7be610  mov      eax, dword ptr [esp + 0x10]              8b442410
0x7be614  mov      dword ptr [eax], 0xffffffff              c700ffffffff
0x7be61a  mov      eax, esi                                 8bc6
0x7be61c  pop      esi                                      5e
0x7be61d  ret                                               c3
0x7be61e  mov      edi, edi                                 8bff
0x7be620  out      0xe5, al                                 e6e5
0x7be622  jnp      0x7be624                                 7b00
0x7be624  mul      ebp                                      f7e5
0x7be626  jnp      0x7be628                                 7b00
0x7be628  or       dh, ah                                   08e6
0x7be62a  jnp      0x7be62c                                 7b00
0x7be62c  or       dh, ah                                   08e6
0x7be62e  jnp      0x7be630                                 7b00
0x7be630  adc      dh, ah                                   10e6
0x7be632  jnp      0x7be634                                 7b00
0x7be634  nop                                               90
0x7be635  nop                                               90
0x7be636  nop                                               90
0x7be637  nop                                               90
0x7be638  nop                                               90
0x7be639  nop                                               90
0x7be63a  nop                                               90
0x7be63b  nop                                               90
0x7be63c  nop                                               90
0x7be63d  nop                                               90
0x7be63e  nop                                               90
0x7be63f  nop                                               90
0x7be640  push     esi                                      56
0x7be641  push     edi                                      57
0x7be642  mov      edi, ecx                                 8bf9
0x7be644  mov      esi, 0x84e738                            be38e78400
0x7be649  mov      ecx, 0x22                                b922000000
0x7be64e  rep movsd dword ptr es:[edi], dword ptr [esi]      f3a5
0x7be650  pop      edi                                      5f
0x7be651  pop      esi                                      5e
0x7be652  ret                                               c3
0x7be653  nop                                               90
0x7be654  nop                                               90
0x7be655  nop                                               90
0x7be656  nop                                               90
0x7be657  nop                                               90
0x7be658  nop                                               90
0x7be659  nop                                               90
0x7be65a  nop                                               90
0x7be65b  nop                                               90
0x7be65c  nop                                               90
0x7be65d  nop                                               90
0x7be65e  nop                                               90
0x7be65f  nop                                               90
0x7be660  or       eax, 0xffffffff                          83c8ff
0x7be663  mov      dword ptr [ecx + 0x6d0], eax             8981d0060000
0x7be669  ret                                               c3
0x7be66a  nop                                               90
0x7be66b  nop                                               90
0x7be66c  nop                                               90
0x7be66d  nop                                               90
0x7be66e  nop                                               90
0x7be66f  nop                                               90
0x7be670  push     esi                                      56
0x7be671  mov      esi, ecx                                 8bf1
0x7be673  xor      eax, eax                                 33c0
0x7be675  xor      ecx, ecx                                 33c9
0x7be677  mov      ax, word ptr [esi + 0xee]                668b86ee000000
0x7be67e  mov      cl, byte ptr [esi + 0xf2]                8a8ef2000000
0x7be684  cdq                                               99
0x7be685  idiv     ecx                                      f7f9
0x7be687  xor      ecx, ecx                                 33c9
0x7be689  mov      dword ptr [esi + 0x6c4], eax             8986c4060000
0x7be68f  mov      cl, byte ptr [esi + 0xf3]                8a8ef3000000
0x7be695  xor      eax, eax                                 33c0
0x7be697  mov      ax, word ptr [esi + 0xf0]                668b86f0000000
0x7be69e  cdq                                               99
0x7be69f  idiv     ecx                                      f7f9
0x7be6a1  mov      edx, dword ptr [esi + 0x6c4]             8b96c4060000
0x7be6a7  xor      ecx, ecx                                 33c9
0x7be6a9  imul     edx, eax                                 0fafd0
0x7be6ac  mov      dword ptr [esi + 0x6c8], eax             8986c8060000
0x7be6b2  mov      dword ptr [esi + 0x6cc], edx             8996cc060000
0x7be6b8  mov      ch, byte ptr [esi + 0xf2]                8aaef2000000
0x7be6be  mov      eax, 0x7bf220                            b820f27b00
0x7be6c3  mov      cl, byte ptr [esi + 0xf3]                8a8ef3000000
0x7be6c9  mov      dword ptr [esi + 0x784], eax             898684070000
0x7be6cf  mov      dword ptr [esi + 0x788], eax             898688070000
0x7be6d5  mov      eax, dword ptr [esi + 0x80]              8b8680000000
0x7be6db  test     al, 1                                    a801
0x7be6dd  mov      dword ptr [esi + 0x780], 0x7bf230        c7868007000030f27b00
0x7be6e7  jne      0x7be6ff                                 7516
0x7be6e9  mov      dword ptr [esi + 0x77c], 0x7bea40        c7867c07000040ea7b00
0x7be6f3  mov      dword ptr [esi + 0x780], 0x7bf0b0        c78680070000b0f07b00
0x7be6fd  jmp      0x7be713                                 eb14
0x7be6ff  mov      dword ptr [esi + 0x77c], 0x7bf140        c7867c07000040f17b00
```

### 0x7c2f00..0x7c3040

```asm
0x7c2f00  add      ch, bl                                   02eb
0x7c2f02  or       al, 0xa8                                 0ca8
0x7c2f04  add      dh, byte ptr [esi + ecx - 0x75]          02740e8b
0x7c2f08  xchg     byte ptr [ecx + eax - 0x3cf50000], ah    86a40100000bc3
0x7c2f0f  mov      dword ptr [esi + 0x1a4], eax             8986a4010000
0x7c2f15  mov      ecx, esi                                 8bce
0x7c2f17  call     dword ptr [esi + 0x77c]                  ff967c070000
0x7c2f1d  mov      edi, eax                                 8bf8
0x7c2f1f  cmp      edi, -1                                  83ffff
0x7c2f22  jne      0x7c2f5e                                 753a
0x7c2f24  test     byte ptr [esi + 0x1a4], 8                f686a401000008
0x7c2f2b  jne      0x7c2f30                                 7503
0x7c2f2d  inc      dword ptr [esi + 0x18]                   ff4618
0x7c2f30  mov      ecx, esi                                 8bce
0x7c2f32  call     0x7c3750                                 e819080000
0x7c2f37  mov      edi, eax                                 8bf8
0x7c2f39  cmp      edi, -1                                  83ffff
0x7c2f3c  je       0x7c2f48                                 740a
0x7c2f3e  mov      eax, dword ptr [esi + 0x150]             8b8650010000
0x7c2f44  or       al, 6                                    0c06
0x7c2f46  jmp      0x7c2f6f                                 eb27
0x7c2f48  mov      eax, dword ptr [esi + 0x1a4]             8b86a4010000
0x7c2f4e  mov      edi, dword ptr [esi + 0x6d0]             8bbed0060000
0x7c2f54  and      al, 0xf9                                 24f9
0x7c2f56  mov      dword ptr [esi + 0x1a4], eax             8986a4010000
0x7c2f5c  jmp      0x7c2faf                                 eb51
0x7c2f5e  cmp      edi, -9                                  83fff7
0x7c2f61  jne      0x7c2f75                                 7512
0x7c2f63  mov      eax, dword ptr [esi + 0x150]             8b8650010000
0x7c2f69  test     bl, al                                   84c3
0x7c2f6b  je       0x7c2f75                                 7408
0x7c2f6d  or       al, 2                                    0c02
0x7c2f6f  mov      dword ptr [esi + 0x150], eax             898650010000
0x7c2f75  mov      eax, dword ptr [esi + 0x1a4]             8b86a4010000
0x7c2f7b  and      al, 0xf9                                 24f9
0x7c2f7d  mov      dword ptr [esi + 0x1a4], eax             8986a4010000
0x7c2f83  jmp      0x7c2faf                                 eb2a
0x7c2f85  mov      eax, dword ptr [esi + 0x150]             8b8650010000
0x7c2f8b  or       al, 2                                    0c02
0x7c2f8d  mov      dword ptr [esi + 0x150], eax             898650010000
0x7c2f93  mov      eax, dword ptr [esi + 0x1a0]             8b86a0010000
0x7c2f99  mov      dword ptr [eax + 0x14], 0                c7401400000000
0x7c2fa0  mov      ecx, dword ptr [esi + 0x1a0]             8b8ea0010000
0x7c2fa6  mov      edx, dword ptr [ecx + 0xc]               8b510c
0x7c2fa9  mov      dword ptr [esi + 0x1a0], edx             8996a0010000
0x7c2faf  cmp      dword ptr [esp + 0x10], 1                837c241001
0x7c2fb4  je       0x7c3083                                 0f84c9000000
0x7c2fba  mov      eax, dword ptr [esi + 0x150]             8b8650010000
0x7c2fc0  mov      ecx, eax                                 8bc8
0x7c2fc2  and      ecx, 6                                   83e106
0x7c2fc5  cmp      cl, 6                                    80f906
0x7c2fc8  jne      0x7c2e19                                 0f854bfeffff
0x7c2fce  jmp      0x7c3083                                 e9b0000000
0x7c2fd3  mov      edi, 0xfffffff6                          bff6ffffff
0x7c2fd8  jmp      0x7c3083                                 e9a6000000
0x7c2fdd  test     al, 0x40                                 a840
0x7c2fdf  jne      0x7c3004                                 7523
0x7c2fe1  or       al, 0x40                                 0c40
0x7c2fe3  mov      ecx, esi                                 8bce
0x7c2fe5  mov      dword ptr [esi + 0x150], eax             898650010000
0x7c2feb  call     0x7c3960                                 e870090000
0x7c2ff0  mov      dword ptr [esi + 0x24], eax              894624
0x7c2ff3  mov      al, byte ptr [esi + 0x7bc]               8a86bc070000
0x7c2ff9  test     al, 0x40                                 a840
0x7c2ffb  je       0x7c3004                                 7407
0x7c2ffd  mov      ecx, esi                                 8bce
0x7c2fff  call     0x7bd290                                 e88ca2ffff
0x7c3004  test     byte ptr [esp + 0x18], 2                 f644241802
0x7c3009  je       0x7c307e                                 7473
0x7c300b  mov      ecx, dword ptr [esi + 0x1a4]             8b8ea4010000
0x7c3011  or       ecx, 0x14                                83c914
0x7c3014  mov      dword ptr [esi + 0x1a4], ecx             898ea4010000
0x7c301a  mov      ecx, esi                                 8bce
0x7c301c  call     dword ptr [esi + 0x77c]                  ff967c070000
0x7c3022  mov      edi, eax                                 8bf8
0x7c3024  cmp      edi, -1                                  83ffff
0x7c3027  jne      0x7c3057                                 752e
0x7c3029  mov      ecx, esi                                 8bce
0x7c302b  call     0x7c3750                                 e820070000
0x7c3030  mov      edi, eax                                 8bf8
0x7c3032  cmp      edi, -1                                  83ffff
0x7c3035  je       0x7c3041                                 740a
0x7c3037  mov      eax, dword ptr [esi + 0x150]             8b8650010000
0x7c303d  or       al, 6                                    0c06
0x7c303f  jmp      0x7c3068                                 eb27
```

### 12 条写入 `.text` imm32 的精确清单

| # | 指令地址 | offset | imm32（.text 函数地址） | 指令 |
|---:|---|---|---|---|
| 1 | 0x7be6dd | 0x780 | 0x7bf230 | mov dword ptr [esi + 0x780], 0x7bf230 |
| 2 | 0x7be6e9 | 0x77c | 0x7bea40 | mov dword ptr [esi + 0x77c], 0x7bea40 |
| 3 | 0x7be6f3 | 0x780 | 0x7bf0b0 | mov dword ptr [esi + 0x780], 0x7bf0b0 |
| 4 | 0x7be6ff | 0x77c | 0x7bf140 | mov dword ptr [esi + 0x77c], 0x7bf140 |
| 5 | 0x7be709 | 0x780 | 0x7bf190 | mov dword ptr [esi + 0x780], 0x7bf190 |
| 6 | 0x7be741 | 0x784 | 0x7c3d60 | mov dword ptr [esi + 0x784], 0x7c3d60 |
| 7 | 0x7be74b | 0x788 | 0x7c3eb0 | mov dword ptr [esi + 0x788], 0x7c3eb0 |
| 8 | 0x7be75a | 0x784 | 0x7c6fc8 | mov dword ptr [esi + 0x784], 0x7c6fc8 |
| 9 | 0x7be764 | 0x788 | 0x7c39c0 | mov dword ptr [esi + 0x788], 0x7c39c0 |
| 10 | 0x7be773 | 0x784 | 0x7c6dd6 | mov dword ptr [esi + 0x784], 0x7c6dd6 |
| 11 | 0x7be78c | 0x788 | 0x7c4b80 | mov dword ptr [esi + 0x788], 0x7c4b80 |
| 12 | 0x7be79f | 0x788 | 0x7c4f90 | mov dword ptr [esi + 0x788], 0x7c4f90 |
| 13 | 0x7be7ae | 0x788 | 0x7c4730 | mov dword ptr [esi + 0x788], 0x7c4730 |
| 14 | 0x7be7c1 | 0x784 | 0x7c6e94 | mov dword ptr [esi + 0x784], 0x7c6e94 |
| 15 | 0x7be7df | 0x784 | 0x7c4260 | mov dword ptr [esi + 0x784], 0x7c4260 |
| 16 | 0x7be7e9 | 0x788 | 0x7c43a0 | mov dword ptr [esi + 0x788], 0x7c43a0 |
| 17 | 0x7be7f8 | 0x784 | 0x7c6d40 | mov dword ptr [esi + 0x784], 0x7c6d40 |
| 18 | 0x7be811 | 0x788 | 0x7c57d0 | mov dword ptr [esi + 0x788], 0x7c57d0 |
| 19 | 0x7be820 | 0x788 | 0x7c53a0 | mov dword ptr [esi + 0x788], 0x7c53a0 |
| 20 | 0x7c323c | 0x784 | 0x7bf220 | mov dword ptr [ecx + 0x784], 0x7bf220 |
| 21 | 0x7c325a | 0x788 | 0x7bf220 | mov dword ptr [ecx + 0x788], 0x7bf220 |

- 合计 **21** 条（卡面写「应为 12 条」，实测 21 条，差额 9 条全部来自 0x7be741..0x7be820 区间内 0x784/0x788 的 imm32 函数地址写入；卡面 12 可能只计了部分 offset；此处按字面全量列出，不做裁剪）。
- 分布：0x7be66a 邻域（0x7be6dd..0x7be820）19 条，0x7c2f6b 邻域（0x7c323c、0x7c325a）2 条；`0x6660f3` 写入非 .text imm32 0x7d0 不计入。

## T6 宿主类定位

- 用 RTTI COL 形态（`.rdata`/`.data` 内 `dw(V-4)==COL` 且 COL 名 `.?A..@@`）重建 vftable：COL=1214，可唯一定位的 vftable 起点=1214，虚表槽目标总数（.text）=14044。
- 12 条写入端经 0xCC 判界归并为 start=0x7bc640；与虚表槽目标交集 **1** 条：
  - vftable=0x7f7bdc slot=0 target=0x7bc640
- 注意：写入端集中在不同类的初始化函数（如 0x7bc640 为公共构造段），单个 vftable 仅 1 个槽命中；不据此硬编造 RTTI 类名归属。

## T7 正反控

- **正控**：0x7bea07 被识别为 `call dword ptr [esi+0x784]` → PASS（detail：call dword ptr [esi + 0x784]）。

| 负控 offset | 合计 | 读 | 写 |
|---:|---:|---:|---:|
| 0x778 | 19 | 16 | 3 |
| 0x78c | 32 | 27 | 5 |
| 0x7a4 | 15 | 8 | 7 |

- 0x778=19、0x78c=32，与四字段总量 60 明显不同；0x7a4 卡面写「预期 0」，实测 **15**（全部为真实字段访问，非误报），说明「0x7a4 不存在」的假设不成立，不能据此当作负控通过。

## 口径与不确定性

- 全 .text `disasm_lite` 指令数约 1,394,300（与 R219 的 1,394,120 差异来自本扫描不含跨块边界 flush；字段命中不依赖总数）。
- `0x7c2f6b` 所在字节位于前一条 `jcc` 的分支路径，0xCC 判界把它归到 0x7bc640 段；T5 的 imm32 写入按指令地址逐条计，与函数聚合口径不同。
- T3 函数入口用「>=2 连续 0xCC 后首字节」规则；E8 站点统计全 .text rel32 精确指向，不统计间接调用。
- T6 只报告「写入端 start 与虚表槽目标地址交集」，不推断 RTTI 类名。
