# 卡 r169-exec-7d0cba（执行员 · 一次取证）

## 角色与产出
你是执行员。工作目录 /home/t628/projects/ra2-campaign-forge。只读 gamemd.exe，不修改任何事实台账。
把全部实测写进单文件 _r169/r169_exec_repro.json（UTF-8，LF），并在最后一条命令里打印该 JSON 的关键字段。
**要求：一条 python3 命令做完下面全部取证**，禁止把一个事实拆成多次单点命令。
可用库：pefile、capstone（python3-capstone）。禁止对整段 .text 开 detail=True；用 disasm_lite 或 64KB 分块。

## 背景（已定事实，不必重证，但要正控）
- .text 段 VirtualSize 口径线性解码起点数 = 1,392,527（这是正控，必须复现同值）。
- 镜像基址由 pefile 的 OPTIONAL_HEADER.ImageBase 给出；.text 的 VA 区间 = ImageBase + VirtualAddress 起，长 Misc_VirtualSize。

## 必测项（逐条给数，不许估算）
1. 正控：线性解码起点集合 S 的大小，必须等于 1,392,527；同时给 .text 的 [起, 止) VA 十六进制。
2. 表基址 0x7d0cb0：从该地址起按 4 字节步进读 dword，只要值落在 .text 的 VirtualSize 区间内就继续，遇到第一个不落的值就停。报告：
   a) 有效条目数 entries；
   b) 每一个条目的地址、值、值是否为 S 的成员；
   c) 停下的那个槽的地址与值（十六进制）。
3. 引用侧：在 .text 的 raw 字节里扫 ff 24 / ff 14 各配 7 种 modrm（8d 85 95 9d a5 b5 bd）后跟 4 字节小端 disp32，统计 disp32 恰等于 0x7d0cb0 的站点个数、站点 VA，并对 0x7d0be2 这一个地址单独做一次 capstone 解码，打印助记符与操作数串。
4. 0x7d0be2 是否为 S 成员（真指令起点），以及覆盖它的那条指令的 VA、长度、助记符。
5. 洞 0x7d0cba 的定性：
   a) 它相对表基址 0x7d0cb0 的字节偏移、所属 4 字节槽序号、槽内偏移；
   b) 从 0x7d0cba 起用 capstone 解 count=1，报告是否解得出来（应为解不出）；
   c) 打印 0x7d0cba 起 16 字节的十六进制；
   d) 解析首字节 8f：说明 8f 的 opcode 语义（POP r/m32，要求 reg 域为 0），并给出 0x7d0cba 处 modrm 的 reg 域取值，据此说明为何不可解码。
6. 邻域归属：列出 [0x7d0c9c, 0x7d0ce8) 内所有 S 成员，逐个给 VA、长度、助记符+操作数；并回答「0x7d0cba 落在哪一条真指令的字节区间内」这一问（若落在任何一条内，给该指令 VA 与相对偏移；若不在任何一条内，明确写 0 条）。
7. 反控三条：
   a) 从 r168 的成品 _r168/r168c_final_buckets.json 里取一个 tables 非空的洞（例如 0x46f5a0），用你上面的 span 逻辑复算它的表基址与条目数，报告是否与 JSON 里对该洞记录的 tab 与 entries 逐项相等；
   b) 取 .text 内一个随机 4 字节对齐地址（固定种子 169），按同样逻辑量它的有效条目数，报告是否 <= 1（用来表明「1 条目」是常见形态，不是发现）；
   c) 负控：把 0x7d0cb0 的表基址故意 +2 错位后再 4 字节步进读，报告条目数是否变小（证明相位敏感）。

## 输出字段（JSON 顶层必须有这些键）
starts_count, text_lo, text_hi, table_base, entries, entry_list, stop_slot_addr, stop_slot_value,
ref_count, ref_vas, decode_0x7d0be2, site_is_start, cover_insn, hole_delta, hole_slot_idx, hole_off_in_slot,
hole_decodable, hole_bytes16, modrm_reg_field, neighborhood, hole_covering_insn, controls{ctrl_a, ctrl_b, ctrl_c}

## 纪律
- 卡面禁反引号已由调度方保证；你的回件里也不要贴大段源码，只给数与判定。
- 若某条你测不出或与上述「已定事实」冲突，如实写进 conflicts 字段，不要迁就。
- 后台命令一律带 timeout 600。
