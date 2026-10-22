# 公开仓泄漏核查：`ra2render/` 源码与编译产物

**核查时间**：2026-10-23 01:20
**仓库**：`https://github.com/Lawrence7y/ra2-campaign-forge.git`（`gh repo view` 实测 `visibility=PUBLIC`, `isPrivate=false`）
**核查人**：Lead（DeepSeek 族）
**性质**：**铁律 2 违反**，需用户裁决处置方式。本件只陈述事实，不擅自处置。

---

## 一、结论（TLDR）

| 项 | 事实 |
|:--|:--|
| 铁律 2 是否被违反 | **是** |
| 泄漏内容 | `ra2render/` 的 4 个源码 + 3 个 `.obj` + 1 个 `.dll`，另加 `lead/.../\_work/` 的 2 个 `.cpp` |
| 是否只在历史里 | **否**。`.obj` ×3 与 `ra2render.dll` **现在仍在 HEAD**（即公开仓当前文件树） |
| 是否可"悄悄删掉" | **不能**。已 push 到公开仓，删除当前文件不改变历史；`b7f0508` 仍可检出 |
| 禁止件是否泄漏 | **否**。`gamemd.exe` / `.dmp` / `.mix` / `ra2youli/` / `ra2bench/` 均零命中 |
| 是否含明文密钥 | **否**。6 个文件全扫 `api_key|secret|password|token|BEGIN RSA`，仅命中 `s_visionToken` 等变量名 |

---

## 二、逐件明细

### 2.1 源码（违反「cpp/h 不上公开仓」）

| 文件 | 大小 | 首次引入 | 现状 |
|:--|--:|:--|:--|
| `ra2render/blitter_hooks.cpp` | 227,989 B | `b7f0508` | **仍在 HEAD** |
| `ra2render/ra2render.h` | 33,415 B | `b7f0508` | **仍在 HEAD** |
| `ra2render/dllmain.cpp` | 1,451 B | `b7f0508` | **仍在 HEAD** |
| `ra2render/ra2loader.cpp` | 2,818 B | `b7f0508` | **仍在 HEAD** |
| `lead/goal3_p1sbh_merge_20261020/_work/p1base.cpp` | 257,433 B | `b7f0508` | **仍在 HEAD** |
| `lead/goal3_p1sbh_merge_20261020/_work/out_fuzz0.cpp` | 273,750 B | `b7f0508` | **仍在 HEAD** |

### 2.2 编译产物（此前台账**未记录**，本轮新发现）

| 文件 | 大小 | 现状 |
|:--|--:|:--|
| `ra2render/ra2render.dll` | 163,328 B | **仍在 HEAD** |
| `ra2render/blitter_hooks.obj` | 139,606 B | **仍在 HEAD** |
| `ra2render/ra2loader.obj` | 8,282 B | **仍在 HEAD** |
| `ra2render/dllmain.obj` | 5,512 B | **仍在 HEAD** |

⇒ **`.obj` 里含完整调试符号与函数名，`.dll` 是可执行产物。这三件比 `.cpp` 更难解释为"只是源码"。**

### 2.3 构建脚本

| 文件 | 现状 |
|:--|:--|
| `ra2render/build.bat` | 仅在 `b7f0508` 历史中，**已不在 HEAD** |

---

## 三、引入路径（为什么一次进了 1166 个文件）

`b7f0508`（2026-10-21，`re-atlas: R-019 R2-2 第五轮`）这一个提交：

```
1166 files changed, 1444161 insertions(+)
```

它的提交信息只提到 `tools/dump_ini_keyindex.py`、`evidence/ini_keyindex.txt`、`kb/30 §12`。
`ra2render/` 那 16 个文件与提交主题**完全无关**，是被一并卷进去的。

⇒ **根因是"提交前未核 `git --cached --name-only`"**（与既有记忆
[多会话 git 索引抢占] 同源：commit 提交的是**整个索引**，不是你以为的那几个路径）。
本轮之前我已改用 `git commit -- <paths>` 限定路径，但这个提交发生在该纪律建立之前。

---

## 四、三种处置方案（供裁决，**均未执行**）

### 方案 A：只删当前树，不碰历史
```
git rm --cached ra2render/*.cpp ra2render/*.h ra2render/*.obj ra2render/*.dll \
  lead/goal3_p1sbh_merge_20261020/_work/*.cpp
# 补 .gitignore 规则，然后 commit + push
```
- **代价**：当前树干净；工作树文件保留（`.gitignore` 生效后不再被跟踪）
- **残留**：`b7f0508` 仍可从历史检出，**公开仓历史永久可读**
- **适用**：判定"内容敏感度不高，只是纪律问题"

### 方案 B：A + 改写历史（`filter-repo` / `filter-branch`）
- **代价**：全部 62 个后续提交的 SHA 改变；需 `push --force`
- **残留**：无（但 GitHub 可能保留旧对象一段时间，需联系支持彻底清除）
- **风险**：`--force` 推公开仓是不可逆动作；若他人已 clone 会全部冲突
- **适用**：判定"内容确实不能公开"

### 方案 C：维持现状，只补纪律
- **代价**：零
- **残留**：全部保留
- **适用**：判定"这些源码本就打算公开（如作为 re-atlas 的一部分）"

---

## 五、我为什么没有自行处置

1. **删历史是不可逆动作**，且 `--force` 推公开仓会破坏他人 clone。这属于"用户必须决定"的范畴。
2. **我不知道这些源码是否本就有意公开**。`ra2render/` 是项目的核心产物之一，
   公开它可能是产品决策而非失误——`.gitignore:44` 的注释也写了
   "仓库里确有少量刻意公开的头文件"。
3. 但 **`.obj` 与 `.dll` 几乎不可能是有意的**：编译产物进版本库没有任何合理理由。

⇒ 我的建议：**先做方案 A 处理 `.obj`/`.dll`（这三件无争议），
cpp/h 是否删除请用户明确表态。** 历史改写（方案 B）只在用户确认"内容不可公开"后再做。

---

## 六、本轮已做的（未触碰泄漏件）

`.gitignore` 已加（上一轮）：
```
**/rc4_guard*.cpp
**/rc4_loader*.cpp
**/ra2rc4guard*.dll
```
这三条只对新文件生效，**对已跟踪的 `ra2render/*` 无效** —— 这一点已在
`.gitignore:76` 的注释里写明，不是遗漏。
