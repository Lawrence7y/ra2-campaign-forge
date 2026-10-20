# T55k 载体清单复原（修正设计件 §6 的「不可复现」登记）

**日期**：2026-10-20 12:5x  **性质**：离线复原，未启动游戏。

## 结论

设计件 §6 末尾登记「T55k 的确切 `--carrier-create-files` 字符串未落进 trip 记录 ⇒ 载体组成不可复现」——**该登记可以撤回**：
`t55k_20261020/carrier_creation_receipt.json` 的 `files` 字典完整记录了**实际复制成功的 88 个文件名**，
其中 5 个是 `CARRIER_FILES` 默认项、83 个是 `--carrier-create-files` 附加项（逐名核对，默认项无一缺失）。

因此「按 receipt 的 88 件反向重建 `--carrier-create-files`」是**确定性可复现**的：把下面这 83 个名字按接收顺序拼成逗号串即可。

## 复原串（83 项，接收顺序）

```
00000409.016,00000409.256,0ne.bat,BATTLEMD.INI,BINKW32.DLL,Blowfish.dll,Blowfish.tlb,Cbnacw32.dll,Conquer.dat,ConquerMD.dat,IsleLand.bat,PATCHW32.DLL,PServer.exe,RA2.ico,RA2MD.INI,RA2MD.ico,Ra2.lcf,Ra2.tlb,Readme.txt,RegSetup.exe,Register.exe,Register.ini,SetupReg.exe,WSOCK32.DLL,Wolapi.dll,Woldata.key,XMP29U2.MAP,XYR.dll,YURI.exe,[2]0LoadBench_U0400.yrm,becdrv.bat,changes.txt,ddraw.dll,ddraw.ini,directplay-win32.reg,directplay-win64.reg,dpwsockx.dll,drvmgt.dll,expandmd01.mix,game.exe,ipxconfig.exe,ipxwrapper.dll,langmd.mix,language.mix,launcher.bmp,launcher.txt,launchermd.bmp,license.txt,maps01.mix,maps02.mix,mapsmd03.mix,movies01.mix,movies02.mix,movmd03.mix,mph.exe,mphmd.exe,mswsock.dll,multi.mix,multimd.mix,notes.ico,patchget.dat,patchgetmd.dat,ra2.csf,ra2.exe,ra2.ini,ra2.mix,ra2md.csf,ra2md.exe,ra2md.lcf,ra2md.mix,ra2render.ini,secdrv.sys,subtitle.txt,subtitlemd.txt,theme.mix,thememd.mix,unins000.dat,wdt.mix,xlh.bat,xwis.dll,xwis0.dll,yuri.lcf,配置器.exe
```

## 与设计件 A12 检查项的对应

设计件 §7-A12 要求「`--carrier-create-files` 字符串已落回执」。本件即为该回执项；发射时把上面的串原样写入趟回执，
并核对趟后 `carrier_creation_receipt.json` 的 `files` 数 = 88。

## 边界

- 本件只复原**文件名清单**，不复原参数的**引号/转义写法**（含空格项如 `RA2MD Update.ico` 未在列内；`配置器.exe` 为非 ASCII 名，需确认命令行编码）。
- `RA2MD Update.ico` 在源目录存在但**未进 T55k 载体**（88 件里没有它）——这是源目录 97 件 vs 载体 88 件的差额之一，不是遗漏错误。
- 本件不改设计件正文；§6 的「不可复现」表述以本件为准。
