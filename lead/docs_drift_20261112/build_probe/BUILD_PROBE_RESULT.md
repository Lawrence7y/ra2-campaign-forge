# 交付线 C · ra2forge 构建实测（STEP 2 第 5 条）

> 命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/docs_drift_20261112/_fd_build_probe.py`
> 等价于 `python -m ra2forge example` + `python -m ra2forge build --design ... --out ...`，
> 但用单一 `-I -X utf8 <绝对脚本>` 调用以满足本任务铁律；脚本内 `sys.path.insert` 提供 `PYTHONPATH` 等价物。
> `--install` 未传；**未启动任何游戏/加载器、未读活进程内存、未写游戏目录**。
> `sys.dont_write_bytecode=True` 在任何 import 前置位，避免 `ra2forge/__pycache__` 落在写域外。

## 调用：`example D:\Project\ra2-campaign-forge\lead\docs_drift_20261112\build_probe\demo_campaign.json`

- **exit = 0**
- stdout：
```text
wrote D:\Project\ra2-campaign-forge\lead\docs_drift_20261112\build_probe\demo_campaign.json
```

## 调用：`build --design D:\Project\ra2-campaign-forge\lead\docs_drift_20261112\build_probe\demo_campaign.json --out D:\Project\ra2-campaign-forge\lead\docs_drift_20261112\build_probe\out`

- **exit = 0**
- stdout：
```text
built: D:\Project\ra2-campaign-forge\lead\docs_drift_20261112\build_probe\out\Example Operation\expandmd98.mix
package: D:\Project\ra2-campaign-forge\lead\docs_drift_20261112\build_probe\out\Example Operation
```

## 产物（仅写域内，hashlib 实算）

共 6 个文件。

| 文件 | 字节数 | sha256 |
|:--|--:|:--|
| `lead/docs_drift_20261112/build_probe/out/Example Operation/BATTLEMD98.INI` | 396 | `9898db18dd113ce1edf7359f8d5312939f1dc5ea199cb979aa50679ce5114d21` |
| `lead/docs_drift_20261112/build_probe/out/Example Operation/BUILD_REPORT.txt` | 1102 | `0a58336e770e7fbaee41e73788600f192b32fc956671f427c942a117d6c5fa16` |
| `lead/docs_drift_20261112/build_probe/out/Example Operation/EX01.MAP` | 4300 | `d5c7f3c2ab87eb858d6fbba279c8cfbd067a2e245dfbbe74f5bb46a835681fc6` |
| `lead/docs_drift_20261112/build_probe/out/Example Operation/expandmd98.mix` | 4322 | `022fc9413fb51afbb60aca1d8e896cdefe97d4c979b612c056e53699aaf4e9f5` |
| `lead/docs_drift_20261112/build_probe/out/Example Operation/INSTALL.txt` | 1561 | `90cc4a487aed56ecbd90c611b2f48188110597b80d98a8f686107c5aa8f88347` |
| `lead/docs_drift_20261112/build_probe/out/Example Operation/story.md` | 173 | `8e3966786057776f0209b358cbc298e50811422a3864dc9871dbbae44549a92b` |

