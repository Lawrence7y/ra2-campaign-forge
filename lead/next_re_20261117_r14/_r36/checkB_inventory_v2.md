# R36 Check B v2 · `statement` 列引用核验（修正正则后）

含引用的行数 = 15；各类计数 = {'BARECARD': 10, 'SECTION': 8, 'DECIDE': 2, 'FACT': 3, 'CARD': 3, 'FILEREF': 1}

## F05 [[已证]]
  - BARECARD R18      候选目录=R17_R18_EDI_GAP

## F08 [[静态推断]]
  - SECTION  §2.10    ns=R14_COMMON 可解析=True  在本行锚内=True
  - DECIDE   D-53     PENDING_DECISIONS=True  R14_COMMON=True  在本行锚内=False

## F09 [未取得]
  - BARECARD R27      候选目录=R17_R27_SLOT107_V2
  - BARECARD R25      候选目录=R17_R25_SLOT107
  - BARECARD R33      候选目录=R17_R33_SLOT107_DISPATCH

## F12 [[已证]]
  - BARECARD R22      候选目录=R17_R22_RING2_CORROB
  - BARECARD R19      候选目录=R17_R19_RTTI_XCHECK

## F14 [[已证]]
  - SECTION  §1061    ns=台账         可解析=True  在本行锚内=False
  - SECTION  §1062    ns=台账         可解析=True  在本行锚内=False
  - SECTION  §1060    ns=台账         可解析=True  在本行锚内=False
  - BARECARD R19      候选目录=R17_R19_RTTI_XCHECK

## F15 [[已证]]
  - BARECARD R28      候选目录=R17_R28_R12_REPAIR

## F16 [未取得]
  - FACT     F09      存在于索引=True  在本行锚内=False

## F17 [[已证]]
  - SECTION  §2.6     ns=R14_COMMON 可解析=False 在本行锚内=True
  - SECTION  §2.10    ns=R14_COMMON 可解析=True  在本行锚内=True
  - CARD     R14_COMMON             目录存在=False 在本行锚内=True

## F26 [[流程]]
  - DECIDE   D-49     PENDING_DECISIONS=True  R14_COMMON=True  在本行锚内=True

## F33 [[已证]]
  - FILEREF  gamemd.exe     （见下：对象 vs 来源）

## F34 [[流程]]
  - BARECARD R16      候选目录=R17_R16_SLOT73_SEM

## F35 [[流程]]
  - BARECARD R14      候选目录=R17_R14_VT_STRUCT

## F36 [[流程]]
  - SECTION  §2.6     ns=R14_COMMON 可解析=False 在本行锚内=True
  - SECTION  §2.7     ns=R14_COMMON 可解析=True  在本行锚内=True
  - CARD     S02B-GATE              目录存在=False 在本行锚内=False
  - CARD     R14_COMMON             目录存在=False 在本行锚内=True

## F49 [[已证]]
  - FACT     F29      存在于索引=True  在本行锚内=False

## F51 [[已证]]
  - FACT     F10      存在于索引=True  在本行锚内=False


## 判定汇总（需人工追查的项）

- F14 SECTION `§1061` 可解析=True 锚内=False
- F14 SECTION `§1062` 可解析=True 锚内=False
- F14 SECTION `§1060` 可解析=True 锚内=False
- F17 SECTION `§2.6` 可解析=False 锚内=True
- F17 CARD `R14_COMMON` 可解析=False 锚内=True
- F36 SECTION `§2.6` 可解析=False 锚内=True
- F36 CARD `S02B-GATE` 可解析=False 锚内=False
- F36 CARD `R14_COMMON` 可解析=False 锚内=True