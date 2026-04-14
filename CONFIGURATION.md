# SPSS-MCP 配置管理面板

> 完整的配置指南：全局注册、局部注册、系统配置和 API 密钥管理

---

## 📋 目录

- [配置方式对比](#配置方式对比)
- [全局注册（推荐）](#全局注册推荐)
- [局部注册](#局部注册)
- [系统配置](#系统配置)
- [环境变量配置](#环境变量配置)
- [配置验证](#配置验证)

---

## 配置方式对比

| 配置方式 | 适用场景 | 配置文件位置 | 作用范围 |
|---------|---------|-------------|---------|
| **全局注册** | 所有项目都使用 SPSS-MCP | `~/.claude/settings.json` | 全局生效 |
| **局部注册** | 仅特定项目使用 | `项目/.claude/settings.local.json` | 仅当前项目 |
| **系统配置** | SPSS 路径、超时等 | `项目/.env` | 项目级别 |

---

## 全局注册（推荐）

### 适用场景

- ✅ 经常使用 SPSS 进行数据分析
- ✅ 多个项目都需要 SPSS 功能
- ✅ 希望在任何目录都能调用 SPSS

### 配置步骤

#### 1. 打开全局配置文件

**Windows:**
```
%USERPROFILE%\.claude\settings.json
```

**快速打开方式：**
- 在 Claude Code 中按 `Ctrl + ,`
- 搜索 `mcpServers`
- 点击 "Edit in settings.json"

#### 2. 添加 SPSS-MCP 配置

在 `mcpServers` 部分添加：

```json
{
  "mcpServers": {
    "spss": {
      "command": "spss-mcp",
      "args": ["serve", "--transport", "stdio"],
      "disabled": false
    }
  }
}
```

**如果使用虚拟环境：**

```json
{
  "mcpServers": {
    "spss": {
      "command": "C:\\Users\\你的用户名\\SPSS-MCP\\.venv\\Scripts\\spss-mcp.exe",
      "args": ["serve", "--transport", "stdio"],
      "disabled": false
    }
  }
}
```

**获取完整路径：**
```bash
# Windows CMD
where spss-mcp

# Windows PowerShell
(Get-Command spss-mcp).Source

# 或使用自动生成
spss-mcp setup-info
```

#### 3. 重启 Claude Code

配置保存后必须重启才能生效。

#### 4. 验证全局注册

在任意目录打开 Claude Code，检查右下角或侧边栏：
- ✅ 应该看到 `spss` 服务器已连接

---

## 局部注册

### 适用场景

- ✅ 仅在特定项目中使用 SPSS
- ✅ 不同项目使用不同的 SPSS 版本
- ✅ 测试新配置而不影响全局设置

### 配置步骤

#### 1. 创建项目配置文件

在项目根目录创建：
```
项目目录/
└── .claude/
    └── settings.local.json
```

**Windows CMD:**
```cmd
mkdir .claude
echo {} > .claude\settings.local.json
```

**Windows PowerShell:**
```powershell
New-Item -ItemType Directory -Force .claude
New-Item -ItemType File -Force .claude\settings.local.json
```

#### 2. 编辑局部配置

`.claude/settings.local.json` 内容：

```json
{
  "mcpServers": {
    "spss": {
      "command": "spss-mcp",
      "args": ["serve", "--transport", "stdio"],
      "env": {
        "SPSS_INSTALL_PATH": "C:\\Program Files\\IBM\\SPSS Statistics\\31",
        "SPSS_TIMEOUT": "120"
      }
    }
  }
}
```

#### 3. 配置优先级

```
局部配置 > 全局配置
```

如果同时存在全局和局部配置，局部配置会覆盖全局配置。

#### 4. 验证局部注册

在项目目录打开 Claude Code：
- ✅ 应该使用局部配置的 SPSS 路径
- ✅ 其他项目不受影响

---

## 系统配置

### SPSS 路径配置

#### 方式 1：环境变量（推荐）

在 MCP 配置中添加 `env` 字段：

```json
{
  "mcpServers": {
    "spss": {
      "command": "spss-mcp",
      "args": ["serve", "--transport", "stdio"],
      "env": {
        "SPSS_INSTALL_PATH": "C:\\Program Files\\IBM\\SPSS Statistics\\31",
        "SPSS_TIMEOUT": "120",
        "SPSS_RESULTS_DIR": "C:\\Users\\你的用户名\\spss_results"
      }
    }
  }
}
```

#### 方式 2：.env 文件

在项目根目录创建 `.env` 文件：

```ini
# SPSS 安装路径（必需，如果自动检测失败）
SPSS_INSTALL_PATH=C:\Program Files\IBM\SPSS Statistics\31

# 超时时间（秒，默认 120）
SPSS_TIMEOUT=120

# 临时工作目录（默认 %TEMP%\spss-mcp）
SPSS_TEMP_DIR=%TEMP%\spss-mcp

# 持久化输出目录（默认 %TEMP%\spss-mcp\results）
SPSS_RESULTS_DIR=%TEMP%\spss-mcp\results

# 强制文件模式（1 = 仅使用文件工具，不调用 SPSS）
SPSS_NO_SPSS=0
```

#### 配置优先级

```
MCP env 配置 > .env 文件 > 自动检测
```

---

## 环境变量配置

### 可用环境变量

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `SPSS_INSTALL_PATH` | SPSS 安装目录 | 自动检测 | `C:\Program Files\IBM\SPSS Statistics\31` |
| `SPSS_TIMEOUT` | 分析超时时间（秒） | `120` | `300` |
| `SPSS_TEMP_DIR` | 临时工作目录 | `%TEMP%\spss-mcp` | `C:\temp\spss` |
| `SPSS_RESULTS_DIR` | 输出文件目录 | `%TEMP%\spss-mcp\results` | `C:\spss_output` |
| `SPSS_NO_SPSS` | 强制文件模式 | `0` | `1` |

### 配置示例

#### 示例 1：标准配置

```json
{
  "mcpServers": {
    "spss": {
      "command": "spss-mcp",
      "args": ["serve", "--transport", "stdio"],
      "env": {
        "SPSS_INSTALL_PATH": "C:\\Program Files\\IBM\\SPSS Statistics\\31"
      }
    }
  }
}
```

#### 示例 2：自定义输出目录

```json
{
  "mcpServers": {
    "spss": {
      "command": "spss-mcp",
      "args": ["serve", "--transport", "stdio"],
      "env": {
        "SPSS_INSTALL_PATH": "C:\\Program Files\\IBM\\SPSS Statistics\\31",
        "SPSS_RESULTS_DIR": "D:\\Projects\\SPSS_Results"
      }
    }
  }
}
```

#### 示例 3：增加超时时间

```json
{
  "mcpServers": {
    "spss": {
      "command": "spss-mcp",
      "args": ["serve", "--transport", "stdio"],
      "env": {
        "SPSS_TIMEOUT": "300"
      }
    }
  }
}
```

#### 示例 4：多版本 SPSS 切换

**项目 A（使用 SPSS 31）：**
```json
// 项目A/.claude/settings.local.json
{
  "mcpServers": {
    "spss": {
      "command": "spss-mcp",
      "args": ["serve", "--transport", "stdio"],
      "env": {
        "SPSS_INSTALL_PATH": "C:\\Program Files\\IBM\\SPSS Statistics\\31"
      }
    }
  }
}
```

**项目 B（使用 SPSS 29）：**
```json
// 项目B/.claude/settings.local.json
{
  "mcpServers": {
    "spss": {
      "command": "spss-mcp",
      "args": ["serve", "--transport", "stdio"],
      "env": {
        "SPSS_INSTALL_PATH": "C:\\Program Files\\IBM\\SPSS Statistics\\29"
      }
    }
  }
}
```

---

## 配置验证

### 1. 检查 MCP 服务器状态

在 Claude Code 中输入：
```
请检查 SPSS-MCP 服务器状态
```

**预期输出：**
```
✓ pyreadstat: 1.2.x
✓ pandas: 2.x.x
✓ SPSS: C:\Program Files\IBM\SPSS Statistics\31\stats.exe
✓ SPSS Python: C:\Program Files\IBM\SPSS Statistics\31\Python3\python.exe
✓ 可用工具: 36 个
```

### 2. 命令行验证

```bash
# 检查安装状态
spss-mcp status

# 生成配置代码
spss-mcp setup-info

# 查看版本
spss-mcp --version
```

### 3. 测试分析功能

创建测试数据文件或使用现有 `.sav` 文件：

```
请读取 data.sav 文件的变量列表
```

如果返回变量信息，说明配置成功。

---

## 🔧 高级配置

### 禁用 MCP 服务器

临时禁用而不删除配置：

```json
{
  "mcpServers": {
    "spss": {
      "command": "spss-mcp",
      "args": ["serve", "--transport", "stdio"],
      "disabled": true  // ← 添加此行
    }
  }
}
```

### 调试模式

启用详细日志输出：

```json
{
  "mcpServers": {
    "spss": {
      "command": "spss-mcp",
      "args": ["serve", "--transport", "stdio", "--log-level", "debug"],
      "env": {
        "SPSS_DEBUG": "1"
      }
    }
  }
}
```

### 自定义工作目录

指定 MCP 服务器的工作目录：

```json
{
  "mcpServers": {
    "spss": {
      "command": "spss-mcp",
      "args": ["serve", "--transport", "stdio"],
      "cwd": "C:\\Projects\\SPSS-MCP"
    }
  }
}
```

---

## 🚨 常见配置问题

### 问题 1：配置不生效

**症状：** 修改配置后 MCP 服务器仍使用旧配置

**解决方案：**
1. 确认配置文件已保存
2. **完全重启** Claude Code（不是重新加载窗口）
3. 检查 JSON 格式是否正确（逗号、引号）

### 问题 2：路径包含空格

**症状：** SPSS 路径包含空格导致无法识别

**解决方案：**
使用双反斜杠或正斜杠：

```json
// 正确 ✓
"SPSS_INSTALL_PATH": "C:\\Program Files\\IBM\\SPSS Statistics\\31"

// 正确 ✓
"SPSS_INSTALL_PATH": "C:/Program Files/IBM/SPSS Statistics/31"

// 错误 ✗
"SPSS_INSTALL_PATH": "C:\Program Files\IBM\SPSS Statistics\31"
```

### 问题 3：虚拟环境路径

**症状：** 使用虚拟环境时找不到 spss-mcp 命令

**解决方案：**
使用完整路径：

```bash
# 1. 激活虚拟环境
.venv\Scripts\activate

# 2. 获取完整路径
where spss-mcp
# 输出: C:\Projects\SPSS-MCP\.venv\Scripts\spss-mcp.exe

# 3. 在配置中使用完整路径
```

### 问题 4：权限问题

**症状：** 无法写入输出目录

**解决方案：**
1. 确保输出目录有写入权限
2. 或使用用户目录：
```json
"SPSS_RESULTS_DIR": "%USERPROFILE%\\spss_results"
```

---

## 📖 配置模板

### 最小配置（自动检测 SPSS）

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

### 标准配置（指定 SPSS 路径）

```json
{
  "mcpServers": {
    "spss": {
      "command": "spss-mcp",
      "args": ["serve", "--transport", "stdio"],
      "env": {
        "SPSS_INSTALL_PATH": "C:\\Program Files\\IBM\\SPSS Statistics\\31",
        "SPSS_TIMEOUT": "120"
      }
    }
  }
}
```

### 完整配置（所有选项）

```json
{
  "mcpServers": {
    "spss": {
      "command": "spss-mcp",
      "args": ["serve", "--transport", "stdio"],
      "env": {
        "SPSS_INSTALL_PATH": "C:\\Program Files\\IBM\\SPSS Statistics\\31",
        "SPSS_TIMEOUT": "300",
        "SPSS_TEMP_DIR": "C:\\temp\\spss-mcp",
        "SPSS_RESULTS_DIR": "C:\\Users\\你的用户名\\spss_results",
        "SPSS_NO_SPSS": "0"
      },
      "disabled": false,
      "cwd": "C:\\Projects\\SPSS-MCP"
    }
  }
}
```

---

## 🔗 相关文档

- **快速开始**: [QUICK_START.md](QUICK_START.md)
- **连接教程**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **流程图解**: [CONNECTION_DIAGRAM.md](CONNECTION_DIAGRAM.md)
- **完整文档**: [README.md](README.md)

---

## 💡 配置建议

1. **新手用户**: 使用全局注册 + 自动检测（最小配置）
2. **多项目用户**: 使用全局注册 + 局部 .env 文件
3. **多版本 SPSS**: 使用局部注册，每个项目指定不同版本
4. **团队协作**: 将 `.env.example` 提交到版本控制，`.env` 加入 `.gitignore`

---

## 📞 获取帮助

- **问题反馈**: https://github.com/Exekiel179/SPSS-MCP/issues
- **配置生成**: 运行 `spss-mcp setup-info`
- **状态检查**: 运行 `spss-mcp status`
