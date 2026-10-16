import sys

import pytest

from scripts import check_env

VALID_STATUSES = {check_env.PASS, check_env.FAIL, check_env.WARN, check_env.INFO}


@pytest.mark.slow
def test_run_checks_returns_well_formed_results_without_raising():
    results = check_env.run_checks()

    assert results
    assert all(r.status in VALID_STATUSES for r in results)
    assert all(r.name for r in results)


def test_exit_code_is_1_when_a_required_check_fails():
    results = [check_env.Result("needed", check_env.FAIL, "boom")]

    assert check_env.exit_code(results) == 1


def test_exit_code_is_0_when_only_optional_checks_fail():
    results = [
        check_env.Result("optional", check_env.FAIL, "meh", required=False),
        check_env.Result("fine", check_env.PASS),
    ]

    assert check_env.exit_code(results) == 0


def test_missing_module_reports_fail_with_hint_when_required():
    result = check_env.check_import(
        "ghost", "module_that_does_not_exist_xyz", hint="pip install ghost"
    )

    assert result.status == check_env.FAIL
    assert "pip install ghost" in result.detail


def test_missing_optional_module_is_only_a_warning():
    result = check_env.check_import("ghost", "module_that_does_not_exist_xyz", required=False)

    assert result.status == check_env.WARN
    assert check_env.exit_code([result]) == 0


def test_missing_binary_reports_fail_with_fix():
    result = check_env.check_binary("ghost", "binary_that_does_not_exist_xyz", hint="install it")

    assert result.status == check_env.FAIL
    assert "install it" in result.detail


def test_format_results_lists_failed_required_checks():
    results = [check_env.Result("needed", check_env.FAIL, "boom")]

    text = check_env.format_results(results)

    assert "[FAIL] needed" in text
    assert "1 required check(s) failed" in text


def test_main_passes_the_deep_flag_to_run_checks(monkeypatch):
    seen = {}

    def fake_run_checks(deep=False):
        seen["deep"] = deep
        return [check_env.Result("x", check_env.PASS)]

    monkeypatch.setattr(check_env, "run_checks", fake_run_checks)

    assert check_env.main(["--deep"]) == 0
    assert seen["deep"] is True
    assert check_env.main([]) == 0
    assert seen["deep"] is False


def test_whisper_deep_check_fails_cleanly_when_library_is_missing(monkeypatch):
    # a None entry in sys.modules makes `import faster_whisper` raise ImportError
    monkeypatch.setitem(sys.modules, "faster_whisper", None)

    result = check_env.check_whisper_transcribe()

    assert result.status == check_env.FAIL
    assert result.required
    assert "faster-whisper not importable" in result.detail
