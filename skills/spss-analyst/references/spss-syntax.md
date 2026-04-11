# SPSS Syntax Reference

## Table of Contents
1. [语法基础规则](#1-语法基础规则)
2. [数据读取与保存](#2-数据读取与保存)
3. [变量操作](#3-变量操作)
4. [数据筛选与排序](#4-数据筛选与排序)
5. [描述性统计](#5-描述性统计)
6. [推断统计](#6-推断统计)
7. [相关与回归](#7-相关与回归)
8. [多元分析](#8-多元分析)
9. [数据转换与重构](#9-数据转换与重构)
10. [OMS 输出管理](#10-oms-输出管理)

---

## 1. 语法基础规则

```spss
* 单行注释（必须以句点结尾）.
/* 块注释（不需要句点） */

* 命令续行：行末不加句点，下一行缩进.
FREQUENCIES VARIABLES=var1 var2
  /STATISTICS=MEAN STDDEV
  /ORDER=ANALYSIS.

* 变量列表简写.
var1 TO var5          /* var1、var2、var3、var4、var5 */
ALL                   /* 全部变量 */

* 缺失值.
SYSMIS                /* 系统缺失 */
$SYSMIS               /* 在表达式中使用 */
MISSING(var)          /* 函数：判断是否缺失 */
```

**数据类型：**
- 数值型（Numeric）：`F8.2`（宽度8，2位小数）
- 字符串型（String）：`A20`（20字符）
- 日期型：`DATE11`、`DATETIME20`

---

## 2. 数据读取与保存

```spss
* 读取 .sav 文件.
GET FILE='C:/Data/survey.sav'.

* 保存为 .sav.
SAVE OUTFILE='C:/Data/cleaned.sav'
  /COMPRESSED.

* 读取 Excel.
GET DATA
  /TYPE=XLS
  /FILE='C:/Data/data.xlsx'
  /SHEET=NAME 'Sheet1'
  /CELLRANGE=FULL
  /READNAMES=ON.

* 读取 CSV.
GET DATA
  /TYPE=TXT
  /FILE='C:/Data/data.csv'
  /DELIMITERS=','
  /QUALIFIER='"'
  /FIRSTCASE=2
  /VARIABLES=id F3 name A20 score F5.2.

* 导出为 CSV.
SAVE TRANSLATE OUTFILE='C:/Data/output.csv'
  /TYPE=CSV
  /FIELDNAMES
  /REPLACE.

* 合并数据集（纵向：增加案例）.
ADD FILES FILE='C:/Data/wave1.sav'
  /FILE='C:/Data/wave2.sav'.
EXECUTE.

* 合并数据集（横向：增加变量，需按 id 排序）.
SORT CASES BY id.
MATCH FILES FILE=*
  /FILE='C:/Data/extra_vars.sav'
  /BY id.
EXECUTE.
```

---

## 3. 变量操作

```spss
* 变量标签.
VARIABLE LABELS
  age   '年龄（岁）'
  score '测试得分'
  gender '性别'.

* 值标签.
VALUE LABELS gender
  1 '男'
  2 '女'.

VALUE LABELS education
  1 '小学及以下'
  2 '初中'
  3 '高中'
  4 '大专'
  5 '本科及以上'.

* 定义缺失值.
MISSING VALUES age (99)
  income (999 9999)
  name ('N/A').

* 变量类型与宽度.
FORMATS score (F5.2) date (DATE11).

* 变量度量级别.
VARIABLE LEVEL gender (NOMINAL) age (SCALE) edu (ORDINAL).

* 计算变量（COMPUTE）.
COMPUTE total = item1 + item2 + item3.
COMPUTE mean_score = MEAN(item1, item2, item3).
COMPUTE log_income = LG10(income).
COMPUTE age_sq = age ** 2.
EXECUTE.

* 条件计算（IF）.
IF (gender = 1) gender_label = 1.
IF (gender = 2) gender_label = 2.
EXECUTE.

* 重新编码（RECODE）.
RECODE score
  (0 THRU 59 = 1)
  (60 THRU 74 = 2)
  (75 THRU 89 = 3)
  (90 THRU 100 = 4)
  INTO grade.
VALUE LABELS grade 1'不及格' 2'及格' 3'良好' 4'优秀'.
EXECUTE.

* 反向编码（Likert 量表常用）.
RECODE item3 (1=5)(2=4)(3=3)(4=2)(5=1) INTO item3r.
EXECUTE.

* 删除变量.
DELETE VARIABLES tmpvar1 tmpvar2.
```

**常用 COMPUTE 函数：**

| 函数 | 说明 |
|---|---|
| `MEAN(v1,v2,...)` | 均值（忽略缺失） |
| `SUM(v1,v2,...)` | 求和 |
| `SD(v1,v2,...)` | 标准差 |
| `MIN(v1,v2,...)` | 最小值 |
| `MAX(v1,v2,...)` | 最大值 |
| `NMISS(v1,v2,...)` | 缺失个数 |
| `ABS(x)` | 绝对值 |
| `SQRT(x)` | 平方根 |
| `LG10(x)` | 以10为底的对数 |
| `EXP(x)` | 自然指数 |
| `RND(x)` | 四舍五入 |
| `TRUNC(x)` | 截断取整 |
| `SUBSTR(s,p,n)` | 字符串截取 |
| `CONCAT(s1,s2)` | 字符串连接 |
| `NUMBER(s,fmt)` | 字符转数值 |
| `STRING(x,fmt)` | 数值转字符 |
| `CTIME.DAYS(t)` | 时间转天数 |
| `DATE.DMY(d,m,y)` | 构造日期 |

---

## 4. 数据筛选与排序

```spss
* 临时筛选（只影响下一个过程）.
TEMPORARY.
SELECT IF (age >= 18 AND gender = 1).
FREQUENCIES VARIABLES=income.

* 永久筛选（激活过滤器）.
USE ALL.                          /* 取消过滤 */
FILTER BY filter_$var.            /* 用0/1变量过滤 */

COMPUTE filter_adults = (age >= 18).
FILTER BY filter_adults.
EXECUTE.

* 按条件删除案例.
SELECT IF (age >= 0 AND age <= 120).  /* 保留合理值 */
EXECUTE.

* 排序.
SORT CASES BY age (A).            /* A=升序，D=降序 */
SORT CASES BY gender (A) age (D). /* 多变量排序 */

* 加权.
WEIGHT BY freq_var.
WEIGHT OFF.

* 分割文件（分组运行分析）.
SORT CASES BY gender.
SPLIT FILE SEPARATE BY gender.
DESCRIPTIVES VARIABLES=score.
SPLIT FILE OFF.
```

---

## 5. 描述性统计

```spss
* 频率表.
FREQUENCIES VARIABLES=gender education
  /STATISTICS=MEAN MEDIAN MODE STDDEV SKEWNESS KURTOSIS
  /HISTOGRAM NORMAL
  /ORDER=ANALYSIS.

* 描述统计（连续变量）.
DESCRIPTIVES VARIABLES=age score income
  /STATISTICS=MEAN STDDEV MIN MAX VARIANCE RANGE SKEWNESS KURTOSIS.

* 探索性分析（含正态检验）.
EXAMINE VARIABLES=score BY gender
  /PLOT BOXPLOT STEMLEAF HISTOGRAM NPPLOT
  /STATISTICS DESCRIPTIVES
  /CINTERVAL 95.

* 交叉表.
CROSSTABS
  /TABLES=gender BY education
  /STATISTICS=CHISQ PHI CC LAMBDA SOMER
  /CELLS=COUNT ROW COLUMN EXPECTED.

* 自定义表格.
CTABLES
  /TABLE gender [C] BY score [MEAN, STDDEV, COUNT].
```

---

## 6. 推断统计

```spss
* 单样本 t 检验.
T-TEST
  /TESTVAL=50
  /VARIABLES=score.

* 独立样本 t 检验.
T-TEST GROUPS=gender(1 2)
  /VARIABLES=score income.

* 配对样本 t 检验.
T-TEST PAIRS=pre_score WITH post_score (PAIRED).

* 单因素 ANOVA + 事后比较.
ONEWAY score BY group
  /STATISTICS DESCRIPTIVES HOMOGENEITY
  /POSTHOC=TUKEY BONFERRONI LSD ALPHA(.05)
  /PLOT MEANS.

* 双因素 ANOVA（GLM）.
UNIANOVA score BY gender group
  /METHOD=SSTYPE(3)
  /INTERCEPT=INCLUDE
  /POSTHOC=group(TUKEY)
  /PLOT=PROFILE(gender*group)
  /PRINT=DESCRIPTIVE ETASQ HOMOGENEITY
  /CRITERIA=ALPHA(.05).

* 非参数检验.
NPAR TESTS
  /MANN-WHITNEY=score BY gender(1 2)   /* Mann-Whitney U */
  /WILCOXON=pre_score WITH post_score  /* Wilcoxon 符号秩 */
  /K-W=score BY group(1 4)             /* Kruskal-Wallis */
  /CHI-SQUARE=category.                /* 单样本卡方 */
```

---

## 7. 相关与回归

```spss
* Pearson 相关.
CORRELATIONS
  /VARIABLES=age income score
  /PRINT=TWOTAIL SIG.

* Spearman 相关.
NONPAR CORR
  /VARIABLES=rank1 rank2
  /PRINT=SPEARMAN TWOTAIL SIG.

* 线性回归.
REGRESSION
  /DESCRIPTIVES MEAN STDDEV CORR
  /DEPENDENT score
  /METHOD=ENTER age gender edu
  /STATISTICS COEFF OUTS R ANOVA CHANGE COLLIN TOL
  /RESIDUALS HISTOGRAM(ZRESID) NORMAL(ZRESID)
  /CASEWISE PLOT(ZRESID) OUTLIERS(3).

* 逐步回归.
REGRESSION
  /DEPENDENT score
  /METHOD=STEPWISE age gender edu income.

* Logistic 回归（二分类）.
LOGISTIC REGRESSION VARIABLES outcome
  /METHOD=ENTER age gender score
  /PRINT=GOODFIT ITER(1) CI(95)
  /CRITERIA=PIN(.05) POUT(.10).

* 多元线性回归（多个因变量）.
MANOVA y1 y2 WITH x1 x2 x3
  /PRINT=SIGNIF(MULT UNIV).
```

---

## 8. 多元分析

```spss
* 探索性因子分析.
FACTOR
  /VARIABLES item1 TO item20
  /MISSING LISTWISE
  /ANALYSIS item1 TO item20
  /PRINT INITIAL EXTRACTION ROTATION KMO AIC
  /PLOT EIGEN
  /EXTRACTION PC              /* PC=主成分，PAF=主轴因子 */
  /CRITERIA MINEIGEN(1)       /* 保留特征值>1的因子 */
  /ROTATION VARIMAX
  /SAVE REG(ALL FAC).         /* 保存因子得分 */

* 验证性因子分析（via AMOS — 需在语法外运行）.
* 使用 FACTOR 仅做 EFA.

* 聚类分析（K-Means）.
QUICK CLUSTER var1 var2 var3
  /MISSING=LISTWISE
  /CRITERIA=CLUSTER(3) MXITER(10) CONVERGE(0)
  /METHOD=KMEANS(NOUPDATE)
  /SAVE CLUSTER(cluster_id).

* 判别分析.
DISCRIMINANT
  /GROUPS=group(1 3)
  /VARIABLES=var1 var2 var3
  /STATISTICS=MEAN STDDEV UNIVF BOXM COEFF RAW TABLE.

* 可靠性分析（Cronbach α）.
RELIABILITY
  /VARIABLES=item1 TO item10
  /SCALE('总量表') ALL
  /MODEL=ALPHA
  /STATISTICS=DESCRIPTIVE SCALE CORR
  /SUMMARY=TOTAL MEANS.
```

---

## 9. 数据转换与重构

```spss
* 宽格式转长格式（Restructure）.
VARSTOCASES
  /MAKE score FROM time1 time2 time3
  /INDEX=time(3)
  /KEEP=id gender.

* 长格式转宽格式.
CASESTOVARS
  /ID=id
  /INDEX=time
  /GROUPBY=VARIABLE.

* 汇总（Aggregate）.
AGGREGATE
  /OUTFILE='C:/Data/summary.sav'
  /BREAK=group gender
  /mean_score=MEAN(score)
  /n=N.

* 标准化（Z 分数）.
DESCRIPTIVES VARIABLES=score
  /SAVE.                      /* 自动保存为 Zscore(score) */

* 手动标准化.
COMPUTE z_score = (score - mean_score) / sd_score.
EXECUTE.

* 缺失值插补（均值替代）.
RMV /score_imp=SMEAN(score).

* 多重插补（MI）.
MULTIPLE IMPUTATION score income edu
  /IMPUTE METHOD=FCS NIMPUTATIONS=5
  /OUTFILE IMPUTATIONS='C:/Data/imputed.sav'.
```

---

## 10. OMS 输出管理

OMS（Output Management System）将 SPSS 输出重定向到文件，是 spss-mcp 内部自动使用的机制。手动编写时：

```spss
* 将所有输出导出为文本文件.
OMS
  /SELECT ALL
  /DESTINATION FORMAT=TEXT
    OUTFILE='C:/Output/results.txt'.

FREQUENCIES VARIABLES=gender.
DESCRIPTIVES VARIABLES=score.

OMSEND.

* 只导出指定过程.
OMS
  /SELECT TABLES
  /IF COMMANDS=['Frequencies'] SUBTYPES=['Frequencies']
  /DESTINATION FORMAT=XLSX
    OUTFILE='C:/Output/freq_table.xlsx'.

FREQUENCIES VARIABLES=gender education.

OMSEND.

* 将输出保存为 XML（用于程序处理）.
OMS
  /SELECT ALL
  /DESTINATION FORMAT=OXML
    OUTFILE='C:/Output/output.xml'.
```

**注意：** 当通过 `spss_run_syntax` 工具执行时，OMS 由工具自动注入，无需手动添加。

---

## 常见错误与解决

| 错误 | 原因 | 解决 |
|---|---|---|
| `Undefined variable` | 变量名拼写错误或大小写 | SPSS 变量名不区分大小写，检查拼写 |
| `End of command expected` | 缺少句点 | 每条命令末尾加 `.` |
| `Invalid subcommand` | 子命令拼写错误 | 参照本手册检查子命令名 |
| `Insufficient data` | 有效案例过少 | 检查 SELECT IF 和缺失值处理 |
| `File not found` | 路径错误 | 使用正斜杠 `/` 或双反斜杠 `\\` |
