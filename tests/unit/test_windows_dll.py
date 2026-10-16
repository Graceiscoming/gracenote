import os
import sys

import pytest

from app import windows_dll


@pytest.fixture(autouse=True)
def clean_module_state(monkeypatch):
    monkeypatch.setattr(windows_dll, "_registered", set())
    monkeypatch.setattr(windows_dll, "_handles", [])


def make_site_packages(tmp_path, *packages):
    site_packages = tmp_path / "site-packages"
    for package in packages:
        (site_packages / "nvidia" / package / "bin").mkdir(parents=True)
    return site_packages


def test_find_nvidia_bin_dirs_returns_existing_bin_folders_sorted(tmp_path):
    site_packages = make_site_packages(tmp_path, "cudnn", "cublas")
    (site_packages / "nvidia" / "no_bin_here").mkdir()

    found = windows_dll.find_nvidia_bin_dirs(site_packages)

    assert found == [
        site_packages / "nvidia" / "cublas" / "bin",
        site_packages / "nvidia" / "cudnn" / "bin",
    ]


def test_find_nvidia_bin_dirs_is_empty_without_nvidia_folder(tmp_path):
    assert windows_dll.find_nvidia_bin_dirs(tmp_path) == []


def test_add_nvidia_dll_dirs_does_nothing_outside_windows(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    site_packages = make_site_packages(tmp_path, "cudnn")
    path_before = os.environ.get("PATH", "")

    added = windows_dll.add_nvidia_dll_dirs([site_packages])

    assert added == []
    assert os.environ.get("PATH", "") == path_before


def test_add_nvidia_dll_dirs_registers_folders_and_updates_path_on_windows(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    registered = []
    monkeypatch.setattr(os, "add_dll_directory", registered.append, raising=False)
    monkeypatch.setenv("PATH", "original")
    site_packages = make_site_packages(tmp_path, "cudnn", "cublas")

    added = windows_dll.add_nvidia_dll_dirs([site_packages])

    expected = [
        site_packages / "nvidia" / "cublas" / "bin",
        site_packages / "nvidia" / "cudnn" / "bin",
    ]
    assert added == expected
    assert registered == [str(path) for path in expected]
    path_entries = os.environ["PATH"].split(os.pathsep)
    assert all(str(path) in path_entries for path in expected)
    assert path_entries[-1] == "original"


def test_add_nvidia_dll_dirs_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    registered = []
    monkeypatch.setattr(os, "add_dll_directory", registered.append, raising=False)
    monkeypatch.setenv("PATH", "original")
    site_packages = make_site_packages(tmp_path, "cudnn")

    first = windows_dll.add_nvidia_dll_dirs([site_packages])
    second = windows_dll.add_nvidia_dll_dirs([site_packages])

    assert first == second
    assert len(registered) == 1
    assert os.environ["PATH"].count(str(first[0])) == 1
