"""Make pip-installed NVIDIA DLLs visible on Windows.

CTranslate2 4.5+ (used by faster-whisper) needs cuDNN 9 and cuBLAS at runtime and does
not bundle them. The pip packages ``nvidia-cudnn-cu12`` and ``nvidia-cublas-cu12`` put the
DLLs in ``site-packages/nvidia/<package>/bin``, which Windows does not search by default.

Call :func:`add_nvidia_dll_dirs` once, before the first import of ``faster_whisper`` or
``ctranslate2``. It registers the folders with ``os.add_dll_directory`` and also puts them
on this process's ``PATH`` (some native loaders only honour ``PATH``). It affects only the
current process and does nothing on other operating systems.
"""

from __future__ import annotations

import contextlib
import os
import site
import sys
import sysconfig
from pathlib import Path

_registered: set[Path] = set()
_handles: list[object] = []  # keep the objects returned by os.add_dll_directory alive


def find_nvidia_bin_dirs(site_packages: Path) -> list[Path]:
    """Return ``site_packages/nvidia/*/bin`` folders that exist, sorted for stable output."""
    nvidia_root = site_packages / "nvidia"
    if not nvidia_root.is_dir():
        return []
    return sorted(path for path in nvidia_root.glob("*/bin") if path.is_dir())


def default_site_packages() -> list[Path]:
    """Site-packages folders of the running interpreter (virtual environment aware)."""
    paths = sysconfig.get_paths()
    candidates = [paths.get("purelib", ""), paths.get("platlib", "")]
    with contextlib.suppress(AttributeError):  # very old virtualenv builds lack getsitepackages
        candidates.extend(site.getsitepackages())

    unique: list[Path] = []
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if path.is_dir() and path not in unique:
            unique.append(path)
    return unique


def add_nvidia_dll_dirs(site_packages_dirs: list[Path] | None = None) -> list[Path]:
    """Register NVIDIA DLL folders for this process and return them.

    ``site_packages_dirs`` is only for tests; by default the interpreter's own
    site-packages folders are searched.
    """
    if sys.platform != "win32":
        return []

    roots = site_packages_dirs if site_packages_dirs is not None else default_site_packages()

    found: list[Path] = []
    for root in roots:
        for directory in find_nvidia_bin_dirs(root):
            if directory in found:
                continue
            found.append(directory)
            if directory in _registered:
                continue
            _handles.append(os.add_dll_directory(str(directory)))
            os.environ["PATH"] = f"{directory}{os.pathsep}{os.environ.get('PATH', '')}"
            _registered.add(directory)
    return found
