# SPSS-MCP 连接配置详细教程

> 手把手教你将 SPSS-MCP、Claude Code 和 IBM SPSS Statistics 连接起来

---

## 📋 整体架构

```
┌─────────────────┐
│  Claude Code    │  ← 你在这里输入自然语言指令
│  (AI 助手)      │
└────────┬────────┘
         │
         │ MCP 协议通信
         │
┌────────▼────────┐
│   SPSS-MCP      │  ← 中间层：翻译指令 + 调用 SPSS
│  (MCP 服务器)   │
└────────┬────────┘
         │
         │ Python API 调用
         │
┌────────▼────────┐
│  IBM SPSS       │  ← 实际执行统计分析
│  Statistics     │
└─────────────────┘
```

---

## 🔧 连接步骤

### 第一步：安装 SPSS-MCP

#### 方法 A：使用一键安装脚本（推荐）

1. 克隆项目到本地：
```bash
git clone https://github.com/Exekiel179/SPSS-MCP.git
cd SPSS-MCP
```

2. 双击运行 `install.bat`（CMD）或 `install.ps1`（PowerShell）

3. 脚本会自动完成：
   - ✅ 检查 Python 环境
   - ✅ 安装 Python 依赖包
   - ✅ 检测 SPSS 安装路径
   - ✅ 安装 Claude Code 技能
   - ✅ 生成配置代码

#### 方法 B：手动安装

```bash
# 1. 克隆项目
git clone https://github.com/Exekiel179/SPSS-MCP.git
cd SPSS-MCP

# 2. 安装依赖
pip install -e .

# 3. 验证安装
spss-mcp status
```

**预期输出：**
```
pyreadstat : ✓ 1.2.x
pandas     : ✓ 2.x.x
SPSS       : ✓ C:\Program Files\IBM\SPSS Statistics\31\stats.exe
SPSS Python: ✓ C:\Program Files\IBM\SPSS Statistics\31\Python3\python.exe
```

---

### 第二步：配置 Claude Code

#### 2.1 打开 Claude Code 设置

1. 启动 Claude Code
2. 按 `Ctrl + ,`（逗号）打开设置
3. 在搜索框输入 `mcpServers`

#### 2.2 添加 SPSS-MCP 配置

**自动获取配置（推荐）：**

在命令行运行：
```bash
spss-mcp setup-info
```

复制输出的 JSON 配置。

**手动配置：**

在 Claude Code 设置的 `mcpServers` 部分添加：

```json
{
  "mcpServers": {
    "spss": {
      "command": "spss-mcp",
      "args": ["serve", "--transport", "stdio"]
    }
  }
}
```

**如果使用虚拟环境：**

```json
{
  "mcpServers": {
    "spss": {
      "command": "C:\\path\\to\\SPSS-MCP\\.venv\\Scripts\\spss-mcp.exe",
      "args": ["serve", "--transport", "stdio"]
    }
  }
}
```

#### 2.3 重启 Claude Code

配置保存后，**必须重启 Claude Code** 才能生效。

#### 2.4 验证连接

重启后，在 Claude Code 中：
1. 查看右下角或侧边栏的 MCP 服务器列表
2. 应该能看到 `spss` 服务器显示为已连接 ✅

---

### 第三步：配置 SPSS 路径（如果自动检测失败）

如果 `spss-mcp status` 显示 `SPSS : ✗`，需要手动配置：

#### 3.1 找到 SPSS 安装路径

常见路径：
- `C:\Program Files\IBM\SPSS Statistics\31`
- `C:\Program Files\IBM\SPSS Statistics\30`
- `C:\Program Files\IBM\SPSS Statistics\29`

#### 3.2 创建 .env 文件

在 SPSS-MCP 项目根目录创建 `.env` 文件：

```ini
# SPSS 安装路径（修改为你的实际路径）
SPSS_INSTALL_PATH=C:\Program Files\IBM\SPSS Statistics\31

# 可选：超时时间（秒）
SPSS_TIMEOUT=120

# 可选：输出目录
SPSS_RESULTS_DIR=%TEMP%\spss-mcp\results
```

#### 3.3 重启 Claude Code

修改 `.env` 后需要重启 Claude Code 使配置生效。

---

### 第四步：安装 Claude Code 技能（强烈推荐）

技能会让分析更可靠，并自动保存结果文件。

#### 4.1 安装技能

**Windows CMD：**
```cmd
set SKILLS_DIR=%USERPROFILE%\.claude\skills
xcopy /E /I skills\spss-analyst "%SKILLS_DIR%\spss-analyst"
xcopy /E /I skills\spss-mcp-guard "%SKILLS_DIR%\spss-mcp-guard"
```

**Windows PowerShell：**
```powershell
$skillsDir = "$env:USERPROFILE\.claude\skills"
Copy-Item -Recurse -Force skills\spss-analyst  "$skillsDir\spss-analyst"
Copy-Item -Recurse -Force skills\spss-mcp-guard "$skillsDir\spss-mcp-guard"
```

#### 4.2 验证技能安装

检查文件夹是否存在：
```
%USERPROFILE%\.claude\skills\
├── spss-analyst\
│   └── SKILL.md
└── spss-mcp-guard\
    └── SKILL.md
```

#### 4.3 重启 Claude Code

技能安装后需要重启才能激活。

---

## ✅ 测试连接

### 测试 1：检查 MCP 服务器状态

在 Claude Code 中输入：
```
请检查 SPSS-MCP 服务器状态
```

Claude 应该会调用 `spss_check_status` 工具并返回：
- pyreadstat 版本
- pandas 版本
- SPSS 安装路径
- 可用工具数量

### 测试 2：读取 SPSS 数据文件

准备一个 `.sav` 文件，然后在 Claude Code 中输入：
```
请读取 data.sav 文件的变量信息
```

Claude 应该会：
1. 调用 `spss_list_variables` 工具
2. 返回变量列表和标签

### 测试 3：执行简单分析

```
请对 data.sav 文件进行描述性统计分析
```

Claude 应该会：
1. 读取数据文件
2. 生成 SPSS 语法
3. 执行分析
4. 返回 Markdown 格式的结果表格
5. 保存 `.spv` 和 `.sps` 文件到 `spss_result/` 目录

---

## 🔍 连接故障排查

### 问题 1：Claude Code 看不到 spss 服务器

**可能原因：**
- 配置未保存
- 未重启 Claude Code
- JSON 格式错误

**解决方法：**
1. 检查 `settings.json` 中的 JSON 格式是否正确（注意逗号、引号）
2. 保存配置后**必须重启** Claude Code
3. 查看 Claude Code 的日志输出是否有错误信息

### 问题 2：SPSS 未检测到

**可能原因：**
- SPSS 未安装
- SPSS 安装路径不标准
- 环境变量未配置

**解决方法：**
1. 运行 `spss-mcp status` 查看详细信息
2. 手动在 `.env` 文件中指定 SPSS 路径
3. 确认 SPSS 版本在 20-31 之间

### 问题 3：分析执行失败

**可能原因：**
- 数据文件路径错误
- 变量名不存在
- SPSS 语法错误
- 超时

**解决方法：**
1. 确认数据文件路径正确（使用绝对路径）
2. 先用 `spss_list_variables` 查看可用变量
3. 增加 `.env` 中的 `SPSS_TIMEOUT` 值
4. 查看 `spss_result/` 目录中的 `.sps` 文件检查语法

### 问题 4：技能未激活

**可能原因：**
- 技能文件夹位置错误
- 未重启 Claude Code
- SKILL.md 文件缺失

**解决方法：**
1. 确认技能文件夹在 `%USERPROFILE%\.claude\skills\` 下
2. 检查 `SKILL.md` 文件是否存在
3. 重启 Claude Code

---

## 📂 文件输出位置

### 默认输出（无技能）

分析结果保存在：
```
%TEMP%\spss-mcp\results\
├── analysis_20260415_143022.spv
├── analysis_20260415_143022.sps
└── ...
```

### 技能自动归档（推荐）

安装 `spss-analyst` 技能后，结果自动保存到当前工作目录：
```
spss_result/
├── 01_descriptives.sps     ← 带注释的 SPSS 语法
├── 01_descriptives.spv     ← SPSS 查看器文件
├── 02_regression.sps
├── 02_regression.spv
└── NN_<分析类型>.*         ← 全局递增序号
```

---

## 🎯 使用示例

### 示例 1：描述性统计

```
请对 employee.sav 文件中的 salary 变量进行描述性统计
```

**Claude 会：**
1. 读取文件元数据
2. 生成 DESCRIPTIVES 语法
3. 执行分析
4. 返回均值、标准差、最小值、最大值等

### 示例 2：相关分析

```
分析 age、income、education 三个变量之间的相关性
```

**Claude 会：**
1. 生成 CORRELATIONS 语法
2. 计算 Pearson 相关系数
3. 返回相关矩阵和显著性检验结果

### 示例 3：回归分析

```
用 income 作为因变量，age 和 education 作为自变量做线性回归
```

**Claude 会：**
1. 生成 REGRESSION 语法
2. 执行回归分析
3. 返回回归系数、R²、ANOVA 表等

---

## 📚 更多资源

- **快速开始**：[QUICK_START.md](QUICK_START.md)
- **完整文档**：[README.md](README.md)
- **问题反馈**：https://github.com/Exekiel179/SPSS-MCP/issues
- **MCP 协议**：https://modelcontextprotocol.io

---

## 💡 提示

1. **使用绝对路径**：指定数据文件时使用完整路径，避免路径错误
2. **先探索后分析**：不熟悉数据时，先用 `spss_file_summary` 和 `spss_list_variables` 探索
3. **保存结果文件**：`.spv` 文件可以在 SPSS 中打开查看完整的图表和格式化表格
4. **查看语法文件**：`.sps` 文件包含实际执行的 SPSS 语法，可用于学习或复现
5. **自然语言描述**：不需要了解 SPSS 语法，直接用中文描述分析需求即可
