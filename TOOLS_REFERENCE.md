# SPSS-MCP 工具完整列表

版本：0.2.0
总计：36个工具

---

## 文件与数据工具 (6个)

### spss_check_status
检查服务器能力状态（SPSS是否可用、pyreadstat版本等）

### spss_list_files
列出目录下的 .sav/.zsav 文件

**参数**:
- `directory`: 目录路径
- `recursive`: 是否递归搜索

### spss_list_variables
列出变量名和标签，支持关键词搜索

**参数**:
- `file_path`: .sav文件路径
- `search`: 搜索关键词（可选）

### spss_read_metadata
读取变量类型、值标签、缺失值定义

**参数**:
- `file_path`: .sav文件路径

### spss_read_data
预览数据行

**参数**:
- `file_path`: .sav文件路径
- `variables`: 指定变量列表（可选）
- `max_rows`: 最大行数（默认50）
- `apply_value_labels`: 是否应用值标签

### spss_file_summary
快速概览：案例数、变量数、基础统计

**参数**:
- `file_path`: .sav文件路径

---

## 基础统计 (9个)

### spss_frequencies
频率分析

**参数**:
- `file_path`: .sav文件路径
- `variables`: 变量列表
- `statistics`: 统计量列表（可选）

### spss_descriptives
描述统计

**参数**:
- `file_path`: .sav文件路径
- `variables`: 变量列表
- `statistics`: 统计量列表（可选）

### spss_crosstabs
列联表与卡方检验

**参数**:
- `file_path`: .sav文件路径
- `row_variable`: 行变量
- `column_variable`: 列变量
- `include_chisquare`: 是否包含卡方检验
- `include_row_pct`: 是否包含行百分比
- `include_col_pct`: 是否包含列百分比

### spss_t_test
t检验（独立样本/配对/单样本）

**参数**:
- `file_path`: .sav文件路径
- `test_type`: 检验类型（one_sample/independent/paired）
- `variables`: 变量列表
- `grouping_variable`: 分组变量（独立样本）
- `test_value`: 检验值（单样本）

### spss_anova
单因素方差分析

**参数**:
- `file_path`: .sav文件路径
- `dependent`: 因变量
- `factor`: 因子变量
- `post_hoc`: 事后比较方法列表（可选）

### spss_correlations
相关分析

**参数**:
- `file_path`: .sav文件路径
- `variables`: 变量列表
- `method`: 相关类型（pearson/spearman）
- `two_tailed`: 是否双尾检验

### spss_regression
线性回归

**参数**:
- `file_path`: .sav文件路径
- `dependent`: 因变量
- `predictors`: 预测变量列表
- `method`: 变量选择方法（ENTER/STEPWISE等）
- `include_diagnostics`: 是否包含诊断

### spss_normality_outliers
正态性检验与异常值检测

**参数**:
- `file_path`: .sav文件路径
- `variables`: 变量列表
- `plots`: 是否生成图形

### spss_nonparametric_tests
非参数检验（Mann-Whitney/Wilcoxon/Kruskal-Wallis）

**参数**:
- `file_path`: .sav文件路径
- `test_type`: 检验类型
- `variables`: 变量列表
- `grouping_variable`: 分组变量（可选）
- `group_values`: 分组值（可选）

---

## 高级回归与广义线性模型 (3个)

### spss_logistic_regression
二分类/多分类逻辑回归

**参数**:
- `file_path`: .sav文件路径
- `dependent`: 因变量
- `predictors`: 预测变量列表
- `method`: 变量选择方法（ENTER/FSTEP/BSTEP）
- `categorical`: 分类预测变量列表（可选）
- `contrast`: 对比编码方式（可选）
- `save_predicted`: 是否保存预测值
- `print_options`: 打印选项列表（可选）

### spss_ordinal_regression
有序回归（PLUM）

**参数**:
- `file_path`: .sav文件路径
- `dependent`: 有序因变量
- `predictors`: 预测变量列表
- `link`: 连接函数（LOGIT/PROBIT/CLOGLOG/NLOGLOG/CAUCHIT）
- `categorical`: 分类预测变量列表（可选）
- `save_predicted`: 是否保存预测值
- `test_parallel`: 是否检验平行线假设

### spss_genlin
广义线性模型

**参数**:
- `file_path`: .sav文件路径
- `dependent`: 因变量
- `predictors`: 预测变量列表
- `distribution`: 分布族（NORMAL/BINOMIAL/POISSON/GAMMA/IGAUSS/NEGBIN/MULTINOMIAL）
- `link`: 连接函数（可选，自动选择）
- `scale`: 尺度参数方法（可选）
- `categorical`: 分类预测变量列表（可选）
- `save_predicted`: 是否保存预测值

---

## 多层与混合模型 (2个)

### spss_mixed
线性混合效应模型

**参数**:
- `file_path`: .sav文件路径
- `dependent`: 因变量
- `fixed_effects`: 固定效应列表
- `random_effects`: 随机效应列表（可选）
- `subject`: 主体/分组变量（可选）
- `repeated`: 重复测量变量（可选）
- `repeated_type`: 重复测量协方差结构（可选）
- `method`: 估计方法（REML/ML）
- `covtype_random`: 随机效应协方差类型（可选）

### spss_genlinmixed
广义线性混合模型

**参数**:
- `file_path`: .sav文件路径
- `dependent`: 因变量
- `fixed_effects`: 固定效应列表
- `random_effects`: 随机效应列表（可选）
- `subject`: 主体变量（可选）
- `distribution`: 分布族（NORMAL/BINOMIAL/POISSON/GAMMA/NEGBIN）
- `link`: 连接函数（可选）

---

## 生存分析 (2个)

### spss_cox_regression
Cox比例风险回归

**参数**:
- `file_path`: .sav文件路径
- `time_variable`: 时间变量
- `status_variable`: 状态变量
- `status_event_value`: 事件发生值
- `predictors`: 预测变量列表
- `method`: 变量选择方法（ENTER/FSTEP/BSTEP）
- `categorical`: 分类预测变量列表（可选）
- `strata`: 分层变量列表（可选）
- `save_survival`: 是否保存生存函数

### spss_kaplan_meier
Kaplan-Meier生存分析

**参数**:
- `file_path`: .sav文件路径
- `time_variable`: 时间变量
- `status_variable`: 状态变量
- `status_event_value`: 事件发生值
- `strata`: 分组变量（可选）
- `compare_method`: 组间比较方法（LOGRANK/BRESLOW/TARONE）
- `percentiles`: 生存百分位数列表（可选）

---

## 多元分析 (5个)

### spss_factor
探索性因子分析

**参数**:
- `file_path`: .sav文件路径
- `variables`: 变量列表
- `method`: 提取方法（PC/PA）
- `n_factors`: 因子数（可选）
- `rotation`: 旋转方法（VARIMAX/OBLIMIN/NONE）

### spss_discriminant
判别分析

**参数**:
- `file_path`: .sav文件路径
- `groups`: 分组变量
- `predictors`: 判别变量列表
- `method`: 变量选择方法（DIRECT/WILKS/MAHAL）
- `priors`: 先验概率（EQUAL/SIZE）
- `save_scores`: 是否保存判别得分
- `save_class`: 是否保存预测分组

### spss_manova
多元方差分析

**参数**:
- `file_path`: .sav文件路径
- `dependents`: 因变量列表
- `factors`: 因子列表
- `covariates`: 协变量列表（可选）
- `method`: 平方和类型（SSTYPE1/2/3/4）
- `print_multivariate`: 是否打印多元检验
- `print_univariate`: 是否打印单变量检验

### spss_glm_univariate
单变量一般线性模型

**参数**:
- `file_path`: .sav文件路径
- `dependent`: 因变量
- `factors`: 因子列表
- `covariates`: 协变量列表（可选）
- `emmeans`: 估计边际均值变量列表（可选）
- `posthoc`: 事后比较变量列表（可选）
- `posthoc_method`: 事后比较方法（可选）
- `save_predicted`: 是否保存预测值

### spss_repeated_measures_anova
重复测量方差分析

**参数**:
- `file_path`: .sav文件路径
- `within_factor_name`: 组内因子名称
- `levels`: 水平数
- `variables`: 变量列表（每个水平一个）
- `include_pairwise`: 是否包含成对比较

---

## 聚类分析 (2个)

### spss_cluster_hierarchical
层次聚类分析

**参数**:
- `file_path`: .sav文件路径
- `variables`: 聚类变量列表
- `method`: 连接方法（BAVERAGE/WAVERAGE/SINGLE/COMPLETE/CENTROID/MEDIAN/WARD）
- `measure`: 距离测量（SEUCLID/EUCLID/COSINE/PEARSON等）
- `id_variable`: 案例标识变量（可选）
- `dendrogram`: 是否生成树状图

### spss_twostep_cluster
两步聚类分析

**参数**:
- `file_path`: .sav文件路径
- `continuous`: 连续变量列表（可选）
- `categorical`: 分类变量列表（可选）
- `distance`: 距离测量（EUCLID/CHISQ）
- `num_clusters`: 固定类数（可选，None为自动）
- `max_clusters`: 最大类数（自动模式）
- `outlier_handling`: 是否处理异常值

---

## 信度与量表 (2个)

### spss_reliability_alpha
Cronbach's α信度分析

**参数**:
- `file_path`: .sav文件路径
- `variables`: 条目变量列表
- `model`: 模型类型（ALPHA/OMEGA）
- `scale_name`: 量表名称（可选）

### spss_compute_scale_score
计算量表得分

**参数**:
- `file_path`: .sav文件路径
- `new_variable`: 新变量名
- `items`: 条目变量列表
- `method`: 计算方法（sum/mean）
- `reverse_items`: 反向计分条目列表（可选）
- `reverse_min`: 反向计分最小值（可选）
- `reverse_max`: 反向计分最大值（可选）
- `min_valid`: 最小有效条目数（可选）

---

## 实用工具 (2个)

### spss_run_syntax
执行任意SPSS语法

**参数**:
- `syntax`: SPSS语法字符串
- `data_file`: 数据文件路径（可选）
- `save_viewer_output`: 是否保存.spv文件
- `save_syntax_file`: 是否保存.sps文件

### spss_validate_syntax
验证语法（不执行）

**参数**:
- `syntax`: SPSS语法字符串

---

## 输出说明

所有分析工具默认会：
1. 生成 Markdown 格式的结果表格
2. 保存 `.spv` Viewer 文件（可在 SPSS 中打开）
3. 保存 `.sps` 语法文件（可复现分析）
4. 在返回文本中附带文件路径

输出目录由 `SPSS_RESULTS_DIR` 环境变量控制，默认为 `%TEMP%\spss-mcp\results`。
