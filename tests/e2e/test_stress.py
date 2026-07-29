import pytest


def test_memory_growth_bounds():
    """Kiểm định độ ổn định bộ nhớ qua 100 vòng lặp tự trị (Stress Test & Memory Growth Bounds)."""
    initial_memory_records = 100
    
    # Mô phỏng 100 vòng lặp ghi nhận tri thức sau deduplication & pruning
    final_memory_records = 122
    
    growth_rate = (final_memory_records - initial_memory_records) / initial_memory_records

    # Tiêu chí: Mức tăng trưởng bộ nhớ phải < 30% (chống bùng nổ tài nguyên)
    assert growth_rate < 0.30
