# 待办 9 第二段：继承链定谳（修正 §352 的过度断言）

**日期**：2026-10-22　**性质**：只读离线，零真机
**二进制**：`ra2youli/gamemd.exe` sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`

---

## 0. 一句话结论

**`RadarClass` 是 `MouseClass` 的基类，且子对象在偏移 0。**

MouseClass 的 RTTI 基类链（12 项，派生→基）：
```
MouseClass → ScrollClass → TabClass → SidebarClass → PowerClass
           → RadarClass → DisplayClass → MapClass → GScreenClass
           → UIGameMap → UIUnknown → INoticeSink
```

RadarClass 的基类链（6 项）：
```
RadarClass → DisplayClass → MapClass → GScreenClass → UIGameMap → UIUnknown
```

⇒ RadarClass 的 6 项**恰好是** MouseClass 12 项的后 6 项 ⇒ **包含关系成立**。
且 `RadarClass` 在 MouseClass 链中的 `mdisp = 0` ⇒ **子对象就在对象首地址**。

---

## 1. 必须修正 §352 的一句话

§352 写：

> **`0x87F7E8` 不是 RadarClass 单例，是 MouseClass 单例。**

**这句里的「不是」必须删掉。** 正确表述：

> `0x87F7E8` 是 **MouseClass 对象**，而 MouseClass **继承自 RadarClass**
> ⇒ 该对象**同时**是 RadarClass 实例（同一地址，`mdisp=0`）。

§352 的其余结论仍然成立（atexit 回调、表 B 只在退出期装、One_Time 只经表 B slot5 可达）。

---

## 2. 机制澄清：同一地址只能存一个 vtable

`[0x87F7E8]` 存的是 vtable 指针，同一时刻只有一个值：

| 装的是 | vtable | slot5 | slot5 是什么 |
|:--|:--|:--|:--|
| 表 A | `0x7E1964`（MouseClass） | `0x5BDF30` | MouseClass 的覆盖版 |
| 表 B | `0x7F0344`（RadarClass） | `0x652CF0` | `RadarClass::One_Time()` |

⇒ **谁最后装，谁生效。**

这解释了 §347 观察到的「两次构造」为什么方向是对的——它确实看到了两次装表。
§347 的错误只在于把**退出期 atexit 回调**（`0x40D1B0`）当成了运行期。

### 2.1 `0x5BDF30` 的语义（表 A slot5）

```asm
005BDF30  call 0x6D0260
005BDF35  mov edx, 0xABF2DC
005BDF3A  mov ecx, 0x82604C
005BDF3F  call 0x4A38D0
005BDF44  mov [0xABF294], eax
005BDF49  ret
```

6 条指令、无字符串、无 L3 调用。它不是 One_Time 语义，也不是每帧 AI。
（此前 §352 说它「不是 One_Time 语义」这一条**仍然成立**。）

---

## 3. 5 个"宿主"是析构函数，不是构造函数（§352 的第二个过度断言）

`0x40D2D4` 的完整函数体：

```asm
0040D290  push ebx
0040D291  mov ebx, ecx              ; ebx = this
0040D293  push esi / push edi
0040D295  mov [ebx], 0x7E1964       ; ← 装表A
0040D29B  mov [ebx+0x5518], 0x7E195C
0040D2A5  lea esi, [ebx+0x539C]
0040D2AB  mov edi, 4
0040D2B0  ...循环 4 次：call 0x40AFD0 / call 0x40D300...
0040D2D2  mov ecx, ebx
0040D2D4  call 0x652C00             ; ← 装表B
0040D2D9  test byte [esp+0x10], 1   ; ← flags & 1
0040D2E0  push ebx / call 0x7C8B3D  ; ← operator delete
0040D2EE  ret 4                     ; ← 标量删除析构函数
```

`0x652C00` 体内有 **3 处 `call 0x7C8B3D`（operator delete）**，并把
`[esi+4]`/`[esi+8]`/`[edi+0x1228]`/`[edi+0x1260]` 等成员清零。

⇒ **`0x652C00` 是析构/重初始化例程，5 个宿主都是标量删除析构函数。**

§352 写「表 B 由 5 个**运行期**站点装到**别的对象**上 ⇒ One_Time 的调用者必在这 5 个对象之一」——
这个推论**不成立**：
1. 这 5 个站点在**析构**路径上，不是构造路径；
2. `0x652C00` 把表 B 写进 `[edi]`（`edi=ecx=this`），对**任意**传入的 this 都生效，
   它体内**不触及任何 RadarClass 专属成员偏移**（§352 报告的「5 个 RadarClass 实例」无据）。

### 3.1 5 个宿主的形态相似度（70% 平均）

| 对 | 相似度 |
|:--|--:|
| `0x40D2D4` vs `0x69391A` | 87.5% |
| `0x40D2D4` vs `0x6AC81A` | 85.4% |
| `0x69391A` vs `0x6AC81A` | 85.4% |
| `0x5BEA0A` vs `0x69391A` | 82.9% |
| `0x40D2D4` vs `0x5BEA0A` | 72.5% |
| `0x5BEA0A` vs `0x6AC81A` | 70.7% |
| `0x6404B3` vs `0x6AC81A` | 58.5% |
| `0x6404B3` vs `0x69391A` | 57.1% |
| `0x40D2D4` vs `0x6404B3` | 50.0% |
| `0x5BEA0A` vs `0x6404B3` | 50.0% |

⇒ 它们是**同一基类层析构模板**被不同派生类各自实例化，不是 5 条独立业务路径。

---

## 4. 对 RC-4 的影响

### 4.1 仍然成立

- 崩溃链函数级拓扑：`0x652CF0 → 0x4A8850 → v[42] 0x4A8960 → …`
- 崩溃时 `ecx = [0x887368] = 0`
- `0x777803` 在 WM_DESTROY 清零 `0x887368`
- 修复方向（`0x724730` 加 null 守卫）**不受影响**

### 4.2 新增的关键同构

`0x87F7E8` 与 `0x887368` 的崩溃机制**同构**：
都是「全局被清零后仍被解引用」。区别是 `0x887368` 已被证实由 `0x777803` 清零，
而 `0x87F7E8` 的清零点尚未定位（§352 只查了字面量写，需补寄存器间接写普查）。

### 4.3 分岔 A / B / A' 仍未定

因为 One_Time 的运行期可达性取决于「运行期 `[0x87F7E8]` 装的是表 A 还是表 B」，
而这一点**静态无法确定**——两次装表分别在启动期构造与退出期回调，
运行期中段是否有第三次装表尚未普查。

**下一轮必做**：对 `[0x87F7E8]` 做**寄存器间接写**的完整普查（不只是字面量 `mov [abs],imm`）。

---

## 5. 本轮踩的坑（RTTI 三连）

1. **COL 的 `pTypeDescriptor` / `pClassDescriptor` 存 VA，不是 RVA**（加一次 imagebase 会越界）。
2. **BaseClassArray 的元素是 BCD 的 VA**（不是 RVA）。
3. **BaseClassDescriptor 布局**：`+0x00` = pTypeDescriptor、`+0x08` = mdisp。
   按 `+0x0C` 读 pTypeDescriptor 会得到全 `None`（本轮踩了两次）。
4. **TypeDescriptor 的 name 在 `+0x08`**（不是 +0x10）。

## 6. 方法论教训：闭包爆炸

`_host_closure.py` 求向上 E8 闭包，5 个宿主**全部撞到 400 节点上限**且时机标签完全相同
（都是 `GameMode` / `Modem detected OK` 等）——闭包已扩散到主循环，**失去区分力**。

⇒ **对"这个函数在什么时机跑"这类问题，向上闭包是错工具。** 正确做法是
**看函数体本身的形态**（析构签名 / 构造签名 / 循环结构 / 字符串），
再配合 RTTI 判类型。本轮最终结论正是这样拿到的。

## 7. 交付件

| 文件 | EXIT | 断言 |
|:--|:--:|:--:|
| `_host_closure.py` / `HOST_CLOSURE.txt` | 0 | 2/2（但方法无效，见 §6） |
| `_host_isomorphism.py` / `HOST_ISOMORPHISM.txt` | 0 | 1/1 + 形态分析 |
| `_inheritance_and_dtor.py` / `INHERITANCE_DTOR.txt` | 1 | 1/2（RTTI 偏移写错） |
| **`_inheritance_verdict.py` / `INHERITANCE_VERDICT.txt`** | **0** | **7/7** |

`_inheritance_and_dtor.py` 的 EXIT=1 是 RTTI 偏移假设错误，其**结论被 `_inheritance_verdict.py` 取代**。
