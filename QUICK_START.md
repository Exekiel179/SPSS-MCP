# SPSS-MCP 快速部署指南

> 5 分钟完成部署，让 Claude 直接调用 SPSS 进行统计分析

---

## 前置要求

- ✅ Windows 10/11
- ✅ Python 3.10 或更高版本
- ✅ IBM SPSS Statistics（任意版本 20-31）
- ✅ Claude Code 或 Claude Desktop

---

## 一键部署（3 步）

### 步骤 1：安装 SPSS-MCP

打开命令提示符（CMD）或 PowerShell，复制粘贴以下命令：

```bash
git clone https://github.com/Exekiel179/SPSS-MCP.git
cd SPSS-MCP
pip install -e .
```

**验证安装：**

```bash
spss-mcp status
```

如果看到 `SPSS : ✓`，说明安装成功。如果显示 `✗`，跳到[故障排除](#故障排除)。

---

### 步骤 2：连接到 Claude Code

#### 方法 A：自动配置（推荐）

运行以下命令，自动获取配置代码：

```bash
spss-mcp setup-info
```

复制输出的 JSON 配置，然后：

1. 打开 Claude Code
2. 按 `Ctrl+,` 打开设置
3. 搜索 `mcpServers`
4. 粘贴配置代码
5. 重启 Claude Code

#### 方法 B：手动配置

在 Claude Code 设置中添加：

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

**重启 Claude Code** 后，在 MCP 服务器列表中应该能看到 `spss`。

---

### 步骤 3：安装智能技能（可选但强烈推荐）

这两个技能会让 SPSS 分析更可靠，并自动保存结果文件。

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

**重启 Claude Code** 后技能自动激活。

---

## 开始使用

在 Claude Code 中直接用自然语言描述分析需求：

```
请对 data.sav 文件进行描述性统计分析
```

```
对变量 age 和 income 做相关分析
```

```
用 t 检验比较男女两组的收入差异
```

Claude 会自动：
1. 读取数据文件
2. 生成 SPSS 语法
3. 执行分析
4. 返回 Markdown 格式的结果
5. 保存 `.spv` 和 `.sps` 文件到 `spss_result/` 目录

---

## 输出文件位置

安装技能后，每次分析会自动保存到当前工作目录：

```
spss_result/
├── 01_descriptives.sps     ← SPSS 语法文件
├── 01_descriptives.spv     ← SPSS 查看器文件（用 SPSS 打开查看完整图表）
├── 02_regression.sps
├── 02_regression.spv
└── ...
```

---

## 故障排除

### SPSS 未检测到

如果 `spss-mcp status` 显示 `SPSS : ✗`：

1. 在项目目录创建 `.env` 文件
2. 添加以下内容（修改为你的 SPSS 安装路径）：

```ini
SPSS_INSTALL_PATH=C:\Program Files\IBM\SPSS Statistics\31
```

3. 重启 Claude Code

### 分析超时

在 `.env` 文件中增加超时时间：

```ini
SPSS_TIMEOUT=300
```

### 技能未激活

确认文件夹存在：

```
%USERPROFILE%\.claude\skills\spss-analyst\SKILL.md
%USERPROFILE%\.claude\skills\spss-mcp-guard\SKILL.md
```

重启 Claude Code。

---

## 完整文档

详细配置选项、所有可用工具和高级用法，请参考 [README.md](README.md)。

---

## 支持

- 问题反馈：https://github.com/Exekiel179/SPSS-MCP/issues
- 完整文档：[README.md](README.md)
