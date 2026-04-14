# SPSS-MCP 快速开始

> 3 步完成部署，5 分钟开始使用

---

## 🚀 一键安装（推荐）

### Windows 用户

1. **克隆项目**
```bash
git clone https://github.com/Exekiel179/SPSS-MCP.git
cd SPSS-MCP
```

2. **运行安装脚本**
```bash
# 双击运行（或在命令行执行）
install.bat
```

3. **重启 Claude Code**

完成！现在可以在 Claude Code 中使用自然语言进行 SPSS 分析了。

---

## 📝 手动安装

如果一键安装失败，按以下步骤操作：

### 步骤 1：安装 SPSS-MCP

```bash
pip install -e .
```

验证安装：
```bash
spss-mcp status
```

### 步骤 2：配置 Claude Code

1. 打开 Claude Code，按 `Ctrl + ,`
2. 搜索 `mcpServers`
3. 添加以下配置：

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

4. 保存并重启 Claude Code

### 步骤 3：验证连接

在 Claude Code 中输入：
```
检查 SPSS 状态
```

如果看到版本信息，说明配置成功！

---

## ⚙️ 可选配置

### SPSS 路径未检测到？

创建 `.env` 文件：
```ini
SPSS_INSTALL_PATH=C:\Program Files\IBM\SPSS Statistics\31
```

### 分析超时？

在 `.env` 中增加超时：
```ini
SPSS_TIMEOUT=300
```

---

## 💡 开始使用

直接用中文描述分析需求：

```
请对 data.sav 进行描述性统计
```

```
分析 age 和 income 的相关性
```

```
用 t 检验比较男女收入差异
```

---

## 📖 完整文档

详细配置和所有功能请查看 [README.md](README.md)

## 🆘 遇到问题？

- 运行 `spss-mcp status` 检查状态
- 查看 [README.md](README.md) 的故障排除部分
- 提交问题：https://github.com/Exekiel179/SPSS-MCP/issues
