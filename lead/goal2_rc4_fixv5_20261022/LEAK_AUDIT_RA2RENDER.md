# 公开仓泄漏核查：`ra2render/` 源码与编译产物

**核查时间**：2026-10-23 01:20（初版）／**2026-10-23 复核更新**
**仓库**：`https://github.com/Lawrence7y/ra2-campaign-forge.git`
**公开性复核**：`curl https://api.github.com/repos/Lawrence7y/ra2-campaign-forge`
匿名访问返回 **HTTP 200** ⇒ **确认公开**（未登录即可读）
**核查人**：Lead（DeepSeek 族）
**性质**：**铁律 2 违反**，需用户裁决处置方式。本件只陈述事实，不擅自处置。

---

## 零、复核新增的关键事实（2026-10-23）

> **`b7f0508` 是仓库的\*\*根提交\*\*（root commit，无父提交）。**

```
$ git rev-list --max-parents=0 HEAD
b7f0508a4e8cfe24157ec21f860bf7b6ea9507cc
```

这一条显著加重了问题，也改变了方案 B 的代价估计：

| 项 | 初版记录 | **复核实测** |
|:--|:--|:--|
| `b7f0508` 在历史中的位置 | 未记录 | **第 1 个提交（根）** |
| 其后提交数 | 62（估） | **82** |
| 全仓提交数 | 83 | 83 |
| 泄漏文件出现过的提交数 | 未记录 | **10 个文件各只出现 1 次**（都在 `b7f0508`） |
| 当前 HEAD 是否仍含 | 是 | **是，10 个全在** |

⇒ 因为它在**根提交**，**每一个**后续提交的树里都带着这 10 个文件。
「只删当前树」（方案 A）之后，`git checkout b7f0508` 或任何旧 commit 仍能取到它们。

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
- **代价**：**全部 82 个后续提交的 SHA 改变**（`b7f0508` 是根，无法只改它之后）
- **代价（复核补）**：根提交改写 ⇒ 整棵树重建 ⇒ **推送体积接近全仓重传**，
  且 GitHub 侧旧对象需联系支持清除
- **残留**：无（GitHub 可能保留旧对象一段时间）
- **风险**：`--force` 推公开仓是不可逆动作；若他人已 clone 会全部冲突
- **适用**：判定"内容确实不能公开"

### 方案 B′（复核新增）：`git filter-repo --path ... --invert-paths` 局部剔除
- 与 B 的区别：只从**所有历史**里剔除这 10 个路径，其余文件内容不变
- **代价**：SHA 仍全变（根提交被重写），但**改动面最小、最不容易出错**
- **命令草案（未执行）**：
  ```
  git filter-repo --invert-paths \
    --path ra2render/blitter_hooks.cpp --path ra2render/blitter_hooks.obj \
    --path ra2render/dllmain.cpp      --path ra2render/dllmain.obj \
    --path ra2render/ra2loader.cpp    --path ra2render/ra2loader.obj \
    --path ra2render/ra2render.h      --path ra2render/ra2render.dll \
    --path lead/goal3_p1sbh_merge_20261020/_work/p1base.cpp \
    --path lead/goal3_p1sbh_merge_20261020/_work/out_fuzz0.cpp
  git remote add origin <url> && git push --force --all
  ```
- **适用**：判定"这些内容不该公开，但仓库其余历史要保留"

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
cpp/h 是否删除请用户明确表态。** 历史改写（方案 B / B′）只在用户确认"内容不可公开"后再做。

**复核后补充建议**：因为 `b7f0508` 是**根提交**，方案 A 的实际保护力比初版估计的更低
—— 任何一次 `git checkout <旧commit>` 都能取回全部 10 件。
若用户判定这些内容**确实不该公开**，则**只有 B′ 能真正解决**，A 只是"当前树看起来干净"。

若用户判定"内容可公开、只是纪律问题"，则 A 即可，并把本次事件登记为
"索引抢占导致误提交"的教训（已有记忆条目，无需新增）。

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
