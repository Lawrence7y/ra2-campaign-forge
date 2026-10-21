# ③ 门 · 真机 deploy → smoke → rollback → 哈希复核（完整周期回执）

**时间**：2026-10-21 19:47–19:49
**性质**：真机（用户本会话授权「每次复制的游戏本体测试后删掉」）。
**结论**：**S1 / S2 / S3 / S4 四项全 PASS ⇒ ③ 第 3 条「一次完整真机周期」完成。**
**母本零改动**：`ra2render/blitter_hooks.cpp` `656e6b4e48cdd251` / `ra2render/ra2render.ini` `27c9a60c55a8a1b4` 全程未变。

---

## 一、总判

| 阶段 | 判据 | 结果 |
|:--|:--|:--|
| **S1 deploy** | 部署后载体哈希 == 源件哈希 | ✅ PASS |
| **S2 smoke** | loader 起来 + gamemd 派生 + ra2render 在 gamemd 模块表内 | ✅ PASS |
| **S3 rollback** | 逐字节还原到原版，且 == 源变体 | ✅ PASS |
| **S4 verify** | 母本未改 + 载体已删 + 零残留进程 | ✅ PASS |

`_deploy_cycle.json` 的 `all_pass = true`。

---

## 二、S1 deploy

| 件 | 部署前（载体原版） | 部署后 | 源件 |
|:--|:--|:--|:--|
| `ra2render.dll` | `39cbd66550141610` / 165,376 B | **`4d3aacf7ddf5139f` / 178,688 B** | `4d3aacf7ddf5139f` |
| `ra2render.ini` | `27c9a60c55a8a1b4` / 16,496 B | **`577baa489cb3d8a5` / 16,645 B** | `577baa489cb3d8a5` |

- 载体件集 = **冻结清单 88 件全量**（`_src_L1_sf8_20261020_MANIFEST.json`），复制 88 / 缺 0。
- 部署后哈希 == 源件哈希（`assert` 硬门）。
- 载体目录 `len=127`（门禁 130，余量 3）。

**合批 DLL**：`goal3_p1sbh_merge_20261020/build/ra2render_merged.dll`（P1 版本门 + SBH 守卫，`CL_EXIT=0 / LINK_EXIT=0`）。
**ini.v2**：`goal3_verifyhooks_fix_20261020/ra2render.ini.v2`，相对母本**仅多两行**
（一行注释 + `EnableSbhGuard=0`），其余逐字节一致。

---

## 三、S2 smoke（决定性证据）

```
loader pid = 42816
gamemd pid = 36748
✅ ra2render.dll 已加载 base=0x54060000 size=3145728
ra2render.log 存在，9077 B
```

### 3.1 关键发现：**ra2render 注入的是 gamemd，不是 loader**

`ra2loader.exe` 与 `gamemd.exe` 是**两个不同 pid**（42816 vs 36748）。
loader 负责 `CreateProcess` 出 gamemd，再把 DLL 注入 gamemd。
⇒ 模块表必须查 **gamemd 的 pid**。

**这是本脚本第一版的缺陷**：查 loader 的 pid ⇒ `modules=None` ⇒ 冒烟假失败。
与 U8 探针实证一致（`launch_pid=38192` / `gamemd_pid=41604`）。

### 3.2 两个功能都真的接线了（日志原文）

`_smoke_ra2render.log`（47 行，9,077 B，完整留档）第 17 行：

```
[ra2render-vergate] 版本门: PASS（W1 整文件=现役 ra2bench 指纹;
                                  sha256=73201cc021497c95…, size=4825360, tds=0x3BDF544E）
```

第 43 行：

```
[ra2render-sbh] SbhGuard=off（EnableSbhGuard 未开；.text 零改动）
```

第 6 行：

```
[ra2render-gameplay] [G3-SPLIT] 玩法配置拆分: 旧节只读迁移命中 0 项 |
                     现行来源 = [Gameplay] 节（缺键 → 旧节 [Logic]/[FogOfWar] 只读回退 → 原版默认全关）；
                     本 DLL 绝不写 ini
```

| 功能 | 日志判据 | 结论 |
|:--|:--|:--|
| **P1 版本门** | `版本门: PASS`，sha256=`73201cc0…`、size=4,825,360、tds=`0x3BDF544E` | ✅ **真的运行并校验通过** |
| **SBH 守卫** | `SbhGuard=off（EnableSbhGuard 未开；.text 零改动）` | ✅ **正确判定为关**（默认 0 = 不碰 .text，与原版逐位等价）|
| G3 配置拆分 | 迁移命中 0 项、绝不写 ini | ✅ 只读语义成立 |

⇒ **③ 第 1 条（合入同一基线并编译通过）** 与 **第 3 条（完整真机周期）** 的
「功能真的生效」侧证都拿到了，不是「文件在盘」级别的弱证据。

### 3.3 冒烟为何不触发 SBH 开启

`EnableSbhGuard=0` 是设计默认（`.text` 零改动、与原版逐位等价）。
本周期验证的是**部署/回滚机制**，不是 SBH 的 A/B 效果（那属 ② 的活）。

---

## 四、S3 rollback

| 件 | 回滚后 | == 原版 | == 源变体 |
|:--|:--|:--|:--|
| `ra2render.dll` | `39cbd66550141610` | ✅ True | ✅ True |
| `ra2render.ini` | `27c9a60c55a8a1b4` | ✅ True | ✅ True |

**踩到的坑**：`TerminateProcess` 后 DLL 映像仍被映射 ⇒ 立即写回 `PermissionError`。
修法 = 退避重试（20 次、`0.5 + i*0.25` 秒），实测 2–6 s 内释放。
**这是可复用经验**：真机回滚不能「杀完立刻写」，必须带退避。

---

## 五、S4 verify（卫生）

| 项 | 值 | 结果 |
|:--|:--|:--|
| 母本 `blitter_hooks.cpp` | `656e6b4e48cdd251` | ✅ 未改 |
| 母本 `ra2render.ini` | `27c9a60c55a8a1b4` | ✅ 未改 |
| 载体已删 | `True` | ✅ |
| 残留进程 | `[]` | ✅ |
| 中间备份 `_orig_bak` | 已删 | ✅ |

---

## 六、③ 判据对照

| ③ 判据 | 状态 | 证据 |
|:--|:--|:--|
| P1 版本门 + SBH 守卫合入同一基线并编译 | ✅ | `RECEIPT.md`（5/5 hunk、`CL_EXIT=0/LINK_EXIT=0`）+ 本轮日志双功能均在跑 |
| 白名单 + 13 vtable 槽 + 9 code site 期望值重算，异族核验 | ✅ | `goal3_expect_recompute_20261021/`、`goal3_xfamily_verify_20261021/XFAMILY_VERDICT.md` |
| `verify_hooks` 23/23 + exit 0 | ✅ | `verify_hooks.v3.py`（修 P1 假绿），8/8 负控 |
| **一次完整真机 deploy→smoke→rollback→哈希复核** | ✅ **本轮完成** | 本回执 |
| 补丁副本制写成固定规程 | ✅ | `goal3_patchdiscipline_20261021/PATCH_DISCIPLINE.md`（S1–S7 + 三铁律 + 12 陷阱） |

⇒ **③ 五条判据全部达成**（待用户签署）。

---

## 七、取证件

| 件 | 路径 |
|:--|:--|
| 本回执 | `lead/goal3_deploy_cycle_20261021/RECEIPT_DEPLOY_CYCLE.md` |
| 周期全记录 | `lead/goal3_deploy_cycle_20261021/_deploy_cycle.json` |
| 冒烟完整日志 | `lead/goal3_deploy_cycle_20261021/_smoke_ra2render.log`（47 行 / 9,077 B）|
| 执行脚本 | `lead/goal3_deploy_cycle_20261021/_deploy_cycle.py` |
| 合批 DLL | `lead/goal3_p1sbh_merge_20261020/build/ra2render_merged.dll` |
| ini.v2 | `lead/goal3_verifyhooks_fix_20261020/ra2render.ini.v2` |
