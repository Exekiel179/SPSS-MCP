# SPSS-MCP 功能扩展计划

基于 IBM SPSS Statistics 31 Command Syntax Reference (2548页)

## 当前已实现工具 (21个)

### 文件工具 (6个)
- spss_check_status
- spss_list_files
- spss_list_variables
- spss_read_metadata
- spss_read_data
- spss_file_summary

### 基础统计工具 (15个)
- spss_run_syntax (通用)
- spss_frequencies
- spss_descriptives
- spss_crosstabs
- spss_t_test
- spss_anova (单因素)
- spss_correlations
- spss_regression (线性)
- spss_factor (探索性因子分析)
- spss_reliability_alpha
- spss_compute_scale_score
- spss_nonparametric_tests
- spss_normality_outliers
- spss_repeated_measures_anova
- spss_validate_syntax

---

## 待扩展工具 (按优先级)

### 第一优先级：高级回归与广义线性模型

#### 1. spss_logistic_regression
**SPSS命令**: LOGISTIC REGRESSION
**页码**: 1129-1150
**用途**: 二分类/多分类逻辑回归
**关键参数**:
- dependent: 因变量
- predictors: 预测变量列表
- method: ENTER / FSTEP / BSTEP
- categorical: 分类变量列表
- contrast: 对比编码方式
- save: 保存预测值/残差
- print: 输出选项 (分类表/拟合优度/参数估计)

#### 2. spss_ordinal_regression
**SPSS命令**: PLUM (Polytomous Universal Model)
**页码**: 1451-1465
**用途**: 有序分类因变量回归
**关键参数**:
- dependent: 有序因变量
- predictors: 预测变量
- link: 连接函数 (LOGIT/PROBIT/CLOGLOG)
- scale: 尺度变量
- print: 参数估计/拟合信息

#### 3. spss_genlin
**SPSS命令**: GENLIN
**页码**: 727-750
**用途**: 广义线性模型
**关键参数**:
- dependent: 因变量
- predictors: 预测变量
- distribution: 分布族 (NORMAL/BINOMIAL/POISSON/GAMMA等)
- link: 连接函数
- scale: 尺度参数估计方法

### 第二优先级：多层与混合模型

#### 4. spss_mixed
**SPSS命令**: MIXED
**页码**: 1253-1270
**用途**: 线性混合效应模型/多层模型
**关键参数**:
- dependent: 因变量
- fixed: 固定效应
- random: 随机效应
- subject: 主体变量
- repeated: 重复测量结构
- method: REML / ML
- covtype: 协方差结构类型

#### 5. spss_genlinmixed
**SPSS命令**: GENLINMIXED
**页码**: 753+
**用途**: 广义线性混合模型
**关键参数**:
- dependent: 因变量
- fixed: 固定效应
- random: 随机效应
- distribution: 分布族
- link: 连接函数

### 第三优先级：生存分析

#### 6. spss_cox_regression
**SPSS命令**: COXREG
**页码**: 371-385
**用途**: Cox比例风险回归
**关键参数**:
- time: 时间变量
- status: 状态变量 (事件发生=1)
- predictors: 协变量
- categorical: 分类变量
- method: ENTER / FSTEP / BSTEP
- strata: 分层变量
- save: 保存生存函数/风险

#### 7. spss_kaplan_meier
**SPSS命令**: KM
**页码**: 843-850
**用途**: Kaplan-Meier生存分析
**关键参数**:
- time: 时间变量
- status: 状态变量
- strata: 分组变量
- compare: 组间比较方法 (LOGRANK/BRESLOW/TARONE)
- percentiles: 百分位数
- mean: 均值估计

### 第四优先级：判别与聚类

#### 8. spss_discriminant
**SPSS命令**: DISCRIMINANT
**页码**: 585-600
**用途**: 判别分析
**关键参数**:
- groups: 分组变量
- predictors: 判别变量
- method: DIRECT / WILKS / MAHAL
- priors: 先验概率
- save: 保存判别得分/分类

#### 9. spss_cluster_hierarchical
**SPSS命令**: CLUSTER
**页码**: 315-325
**用途**: 层次聚类
**关键参数**:
- variables: 聚类变量
- method: 聚类方法 (BAVERAGE/WAVERAGE/SINGLE/COMPLETE/WARD等)
- measure: 距离测量 (SEUCLID/EUCLID/COSINE等)
- id: 案例标识变量
- dendrogram: 树状图

#### 10. spss_twostep_cluster
**SPSS命令**: TWOSTEP CLUSTER
**用途**: 两步聚类 (自动确定类数)
**关键参数**:
- continuous: 连续变量
- categorical: 分类变量
- distance: 距离测量
- numclusters: 类数 (AUTO或指定)
- outliers: 异常值处理

### 第五优先级：多元方差分析

#### 11. spss_manova
**SPSS命令**: MANOVA
**页码**: 841+
**用途**: 多元方差分析
**关键参数**:
- dependents: 多个因变量
- factors: 因子变量
- covariates: 协变量
- method: SSTYPE(1/2/3/4)
- print: 多元检验/单变量检验

#### 12. spss_glm_univariate
**SPSS命令**: UNIANOVA
**用途**: 单变量一般线性模型
**关键参数**:
- dependent: 因变量
- factors: 因子
- covariates: 协变量
- design: 模型设计
- emmeans: 估计边际均值
- posthoc: 事后比较

---

## 实现策略

### 阶段1：核心语法生成函数 (1-2天)
为每个新工具创建语法构建函数，确保参数校验与语法正确性

### 阶段2：MCP工具封装 (2-3天)
在 server.py 中添加 @mcp.tool 装饰器定义，统一返回格式

### 阶段3：参数校验增强 (1天)
使用 Pydantic 模型定义参数 schema，加入类型检查与范围校验

### 阶段4：测试与文档 (1-2天)
- 针对每个工具编写测试用例
- 更新 README 工具列表
- 补充使用示例

---

## 技术要点

### 1. 语法构建模式
```python
def _build_logistic_syntax(
    dependent: str,
    predictors: list[str],
    method: str = "ENTER",
    categorical: list[str] | None = None,
    ...
) -> str:
    syntax = f"LOGISTIC REGRESSION VARIABLES {dependent}\n"
    syntax += f"  /METHOD={method} {' '.join(predictors)}\n"
    if categorical:
        syntax += f"  /CATEGORICAL={' '.join(categorical)}\n"
    ...
    return syntax
```

### 2. 参数校验模式
```python
from pydantic import BaseModel, Field, field_validator

class LogisticParams(BaseModel):
    dependent: str
    predictors: list[str] = Field(min_length=1)
    method: Literal["ENTER", "FSTEP", "BSTEP"] = "ENTER"

    @field_validator('predictors')
    def check_predictors(cls, v):
        if len(v) < 1:
            raise ValueError("至少需要1个预测变量")
        return v
```

### 3. 工具定义模式
```python
@mcp.tool(
    name="spss_logistic_regression",
    description="执行二分类或多分类逻辑回归分析"
)
async def spss_logistic_regression(
    file_path: str,
    dependent: str,
    predictors: list[str],
    method: str = "ENTER",
    categorical: list[str] | None = None,
    ctx: Context = None,
) -> str:
    err = _require_spss(ctx)
    if err:
        return f"Error: {err}"

    syntax = _build_logistic_syntax(...)
    result = await run_syntax(syntax, data_file=file_path)
    return _format_run_result(result)
```

---

## 预期成果

完成后系统将提供 **33个MCP工具**，覆盖：
- 基础统计 ✓
- 高级回归 (逻辑/有序/广义线性)
- 多层模型
- 生存分析
- 判别与聚类
- 多元方差分析

满足心理学、社会科学、医学研究的绝大多数统计需求。
