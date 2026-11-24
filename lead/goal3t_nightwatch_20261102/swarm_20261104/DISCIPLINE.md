# 逆向取证纪律（所有子代理必读，逐条硬约束）

## 0. 铁律（违反即作废，不要绕过）

1. **零真机**：不得启动 `gamemd.exe` / `ra2loader.exe` / YURI，不得 `taskkill`，不得读取运行中游戏进程内存。
2. **零改动母本**：`ra2youli/gamemd.exe`（sha256 `73201cc0…f67476`）**只读**。不得改一个字节。
3. **不写他人写域**：你只能写 `lead/goal3t_nightwatch_20261102/swarm_20261104/<你的编号>/` 目录内。
   不得改 `lead/GOAL_THREE_TARGETS_20261018.md`、`lead/PENDING_DECISIONS.md`、
   `lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md`、`re_atlas/` 任何文件、任何 `.py` 母本/冻结件。
4. **不 commit / 不 push**。
5. **python 一律** `python -I -X utf8`。

## 1. 解码口径（本仓血泪教训，务必遵守）

**禁止**用 `for ins in md.disasm(blob, va)` 扫全镜像——capstone 在首个不可解码字节处
**静默停止**，会造出「0 处命中」的假零（本仓 G-23，已犯过多次）。

**必须**用重同步线性解码（逐址 +1 恢复），或直接用共享工具：

```python
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine
eng = Engine()
print(eng.coverage)                 # 必须打印覆盖率自证：100.00% / 1394120 insns / 66 resync
eng.disp_hits(0x00A8ED84)           # 绝对全局访存 → [(va,'W'|'R',mnem,op_str)]
eng.disp_hits_field(0x62C)          # 任意基址 [reg+0x62C]
eng.disasm(0x55D360, 0x200)         # 函数窗口反汇编
eng.rd(va, n) / eng.u32(va)         # 原始字节 / dword
eng.resolve_iat(0x7E11F0)           # → ('KERNEL32.dll','Sleep')
eng.func_rets(lo,hi)                # (rets, succ)
eng.reach_without(head,hi,cut_lo,cut_hi)   # 绕开某直线块的可达集
eng.loop_backedges(lo,hi)           # 回边
```

每份报告**必须**开头打印一次 `eng.coverage` 结果，作为「扫描器真的跑起来了」的自证。

## 2. 证据分级（每个结论必须带级别）

| 级别 | 含义 |
|---|---|
| **[字节]** | 直接读出的字节/指令，附 VA + 十六进制，任何人可复算 |
| **[推导]** | 从字节经 CFG/数据流推断，须列出推导链的每一跳 |
| **[推测]** | 无直接字节支撑的判断，**必须**明写「推测」，不得混入结论 |

**禁止**把 [推测] 写成结论。禁止用「显然」「必然」掩盖跳步。

## 3. 必须写诚实账

每份报告最后一节 `## 诚实账`，列：
- 没做的、没验证的；
- 样本薄的（单例/单函数）；
- 已知可能出错的地方；
- 与既有台账记载冲突之处（**如有冲突必须指出，不得沉默**）。

## 4. 本仓已定谳的数字（不许擅自改口径，除非给出字节反证）

| 事项 | 值 | 出处 |
|---|---|---|
| `CurrentFrame 0xA8ED84` | 1007 处引用 / **10 处写** / 唯一定常 inc `0x55DE7E`+写回 `0x55DE81` | ATLAS §8.4 + 本轮重同步复核逐位吻合 |
| 焦点旗标 `0xA8ED80` | 46 处引用 / **唯一写者 `0x7778CE`**（WndProc WM_ACTIVATEAPP 激活沿） | R-063a + 本轮复核逐位吻合 |
| MainLogicFrame `0x55D360` | 3 个 ret：`0x55D877` / `0x55DEC7` / `0x55DEDB`；其中 **`0x55D877` 与 `0x55DEDB` 不经 inc 即可达** | 本轮 §533 probe B |
| `0x7E11F0` / `0x7E1530` | `KERNEL32!Sleep` / `WINMM!timeGetTime` | 本轮 IAT 自解析 |

## 5. 产出格式

写 `<你的编号>/REPORT.md`，中文，结构：

```
# <编号> · <一句话结论>

## 0. 现场自证
（eng.coverage 输出 + 进程检查：tasklist 无 gamemd/ra2loader）

## 1. 结论（带证据级别）
1. ...
2. ...

## 2. 证据（逐条 VA + 字节 + 推导链）

## 3. 与本仓既有记载的对账（一致/冲突）

## 4. 诚实账

## 5. 复算入口
（贴出你跑的脚本路径与关键命令行，别人能一键复现）
```

脚本放同目录，命名 `<编号>_probe*.py`，输出存 `<编号>_probe*_out.txt`。
