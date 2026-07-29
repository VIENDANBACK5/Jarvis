import os
import pytest
import shutil
import asyncio

from backend.tools.aci.coding_tools import CodingTools


def is_docker_available() -> bool:
    return shutil.which("docker") is not None


def test_aci_list_files(tmp_path):
    # Tạo cấu trúc file tạm
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print(1)\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("def test(): assert 1 == 1\n", encoding="utf-8")
    (tmp_path / "ignored.tmp").write_text("temp", encoding="utf-8")

    aci = CodingTools(str(tmp_path))
    files = aci.list_files()

    assert "src/main.py" in files
    assert "tests/test_main.py" in files
    # Lọc bỏ file .tmp nếu scanner loại trừ hoặc kiểm tra xem extension py được quét
    assert "ignored.tmp" in files  # vì scanner của chúng ta chỉ loại trừ thư mục, không loại trừ file .tmp mặc định
    

def test_aci_search_code(tmp_path):
    (tmp_path / "main.py").write_text(
        "class AuthService:\n"
        "    def login(self):\n"
        "        pass\n",
        encoding="utf-8"
    )

    aci = CodingTools(str(tmp_path))
    
    # 1. Tìm kiếm chuỗi thường (case-insensitive)
    results = aci.search_code("authservice")
    assert len(results) == 1
    assert results[0]["filepath"] == "main.py"
    assert results[0]["line_number"] == 1
    assert "class AuthService:" in results[0]["line_content"]

    # 2. Tìm kiếm regex
    results_re = aci.search_code(r"def \w+\(self\)", is_regex=True)
    assert len(results_re) == 1
    assert results_re[0]["line_number"] == 2
    assert "def login(self):" in results_re[0]["line_content"]


def test_aci_open_file(tmp_path):
    (tmp_path / "main.py").write_text(
        "line one\n"
        "line two\n"
        "line three\n",
        encoding="utf-8"
    )

    aci = CodingTools(str(tmp_path))

    # 1. Đọc toàn bộ file
    content = aci.open_file("main.py")
    assert "1: line one\n" in content
    assert "2: line two\n" in content
    assert "3: line three\n" in content

    # 2. Đọc dòng 2 đến 3
    content_sub = aci.open_file("main.py", start_line=2, end_line=3)
    assert "1: line one" not in content_sub
    assert "2: line two\n" in content_sub
    assert "3: line three\n" in content_sub


def test_aci_edit_file_success_and_syntax_error(tmp_path):
    file_path = tmp_path / "app.py"
    file_path.write_text("def run():\n    print('Running')\n", encoding="utf-8")

    aci = CodingTools(str(tmp_path))

    # 1. Edit thành công
    patch_success = (
        "@@ -1,2 +1,2 @@\n"
        " def run():\n"
        "-    print('Running')\n"
        "+    print('Jarvis ACI')\n"
    )
    res = aci.edit_file("app.py", patch_success)
    assert res["success"] is True
    assert "Jarvis ACI" in file_path.read_text(encoding="utf-8")

    # 2. Edit lỗi cú pháp (chặn không cho ghi đè)
    patch_syntax_error = (
        "@@ -1,2 +1,2 @@\n"
        " def run():\n"
        "-    print('Jarvis ACI')\n"
        "+    print('Error\n"  # Lỗi thiếu ngoặc đóng
    )
    res_err = aci.edit_file("app.py", patch_syntax_error)
    assert res_err["success"] is False
    assert "lỗi cú pháp" in res_err["error"].lower()
    # Kiểm tra file không bị hỏng, vẫn giữ nguyên nội dung cũ
    assert "Jarvis ACI" in file_path.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_aci_run_test(tmp_path):
    if not is_docker_available():
        pytest.skip("Bỏ qua test vì Docker không khả dụng.")

    # Tạo unit test thành công tương thích cả pytest và unittest
    (tmp_path / "test_simple.py").write_text(
        "import unittest\n"
        "class TestSimple(unittest.TestCase):\n"
        "    def test_ok(self):\n"
        "        self.assertEqual(1, 1)\n",
        encoding="utf-8"
    )

    aci = CodingTools(str(tmp_path))
    res = await aci.run_test("test_simple.py")

    assert res["exit_code"] == 0
    # Kết quả stdout chứa thông thông tin passed hoặc OK
    combined_out = f"{res['stdout']}\n{res['stderr']}"
    assert "OK" in combined_out or "passed" in combined_out or "passed" in res["stdout"]
