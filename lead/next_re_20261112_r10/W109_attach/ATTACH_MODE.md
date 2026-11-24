# ATTACH_MODE.md — `cell_sentinel.py --attach` 只读附加模式
> 卡：R10 / **W109**｜2026-11-14｜基线：R09 W104 `cell_sentinel.py`（复制到本卡目录后改，原件未动）
> 本卡**不启动游戏、不注入、不附加到 gamemd**。分级：`[已证]` / `[静态推断]` / `[未证]`。
> `<PY>` = `C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe`

## 0 · 一屏结论

| 项 | 结果 | 分级 |
|---|---|---|
| `--attach <pid>` 跑通 | 是（**自造替身**，`EVIDENCE/e2e_attach.txt`） | `[已证]`（限替身） |
| 真机 gamemd 上跑通 | **没做，也不声称** | `[未证]` |
| 原 14 项 `--self-test` | **仍 GREEN（14/14）** | `[已证]` |
| 新增 `--selftest-attach` | GREEN（20/20，含只读源码自审） | `[已证]` |
| 单次全扫 512×512（一半空格） | **4.64 s**（17.7 µs/cell，本机合成表） | `[已证]`（本机） |
| 建议轮询 | **20×20～40×40 窗口 @ 0.5–2 Hz**；全表只做一次性诊断 | `[静态推断]` |

## 1 · 用法

```powershell
<PY> cell_sentinel.py --self-test                      # 原 14 项回归
<PY> cell_sentinel.py --selftest-attach                # 替身 + RPM 通路 + 降级路径（20 项）
<PY> cell_sentinel.py --attach <pid>                   # 全表（512×512）
<PY> cell_sentinel.py --attach <pid> --rows 200-239 --cols 200-239 --quiet
<PY> cell_sentinel.py --perf ; <PY> cell_sentinel.py --dump
```
参数：`--rows/--cols A-B`（含端点，默认 `0-511`）、`--max-nodes N`（默认 64）、`--hex N`（默认 `0x40`）、
`--max-report N`（默认 200）、`--quiet`。返回码：`0` 完成；`2` 参数错；`3` OpenProcess 失败；
`4` 目标是游戏进程（拒绝附加）。

## 2 · 读路径（严格按 L8）
```
table = *(uint32*)0x0087F924     # 全局存"表基址"   [已证] 0x00429DF5: a1 24 f9 87 00
obj   = table[Y*512 + X]         # 表项是 uint32 指针，可为 0（空格）  [已证]
                                 #   Y = idx>>9, X = idx&0x1FF        [已证] 0x00429DFA: c1 e1 09
node  = *(uint32*)obj            # obj 就是 CellClass 对象本身
headA = *(uint32*)(obj + 0xE4)   # [已证] 0x0047C52A: 8b b1 e4 00 00 00
headB = *(uint32*)(obj + 0xE8)   # [已证] 0x0047C4E3: 8b b1 e8 00 00 00
next  = *(uint32*)(node + 0x30)  # [已证] 0x0047C540: 8b 76 30
vptr  = *(uint32*)(node)
```
另加两个**运行时读值**的静态锚点作额外起点：`0x0089C2E0`、`0x00ABDC50`。
`--dump` 自核四条 L8 字节 + W104 的 11 条：**15 ok, 0 mismatch**（`EVIDENCE/dump.txt`）。

## 3 · vptr 白名单怎么定的（本卡关键判断）
W104 那张 280 条表**不能当判决依据**：相邻 vtable 合并成游程会漏起点，且 `step12/step13`
三档口径不一致（280 / 119 / 108）—— 见 `SENTINEL_RULING §4-3`。故本卡用**两级判据**：
1. **镜像派生白名单（弱）**：从 `gamemd.exe` 的非 `.text` 节扫"连续可执行指针游程"，游程里
   **每个 word** 当候选起点（沿用 W104 `step12` 口径）。实测 `11217 runs` / `49045 candidate
   starts`；两个 `[已证]` 锚点在内且 `WhatAmI` 解出 **6 / 15**，与 L2 一致（`dump.txt` 的
   `anchors:` 行）。`[静态推断]`
2. **与静态镜像同构（强）**：把活进程里 `vptr` 起 16 KB 与镜像同位置逐字节比对，跳过"静态目标
   指向运行时分配区/越界"的 word，要求匹配率 ≥ 99.5% 且可比 word ≥ 64。
两者都不满足才报 `suspect` —— 白名单不完备时**只会漏、不会误报**。
`[静态推断]` 依据：`0x0047C538: ff 50 2c` 调第 11 槽（`0x2C/4`）；vptr 指向 `vtbl[0]`，故槽 11
地址 = `vptr + 0x2C`，与 W104 self-test 的 `write_u32(vt + 11*4, thunk)` 同构。

## 4 · 防崩 / 防环

| 风险 | 处理 | 证据 |
|---|---|---|
| 任一 RPM 失败 | 收敛成 `None`，记账继续，**不抛** | `selftest_attach.txt` 4 / 10b |
| 目标中途退出 | 每扫完一行做一次存活检查（读目标自己的私有页），不可读即停并如实报告 | 同上 9/10 |
| 链成环 | 已访问集合 → `stop=cycle` | `guards.txt` 自环 / 二元环 |
| `next` 是垃圾 | 预检 `<0x10000` 或 `>0x7FFFFFFF` → `stop=illegal` | `guards.txt` 0xFFFFFFF0 / 0x10 |
| 链过长 | 每链上限 64 + 硬循环保护 `max_nodes*4+16` | `guards.txt` 上限 1/8/39 |
| 空格子 | 表项 `== 0` 直接跳过（L8-2 的 `test/je`） | e2e：`null=262080` |
| 跨页读 | 按 4 KB 切分，任一段失败整条判失败（不返回半截） | `ProcMem.read_bytes` |
| 同一 cell 被多格引用 | 按**对象地址**去重（`cell_dupe`） | e2e：`objs walked=64` |

## 5 · 性能与轮询建议
产出：`<PY> cell_sentinel.py --perf` → `EVIDENCE/perf.txt`
```
表 512×512 = 262144 格，131072 非空（一半空格），每格两条链、每链 2 节点
单次全扫        : 4.6422 s (17.71 us/cell)  best-of-4
  纯表读        : 0.1902 s ( 4.1%)
  链遍历 + 判定  : 4.4520 s (95.9%)
20x20   =   400 格 :   7.08 ms/sweep   @2 Hz =  1.42% 单核
40x40   =  1600 格 :  28.33 ms/sweep   @2 Hz =  5.67% 单核
100x100 = 10000 格 : 177.08 ms/sweep   @2 Hz = 35.4%  单核
全表 @0.2 Hz       : 92.8% 单核（一秒内几乎扫不完一次）
```
**建议**（`[静态推断]`）：首轮全表只做一次诊断（≈4.6 s，`--quiet`）；常驻轮询用窗口
**20×20～40×40、0.5～2 Hz**；**不要**按全表做常驻轮询。
`[未证]`：① 上表是等接口合成内存的 CPU 成本，跨进程每次 4 B 读还要过一次内核，真机更慢，频率须
重测；② 真实空格比例未知（假设 1/2）；③ 真实每格链长未知（假设 2，节点数是主要成本项）。

## 6 · 本卡顺带证实的四条
1. `GetExitCodeProcess` / `QueryFullProcessImageNameW` **需要 `PROCESS_QUERY_LIMITED_INFORMATION`**；
   只给 `PROCESS_VM_READ` 时前者直接 `ok=0`。`[已证]`
2. `VirtualQueryEx` 同样需要该权限，否则 `err=5 / 返回 0`。`[已证]`
   ⇒ 附加权限取 `PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION`（**均为只读**，与 R10_FACTS §1 一致）。
3. `0x7FFE0000` 这类 KUSER 共享页在**任何**活进程都可读 ⇒ **单次 RPM 成功不能用来判活**。`[已证]`
4. 本机替身里 `VirtualQueryEx` 只见 4 个区域（沙箱特征），私有页探针落在 `0x7FFE0000`。
   `[已证]` → `EVIDENCE/probe_rpm_self.txt`

## 7 · 上真机前必须补的
1. **没有任何真机数据** —— "能读 gamemd" 全部 `[未证]`。
2. `0x87F924` 表的**实际容量**未证（`0x87F928` 语义未证）；越界读记成 `cell_unreadable`，不崩但
   结论不完整。
3. 白名单**不完备**（合并游程漏起点）；"同构"判据只压假阳性，**不保证零漏报**。
4. 真实空格比例 / 链长 / 两链语义，均 `[未证]`（详见 `UNKNOWNS.md`）。

## 8 · 复现（可粘贴）
```powershell
$d = 'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W109_attach'
$env:PYTHONIOENCODING='utf-8'
& python "$d\cell_sentinel.py" --self-test       | Tee-Object "$d\EVIDENCE\selftest.txt"
& python "$d\cell_sentinel.py" --selftest-attach | Tee-Object "$d\EVIDENCE\selftest_attach.txt"
& python "$d\cell_sentinel.py" --perf            | Tee-Object "$d\EVIDENCE\perf.txt"
& python "$d\cell_sentinel.py" --dump            | Tee-Object "$d\EVIDENCE\dump.txt"
& python "$d\e2e_attach.py"                      | Tee-Object "$d\EVIDENCE\e2e_attach.txt"
& python "$d\selftest_guards.py"                 | Tee-Object "$d\EVIDENCE\guards.txt"
```
