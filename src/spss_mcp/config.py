"""
Configuration loading and SPSS installation detection for SPSS MCP.
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load .env from project root first and let repo-local settings override inherited shell values.
load_dotenv(_PROJECT_ROOT / ".env", override=True)
load_dotenv()


def _find_spss_via_registry() -> str | None:
    """Search Windows registry for IBM SPSS Statistics installation path."""
    if sys.platform != "win32":
        return None
    try:
        import winreg
        base_key = r"SOFTWARE\IBM\SPSS Statistics"
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(hive, base_key) as key:
                    i = 0
                    while True:
                        try:
                            version = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, version) as ver_key:
                                try:
                                    install_dir, _ = winreg.QueryValueEx(
                                        ver_key, "InstallationDirectory"
                                    )
                                    candidate = Path(install_dir) / "stats.exe"
                                    if candidate.exists():
                                        return str(candidate)
                                except FileNotFoundError:
                                    pass
                            i += 1
                        except OSError:
                            break
            except FileNotFoundError:
                continue
    except ImportError:
        pass
    return None


def _find_spss_via_filesystem() -> str | None:
    """Check common SPSS installation paths on Windows."""
    common_roots = [
        r"C:\Program Files\IBM\SPSS Statistics",
        r"C:\Program Files (x86)\IBM\SPSS Statistics",
        r"C:\spss",
        r"D:\spss",
        r"E:\spss",
    ]
    versions = list(range(20, 32))  # SPSS 20 through 31
    for root in common_roots:
        # Check versioned subdirectories (newest first)
        for v in reversed(versions):
            candidate = Path(root) / str(v) / "stats.exe"
            if candidate.exists():
                return str(candidate)
        # Check root directly
        candidate = Path(root) / "stats.exe"
        if candidate.exists():
            return str(candidate)
    return None


def get_spss_executable() -> str | None:
    """
    Return path to stats.exe, or None if SPSS is not installed / disabled.

    Detection order:
    1. SPSS_NO_SPSS env var (forces file-only mode)
    2. SPSS_INSTALL_PATH env var (explicit path to install dir)
    3. Windows registry
    4. Common filesystem paths
    5. PATH scan
    """
    if os.environ.get("SPSS_NO_SPSS", "0").strip() in ("1", "true", "yes"):
        return None

    # Explicit install path from env
    install_path = os.environ.get("SPSS_INSTALL_PATH", "").strip()
    if install_path:
        candidate = Path(install_path) / "stats.exe"
        if candidate.exists():
            return str(candidate)
        # Maybe they pointed directly at the exe
        if Path(install_path).name.lower() == "stats.exe" and Path(install_path).exists():
            return install_path

    # Registry
    found = _find_spss_via_registry()
    if found:
        return found

    # Filesystem
    found = _find_spss_via_filesystem()
    if found:
        return found

    # PATH
    found = shutil.which("stats")
    if found:
        return found

    return None


def get_spss_python() -> str | None:
    """Return path to the SPSS Python3 executable bundled with SPSS."""
    stats_exe = get_spss_executable()
    if not stats_exe:
        return None
    from pathlib import Path
    python_exe = Path(stats_exe).parent / "Python3" / "python.exe"
    if python_exe.exists():
        return str(python_exe)
    return None


def _get_positive_int_env(name: str, default: int) -> int:
    """Return a positive integer env var value or a default."""
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


def get_timeout() -> int:
    """Return SPSS analysis timeout in seconds (default 120)."""
    return _get_positive_int_env("SPSS_TIMEOUT", 120)


def get_startup_timeout() -> int:
    """
    Return SPSS engine startup timeout in seconds.

    Startup is often slower than a normal analysis request because SPSS may need
    to initialize licensing, Python integration, and the persistent XD engine.
    Default to 300 seconds unless explicitly overridden.
    """
    return _get_positive_int_env("SPSS_STARTUP_TIMEOUT", 300)


def get_runtime_config() -> dict:
    """Return the effective runtime configuration used for SPSS execution."""
    return {
        "timeout": get_timeout(),
        "startup_timeout": get_startup_timeout(),
        "temp_dir": str(get_temp_dir()),
        "results_dir": str(get_results_dir()),
        "spss_path": get_spss_executable(),
    }


def get_temp_dir() -> Path:
    """Return the directory for temporary SPSS files, creating it if needed."""
    default = Path(tempfile.gettempdir()) / "spss-mcp"
    temp_dir = Path(os.environ.get("SPSS_TEMP_DIR", str(default)))
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def get_results_dir() -> Path:
    """Return directory where persistent SPSS viewer output files (.spv) are saved."""
    default = get_temp_dir() / "results"
    out_dir = Path(os.environ.get("SPSS_RESULTS_DIR", str(default)))
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def detect_capabilities() -> dict:
    """
    Detect what capabilities are available on this machine.

    Returns a dict with:
        pyreadstat: bool
        spss: bool
        spss_path: str | None
        pyreadstat_version: str | None
        pandas_version: str | None
    """
    caps: dict = {
        "pyreadstat": False,
        "pyreadstat_version": None,
        "pandas_version": None,
        "spss": False,
        "spss_path": None,
    }

    try:
        import pyreadstat
        caps["pyreadstat"] = True
        caps["pyreadstat_version"] = getattr(pyreadstat, "__version__", "unknown")
    except ImportError:
        pass

    try:
        import pandas as pd
        caps["pandas_version"] = pd.__version__
    except ImportError:
        pass

    spss_exe = get_spss_executable()
    if spss_exe:
        caps["spss"] = True
        caps["spss_path"] = spss_exe
        # Check for SPSS Python3 (XD API) — preferred execution method
        from pathlib import Path
        spss_py = Path(spss_exe).parent / "Python3" / "python.exe"
        caps["spss_python"] = str(spss_py) if spss_py.exists() else None
    else:
        caps["spss_python"] = None

    return caps
