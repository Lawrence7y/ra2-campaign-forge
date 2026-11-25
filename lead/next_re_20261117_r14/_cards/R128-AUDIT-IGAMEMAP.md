# R128 第二张审计卡（审计员：deepseek 家族，与 hy4 卡不重叠）

## 你的角色
独立审计员，只按字节复算。卡面只给「要核什么」，不给结论。逐条给 PASS 或 FAIL，并写出你自己解出的原始数字。

## 环境（本机 t628，全部只读）
- 工程根目录：/home/t628/projects/ra2-campaign-forge
- 目标文件：ra2bench/gamemd.exe，sha256 必须是 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
- 可用：python3 + pefile + capstone；i686-w64-mingw32-objdump；rg
- 段表（ImageBase 0x400000）：.text 0x401000..0x7e1000，.rdata 0x7e1000..0x812000，.data 0x812000 起，.data 的 raw 只到 0x87e000，其后为 BSS（映像文件里没有字节，静态读回空）

## 内存红线（硬约束）
严禁 md.detail=True 对整段 .text 调用 md.disasm()。整段扫描只用 md.disasm_lite()。脚本必须 timeout 运行，跑完确认无残留 python 进程。

## 要核的五条

### 主张 A（一个全局单例的类型）
地址 0x87f7e8 在 .data 的 BSS 区。核：
1) 是否存在 mov dword ptr [0x87f7e8], imm32 这一形态的指令？有几处、地址、立即数各是多少？
2) 用该立即数作为 vtable 地址，按 MSVC x86 32 位 RTTI 解出类名（vtable 前 4 字节是 COL 指针；COL+12 是 TypeDescriptor，+8 处是类名 C 字符串；COL+16 是 ClassHierarchyDescriptor，其 +8 是基类数、+12 是 BaseClassArray，每项是 BaseClassDescriptor，其 +0 是 TypeDescriptor、+4 是 ncb、+8 是 mdisp）。报类名与全部基类的 (name, ncb, mdisp) 三元组。
3) 该 vtable 的 slot0 地址是多少？

### 主张 B（一个 IID 常量的格式化）
地址 0x7ea6e8 处 16 字节。按 GUID 格式 {Data1(4B LE)-Data2(2B LE)-Data3(2B LE)-Data4[0..1]-Data4[2..7]} 全部大写十六进制输出。同时输出 0x7e36c0 与 0x7f7c90 的同样格式，并说明三者 Data1 是否相同。

### 主张 C（该常量的全部比较点）
用 capstone disasm_lite 全 .text 扫描，列出操作数文本里含 0x7ea6e8 的所有指令（地址 + 文本）。对每一条，从该指令起正向反汇编 32 字节，判断它后面是否紧接着 repe cmpsd（字节 f3 a7）。报每条是否成立。

### 主张 D（函数 0x429270 的转交点）
从 0x429270 起正向反汇编 0xf0 字节。找出所有 call dword ptr [reg] 形态的指令，对每一处报：地址、reg 名、该 reg 在此之前最后一次被赋值的指令文本（若来自 mov reg, dword ptr [绝对地址] 则报该绝对地址）。再报该函数里所有 push 立即数的指令及其立即数值。

### 主张 E（另一条 QI 体的比较常量）
函数 0x429360 起正向反汇编 0x90 字节。报出所有 mov edi, <绝对地址> 指令的地址与立即数，按出现顺序。再报该函数体内对 dword ptr [edx] 的写指令（地址 + 源操作数）。

## 输出格式
写文件到 /home/t628/projects/ra2-campaign-forge/_r128/audit/r128_audit_deepseek.md
- 每条一节：先写「实测原始数字」，再写「与卡面主张是否一致」，再写 PASS 或 FAIL。
- 全文严禁出现反引号字符（写代码片段用四个空格缩进）。
- 你复算不出来、或算出来与卡面不一致的，单列一节写清分歧。
- 不写总结性赞美。
