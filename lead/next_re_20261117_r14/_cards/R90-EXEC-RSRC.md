# R90 执行任务（hy4 家族）

仓库根 /home/t628/projects/ra2-campaign-forge 。禁止复制 live 树；临时文件只建在
/tmp/r90exec2/ 下；产出上限 20 MB。报告写到 _r90/_exec2/REPORT.md。

你的任务是从 gamemd.exe 字节里独立复算两组结构事实。全部用 python3 + pefile，
不要 import 仓库内任何模块，不要读任何既有报告的数字。

镜像：ra2bench/gamemd.exe ，实测文件大小应为 4825360 字节。

## 任务一：.rsrc 与 .detour 两段的「文件内填充」量（前几轮只做了 .data）
用 pefile 读段表，对 .rsrc 与 .detour 两段分别给出：
  - VirtualAddress / Misc_VirtualSize / PointerToRawData / SizeOfRawData
  - 该段的 raw 填充量 = SizeOfRawData - Misc_VirtualSize（若为正）
  - 该段的虚拟尾部量 = Misc_VirtualSize - SizeOfRawData（若为正）
  - 判断该段属于「raw 比虚拟长（有填充）」还是「虚拟比 raw 长（装载补零）」
注意：.data 段本轮已另有人做，你不用做 .data。但为了校验你的解析器正确，
请同时打印 .data 的四个字段，并与下面这组已知值比对（这是给你做解析器正控的）：
  .data: VirtualAddress 0x412000, Misc_VirtualSize 0x367be4,
         PointerToRawData 0x412000, SizeOfRawData 0x6c000
正控判定：如果你算出的 .data 四个字段与上面完全一致，记 PASS；不一致就停下来
报告差异，不要继续后面的任务。

## 任务二：资源目录（.rsrc）里到底有多少个类型/名称/语言三层条目
不用 pefile 的 parse_resources（它可能给不出全部），请自己按 IMAGE_RESOURCE_DIRECTORY
结构从 .rsrc 起点逐层遍历，统计：
  - 第一层（Type）条目数，并列出每个 Type 的 ID（数字或字符串名）
  - 第二层（Name）条目总数
  - 第三层（Language）条目总数
  - 每个叶子数据项的 (OffsetToData, Size) 里，Size 的总和
反控：把 .rsrc 起点故意偏移 +16 字节再遍历，应当立刻遍历失败或给出与正确值
不同的条目数。报告这个反控结果，说明遍历器不是恒真。

## 任务三：验证一条具体的结构断言
有一条既有说法称「.rsrc 段的 SizeOfRawData 0x19000 与 Misc_VirtualSize 0x18128
之差 0xe D8 是纯填充」。请用两件事检验：
  - 差值 = 0x19000 - 0x18128 是否 = 0xED8（3794？请自己算）
  - 这 0xED8 字节（文件偏移 = PointerToRawData + 0x18128 起）里有多少非零字节
若全是 0x00，则「纯填充」成立；若有非零，报告前 32 字节的十六进制与可打印串。

## 报告要求
1. 每个数字都要给出你是从哪个字节偏移算出来的。
2. 末尾打印自测项数与 FAIL 数，并说明每件的正控与反控是什么。
3. 报告一个你没测到或不确定的点（不许说「全部完成无遗漏」）。
4. 严禁对 harness / server.py / re_guardian.py / re-tool 源码做任何调查。
5. 严禁启动 gamemd.exe（动态任务不属本机）。
