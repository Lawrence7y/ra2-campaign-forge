# R128 跨家族审计卡（审计员：hy4 家族）

## 你的角色
你是独立审计员。主会话给了四条主张，你的任务是**只按字节复算**，逐条给 PASS 或 FAIL 并写清你自己解出的原始数字。不要接受卡面给的任何结论，卡面只给「要核什么」。

## 环境（本机 t628，全部只读）
- 工程根目录：/home/t628/projects/ra2-campaign-forge
- 目标文件：ra2bench/gamemd.exe，sha256 必须是 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
- 可用工具：python3 + pefile + capstone；i686-w64-mingw32-objdump；rg
- 段表（ImageBase 0x400000）：.text 0x401000..0x7e1000，.rdata 0x7e1000..0x812000，.data 0x812000 起，raw 只到 0x87e000，其余为 BSS（映像文件里没有字节）

## 内存红线（硬约束，违反会拖垮本机）
- 严禁 md.detail=True 对整段 .text 调用 md.disasm()。整段扫描只能用 md.disasm_lite()，或 64KB 分块。
- 每个脚本必须 timeout 运行。跑完确认没有残留 python 进程。

## 要核的四条主张

### 主张 1（对象身份）
地址 0x87f7e8 落在 .data 的 BSS 区（映像文件无静态字节）。核：
1) 该地址 4 字节 little-endian 在 .text 逐字节出现多少次；
2) 用 capstone disasm_lite 得指令流后，操作数里含该地址的指令有多少条，分别是什么形态（自己分类统计）；
3) 形态为 mov dword ptr [0x87f7e8], imm32 的站点有几处、地址各是多少、写入的立即数是多少；
4) 用该立即数当 vtable 地址，按 MSVC x86 32 位 RTTI 解出类名（vtable 前 4 字节即 vt-4 处是 COL 指针；COL+12 是 TypeDescriptor 指针，TypeDescriptor+8 是类名 C 字符串；COL+16 是 ClassHierarchyDescriptor，其 +8 是基类数、+12 是 BaseClassArray 指针，数组每项是 BaseClassDescriptor 指针，其 +0 是 TypeDescriptor 指针、+4 是 ncb、+8 是 mdisp）。
5) 反控：对 0x87f7e4 与 0x87f7ec 做同样统计，报数字。

### 主张 2（方法调用约定）
vtable 0x7ea564 的 slot0..slot4 分别是 0x429210 / 0x4e8240 / 0x4e8250 / 0x429270 / 0x4e8260。核：这五个函数体各自的 ret 指令后面跟的字节数是多少（ret 4 就报 4，ret 0xc 报 12，纯 ret 报 0）。给出五个数字。

### 主张 3（CreateInstance 的实参位置）
函数 0x429270 体内，从函数入口正向反汇编，前 0x60 字节内：读 [esp+0x10] 存到哪个寄存器、读 [esp+0x18] 存到哪个寄存器、读 [esp+0x1c] 存到哪个寄存器；函数体内是否有一处 mov dword ptr [reg], 0 用于清零出参。给出这四条各自的地址与完整指令文本。

### 主张 4（IID 常量的全部引用点）
常量地址 0x7ea6e8（16 字节 GUID）。核：用 capstone disasm_lite 全 .text 扫描后，操作数文本里含 0x7ea6e8 的指令有几条、地址各是多少、指令文本各是什么。再报 0x7ea6e8 处 16 字节按 GUID 文本格式化后的字符串（格式 {8-4-4-4-12}，Data4 前 2 字节一组、后 6 字节一组）。

## 输出格式
写文件到 /home/t628/projects/ra2-campaign-forge/_r128/audit/r128_audit_hy4.md
- 每条主张一节，先写「你实测的原始数字」，再写「与卡面的主张是否一致」，再写 PASS 或 FAIL。
- 全文**严禁出现反引号字符**（写代码片段用四个空格缩进）。
- 你要指出卡面哪条说法你复算不出来、或者算出来不一样，这类分歧必须单列一节。
- 不要写总结性赞美，只写数字与判定。
