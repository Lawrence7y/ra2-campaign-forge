# R132 跨家族审计报告（hy4 侧，独立复算）

- 审计对象：`/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe`（PE32，ImageBase `0x400000`，`.text` VA `0x1000` / RawPtr `0x1000` / RawSize `0x3e0000`）
- 依赖：python3 + pefile `2024.8.26` + capstone `5.0.7`
- 纪律：全程只读二进制；未阅读 `_r131` / `_r132` 目录；未修改仓库任何既有文件。
- 本报告只记录命令、原始输出片段、直接得出的数字；语义推断不写入。

---

## 任务 A：Oleaut32 两槽的调用点

### A0 节表读取命令与原始输出

```bash
python3 - <<'PY'
import pefile
p=pefile.PE('/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe', fast_load=True)
print('ImageBase',hex(p.OPTIONAL_HEADER.ImageBase))
for s in p.sections:
    print(s.Name.decode(errors='replace').rstrip('\0'), 'VA',hex(s.VirtualAddress),'VSize',hex(s.Misc_VirtualSize),'RawPtr',hex(s.PointerToRawData),'RawSize',hex(s.SizeOfRawData))
PY
```

```
ImageBase 0x400000
.text VA 0x1000 VSize 0x3df38d RawPtr 0x1000 RawSize 0x3e0000
.rdata VA 0x3e1000 VSize 0x30074 RawPtr 0x3e1000 RawSize 0x31000
.data VA 0x412000 VSize 0x367be4 RawPtr 0x412000 RawSize 0x6c000
.rsrc VA 0x77a000 VSize 0x18128 RawPtr 0x47e000 RawSize 0x19000
.detour VA 0x793000 VSize 0x2718 RawPtr 0x497000 RawSize 0x3000
```

### A1 原始字节法：`.text` 内扫 `ff 15 + 4 字节小端地址`

第一次尝试把 `0x7e15fc / 0x7e1600` 直接编码成立即地址，得 0；按 PE32 的 `VA = ImageBase + RVA` 关系改查 `0xbe15fc / 0xbe1600`（即 `0x7e15fc - 0x400000 + 0x400000` 的等价写法）仍得 0。最终确认指令里的 4 字节就是 `0x7e15fc / 0x7e1600` 本身，直接用 `struct.pack('<I', target)` 命中 21 / 7 条。原命令：

```bash
python3 - <<'PY'
import pefile,struct
f='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
p=pefile.PE(f); s=p.sections[0]; base=p.OPTIONAL_HEADER.ImageBase
data=p.__data__
start=s.PointerToRawData; end=start+s.SizeOfRawData
for target in (0xbe15fc,0xbe1600,0x7e15fc,0x7e1600):
    pat=b'\xff\x15'+struct.pack('<I',target)
    hits=[]; pos=data.find(pat,start,end)
    while pos!=-1:
        hits.append(base+s.VirtualAddress+(pos-start)); pos=data.find(pat,pos+1,end)
    print(f'target {target:#x}: count={len(hits)}', ' '.join(hex(h) for h in hits))
PY
```

原始输出（只列非零项，零项也如实保留在命令中）：

```
target 0xbe15fc: count=0
target 0xbe1600: count=0
target 0x7e15fc: count=21 0x413de2 0x41c27d 0x41c2cb 0x437f6e 0x469f4b 0x46a123 0x46a564 0x46a9e2 0x46b072 0x46b3d8 0x517b74 0x67d0dd 0x67e5c1 0x6beddd 0x6bee2b 0x7734be 0x7735be 0x773fc5 0x7853e6 0x7854c4 0x785594
target 0x7e1600: count=7 0x413df1 0x41c28c 0x437f7f 0x517b83 0x67d0ec 0x67e5d0 0x6bedec
```

**数字：`call dword ptr [0x7e15fc]` = 21 处；`call dword ptr [0x7e1600]` = 7 处。**

### A2 capstone `disasm_lite` 全段线性反汇编对照

第一次脚本写成 `for a,mn,op in md.disasm_lite(...)`，报错：

```
ValueError: too many values to unpack (expected 3)
```

检查返回结构：

```bash
python3 - <<'PY'
r=list(md.disasm_lite(code,base+s.VirtualAddress))
print('lite tuple len',len(r[0]),'sample',r[0])
PY
```

```
lite tuple len 4 sample (4198400, 1, 'push', 'ebx')
```

改为 `for a,_,mn,op in ...` 后重跑：

```bash
python3 - <<'PY'
import pefile,capstone
p=pefile.PE('/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'); s=p.sections[0]; data=p.__data__
base=p.OPTIONAL_HEADER.ImageBase
code=data[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=False
targets=['0x7e15fc','0x7e1600']; res={k:[] for k in targets}
for a,_,mn,op in md.disasm_lite(code,base+s.VirtualAddress):
    if mn=='call':
        for k in targets:
            if k in op: res[k].append((a,mn,op))
for k in targets:
    print(f'capstone target {k}: count={len(res[k])}')
    for a,mn,op in res[k]: print(f'  {a:#x} {mn} {op}')
PY
```

原始输出：

```
capstone target 0x7e15fc: count=10
  0x413de2 call dword ptr [0x7e15fc]
  0x41c27d call dword ptr [0x7e15fc]
  0x41c2cb call dword ptr [0x7e15fc]
  0x437f6e call dword ptr [0x7e15fc]
  0x469f4b call dword ptr [0x7e15fc]
  0x46a123 call dword ptr [0x7e15fc]
  0x46a564 call dword ptr [0x7e15fc]
  0x46a9e2 call dword ptr [0x7e15fc]
  0x46b072 call dword ptr [0x7e15fc]
  0x46b3d8 call dword ptr [0x7e15fc]
capstone target 0x7e1600: count=3
  0x413df1 call dword ptr [0x7e1600]
  0x41c28c call dword ptr [0x7e1600]
  0x437f7f call dword ptr [0x7e1600]
```

**数字：capstone 线性反汇编得 10 / 3；原始字节法得 21 / 7。两种方法在 `0x46b3d8` 之后失步：capstone 的 10 个 `0x7e15fc` 站点全部包含在原始字节法的 21 个站点内；capstone 的 3 个 `0x7e1600` 站点全部包含在原始字节法的 7 个站点内。** 失步原因不在解析器元组解包（已修正），capstone 从数据字节继续线性解码后与真实指令边界错位。

### A3 PE 导入表查两个槽位的 DLL 与函数

先按 `base + imp.address` 查，未命中；按 `imp.address` 本身（RVA）查命中。原命令：

```bash
python3 - <<'PY'
import pefile
p=pefile.PE('/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe')
p.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
base=p.OPTIONAL_HEADER.ImageBase
for d in p.DIRECTORY_ENTRY_IMPORT:
    for i in d.imports:
        if getattr(i,'address',None) in (0x7e15fc,0x7e1600):
            print(d.dll, hex(i.address), i.name)
PY
```

原始输出：

```
b'ole32.dll' 0x7e15fc b'CoCreateInstance'
b'ole32.dll' 0x7e1600 b'OleRun'
```

**数字：`0x7e15fc` = `ole32.dll!CoCreateInstance`；`0x7e1600` = `ole32.dll!OleRun`。**

---

## 任务 B：调用点的结构分类

### B0 五条 push 的机械提取

从 A1 得到的 21 个 `call [0x7e15fc]` 站点起，取前 `0x50` 字节用 capstone `disasm_lite` 解码，只按 mnemonic 等于 `push` 机械选取最后 5 条，不按地址连续性过滤（部分站点之间夹有 `mov` / `and` / `lea` 等指令，详见原始 tail 输出）。映射规则按 stdcall 从右到左压栈确定：先压的依次是 `ppv`, `rclsid`, `dwClsContext`, `pUnkOuter`, `riid`。

```bash
python3 - <<'PY'
import pefile,capstone,struct
from collections import Counter
p=pefile.PE('/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe')
s=p.sections[0]; raw=p.__data__; base=p.OPTIONAL_HEADER.ImageBase
code=raw[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData]
pat=b'\xff\x15'+struct.pack('<I',0x7e15fc)
sites=[]; pos=code.find(pat)
while pos!=-1: sites.append(base+s.VirtualAddress+pos); pos=code.find(pat,pos+1)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=False
rows=[]
for va in sites:
    off=va-(base+s.VirtualAddress)-0x50
    ins=list(md.disasm_lite(code[off:va-(base+s.VirtualAddress)],base+s.VirtualAddress+off))
    fif=[(a,mn,op) for a,_,mn,op in ins if mn=='push'][-5:]
    assert len(fif)==5
    rows.append((va,[op for a,mn,op in fif]))
print('site | ppv | rclsid | dwClsContext | pUnkOuter | riid')
for va,f in rows:
    print(f'{va:#x} | {f[0]} | {f[1]} | {f[2]} | {f[3]} | {f[4]}')
print('\ndwClsContext (push#3) distribution:')
for k,v in sorted(Counter(f[2] for va,f in rows).items(),key=lambda x:(-x[1],x[0])): print(k,v)
print('\nriid (push#5) distribution:')
for k,v in sorted(Counter(f[4] for va,f in rows).items(),key=lambda x:(-x[1],x[0])): print(k,v)
PY
```

原始输出：

```
site | ppv | rclsid | dwClsContext | pUnkOuter | riid
0x413de2 | eax | 0x817bc0 | 7 | 0 | ebx
0x41c27d | edx | 0x817bc0 | eax | eax | ecx
0x41c2cb | edi | 0x817bb0 | eax | eax | ecx
0x437f6e | eax | 0x817bc0 | 7 | 0 | 0x7e9500
0x469f4b | eax | 0x7f7c90 | 7 | 0 | 0x7e96e0
0x46a123 | ecx | 0x7f7c90 | 7 | 0 | 0x7e96e0
0x46a564 | ecx | 0x7f7c90 | 7 | 0 | 0x7e96e0
0x46a9e2 | eax | 0x7f7c90 | 7 | 0 | 0x7e96e0
0x46b072 | eax | 0x7f7c90 | 7 | 0 | 0x7e96e0
0x46b3d8 | ecx | 0x7f7c90 | 7 | 0 | 0x7e96e0
0x517b74 | eax | 0x817bc0 | 7 | ebx | ebp
0x67d0dd | edx | 0x817bc0 | 7 | ebp | 0x7e9540
0x67e5c1 | eax | 0x817bc0 | 7 | ebp | 0x7e9540
0x6beddd | edx | 0x817bc0 | eax | eax | ecx
0x6bee2b | edi | 0x817bc0 | eax | eax | ecx
0x7734be | edi | 0x7f7c30 | 1 | 0 | 0x7f7c60
0x7735be | esi | 0x7f7c30 | 1 | 0 | 0x7f7c60
0x773fc5 | ebp | 0x7f7c30 | 1 | 0 | 0x7f7c60
0x7853e6 | 0xac116c | 0x7f7540 | 1 | ebx | 0x7f75e0
0x7854c4 | 0xac1170 | 0x7f7580 | 1 | ebx | 0x7f7600
0x785594 | 0xac1174 | 0x7f7560 | 1 | ebx | 0x7f75f0

dwClsContext (push#3) distribution:
7 11
1 6
eax 4

riid (push#5) distribution:
0x7e96e0 6
ecx 4
0x7f7c60 3
0x7e9540 2
0x7e9500 1
0x7f75e0 1
0x7f75f0 1
0x7f7600 1
ebp 1
ebx 1
```

机械提取的辅助原始输出（每站点前 8 条指令，用于检查 push 是否紧邻）：

```
0x413de2: tail: push eax | call dword ptr [edx + 8] | lea eax, [esp + 0x18] | push eax | push 0x817bc0 | push 7 | push 0 | push ebx
0x41c27d: tail: mov ecx, dword ptr [esp + 0xc] | lea edx, [esp + 0x10] | push edx | push 0x817bc0 | push eax | mov eax, dword ptr [esp + 0x1c] | push eax | push ecx
0x41c2cb: tail: ret 0xc | mov ecx, dword ptr [esp + 0xc] | push edi | push 0x817bb0 | push eax | mov eax, dword ptr [esp + 0x1c] | push eax | push ecx
0x437f6e: tail: push edi | push eax | push 0x817bc0 | mov edi, ecx | push 7 | push 0 | push 0x7e9500 | mov dword ptr [edi], 0
0x469f4b: tail: push 7 | and ebx, 7 | push 0 | push 0x7e96e0 | mov dword ptr [esp + 0x84], ebx | mov dword ptr [esp + 0x64], ecx | mov dword ptr [esp + 0x4c], edx | mov dword ptr [esp + 0x60], 0
0x46a123: tail: push ecx | push 0x7f7c90 | push 7 | push 0 | push 0x7e96e0 | mov dword ptr [esp + 0x24], edx | mov dword ptr [esp + 0x4c], eax | mov dword ptr [esp + 0x60], 0
0x46a564: tail: mov byte ptr [esp + 0xac], al | mov eax, dword ptr [edi + 0xb0] | push 7 | push 0 | push 0x7e96e0 | mov dword ptr [esp + 0x7c], edx | mov dword ptr [esp + 0x44], eax | mov dword ptr [esp + 0xa4], 0
0x46a9e2: tail: mov dword ptr [esp + 0x30], eax | lea eax, [esp + 0x40] | push eax | push 0x7f7c90 | push 7 | push 0 | push 0x7e96e0 | mov dword ptr [esp + 0x54], 0
0x46b072: tail: push eax | push 0x7f7c90 | push 7 | push 0 | mov edi, edx | mov ebx, ecx | push 0x7e96e0 | mov dword ptr [esp + 0x1c], 0
0x46b3d8: tail: push 0x7f7c90 | mov dword ptr [esp + 0x24], eax | mov eax, dword ptr [ebp + 0xb0] | push 7 | push 0 | push 0x7e96e0 | mov dword ptr [esp + 0x34], edx | mov dword ptr [esp + 0x38], eax
0x517b74: tail: push eax | call dword ptr [edx + 8] | lea eax, [esp + 0x18] | push eax | push 0x817bc0 | push 7 | push ebx | push ebp
0x67d0dd: tail: mov dword ptr [esp + 0x14], ebp | call 0x67fde0 | lea edx, [esp + 0x20] | push edx | push 0x817bc0 | push 7 | push ebp | push 0x7e9540
0x67e5c1: tail: mov dword ptr [esp + 0x14], ebp | call 0x67fde0 | lea eax, [esp + 0x10] | push eax | push 0x817bc0 | push 7 | push ebp | push 0x7e9540
0x6beddd: tail: mov ecx, dword ptr [esp + 0xc] | lea edx, [esp + 0x10] | push edx | push 0x817bc0 | push eax | mov eax, dword ptr [esp + 0x1c] | push eax | push ecx
0x6bee2b: tail: ret 0xc | mov ecx, dword ptr [esp + 0xc] | push edi | push 0x817bc0 | push eax | mov eax, dword ptr [esp + 0x1c] | push eax | push ecx
0x7734be: tail: push 0x8495ac | call 0x4068e0 | add esp, 4 | push edi | push 0x7f7c30 | push 1 | push 0 | push 0x7f7c60
0x7735be: tail: call 0x4068e0 | add esp, 4 | lea esi, [edi + 8] | push esi | push 0x7f7c30 | push 1 | push 0 | push 0x7f7c60
0x773fc5: tail: push 0x8495ac | call 0x4068e0 | add esp, 4 | push ebp | push 0x7f7c30 | push 1 | push 0 | push 0x7f7c60
0x7853e6: tail: push 0x7f7540 | push 1 | push ebx | push 0x7f75e0 | mov dword ptr [0xac1174], ebx | mov dword ptr [0xb77e54], ebx | mov dword ptr [0xb77e58], ebx | mov dword ptr [0xb77e5c], ebx
0x7854c4: tail: je 0x78570f | cmp esi, ebx | jne 0x78570f | push 0xac1170 | push 0x7f7580 | push 1 | push ebx | push 0x7f7600
0x785594: tail: je 0x785706 | cmp esi, ebx | jne 0x785706 | push 0xac1174 | push 0x7f7560 | push 1 | push ebx | push 0x7f75f0
```

### B1 dwClsContext 取值分布

原始输出见 B0 尾部：

```
dwClsContext (push#3) distribution:
7 11
1 6
eax 4
```

**数字：常量 `7` = 11 次；常量 `1` = 6 次；寄存器 `eax` = 4 次。常量 `0` = 0 次。**

### B2 riid 取值分布

原始输出见 B0 尾部：

```
riid (push#5) distribution:
0x7e96e0 6
ecx 4
0x7f7c60 3
0x7e9540 2
0x7e9500 1
0x7f75e0 1
0x7f75f0 1
0x7f7600 1
ebp 1
ebx 1
```

**数字：立即数 `0x7e96e0` = 6 次；`0x7f7c60` = 3 次；`0x7e9540` = 2 次；`0x7e9500` = 1 次；`0x7f75e0` = 1 次；`0x7f75f0` = 1 次；`0x7f7600` = 1 次；寄存器 `ecx` = 4 次；寄存器 `ebp` = 1 次；寄存器 `ebx` = 1 次。**

---

## 任务 C：两个候选函数

### C1 / C2 反汇编命令与原始输出

```bash
python3 - <<'PY'
import pefile,capstone
p=pefile.PE('/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe')
s=p.sections[0]; raw=p.__data__; base=p.OPTIONAL_HEADER.ImageBase
code=raw[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=False
for start in (0x6bedb0,0x41c250):
    off=start-(base+s.VirtualAddress)
    print(f'===== disasm {start:#x} +160 bytes =====')
    n=0
    for a,_,mn,op in md.disasm_lite(code[off:off+160],start):
        print(f'{a:#x} {mn:8s} {op}'); n+=1
    print('instructions',n)
PY
```

`0x6bedb0` 起 160 字节原始输出：

```
0x6bedb0 push     esi
0x6bedb1 push     edi
0x6bedb2 mov      edi, ecx
0x6bedb4 mov      eax, dword ptr [edi]
0x6bedb6 test     eax, eax
0x6bedb8 je       0x6bedc0
0x6bedba mov      ecx, dword ptr [eax]
0x6bedbc push     eax
0x6bedbd call     dword ptr [ecx + 8]
0x6bedc0 mov      eax, dword ptr [esp + 0x14]
0x6bedc4 test     al, 0x14
0x6bedc6 je       0x6bee1a
0x6bedc8 mov      ecx, dword ptr [esp + 0xc]
0x6bedcc lea      edx, [esp + 0x10]
0x6bedd0 push     edx
0x6bedd1 push     0x817bc0
0x6bedd6 push     eax
0x6bedd7 mov      eax, dword ptr [esp + 0x1c]
0x6beddb push     eax
0x6beddc push     ecx
0x6beddd call     dword ptr [0x7e15fc]
0x6bede3 test     eax, eax
0x6bede5 jl       0x6bee33
0x6bede7 mov      edx, dword ptr [esp + 0x10]
0x6bedeb push     edx
0x6bedec call     dword ptr [0x7e1600]
0x6bedf2 mov      esi, eax
0x6bedf4 test     esi, esi
0x6bedf6 jl       0x6bee09
0x6bedf8 mov      eax, dword ptr [esp + 0x10]
0x6bedfc push     edi
0x6bedfd push     0x817bc0
0x6bee02 push     eax
0x6bee03 mov      ecx, dword ptr [eax]
0x6bee05 call     dword ptr [ecx]
0x6bee07 mov      esi, eax
0x6bee09 mov      eax, dword ptr [esp + 0x10]
0x6bee0d push     eax
0x6bee0e mov      edx, dword ptr [eax]
0x6bee10 call     dword ptr [edx + 8]
0x6bee13 mov      eax, esi
0x6bee15 pop      edi
0x6bee16 pop      esi
0x6bee17 ret      0xc
0x6bee1a mov      ecx, dword ptr [esp + 0xc]
0x6bee1e push     edi
0x6bee1f push     0x817bc0
0x6bee24 push     eax
0x6bee25 mov      eax, dword ptr [esp + 0x1c]
0x6bee29 push     eax
0x6bee2a push     ecx
0x6bee2b call     dword ptr [0x7e15fc]
0x6bee31 mov      esi, eax
0x6bee33 pop      edi
0x6bee34 pop      esi
0x6bee35 ret      0xc
0x6bee38 nop
0x6bee39 nop
0x6bee3a nop
0x6bee3b nop
0x6bee3c nop
0x6bee3d nop
0x6bee3e nop
0x6bee3f nop
0x6bee40 mov      eax, ecx
0x6bee42 mov      dword ptr [eax + 4], 0
0x6bee49 mov      dword ptr [eax], 0x7f3768
0x6bee4f ret
instructions 68
```

`0x41c250` 起 160 字节原始输出：

```
0x41c250 push     esi
0x41c251 push     edi
0x41c252 mov      edi, ecx
0x41c254 mov      eax, dword ptr [edi]
0x41c256 test     eax, eax
0x41c258 je       0x41c260
0x41c25a mov      ecx, dword ptr [eax]
0x41c25c push     eax
0x41c25d call     dword ptr [ecx + 8]
0x41c260 mov      eax, dword ptr [esp + 0x14]
0x41c264 test     al, 0x14
0x41c266 je       0x41c2ba
0x41c268 mov      ecx, dword ptr [esp + 0xc]
0x41c26c lea      edx, [esp + 0x10]
0x41c270 push     edx
0x41c271 push     0x817bc0
0x41c276 push     eax
0x41c277 mov      eax, dword ptr [esp + 0x1c]
0x41c27b push     eax
0x41c27c push     ecx
0x41c27d call     dword ptr [0x7e15fc]
0x41c283 test     eax, eax
0x41c285 jl       0x41c2d3
0x41c287 mov      edx, dword ptr [esp + 0x10]
0x41c28b push     edx
0x41c28c call     dword ptr [0x7e1600]
0x41c292 mov      esi, eax
0x41c294 test     esi, esi
0x41c296 jl       0x41c2a9
0x41c298 mov      eax, dword ptr [esp + 0x10]
0x41c29c push     edi
0x41c29d push     0x817bb0
0x41c2a2 push     eax
0x41c2a3 mov      ecx, dword ptr [eax]
0x41c2a5 call     dword ptr [ecx]
0x41c2a7 mov      esi, eax
0x41c2a9 mov      eax, dword ptr [esp + 0x10]
0x41c2ad push     eax
0x41c2ae mov      edx, dword ptr [eax]
0x41c2b0 call     dword ptr [edx + 8]
0x41c2b3 mov      eax, esi
0x41c2b5 pop      edi
0x41c2b6 pop      esi
0x41c2b7 ret      0xc
0x41c2ba mov      ecx, dword ptr [esp + 0xc]
0x41c2be push     edi
0x41c2bf push     0x817bb0
0x41c2c4 push     eax
0x41c2c5 mov      eax, dword ptr [esp + 0x1c]
0x41c2c9 push     eax
0x41c2ca push     ecx
0x41c2cb call     dword ptr [0x7e15fc]
0x41c2d1 mov      esi, eax
0x41c2d3 pop      edi
0x41c2d4 pop      esi
0x41c2d5 ret      0xc
0x41c2d8 nop
0x41c2d9 nop
0x41c2da nop
0x41c2db nop
0x41c2dc nop
0x41c2dd nop
0x41c2de nop
0x41c2df nop
0x41c2e0 sub      esp, 8
0x41c2e3 push     esi
0x41c2e4 mov      esi, ecx
0x41c2e6 sub      esp, 8
0x41c2e9 fld      qword ptr [esi + 8]
0x41c2ec fld      qword ptr [esi]
0x41c2ee fld      st(0)
instructions 71
```

### C3 两个函数体里 `call [0x7e15fc]` 计数

依据 C1/C2 的原始反汇编输出逐条核对：

- `0x6bedb0` 起 160 字节内：`0x6beddd`、`0x6bee2b`，计 **2 次**。
- `0x41c250` 起 160 字节内：`0x41c27d`、`0x41c2cb`，计 **2 次**。

### C4 两个函数体里 `call [0x7e1600]` 计数

依据 C1/C2 的原始反汇编输出逐条核对：

- `0x6bedb0` 起 160 字节内：`0x6bedec`，计 **1 次**。
- `0x41c250` 起 160 字节内：`0x41c28c`，计 **1 次**。

### C5 前 136 字节逐字节比较

```bash
python3 - <<'PY'
import pefile
p=pefile.PE('/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe')
s=p.sections[0]; raw=p.__data__; base=p.OPTIONAL_HEADER.ImageBase
def b(va,n):
    off=va-(base+s.VirtualAddress)
    return raw[s.PointerToRawData+off:s.PointerToRawData+off+n]
a=b(0x6bedb0,136); c=b(0x41c250,136)
diff=[(i,a[i],c[i]) for i in range(136) if a[i]!=c[i]]
print('length compared',len(a),len(c))
print('diff count',len(diff))
for i,x,y in diff: print(f'offset {i:#04x} ({i:3d}): {x:#04x} vs {y:#04x}')
PY
```

原始输出：

```
length compared 136 136
diff count 2
offset 0x4e ( 78): 0xc0 vs 0xb0
offset 0x70 (112): 0xc0 vs 0xb0
```

**数字：不相等偏移共 2 个：`0x4e` / `78` 处 `0xc0` vs `0xb0`；`0x70` / `112` 处 `0xc0` vs `0xb0`。**
