# RA2 / 尤复 稳定性与性能体检报告

生成时间：2026-11-12 01:15:19　工具版本：ra2opt 1.0.0
游戏目录：`D:\Project\ra2-campaign-forge\ra2youli`

## 环境

- 系统：Windows-11-10.0.26200-SP0（64 位宿主 = True）
- CPU：AMD Ryzen 7 6800H with Radeon Graphics（16 逻辑核）
- 内存：15613 MB
- Python：3.12.10

## 结论

共 8 项：建议 4，已达标 4。

### 建议（4）

**检测到已安装的 AI 战役（ra2forge 产物）**

expandmd98.mix + 散装 BATTLEMD98.INI（新版：自有条目 RA2F1 追加，BATTLEMD.INI 保持官方原样）或散装 BATTLEMD.INI（旧版：覆盖过官方列表）是 ra2forge 生成的战役包，本工具的优化不碰这些文件（改的是引擎/wrapper/配置层），可以共存。

- `expandmd98.mix = True`
- `BATTLEMD98.INI = True`
- `BATTLEMD.INI = True`

**ra2md.ini（尤复） 渲染细节为最高档（DetailLevel=2）**

多单位场景下渲染是主要瓶颈之一：细节档位越高，要绘制的动画/装饰层越多。降到 1 只影响画面细节，不改动任何游戏规则与胜负判定，是「不换硬件」的最直接手段。

- `[Options] DetailLevel = 2（最高）`

修：`python -m ra2opt apply --profile perf --game <游戏目录>（会设 DetailLevel=1）`

**ra2.ini（原版红警2） 游戏速度偏低（GameSpeed=1）**

速度档位偏低时引擎每帧间隔更长，单位多时的掉速会更明显。这属于个人偏好，仅供参考。

- `[Options] GameSpeed = 1`

**ra2md.ini（尤复） 游戏速度偏低（GameSpeed=2）**

速度档位偏低时引擎每帧间隔更长，单位多时的掉速会更明显。这属于个人偏好，仅供参考。

- `[Options] GameSpeed = 2`

### 已达标

- 存在原始快照，可随时回滚
- cnc-ddraw 版本 7.1.0.0（已是最新或无法确认）
- 已识别引擎版本
- 已开启 Large Address Aware

## 附录：本工具会改什么、怎么撤销

| 层 | 动作 | 可用性 |
|---|---|---|
| 渲染代理 | 升级/安装 cnc-ddraw，重写 `ddraw.ini` 调优项 | 覆盖前快照 `ddraw.dll`/`ddraw.ini` |
| PE 头 | COFF 头 LAA 位、栈保留空间 | 只改 PE 头字段，代码段零改动 |
| 配置 | `ra2md.ini` / `ra2.ini` 少量键 | 行级保留注释与顺序，只改指定键 |
| 系统 | HKCU 兼容性标记 | 记录原值，restore 时还原 |
| 启动 | 生成 `ra2opt_play.bat` | 直接删除即可 |

撤销全部改动：`python -m ra2opt restore --game <游戏目录>`

> 本工具**不改**：`.mix` 资源、地图、`BATTLEMD.INI`（战役内容），也不改游戏代码段。
