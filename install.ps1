# SPSS-MCP 一键安装脚本 (PowerShell)
# 使用方法：右键点击 -> 使用 PowerShell 运行

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SPSS-MCP 一键安装脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[✓] 检测到 Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[✗] 未检测到 Python，请先安装 Python 3.10 或更高版本" -ForegroundColor Red
    Write-Host "下载地址: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""
Write-Host "[1/4] 安装 SPSS-MCP..." -ForegroundColor Yellow
try {
    pip install -e . 2>&1 | Out-Null
    Write-Host "[✓] 安装完成" -ForegroundColor Green
} catch {
    Write-Host "[✗] 安装失败，请检查网络连接或 pip 配置" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""
Write-Host "[2/4] 验证安装..." -ForegroundColor Yellow
$statusOutput = spss-mcp status 2>&1
Write-Host $statusOutput
if ($statusOutput -notmatch "SPSS\s+:\s+✓") {
    Write-Host "[!] SPSS 未检测到，仅文件工具可用" -ForegroundColor Yellow
    Write-Host "如需使用分析工具，请确保已安装 IBM SPSS Statistics" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[3/4] 安装 Claude Code 技能..." -ForegroundColor Yellow
$skillsDir = "$env:USERPROFILE\.claude\skills"
if (-not (Test-Path $skillsDir)) {
    New-Item -ItemType Directory -Path $skillsDir -Force | Out-Null
}
Copy-Item -Recurse -Force "skills\spss-analyst" "$skillsDir\spss-analyst"
Copy-Item -Recurse -Force "skills\spss-mcp-guard" "$skillsDir\spss-mcp-guard"
Write-Host "[✓] 技能已安装到 $skillsDir" -ForegroundColor Green

Write-Host ""
Write-Host "[4/4] 生成 Claude Code 配置..." -ForegroundColor Yellow
Write-Host ""
Write-Host "请将以下配置添加到 Claude Code 设置中（Ctrl+, 打开设置）：" -ForegroundColor Cyan
Write-Host ""
spss-mcp setup-info

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "1. 重启 Claude Code" -ForegroundColor White
Write-Host "2. 在 Claude Code 中输入：请分析 data.sav 文件" -ForegroundColor White
Write-Host ""
Write-Host "详细文档：README.md 或 QUICK_START.md" -ForegroundColor Gray
Write-Host ""
Read-Host "按回车键退出"
