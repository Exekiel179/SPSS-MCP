# SPSS MCP Tools Reference

MCP server: `spss` — 16 tools in two groups.

## Tool Selection Guide

```
用户请求
  ├── 查看文件结构/变量？        → spss_read_metadata / spss_list_variables
  ├── 查看数据行？               → spss_read_data
  ├── 快速概览文件？             → spss_file_summary
  ├── 找 .sav 文件？             → spss_list_files
  ├── 确认 SPSS 是否可用？       → spss_check_status
  ├── 运行分析（已知过程名）？    → 使用对应专项工具（见下表）
  └── 运行自定义/复杂语法？      → spss_run_syntax
```

---

## Group 1: 文件工具（无需 SPSS，仅需 pyreadstat）

### `spss_check_status`
检查服务器能力（pyreadstat 版本、SPSS 路径、是否可用）。**每次会话开始先调用。**

```
参数: 无
返回: Markdown 能力矩阵
```

### `spss_list_files`
列出目录下的 `.sav` / `.zsav` 文件。

```
参数:
  directory  str   必填  要搜索的目录路径
  recursive  bool  可选  是否递归子目录（默认 false）
返回: 文件名、目录、大小的 Markdown 表格
```

### `spss_list_variables`
列出 .sav 文件的所有变量名和标签，支持关键词搜索。

```
参数:
  file_path  str   必填  .sav 文件的绝对路径
  search     str   可选  过滤关键词（变量名或标签中包含此词）
返回: 变量名与标签的 Markdown 表格
```

### `spss_read_metadata`
读取变量类型、值标签、缺失值定义等元数据。

```
参数:
  file_path  str  必填  .sav 文件的绝对路径
返回: 变量详情表 + 值标签表
```

### `spss_read_data`
读取数据行（可限制行数和变量范围）。

```
参数:
  file_path           str        必填  .sav 文件路径
  variables           list[str]  可选  要读取的变量列表（默认全部）
  max_rows            int        可选  最多行数（默认 50）
  apply_value_labels  bool       可选  是否用标签替换编码（默认 true）
返回: 数据 Markdown 表格
```

### `spss_file_summary`
快速概览：案例数、变量数、变量列表、基础描述统计（pandas 计算，无需 SPSS）。

```
参数:
  file_path  str  必填  .sav 文件路径
返回: 综合摘要 Markdown 报告
```

---

## Group 2: 分析工具（需要 IBM SPSS Statistics 已安装）

所有工具内部通过 SPSS XD API 执行，OMS 自动注入，返回 Markdown 格式结果。

### `spss_run_syntax`
执行任意 SPSS 语法，最灵活。用于自定义分析或本参考中没有专项工具覆盖的过程。

```
参数:
  syntax     str  必填  完整 SPSS 语法（可含多条命令）
  data_file  str  可选  若提供，自动在语法前插入 GET FILE='...'
返回: Markdown 输出
```

**示例：**
```python
spss_run_syntax(
  syntax="RELIABILITY /VARIABLES=item1 TO item10 /MODEL=ALPHA.",
  data_file="C:/Data/survey.sav"
)
```

### `spss_frequencies`
运行 `FREQUENCIES` 过程。

```
参数:
  file_path   str        必填  数据文件路径
  variables   list[str]  必填  要分析的变量列表
  statistics  list[str]  可选  统计量列表，默认 ["mean","median","mode","stddev"]
              可选值: mean, median, mode, stddev, variance, skewness, kurtosis, range, minimum, maximum
```

### `spss_descriptives`
运行 `DESCRIPTIVES` 过程（连续变量）。

```
参数:
  file_path   str        必填  数据文件路径
  variables   list[str]  必填  变量列表（应为数值型）
  statistics  list[str]  可选  默认 ["mean","stddev","min","max","variance"]
```

### `spss_crosstabs`
运行 `CROSSTABS` 交叉表。

```
参数:
  file_path          str   必填  数据文件路径
  row_variable       str   必填  行变量名
  column_variable    str   必填  列变量名
  include_chisquare  bool  可选  是否包含卡方检验（默认 true）
  include_row_pct    bool  可选  是否包含行百分比（默认 true）
  include_col_pct    bool  可选  是否包含列百分比（默认 true）
```

### `spss_regression`
运行线性回归（`REGRESSION` 过程）。

```
参数:
  file_path            str        必填  数据文件路径
  dependent            str        必填  因变量名
  predictors           list[str]  必填  自变量列表
  method               str        可选  "ENTER"（默认）/"STEPWISE"/"FORWARD"/"BACKWARD"
  include_diagnostics  bool       可选  是否包含共线性诊断（默认 false）
```

### `spss_t_test`
运行 t 检验。

```
参数:
  test_type          str        必填  "one_sample" / "independent" / "paired"
  file_path          str        必填  数据文件路径
  variables          list[str]  必填  分析变量
  grouping_variable  str        条件  independent 时必填（分组变量名）
  test_value         float      条件  one_sample 时填（检验值，默认 0）
```

### `spss_anova`
运行单因素方差分析（`ONEWAY` 过程）。

```
参数:
  file_path  str        必填  数据文件路径
  dependent  str        必填  因变量名
  factor     str        必填  分组因子名
  post_hoc   list[str]  可选  事后比较方法列表，如 ["TUKEY","BONFERRONI"]
```

### `spss_correlations`
运行相关分析（Pearson 或 Spearman）。

```
参数:
  file_path   str   必填  数据文件路径
  variables   list  必填  变量列表（2个以上）
  method      str   可选  "pearson"（默认）或 "spearman"
  two_tailed  bool  可选  是否双尾检验（默认 true）
```

### `spss_factor`
运行探索性因子分析（`FACTOR` 过程）。

```
参数:
  file_path  str   必填  数据文件路径
  variables  list  必填  纳入分析的变量列表
  method     str   可选  "PC"主成分（默认）或 "PA"主轴因子
  rotation   str   可选  "VARIMAX"（默认）/"OBLIMIN"/"NONE"
  n_factors  int   可选  指定因子数（默认：特征值>1规则）
```

### `spss_validate_syntax`
验证语法是否有语法错误（不实际执行分析）。

```
参数:
  syntax  str  必填  要验证的 SPSS 语法
返回: "Syntax appears valid" 或错误详情
```

---

## 典型工作流示例

### 场景 1：探索新数据集

```python
# 1. 确认服务器状态
spss_check_status()

# 2. 查看文件概览
spss_file_summary(file_path="C:/Data/survey.sav")

# 3. 查看变量详情
spss_read_metadata(file_path="C:/Data/survey.sav")

# 4. 预览数据
spss_read_data(file_path="C:/Data/survey.sav", max_rows=10)
```

### 场景 2：量表分析

```python
# 先查变量（确认 item 变量名）
spss_list_variables(file_path="C:/Data/scale.sav", search="item")

# 运行可靠性分析（使用 run_syntax）
spss_run_syntax(
  syntax="RELIABILITY /VARIABLES=item1 TO item10 /MODEL=ALPHA /STATISTICS=SCALE CORR /SUMMARY=TOTAL.",
  data_file="C:/Data/scale.sav"
)

# 然后运行因子分析
spss_factor(
  file_path="C:/Data/scale.sav",
  variables=["item1","item2","item3","item4","item5"],
  method="PC",
  rotation="VARIMAX"
)
```

### 场景 3：组间比较完整流程

```python
# 描述统计
spss_descriptives(file_path="C:/Data/exp.sav", variables=["score","age"])

# t 检验
spss_t_test(
  file_path="C:/Data/exp.sav",
  test_type="independent",
  variables=["score"],
  grouping_variable="group"
)

# 如果有三组以上
spss_anova(
  file_path="C:/Data/exp.sav",
  dependent="score",
  factor="group",
  post_hoc=["TUKEY"]
)
```
