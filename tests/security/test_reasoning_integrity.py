import pytest
from backend.reasoning.diagnosis.evidence_collector import EvidenceCollector


def test_hallucination_resistance(tmp_path):
    """Kiểm định khả năng chống ảo giác khi bị inject file phụ thuộc không tồn tại (Hallucination Resistance)."""
    collector = EvidenceCollector(workspace_dir=str(tmp_path), experience_dir=str(tmp_path / "exp"))
    
    # Inject file không tồn tại
    evidence = collector.collect_evidence(
        error_filepath="non_existent_payment_service.py",
        error_message="NameError: name 'stripe' is not defined"
    )

    # Hệ thống không được bịa đặt bằng chứng giả lập cho file không tồn tại
    assert isinstance(evidence, list)
    assert len(evidence) == 0
