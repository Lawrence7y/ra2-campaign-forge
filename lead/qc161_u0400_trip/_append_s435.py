#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§435 台账追加：c″ 候选副本构建完成 + 工件级门禁 14/14。"""
import io, os

LEDGER = "lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

CONTENT = """# §435　D-09 裁决执行①：c″ 独立候选副本构建完成（离线，零真机趟），工件级门禁 14/14 全绿

**性质**：离线构建+门禁轮（D-09 裁决 2026-10-25 的第一步）。母本未动
（`rc4_guard.cpp` sha16 `594ac159…` 前后一致）；候选件**不部署、不写载体、不跑游戏**。

## 一、交付物（本线域 `lead/qc161_u0400_trip/d09a_c2_candidate/`）

| 件 | 说明 |
|---|---|
| `src/rc4_guard.cpp` | 候选源=母本 464 行 + **纯增量** c″ 块；diff 证明改动全部限于 DllMain 两处（438-443/445-449 集成点），InstallGuards/RemoveGuards/BuildCave/8 头站点表**一字未动**；上仓铁律 cpp/dll 不入库，落盘件 sha16 见台账文本 |
| `build.py` | 直调 cl.exe（铁律 1：不跑 build.bat）；旗标与母本一致 `/O2 /W3 /EHsc /arch:SSE2 /LD` + `/utf-8`（见三）；无 shell、参数全字面量 |
| `ra2rc4guard_c2.dll` | **117,760 B**，sha256 `edb9a0cde129c105…`（母本 DLL 115,200 B / `0e2a9995…`，Δ+2,560=增量 c″ 代码） |
| `_verify_c2_candidate.py` | 工件级门禁（镜像他线 `_verify_guard_dll.py` 形态：门禁落在 DLL 上，不落在源码自述上） |

c″ 增量内容：`ExitBailSite` 结构（0x6BE0E1 / hook 6B / 原窗 8B / 0x6BE0DC / 0x6BE0E9）、
`BuildExitBailCave`（36B 七指令，逐字节对齐 `d09a_c2_patchspec.json`）、独立事务
`InstallExitBail/RemoveExitBail`（独立 cave 池=姊妹 cave 不共用；预检 fail-closed；
FNV 双断言）、独立开关 `[Logic] EnableRC4ExitBail`（默认 0，双关 ⇒ .text 零改动）。
cave **不写任何退出状态值**（§434 判据修正）。

## 二、工件级门禁 14/14 PASS

- S0 身份：gamemd sha16 ✓ + 候选 DLL sha == 构建钉值 ✓
- S1 **k_sites 8 头表在候选 DLL 内逐字段 == 母本规格（8/8）**——证明 8 头路径未被副本改动
- S2 针值：结构针值（`06`+原窗 9B 连排）候选=1 母本=0；marker 候选=1 母本=0；
  orig_win 候选=1 母本=0；ini_key/marker 对母本全 0（差异性检验）
- S3 **C++ 构造逻辑 Python 镜像重算 == 规格 JSON 逐字节**（测试基址 0x10001000）+
  capstone 7 指令序列断言
- N1 镜像字节变异⇒与规格必不一致（比对是活的）；N2 变异针值在 DLL 内 0 次；
  N3 母本 DLL 对 c″ 针值全 0（候选件判据不认母本）

## 三、造门禁与构建的四个坑（如实登记）

1. **S1 切片偏移错**：Rc4Site 里 orig 起于 offset **7**（va4+hook1+replay1+ret1），
   误写 4 ⇒ 字段值明明全对却逐条 FAIL——门禁红得其所，修脚本不修数据。
2. **site_va「恰 1 次」断言错误**：0x6BE0E1 在候选 DLL 内 13 次 = 1 次 .rdata 结构体
   + 12 次编译器把 const 常量折叠进代码的立即数（`b9 e1 e0 6b 00`/`68 e1 e0 6b 00`）
   ——**这本身是正确性证据**；改为「结构针值恰 1 + 非唯一针值 ≥1 且母本 0」。
3. **编码吞行**：源为 UTF-8 无 BOM，cl 默认按 GBK 读 ⇒ 注释尾多字节吞掉换行，
   后续行并入注释 ⇒ `C3861 Log 找不到` 连环报。加 `/utf-8` 解决（纯源码解释旗标，
   零代码生成差异；母本当年构建应同样带此旗标而台账缩写未记）。
4. **vcvars 引号路径经 cmd 被二次拆坏**（`cmd /c` + list 形式）＋ Mimosa 拦
   `shell=True` 字符串拼接（命令注入高危）⇒ 改为**不用 vcvars**：INCLUDE/LIB
   显式构造 + cl.exe 全字面量参数列表，一次通过。

## 四、边界与下一步

- 候选件**未部署**：未写任何载体/母本/现网路径；`D:\\ra2dumps` 零新增；零真机趟。
- 下一步 = **串行真机 A/B**（判据 v2 = §434 三：CTRL 先验装置+僵尸基线，
  MAIN 后验干净退出；正常退出是硬门槛）。趟内先以 `RC4GuardDryRun=1` 干跑取
  cave 实际字节比对规格（离线门禁管不到运行期基址），再正式臂。
- 欠账不变：227 件积压逐件审计（D-08 附带义务）、L3 墙（D-07 残部，归属线）。

## 五、卫生

零真机趟；快照只读；母本源/DLL sha16 前后一致；新落盘 5 件全在本线域
（cpp/dll/obj 按铁律不入库，仅 .py/.json/台账随提交）；本轮库内无新增他线改动。
"""

def main():
    before = io.open(LEDGER, "rb").read()
    assert b"\xc2\xa7434" in before, "prev section missing"
    assert b"\xc2\xa7435" not in before, "duplicate"
    crlf_before = before.count(b"\r\n")
    add = CONTENT.replace("\n", "\r\n").encode("utf-8")
    after = before + b"\r\n" + add
    assert after.startswith(before)
    assert after.count(b"\r\n") == crlf_before + 1 + CONTENT.count("\n"), "crlf math off"
    tmp = LEDGER + ".tmp435"
    with io.open(tmp, "wb") as fh:
        fh.write(after)
    os.replace(tmp, LEDGER)
    check = io.open(LEDGER, "rb").read()
    assert check == after
    print("OK appended 435; ledger %d bytes crlf=%d" % (len(check), check.count(b"\r\n")))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
