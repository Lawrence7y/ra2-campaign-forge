D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe	73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# R17-R36-VERIFY-TABLEBASE · 定点核验 dword[0x87F924]

PE32, ImageBase=0x400000, SectionAlignment=0x1000, FileAlignment=0x1000, SizeOfHeaders=0x1000. VA = ImageBase + section.VirtualAddress.

## Q1 · 0x87F7E8 是否已映射 VA / 落在哪个节

- RVA(0x87F7E8) = 0x47F7E8。
- 落在 `.data`：虚拟范围 0x812000–0xB79BE4（加载对齐上界 0xB7A000），节内偏移 0x6D7E8。
- 结论：0x87F7E8 不是节间空隙，它是已映射 VA；但节内偏移大于 raw 容量，属于 `.data` 的未初始化尾段（loader zero-fill）。
- `.data` raw 仅 0x412000–0x47E000，对应 VA 上界 0x87E000；0x87F7E8 超出该 raw 上界。
- Lead 用 file_offset=va-0x400000 读到 0x47F7E8；该 file offset 落在 `.rsrc` raw 0x47E000–0x497000，所以读出的 UTF-16 "01 Westwood Studios" 是资源字节，不是 .data。
- 节表全量见 `sections.tsv`。

## Q2 · ecx 是什么 / 调用点字节

- `8B 89 3C 01 00 00` = `mov ecx, dword ptr [ecx+0x13C]`，此处 ecx 是 thiscall 的 `this`。
- 函数 0x5657A0 前几条：`8B 54 24 04`(arg) `56` `0F BF 42 02` `0F BF 32` `C1 E0 09` `03 C6` `5E` `78 14` `3D 00 00 04 00` `7D 0D`；随后 `8B 89 3C 01 00 00` 取 `this+0x13C`，再 `8B 04 81` 取表项，`C2 04 00` 返回。故不是栈参数充当 this。
- 调用点确有立即数装入：VA 0x449476 字节 `B9 E8 F7 87 00` = `mov ecx, 0x87F7E8`；紧接 VA 0x44947B 字节 `E8 20 C3 11 00` = `call 0x5657A0`。
- 因此运行时 `this = 0x87F7E8`（`.data` 中的一个全局对象地址），`this+0x13C = 0x87F924`。

## Q3 · dword[0x87F924] 静态值

- RVA(0x87F924) = 0x47F924；在 `.data` 内偏移 0x6D924，小于 VirtualSize 0x367BE4，但大于 SizeOfRawData 0x6C000（raw 结束偏移）。
- 正确节表映射结论：该 dword 无文件字节；静态值 **未取得**（加载时清零，运行期写入）。不得用 va-ImageBase 得到的资源区字节冒充。

## 三选一判定

① **R35 正确**：`ecx=0x87F7E8` 是调用点真实立即数，函数按 thiscall 使用 ecx，`[ecx+0x13C]` 即 `dword[0x87F924]` 是表指针位置；唯一修正是该位置在静态镜像中无初始化值，需运行期观察。
