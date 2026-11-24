# W134b — `AbstractClass::AbstractClass` 不登记：注册表完整性的推理链断了

**时间**：2026-11-15 14:20
**来源**：DeepSeek 子代理 `ds-t3-registry` 在 `W135_ds\T3_registry\dumps\fn_004101F0_AbstractClass_ctor.txt` 里给出的转储，**由我（lead）独立复核确认**。
**性质**：对 §859-7-1 那条未证项的直接推进，且**结论对我不利**。

---

## 1. 事实（我亲自复核）

`0x004101F0` 处的函数完整内容：

```asm
004101f0  mov dword ptr [ecx],   0x7e1f50      ; vptr for col_offset 0
004101f6  mov dword ptr [ecx+4], 0x7e1f34      ; vptr for col_offset 4
004101fd  mov dword ptr [ecx+8], 0x7e1f2c      ; vptr for col_offset 8
00410204  mov dword ptr [ecx+0xc], 0x7e1f24    ; vptr for col_offset 12
0041020b  ret
```

**不碰 `0xB0F724`（Items），不碰 `0xB0F730`（Count），也不调用任何登记函数。**

### 1.1 它确实属于 `AbstractClass`（独立验证）

`class_atlas_v2.tsv` 里 `.?AVAbstractClass@@` 的虚表集合是
`0x007E1F24 / 0x007E1F2C / 0x007E1F34 / 0x007E1F50`，
且 `vtables_canonical.json` 给出它们的 `col_offset` 分别是
**12 / 8 / 4 / 0** —— 与上面 4 条 `mov` 的目标一一对应。

（`0x7E1F50` 是该类的 `primary`，23 槽。）

⇒ **这不是巧合，`0x004101F0` 就是 `AbstractClass` 的构造器**（或多继承下装 vptr 的那一段）。

### 1.2 函数体就这么长（排除"后面藏着登记代码"）

`function_atlas.tsv` 给出该函数的独立测量：

| 字段 | 值 |
|---|---|
| `entry` | `0x004101f0` |
| `size` | **28 字节** |
| `n_instr` | **5**（4 条 `mov` + 1 条 `ret`） |
| `n_callers` | 31 |
| **`n_callees`** | **0** |
| 紧邻的下一个函数 | `0x00410210` |

⇒ 28 字节 = 4×7 + 0，**整段函数体已在上面完整列出**，不存在"后面还有一段登记代码"的可能。
⇒ `n_callees = 0` 进一步证明它**不可能通过调用辅助函数间接登记**。
⇒ `n_callers = 31` 说明它被 31 个派生类构造器链式调用——**这正是"每类构造器各自负责自己的事"的证据**，
   而不是"根类统一兜底"。

## 2. 由此得到的两条结论

### 2.1 [已证] `AbstractClass` 是 4 基类多继承，4 个 vptr 在 `+0 / +4 / +8 / +0xC`

这推翻了一个**隐含假设**：§859 讲 `VectorClass` 布局时"vptr 在 `+0`"是对的（那是 `VectorClass`），
但不能外推成"所有类只有一个 vptr 在 +0"。`AbstractClass` 有 4 个。

**影响**：凡是"读 `[obj]` 就是 vptr"的写法，对 `AbstractClass` 系对象只拿到**第一个**基类的虚表。
`class_atlas_v2` 里 `.?AVAbstractClass@@` 有 4 个虚表、primary 是 offset 0 那个（`0x7E1F50`）——数据本身是对的，
但如果下游代码假设"一个类一个虚表"，就会漏掉另外 3 个子对象虚表。

### 2.2 [已证] "根类构造即自动登记 ⇒ 注册表完整"这条推理链**不成立**

§859 的写法是：如果登记发生在 `AbstractClass::AbstractClass` 里，则所有派生对象自动登记、数组即完整。
**现在前提被否证**——根类构造器只有 4 条 `mov` + `ret`，什么都不登记。

⇒ **登记必然发生在别处**，可能性：
- (a) 每个叶子类（或中间类）的构造器各自内联 `AddItem`；
- (b) 存在专门的 `Add`/`Remove` 辅助函数，由**工厂/场景载入**调用，而不是由构造器调用。

若是 (a) ⇒ 只要有一个类忘了登记，数组就不完整，**完整性需要逐类核对**。
若是 (b) ⇒ 完整性取决于"所有创建路径是否都调了那个辅助函数"，那比逐类核对**更难**证明。

## 3. 对 §859 的影响（自我更正）

§859 里我写的是"`AbstractClass::Array` 的身份 `[已证]`、完整性 `[未证]`"。
**身份部分仍然成立**（`0xB0F720` 确实是 `DynamicVectorClass<AbstractClass*>`，由静态构造器的 vptr 存储证明）。
**完整性部分不仅未证，而且现在有了明确的负面证据起点**：至少它不是根类构造器兜底的。

⇒ 建议口径：**`0xB0F730` 不可当作"对象总数"使用**，除非 T3 能给出逐类的正面证据。
可用的替代是**各类型计数之和**（`FootClass` + `BuildingClass` + 其它叶子类），
但那需要先确认叶子类清单无重叠。

## 4. 我的复核方法（可复跑）

```python
# 1) 取 AbstractClass 的全部虚表与 col_offset
json.load(open('W130_atlas/vtables_canonical.json'))['vtables']
#    -> 0x7E1F50(offset 0) 0x7E1F34(offset 4) 0x7E1F2C(offset 8) 0x7E1F24(offset 12)

# 2) 反汇编 0x004101F0 起 0x1C 字节，确认 4 条 mov 的目标 == 上面 4 个虚表
#    并确认函数体内对 0xB0F724 / 0xB0F730 的引用数 == 0
```

两条判定都成立。

## 5. 仍然未证

1. 登记到底发生在 (a) 还是 (b) —— 需要 T3 的 `push_sites.tsv` 逐条定性。
2. 是否存在"创建了对象但从不登记"的路径。
3. 本节结论**纯静态**，未真机验证（用户已裁定本轮不跑真机）。
