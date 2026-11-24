# M27 PROGRESS
- 0040F870: `[静态推断] 占位名(slot/vslot/sub),缺具名语义` → `FindItemIndex +0x00 8B5110/+0x13 3931/+0x1F 83C8FF/+0x23 C20400`
- 0054E890: `[静态推断] 占位名(slot/vslot/sub),缺具名语义` → `Clear +0x09 895E10/+0x16 E8…/+0x24 895E08/+0x29 C3`
- 0054EA70: `[静态推断] 占位名(slot/vslot/sub),缺具名语义` → `SetCapacity +0x22 E8…/+0x54 8B5482FC/+0xA4 C20800`
- grade 直方图前：[已证] 1,452 / [静态推断] 5,948 / [未证] 11,031
- grade 直方图后：[已证] 1,452 / [静态推断] 5,948 / [未证] 11,031
- coverage SHA-256 前：dc471354e15e5a92f470a37ea7fa69c41ff2660639c2803ec2cb15ee9dfca80f
- coverage SHA-256 后：2c599504e7025eab3409c643b6c4b99bd29d1938af2bf1c067bc5f5beef30206
- 来源：S13_K12/_audit/VERDICT.md §2（coverage_delta.tsv 第4列为占位，按 VERDICT）
- 校验：18,431 数据行；仅 3 行第 4 列变化；表头逗号、数据行 TAB 保持。
