# S22-CENSUS SUMMARY
- 口径/总体：S22_TOTAL=**4851**（coverage subsystem==S22 ∩ atlas entry，统一大小写）；coverage=18431行，S22全量=10170，atlas=12916，S22在atlas外=5319；SHA-256=`73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`；未改共享表。
- 类名可定性：ANCHORED=**2005/4851=41.33%**（A1=1744,A2=260,A3=1）；UNANCHORED=**2846/4851=58.67%**（A4）；不判grade。
- 独立扫描：TD=988，COL=1214，.rdata虚表=1214，槽值=14044；不读vtables_v2、不用atlas边界；类名链=COL+0xC→TD，TD+8内联串（COL+8仅CD偏移）；★=明确业务类建议；Top40外明显业务类=SpawnManagerClass(1→S10); UnitClass(1→S10); AircraftClass(1→S10); TeamClass(1→S14); BulletClass(1→S13); TriggerClass(1→S15); SuperClass(1→S16); CellClass(2→S06)；直接RTTI类行数=0=InfantryClass/BuildingClass。
## TD类名Top40（按行数；★=建议迁出S22）
| # | TD类名 | 行数 | 建议 |
|---:|---|---:|---|
| 1 | `?$TypeList@H` | 18 | - |
| 2 | `CCFileClass` ★ | 18 | S03 |
| 3 | `?$DynamicVectorClass@PAD` | 14 | S22(保留) |
| 4 | `?$VectorClass@H` | 11 | S22(保留) |
| 5 | `?$VectorClass@PAU_WIN32_FIND_DATAA@@` | 10 | S22(保留) |
| 6 | `?$VectorClass@VCell@@` | 9 | S22(保留) |
| 7 | `?$VectorClass@PAUIConnectionPoint@@` | 9 | S22(保留) |
| 8 | `?$VectorClass@W4DiskID@@` | 9 | S22(保留) |
| 9 | `?$VectorClass@G` | 8 | S22(保留) |
| 10 | `?$DynamicVectorClass@PBVTechnoTypeClass@@` | 8 | S22(保留) |
| 11 | `?$DynamicVectorClass@PAVAbstractClass@@` | 8 | S22(保留) |
| 12 | `?$DynamicVectorClass@PAVParticleClass@@` | 8 | S22(保留) |
| 13 | `?$DynamicVectorClass@PAVBuildingTypeClass@@` | 8 | S22(保留) |
| 14 | `?$DynamicVectorClass@PAG` | 8 | S22(保留) |
| 15 | `?$VectorClass@PBVMultiMission@@` | 8 | S22(保留) |
| 16 | `?$DynamicVectorClass@VHSVClass@@` | 8 | S22(保留) |
| 17 | `?$DynamicVectorClass@PAVPlanningNodeClass@@` | 8 | S22(保留) |
| 18 | `?$VectorClass@V?$rc_ptr@VWDTTerritory@@@@` | 8 | S22(保留) |
| 19 | `?$DynamicVectorClass@I` | 7 | S22(保留) |
| 20 | `?$DynamicVectorClass@VBaseNodeClass@@` | 7 | S22(保留) |
| 21 | `?$VectorClass@V?$TPoint3D@H@@` | 7 | S22(保留) |
| 22 | `?$DynamicVectorClass@PAVDiskLaserClass@@` | 7 | S22(保留) |
| 23 | `?$VectorClass@PAUCrossDissolveEffect@@` | 7 | S22(保留) |
| 24 | `?$DynamicVectorClass@PAVEBolt@@` | 7 | S22(保留) |
| 25 | `?$DynamicVectorClass@PAVEgoClass@@` | 7 | S22(保留) |
| 26 | `?$DynamicVectorClass@UDrawRecord@FoggedObjectClass@@` | 7 | S22(保留) |
| 27 | `?$VectorClass@V?$DistributionObject@PAVCellClass@@@?$DiscreteDistributionClass@VCellClass@@@@` | 7 | S22(保留) |
| 28 | `?$DynamicVectorClass@PAVTagClass@@` | 7 | S22(保留) |
| 29 | `?$VectorClass@PAUThemeControl@@` | 7 | S22(保留) |
| 30 | `?$VectorClass@_N` | 7 | S22(保留) |
| 31 | `XSurface` | 7 | - |
| 32 | `?$DynamicVectorClass@PAVFileEntryClass@@` | 7 | S22(保留) |
| 33 | `?$VectorClass@V?$TRect@H@@` | 7 | S22(保留) |
| 34 | `?$VectorClass@N` | 7 | S22(保留) |
| 35 | `?$DynamicVectorClass@VPoint2D@@` | 7 | S22(保留) |
| 36 | `?$DynamicVectorClass@UAcceleratorTracker@@` | 7 | S22(保留) |
| 37 | `?$DynamicVectorClass@U?$HashObject@VHashString@@PAVSchemeNode@@@@` | 7 | S22(保留) |
| 38 | `?$VectorClass@VWstring@@` | 7 | S22(保留) |
| 39 | `?$DynamicVectorClass@UUndoInfoStruct@@` | 7 | S22(保留) |
| 40 | `?$DynamicVectorClass@PAVSubTitle@@` | 7 | S22(保留) |
| — | 其余428个类名合计 | 1673 | — |
若D-37允许再归属：可迁移建议=**291行**（S03 19行；S05 31行；S06 18行；S09 5行；S10 25行；S11 47行；S13 12行；S14 39行；S15 22行；S16 1行；S19 1行；S20 22行；S21 49行）；模板/容器建议留S22，未定类不可迁移。SpawnManager构造器：S22=006B6C90/006B6EA0，S10=006B7F10/006B8120。
A4抽样40行逐条说明A1/A2/A3为何未命中（EVIDENCE/A4_samples.tsv）；另查等价形（寄存器中介VT写、MEM.disp、raw dword），只在channel_hits.tsv留痕；006B6EA0在atlas body内A2锚到SpawnManagerClass TD=00840120，006B6C90为A4。交付：CENSUS.tsv+EVIDENCE+work/census.py。
