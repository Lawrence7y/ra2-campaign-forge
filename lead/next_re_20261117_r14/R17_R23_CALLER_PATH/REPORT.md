D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe  73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# R17-R23-CALLER-PATH 报告

镜像校验：PASS（sha256 以 73201CC0 开头，尾段 F67476 与卡面一致）。纯静态只读；未创建/启动 gamemd 进程。产物仅写本目录。

## 扫描与锚点

- `.text`：VA 0x401000–0x7E038D，raw 扫描 4,063,232 字节；按 E8 rel32 解算直接 call。
- 反汇编函数：14 个（第 1 步 site 所在函数去重）；第 2 步共反汇编 11363 字节（0x2C63）。
- 第 3 步：未进入；反汇编 0 个函数、0 字节（第 2 步已找到目标）。
- 锚点：host 取直接调用目标/对齐填充后的函数起点；每个 site 均在从 host 起线性反汇编的指令边界上，`call` 首字节为 E8。host/fn_end 为最后一条 ret 的 end（字节实测），逐条位置断言见 `ctor_sites.tsv`。

## 第 1 步 · 构造点

全 `.text` 直接 call 命中 15 处：call 0x43B740 为 14 处，call 0x43B680 为 1 处。全部 site / host / fn_end / 断言见 `ctor_sites.tsv`。

## 第 2 步 · 定偏移虚调用命中与基址判定

在 14 个 host 内命中 6 处 `call [reg+0x124]`；`call [reg+0x1AC]` 0 处；`mov reg2,[reg+0x124/0x1AC]; call reg2` 0 处。逐条见 `dispatch_hits.tsv`。

**找到 0x43F180 的真实调用方：site 0x5A6860。**

完整链（host 0x5A652D，fn_end 0x5A691C；位置断言 0x5A652D <= 0x5A6860 < 0x5A691C）：
1. 0x5A66D4：`E8 67 50 E9 FF` = `call 0x43B740`（BuildingClass ctor A）。该 ctor 在序言后把 vtable 0x7E3EBC 写入 `[esi]`，故返回对象 EAX 的 vptr 为 0x7E3EBC（引用卡面已确立事实）。
2. 0x5A66D9：`8B E8` = `mov ebp,eax`；EBP 即构造出来的对象指针。
3. 0x5A684D：`8B 55 00` = `mov edx,[ebp]`；EDX = 该对象的 vptr（0x7E3EBC）。
4. 0x5A6860：`FF 92 24 01 00 00` = `call dword ptr [edx+0x124]`；即 slot #73 → 0x43F180。

基址判定：EDX 不是无关寄存器；字节链严格来自 ctor 返回对象（EAX → EBP → [EBP] → EDX），未放宽为“任意 BuildingClass-like 对象”。其余 5 处均不满足同一对象（多在 ctor 之前，或 ctor 对象在 EBX 而 hit 用 EBP/EDX）。

## 第 3 步 · 向上扩一层

未执行。第 2 步已在 host 0x5A652D 内取得同一对象派发，按有界原则不向上回溯。

## 覆盖边界

本路径仍不覆盖：对象经全局/成员字段长距离传递后再派发、跨函数传入后由另一函数派发、以及非 0x43B680/0x43B740 构造路径产生的同类对象。但这些情形未参与本次“找到”的判定。

## 对 ②-b 收口的影响

不改变 ②-b 的 `[静态推断]` 收口（D-53(A)）。本次取得的是指令层调用方；D-53(A) 收的是行为层可区分性，两者层级不同。

## 复跑

`python R17_R23_CALLER_PATH\work.py`（只读输入镜像；输入 sha256 如上）。
