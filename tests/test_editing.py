import pytest
from backend.editing.patch_applier import PatchApplier
from backend.editing.patch_validator import PatchValidator
from backend.editing.diff_analyzer import DiffAnalyzer


def test_patch_applier_success():
    original = (
        "def say_hello():\n"
        "    print('Hello World')\n"
        "    return True\n"
    )
    
    # Unified diff thay đổi dòng print
    patch = (
        "@@ -1,3 +1,3 @@\n"
        " def say_hello():\n"
        "-    print('Hello World')\n"
        "+    print('Hello Jarvis')\n"
        "     return True\n"
    )

    success, result, err = PatchApplier.apply_patch(original, patch)
    assert success is True
    assert err is None
    assert "print('Hello Jarvis')" in result
    assert "print('Hello World')" not in result


def test_patch_applier_mismatch():
    original = (
        "def say_hello():\n"
        "    print('Hello World')\n"
        "    return True\n"
    )
    
    # Ngữ cảnh mong đợi không khớp (print('Hello Universe'))
    patch = (
        "@@ -1,3 +1,3 @@\n"
        " def say_hello():\n"
        "-    print('Hello Universe')\n"
        "+    print('Hello Jarvis')\n"
        "     return True\n"
    )

    success, result, err = PatchApplier.apply_patch(original, patch)
    assert success is False
    assert "Không khớp ngữ cảnh" in err


def test_patch_validator_syntax():
    original = (
        "def run():\n"
        "    pass\n"
    )
    
    # Patch gây lỗi cú pháp (thiếu đóng ngoặc)
    patch_error = (
        "@@ -1,2 +1,2 @@\n"
        " def run():\n"
        "-    pass\n"
        "+    print('Syntax Error\n" # Missing quote and parenthesis
    )

    is_valid, err = PatchValidator.validate_patch(original, patch_error, filename="test.py")
    assert is_valid is False
    assert "lỗi cú pháp" in err.lower()


def test_diff_analyzer():
    original = "x = 1\ny = 2\n"
    modified = "x = 1\ny = 3\n"
    
    diff = DiffAnalyzer.get_unified_diff(original, modified, "math.py")
    assert "a/math.py" in diff
    assert "b/math.py" in diff
    assert "-y = 2" in diff
    assert "+y = 3" in diff
