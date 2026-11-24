# S10-K3 · UNKNOWNS

| # | 未知 / 未升级项 | 状态 | 已尝试与下一步 |
|---|---|---|---|
| U1 | S10 仍距 DoD 50% 差 152 行 | [未证] | 本卡穷举只得到 23 行合法升级；合入后 111/526。下一步须另找函数体级 Mission 语义或真语义 GetSize/WhatAmI，不得批量按虚槽归属升级。 |
| U2 | named(S) 口径冲突 | [已证] 定义差 | PANEL/L 口径 named=511/526；按本卡硬规则排除 `sub_`/`Class::sub_`/`Class::slotN`/`Class::vslotN` 后仅 29/526，本卡 delta 后 52/526。未改 PANEL，只逐行替换 delta 行的名字。 |
| U3 | 0x5B3970（MissionClass v13）序列化行为 | [静态推断] | 已见 call 0x5F6250 后写字段 +AC/+B0/+B4/+BC/+C8/+D0/+C0 与 0x4A1D50/0x4A1DE0 字节流助手；但“Save”方法名仍需槽继承推断，故不放宽为已证。反汇编见 EVIDENCE/nonupgraded_candidates.txt。 |
| U4 | 0x5B3A60（MissionClass v8）析构语义 | [静态推断] | 可见写 4 个 vptr、call 0x5F3B80、条件 call 0x7C8B3D；方法名“析构”未由允许的 1–4 类证明绑定，未升级。 |
| U5 | 0x5F5E80（S10 行标 MissionClass::slot5） | [静态推断] | 字节形态是继承 ObjectClass 的字段加载/清零例程，不是 Mission_* 设置/查询/派发；未升级。 |
| U6 | 0x70DD90（AircraftClass slot250） | [未证] | `B8 01 00 00 00 C3`；imm=1 对应 enum Unit，但 RTTI 是 `.?AVAircraftClass@@`，语义不匹配；非 off0 slot11/12，未升级。 |
| U7 | 28 个基类 mission 桩中 8 个未在 S10 atlas 交集 | [已证] | 1 个基线已证（0x5B2E10）、19 个本卡升级、其余 8 个逐址状态见 EVIDENCE/nonupgraded_candidates.txt；未跨子系统偷升。 |
| U8 | 常量 0x1C2 的设计含义 | [未证] | 本卡只证明“返回 0x1C2 且入口到 ret 无其他指令 + dispatch 结果写回”，不解释为何选 450；该未知不妨碍 no-op 行为结论。 |

## 复算入口
- `python work/baseline_recompute.py`、`python work/prove_semantics_s10.py`、`python work/nonupgraded_dump.py`。
- 所有失败关闭项均列在 `EVIDENCE/semantic_census_s10.txt` / `EVIDENCE/nonupgraded_candidates.txt`。
