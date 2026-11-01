#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§433 台账追加（字节级）：c″ cave 字节候选 + 独立验证器交付，门禁 5 绿 + 9/9 变异负控。"""
import io, os

LEDGER = "lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

CONTENT = """# §433　c″ 补丁规格交付（设计件，未部署）：cave 36B 字节候选 + 独立验证器，
#        离线门禁 5 检查全绿 + 9 变异负控全被抓（各钉在声明检查上）

**性质**：纯离线（快照 `73201cc021497c95` 断言通过，零真机趟）。承接 §432 四。

## 一、交付物

- `_design_c2_cave.py` → `d09a_c2_patchspec.json`：站点原窗
  `0x6BE0E1: 39 3D D8 ED A8 00 | 74 F3`（快照字节断言）；站点补丁
  `E9 rel32 + 90`（测试基址 0x10001000 下 = `e9 1a 2f 94 0f 90`）；cave 36B：
  `a1 50 35 b7 00 | 85 c0 | 0f 84→0x6BE0E9 | 83 3d d8 ed a8 00 01 | 0f 85→exit |
   e9→0x6BE0DC | e9→exit`（capstone 解码=精确 7 条指令序列）。
- `_verify_c2_cave.py`：独立验证器——**不 import 生成器**（对账器复用被测物=两边同绿的
  已知坑），只吃 JSON+快照+capstone。5 检查：C1 快照锚 / C2 站点补丁字节 /
  C3 cave 指令序列 / C4 四个 rel32 目标独立重算 / C5 长度 36B 钉界。

## 二、门禁结果

- 净版：`PASS`（5 检查全绿）。
- 负控：9 个变异（原窗字节 / 基址平移 / 站点 rel32 / test 操作数 / je→jne 操作码 /
  je·jmp·tail 三个 rel32 / cave 长度）**逐一必红，且全部抓在声明检查上**
  （`--selfcheck` 断言「错抓」也算失败——防多退路假捕获）。

## 三、造门禁过程中的三个坑（如实登记）

1. **C2 初版是恒真式**：rel32 由 base 现算再解回 base 自证——被测物只出现在等式一侧。
   改为 JSON 存具体字节 `patch_hex_at_test_base`，验证器只解字节比基址（变种 M 的老坑）。
2. **C4 布局偏移初版错位**（jmp@31/tail@36，实为 26/31）——第一次跑自检必然「净版红」
   才暴露；布局偏移由 C3 的指令序列钉死后引用。
3. selfcheck 匹配器初版用整串相等，`C3.seq` 对不上 `C3.seq[1]` 报「错抓」——
   改前缀匹配。另：验证器首跑两次 NameError（漏定义 load_spec/snapshot）=同名函数
   重写时掉了辅助函数，如实记。

## 四、边界与待决

- 本件=**设计工件**，未写入任何载体/母本/守卫 DLL；运行期 cave 基址由守卫分配器给
  （v5 同域，参考基址 0x10000000 区；姊妹 cave 不共用=RC4-SPEC-V2 规则）。
- ini 闸门用哪个（复用 `[Logic] EnableRC4Guard` 还是独立 `EnableRC4ExitBail`）＝
  D-09 裁决点之一。
- 真机验证判据（裁决通过后）：守卫+c″ 双开 → 关窗 → **出环走 teardown 正常退出、
  无新对话框、except.txt 零新增、exitstate 观测到 1→2**；对照=仅守卫（僵尸复现）。

## 五、卫生

零真机趟；本轮探针只读快照；新落盘 3 件（generator/verifier/JSON）全在本线目录；
他线件零改动（`_rc4_ab_probe.py` sha16 `b063052c…` 开工与收工一致）。
"""

def main():
    before = io.open(LEDGER, "rb").read()
    assert b"\xc2\xa7432" in before, "prev section missing"
    assert b"\xc2\xa7433" not in before, "duplicate"
    crlf_before = before.count(b"\r\n")
    add = CONTENT.replace("\n", "\r\n").encode("utf-8")
    after = before + b"\r\n" + add
    assert after.startswith(before)
    assert after.count(b"\r\n") == crlf_before + 1 + CONTENT.count("\n"), "crlf math off"
    tmp = LEDGER + ".tmp433"
    with io.open(tmp, "wb") as fh:
        fh.write(after)
    os.replace(tmp, LEDGER)
    check = io.open(LEDGER, "rb").read()
    assert check == after
    print("OK appended 433; ledger %d bytes crlf=%d" % (len(check), check.count(b"\r\n")))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
