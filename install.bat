@echo off
chcp 65001 >nul
echo ========================================
echo   SPSS-MCP 一键安装脚本
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] 安装 SPSS-MCP...
pip install -e . >nul 2>&1
if errorlevel 1 (
    echo [错误] 安装失败，请检查网络连接或 pip 配置
    pause
    exit /b 1
)
echo ✓ 安装完成

echo.
echo [2/4] 验证安装...
spss-mcp status
if errorlevel 1 (
    echo [警告] SPSS 未检测到，仅文件工具可用
    echo 如需使用分析工具，请确保已安装 IBM SPSS Statistics
)

echo.
echo [3/4] 安装 Claude Code 技能...
set SKILLS_DIR=%USERPROFILE%\.claude\skills
if not exist "%SKILLS_DIR%" mkdir "%SKILLS_DIR%"
xcopy /E /I /Y skills\spss-analyst "%SKILLS_DIR%\spss-analyst" >nul 2>&1
xcopy /E /I /Y skills\spss-mcp-guard "%SKILLS_DIR%\spss-mcp-guard" >nul 2>&1
echo ✓ 技能已安装到 %SKILLS_DIR%

echo.
echo [4/4] 自动配置 Claude Code...
spss-mcp configure-claude
if errorlevel 1 (
    echo [错误] 自动配置失败，请手动执行: spss-mcp configure-claude
    pause
    exit /b 1
)
echo ✓ Claude Code 配置已更新

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 下一步：
echo 1. 重启 Claude Code
echo 2. 在 Claude Code 中输入：检查 SPSS 状态
echo.
echo 详细文档：README.md 或 QUICK_START.md
echo.
pause
