# R104 执行报告 · 第三套反汇编器（iced-x86 1.22.0）复算 88 个地址

## 前提核验

- exe: ra2bench/gamemd.exe, SHA-256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476（与卡面期望一致）
- 反汇编文本: /tmp/r93_disasm.txt, SHA-256 = 5935356b2914d90baeaeb0d8ea5198961976118526b37d341ab72f06d4046c70（与卡面期望一致）
- ImageBase 0x400000；.text = [0x401000, 0x7E038D)；VirtualSize = 4060045；iced 线性扫描共 1392537 个单元，sum(len) = 4060045 = VirtualSize，铺满且末单元恰好收于 0x7E038D。
- 所有数字均由本脚本从 exe 字节重算；R101 的 json 仅取原始地址清单（only_cap_ne_list / host_of_88 / detail 的 a,host,class / cap_bad_list / setA_target_form 的 src 字节与 at），未使用任何结论字段。

## T1 iced 是否也把这 88 个地址当起点

- iced valid 起点: **50**
- iced invalid 起点（落在线性扫描 invalid 起点集中）: **0**
- 既非起点、落在某个 iced 单元内部: **38**
- 补充：若脱离线性扫描、直接从这 88 个地址各自解码，iced 报 Code.INVALID 的有 0 个。
- 全局 iced 线性扫描 invalid 起点数 = 66。

### T1-A iced valid 起点（50 个，地址 / 该单元长度）
- 0x48db27 len=6
- 0x6a92d2 len=2
- 0x6a92d4 len=2
- 0x6a92d6 len=2
- 0x6a92d8 len=2
- 0x6a92da len=2
- 0x6a92dc len=2
- 0x6a92de len=6
- 0x6a92e4 len=1
- 0x6a92e5 len=2
- 0x6dfee7 len=2
- 0x6dfef7 len=6
- 0x6dfeff len=7
- 0x708d5a len=2
- 0x708d5c len=2
- 0x708d5e len=2
- 0x708d60 len=1
- 0x708d61 len=3
- 0x728e10 len=6
- 0x728e16 len=2
- 0x79f02c len=2
- 0x7c5eeb len=1
- 0x7c5eec len=3
- 0x7c8fd6 len=3
- 0x7c90e2 len=3
- 0x7c91ae len=2
- 0x7c91c2 len=2
- 0x7cbef2 len=3
- 0x7cbf1a len=3
- 0x7cefe1 len=6
- 0x7cf064 len=6
- 0x7cf0bb len=6
- 0x7cf0d2 len=6
- 0x7cf0e6 len=6
- 0x7cf0f8 len=2
- 0x7cf10c len=2
- 0x7cf139 len=3
- 0x7cf196 len=6
- 0x7cf1fd len=6
- 0x7cf215 len=6
- 0x7cf44c len=2
- 0x7cf4a5 len=2
- 0x7cf4e1 len=2
- 0x7cf50a len=2
- 0x7d7fe7 len=4
- 0x7dbc5f len=3
- 0x7dbc7c len=3
- 0x7dbcb7 len=2
- 0x7dbcc3 len=1
- 0x7dbcc4 len=2

### T1-B iced invalid 起点（0 个）
- 无

### T1-C 落在 iced 单元内部（38 个，目标 / 包含它的单元起点 / 单元长 / 目标在单元内偏移 / 该单元 iced 文本）
- 0x46f5a1 <- 单元 0x46f5a0 len=4 (at+1) (bad)
- 0x48db26 <- 单元 0x48db25 len=2 (at+1) (bad)
- 0x48dd19 <- 单元 0x48dd18 len=4 (at+1) (bad)
- 0x4c8115 <- 单元 0x4c8114 len=2 (at+1) (bad)
- 0x5001e5 <- 单元 0x5001e4 len=2 (at+1) (bad)
- 0x58bda5 <- 单元 0x58bda4 len=6 (at+1) (bad)
- 0x69b15d <- 单元 0x69b15c len=6 (at+1) (bad)
- 0x69b15f <- 单元 0x69b15c len=6 (at+3) (bad)
- 0x69b166 <- 单元 0x69b162 len=6 (at+4) imul eax,[eax],69AF45h
- 0x69b16c <- 单元 0x69b16a len=6 (at+2) imul eax,[eax],90909090h
- 0x69b16d <- 单元 0x69b16a len=6 (at+3) imul eax,[eax],90909090h
- 0x69b16e <- 单元 0x69b16a len=6 (at+4) imul eax,[eax],90909090h
- 0x69b16f <- 单元 0x69b16a len=6 (at+5) imul eax,[eax],90909090h
- 0x6a92ce <- 单元 0x6a92cd len=5 (at+1) (bad)
- 0x6a92d0 <- 单元 0x6a92cd len=5 (at+3) (bad)
- 0x6adbe1 <- 单元 0x6adbe0 len=6 (at+1) (bad)
- 0x6adbe4 <- 单元 0x6adbe0 len=6 (at+4) (bad)
- 0x6b0249 <- 单元 0x6b0248 len=2 (at+1) (bad)
- 0x6dfe1a <- 单元 0x6dfe19 len=2 (at+1) (bad)
- 0x6dfe42 <- 单元 0x6dfe41 len=2 (at+1) (bad)
- 0x6dfee6 <- 单元 0x6dfee5 len=2 (at+1) (bad)
- 0x6dfef6 <- 单元 0x6dfef5 len=2 (at+1) (bad)
- 0x6dfefe <- 单元 0x6dfefd len=2 (at+1) (bad)
- 0x6dff59 <- 单元 0x6dff58 len=2 (at+1) (bad)
- 0x708d56 <- 单元 0x708d55 len=3 (at+1) (bad)
- 0x71f2c6 <- 单元 0x71f2c5 len=3 (at+1) (bad)
- 0x71f2ca <- 单元 0x71f2c9 len=3 (at+1) (bad)
- 0x71f2e2 <- 单元 0x71f2e1 len=3 (at+1) (bad)
- 0x71f32a <- 单元 0x71f329 len=3 (at+1) (bad)
- 0x71f32e <- 单元 0x71f32d len=3 (at+1) (bad)
- 0x71f33e <- 单元 0x71f33d len=3 (at+1) (bad)
- 0x71f77d <- 单元 0x71f77c len=2 (at+1) (bad)
- 0x71f9e1 <- 单元 0x71f9e0 len=2 (at+1) (bad)
- 0x71f9e5 <- 单元 0x71f9e4 len=2 (at+1) (bad)
- 0x728e0d <- 单元 0x728e0c len=2 (at+1) (bad)
- 0x7291b2 <- 单元 0x7291b1 len=3 (at+1) (bad)
- 0x79f029 <- 单元 0x79f028 len=4 (at+1) (bad)
- 0x79f02a <- 单元 0x79f028 len=4 (at+2) (bad)

## T2 B1 的 41 个逐址定性

B1 计数由 detail 的 class 字段重算 = 41。对每个 B1 目标，取其宿主起点（host_of_88 / detail.host）用 iced 单独解码：
- iced 在宿主起点也是 invalid: 41 / 41
- iced 在宿主起点能解出有效指令: 0 / 41
- iced 宿主单元覆盖到目标地址: 33 / 41（其余 8 个因 invalid 单元长度短于 host 到目标的间距而未覆盖）

逐址表：目标 / 宿主 / iced 在宿主的文本或 invalid / 长度 / 是否覆盖目标 / 目标在宿主内偏移 / 宿主起始 16 字节
- 0x46f5a1 host=0x46f5a0 -> (bad) len=4 covers=Y at+1 bytes=c5 e4 46 00 04 e6 46 00 43 e7 46 00 c9 f4 46 00
- 0x48db26 host=0x48db25 -> (bad) len=2 covers=Y at+1 bytes=d9 48 00 98 d7 48 00 d5 d7 48 00 f4 d7 48 00 9e
- 0x48db27 host=0x48db25 -> (bad) len=2 covers=N at+2 bytes=d9 48 00 98 d7 48 00 d5 d7 48 00 f4 d7 48 00 9e
- 0x48dd19 host=0x48dd18 -> (bad) len=4 covers=Y at+1 bytes=f0 dc 48 00 fa dc 48 00 0d dd 48 00 00 01 01 04
- 0x4c8115 host=0x4c8114 -> (bad) len=2 covers=Y at+1 bytes=f0 6c 4c 00 4d 6d 4c 00 ee 6d 4c 00 ca 71 4c 00
- 0x5001e5 host=0x5001e4 -> (bad) len=2 covers=Y at+1 bytes=f0 fd 4f 00 36 fe 4f 00 47 ff 4f 00 70 01 50 00
- 0x58bda5 host=0x58bda4 -> (bad) len=6 covers=Y at+1 bytes=8c bd 58 00 95 bd 58 00 9e bd 58 00 95 bd 58 00
- 0x69b15d host=0x69b15c -> (bad) len=6 covers=Y at+1 bytes=8c b0 69 00 8c b0 69 00 45 af 69 00 45 af 69 00
- 0x69b15f host=0x69b15c -> (bad) len=6 covers=Y at+3 bytes=8c b0 69 00 8c b0 69 00 45 af 69 00 45 af 69 00
- 0x6a92ce host=0x6a92cd -> (bad) len=5 covers=Y at+1 bytes=8f 6a 00 00 00 02 02 02 01 02 02 02 02 02 02 02
- 0x6a92d0 host=0x6a92cd -> (bad) len=5 covers=Y at+3 bytes=8f 6a 00 00 00 02 02 02 01 02 02 02 02 02 02 02
- 0x6adbe1 host=0x6adbe0 -> (bad) len=6 covers=Y at+1 bytes=62 db 6a 00 cc db 6a 00 00 02 02 00 02 01 02 02
- 0x6b0249 host=0x6b0248 -> (bad) len=2 covers=Y at+1 bytes=8e ff 6a 00 3c 00 6b 00 0f 02 6b 00 90 90 90 90
- 0x6dfe1a host=0x6dfe19 -> (bad) len=2 covers=Y at+1 bytes=f0 6d 00 18 eb 6d 00 4e e0 6d 00 dd fd 6d 00 a8
- 0x6dfe42 host=0x6dfe41 -> (bad) len=2 covers=Y at+1 bytes=f0 6d 00 18 e4 6d 00 57 e4 6d 00 a0 e4 6d 00 01
- 0x6dfee6 host=0x6dfee5 -> (bad) len=2 covers=Y at+1 bytes=dd 6d 00 f6 dd 6d 00 4b de 6d 00 a0 de 6d 00 77
- 0x6dfee7 host=0x6dfee5 -> (bad) len=2 covers=N at+2 bytes=dd 6d 00 f6 dd 6d 00 4b de 6d 00 a0 de 6d 00 77
- 0x6dfef6 host=0x6dfef5 -> (bad) len=2 covers=Y at+1 bytes=dd 6d 00 93 dd 6d 00 af dd 6d 00 94 f0 6d 00 50
- 0x6dfef7 host=0x6dfef5 -> (bad) len=2 covers=N at+2 bytes=dd 6d 00 93 dd 6d 00 af dd 6d 00 94 f0 6d 00 50
- 0x6dfefe host=0x6dfefd -> (bad) len=2 covers=Y at+1 bytes=dd 6d 00 94 f0 6d 00 50 f2 6d 00 71 f2 6d 00 92
- 0x6dfeff host=0x6dfefd -> (bad) len=2 covers=N at+2 bytes=dd 6d 00 94 f0 6d 00 50 f2 6d 00 71 f2 6d 00 92
- 0x6dff59 host=0x6dff58 -> (bad) len=2 covers=Y at+1 bytes=db fd 6d 00 db fd 6d 00 13 d9 6d 00 bf d9 6d 00
- 0x708d56 host=0x708d55 -> (bad) len=3 covers=Y at+1 bytes=8c 70 00 d9 8c 70 00 b4 8c 70 00 4d 8d 70 00 7a
- 0x708d5a host=0x708d58 -> (bad) len=2 covers=N at+2 bytes=d9 8c 70 00 b4 8c 70 00 4d 8d 70 00 7a 8c 70 00
- 0x708d5c host=0x708d58 -> (bad) len=2 covers=N at+4 bytes=d9 8c 70 00 b4 8c 70 00 4d 8d 70 00 7a 8c 70 00
- 0x708d5e host=0x708d58 -> (bad) len=2 covers=N at+6 bytes=d9 8c 70 00 b4 8c 70 00 4d 8d 70 00 7a 8c 70 00
- 0x71f2c6 host=0x71f2c5 -> (bad) len=3 covers=Y at+1 bytes=f0 71 00 58 f0 71 00 3f ef 71 00 8e ef 71 00 eb
- 0x71f2ca host=0x71f2c9 -> (bad) len=3 covers=Y at+1 bytes=f0 71 00 3f ef 71 00 8e ef 71 00 eb ef 71 00 03
- 0x71f2e2 host=0x71f2e1 -> (bad) len=3 covers=Y at+1 bytes=f0 71 00 a9 ee 71 00 a8 ef 71 00 20 ef 71 00 cb
- 0x71f32a host=0x71f329 -> (bad) len=3 covers=Y at+1 bytes=f0 71 00 fb f0 71 00 2f f1 71 00 15 f1 71 00 89
- 0x71f32e host=0x71f32d -> (bad) len=3 covers=Y at+1 bytes=f0 71 00 2f f1 71 00 15 f1 71 00 89 f1 71 00 99
- 0x71f33e host=0x71f33d -> (bad) len=3 covers=Y at+1 bytes=f0 71 00 59 f1 71 00 6f f1 71 00 bd f0 71 00 b1
- 0x71f77d host=0x71f77c -> (bad) len=2 covers=Y at+1 bytes=da f6 71 00 00 01 00 01 01 00 00 00 00 00 01 01
- 0x71f9e1 host=0x71f9e0 -> (bad) len=2 covers=Y at+1 bytes=da f9 71 00 dd f9 71 00 00 01 01 01 01 00 01 01
- 0x71f9e5 host=0x71f9e4 -> (bad) len=2 covers=Y at+1 bytes=dd f9 71 00 00 01 01 01 01 00 01 01 01 01 01 01
- 0x728e0d host=0x728e0c -> (bad) len=2 covers=Y at+1 bytes=d9 8d 72 00 d0 8d 72 00 1e 8c 72 00 e0 8d 72 00
- 0x728e10 host=0x728e0c -> (bad) len=2 covers=N at+4 bytes=d9 8d 72 00 d0 8d 72 00 1e 8c 72 00 e0 8d 72 00
- 0x728e16 host=0x728e15 -> (bad) len=3 covers=Y at+1 bytes=8c 72 00 e0 8d 72 00 e0 8d 72 00 e0 8d 72 00 90
- 0x7291b2 host=0x7291b1 -> (bad) len=3 covers=Y at+1 bytes=8e 72 00 86 8f 72 00 35 90 72 00 42 90 72 00 4f
- 0x79f029 host=0x79f028 -> (bad) len=4 covers=Y at+1 bytes=c5 ed 79 00 0b ee 79 00 87 ee 79 00 7a ed 79 00
- 0x79f02a host=0x79f028 -> (bad) len=4 covers=Y at+2 bytes=c5 ed 79 00 0b ee 79 00 87 ee 79 00 7a ed 79 00

## T3 两个拒解集不是同一集合

- capstone 拒解集（cap_bad_list 原始清单）: **65**
- iced 线性扫描 invalid 起点集: **66**
- 交集: **63**
- 只在 capstone: **2**
- 只在 iced: **3**

### 只在 capstone（地址 / 起始 8 字节 / iced 单独解码文本 / 长度）
- 0x708d59 bytes=8c 70 00 b4 8c 70 00 4d iced=(bad) len=3
- 0x7b0084 bytes=db ff 7a 00 90 90 90 90 iced=(bad) len=2

### 只在 iced（地址 / 起始 8 字节 / iced 单独解码文本 / 长度）
- 0x488ed1 bytes=8e 48 00 90 90 90 90 90 iced=(bad) len=3
- 0x502d18 bytes=f0 2b 50 00 04 2d 50 00 iced=(bad) len=4
- 0x7b007d bytes=fe 7a 00 ef fe 7a 00 db iced=(bad) len=2

### 交集 63 个（地址 / 起始 8 字节）
- 0x46f5a0 bytes=c5 e4 46 00 04 e6 46 00
- 0x48db25 bytes=d9 48 00 98 d7 48 00 d5
- 0x48dd18 bytes=f0 dc 48 00 fa dc 48 00
- 0x4c8114 bytes=f0 6c 4c 00 4d 6d 4c 00
- 0x4d926d bytes=8f 4d 00 cc 90 4d 00 00
- 0x5001e4 bytes=f0 fd 4f 00 36 fe 4f 00
- 0x51c889 bytes=c7 51 00 e7 c6 51 00 0f
- 0x51c88d bytes=c6 51 00 0f c7 51 00 00
- 0x51c891 bytes=c7 51 00 00 01 03 03 03
- 0x51f1fc bytes=c7 f1 51 00 bb f1 51 00
- 0x520efc bytes=c6 0b 52 00 b8 0c 52 00
- 0x58bda4 bytes=8c bd 58 00 95 bd 58 00
- 0x5a0084 bytes=c4 f2 59 00 90 90 90 90
- 0x5bcacc bytes=c6 c9 5b 00 2c ca 5b 00
- 0x5bcaf5 bytes=c7 5b 00 77 c9 5b 00 a8
- 0x5bcb01 bytes=c7 5b 00 b6 c8 5b 00 22
- 0x5efee5 bytes=fe 5e 00 e4 f5 5e 00 b0
- 0x62fe4c bytes=8d fd 62 00 96 fd 62 00
- 0x66301c bytes=c7 29 66 00 ac 2c 66 00
- 0x69b15c bytes=8c b0 69 00 8c b0 69 00
- 0x6a92cd bytes=8f 6a 00 00 00 02 02 02
- 0x6adbe0 bytes=62 db 6a 00 cc db 6a 00
- 0x6afd4c bytes=fe f9 6a 00 c3 fc 6a 00
- 0x6b0241 bytes=fe 6a 00 43 ff 6a 00 8e
- 0x6b0248 bytes=8e ff 6a 00 3c 00 6b 00
- 0x6dfdfc bytes=8d eb 6d 00 f9 eb 6d 00
- 0x6dfe19 bytes=f0 6d 00 18 eb 6d 00 4e
- 0x6dfe41 bytes=f0 6d 00 18 e4 6d 00 57
- 0x6dfee5 bytes=dd 6d 00 f6 dd 6d 00 4b
- 0x6dfee9 bytes=dd 6d 00 4b de 6d 00 a0
- 0x6dfef5 bytes=dd 6d 00 93 dd 6d 00 af
- 0x6dfefd bytes=dd 6d 00 94 f0 6d 00 50
- 0x6dff58 bytes=db fd 6d 00 db fd 6d 00
- 0x6e3c78 bytes=8f 3b 6e 00 83 3b 6e 00
- 0x708d55 bytes=8c 70 00 d9 8c 70 00 b4
- 0x708d58 bytes=d9 8c 70 00 b4 8c 70 00
- 0x71f2c5 bytes=f0 71 00 58 f0 71 00 3f
- 0x71f2c9 bytes=f0 71 00 3f ef 71 00 8e
- 0x71f2e1 bytes=f0 71 00 a9 ee 71 00 a8
- 0x71f329 bytes=f0 71 00 fb f0 71 00 2f
- 0x71f32d bytes=f0 71 00 2f f1 71 00 15
- 0x71f33d bytes=f0 71 00 59 f1 71 00 6f
- 0x71f494 bytes=c4 f3 71 00 f5 f3 71 00
- 0x71f60c bytes=c7 f5 71 00 cd f5 71 00
- 0x71f77c bytes=da f6 71 00 00 01 00 01
- 0x71f9e0 bytes=da f9 71 00 dd f9 71 00
- 0x71f9e4 bytes=dd f9 71 00 00 01 01 01
- 0x723e27 bytes=0f 0f 13 03 13 13 13 10
- 0x728e0c bytes=d9 8d 72 00 d0 8d 72 00
- 0x7291b1 bytes=8e 72 00 86 8f 72 00 35
- 0x7918f1 bytes=ff 78 00 d5 18 79 00 e6
- 0x793455 bytes=fe ff c3 90 90 90 90 90
- 0x799b54 bytes=c7 91 79 00 68 93 79 00
- 0x79f028 bytes=c5 ed 79 00 0b ee 79 00
- 0x7b0079 bytes=fe 7a 00 d0 fe 7a 00 ef
- 0x7b0081 bytes=fe 7a 00 db ff 7a 00 90
- 0x7b0085 bytes=ff 7a 00 90 90 90 90 90
- 0x7c5d92 bytes=fe ff 00 01 f7 f8 fa fb
- 0x7c5d9c bytes=fe ff 00 01 02 03 04 05
- 0x7c80f2 bytes=fe ff 00 01 f7 f8 fa fb
- 0x7c80fc bytes=fe ff 00 01 02 03 04 05
- 0x7d0cba bytes=8f 1c 8b 44 8e 18 89 44
- 0x7d9d2f bytes=fe 9a 7d 00 dd 9a 7d 00

## T4 集 A 的 4 条疑似零位移 jXX

从 r101e_recheck.json 的 setA_target_form 重算：n_srcs=1 且 is_zero_disp_fallthrough=True 的共有 4 条。
- 源 0x71f9e2: jno    0x71f9e4 bytes=71 00 -> 目标 0x71f9e4，target_minus_next=0
- 源 0x728e0a: jb     0x728e0c bytes=72 00 -> 目标 0x728e0c，target_minus_next=0
- 源 0x7b0082: jp     0x7b0084 bytes=7a 00 -> 目标 0x7b0084，target_minus_next=0
- 源 0x7d9d2d: jge    0x7d9d2f bytes=7d 00 -> 目标 0x7d9d2f，target_minus_next=0

卡面抄录的 4 个地址（即 4 条零位移 jXX 的源地址）: 0x71f99e, 0x728e0a, 0x7b0082, 0x7d9d2d
从 setA_target_form 核出的实际 4 个源地址: 0x71f9e2, 0x728e0a, 0x7b0082, 0x7d9d2d
实际 4 个跳转目标地址: 0x71f9e4, 0x728e0c, 0x7b0084, 0x7d9d2f

关键结论：卡面第 1 条 0x71f99e 既不是源（正确源 0x71f9e2）也不是目标（正确目标 0x71f9e4），是抄写错误。其原始 8 字节 00 00 00 00 00 00 01 01 从该地址解码为 add [eax],al（长度 2），不是条件跳转。
判定：**主会话的 4 条清单里第 1 条是抄错的**。

逐址解码（卡面 4 个 + 正确目标 4 个；bytes 为从该地址起的 8 字节）：地址 / 字节 / iced 文本 / 长度 / 是否 jXX / 是否在 88 / 是否 cap 拒解 / 是否 iced invalid 起点
- 0x71f99e bytes=00 00 00 00 00 00 01 01 -> add [eax],al len=2 jcc=N in88=N capbad=N icedbadstart=N
- 0x728e0a bytes=72 00 d9 8d 72 00 d0 8d -> jb short 00728E0Ch len=2 jcc=Y in88=N capbad=N icedbadstart=N
- 0x7b0082 bytes=7a 00 db ff 7a 00 90 90 -> jp short 007B0084h len=2 jcc=Y in88=N capbad=N icedbadstart=N
- 0x7d9d2d bytes=7d 00 fe 9a 7d 00 dd 9a -> jge short 007D9D2Fh len=2 jcc=Y in88=N capbad=N icedbadstart=N
- 0x71f9e4 bytes=dd f9 71 00 00 01 01 01 -> (bad) len=2 jcc=N in88=N capbad=Y icedbadstart=Y
- 0x728e0c bytes=d9 8d 72 00 d0 8d 72 00 -> (bad) len=2 jcc=N in88=N capbad=Y icedbadstart=Y
- 0x7b0084 bytes=db ff 7a 00 90 90 90 90 -> (bad) len=2 jcc=N in88=N capbad=Y icedbadstart=N
- 0x7d9d2f bytes=fe 9a 7d 00 dd 9a 7d 00 -> (bad) len=2 jcc=N in88=N capbad=Y icedbadstart=Y

注：其余 3 条卡面抄的是 jXX 指令自身地址，解码为 jb 0x728e0c / jp 0x7b0084 / jge 0x7d9d2f（各长 2）；其跳转目标处字节分别为 d9 8d / db ff / fe 9a，iced 均解为 (bad) 长 2，即目标落在数据字节中，与 R101 的「数据被读成代码」判读一致。
