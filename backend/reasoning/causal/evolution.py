import os
import json
import logging
import math
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CausalEvolution:
    @staticmethod
    def update_causal_weights(
        graph_file_path: str,
        symptom: str,
        cause: str,
        success: bool,
        context: Dict[str, Any]
    ) -> bool:
        """Cập nhật tịnh tiến trọng số của cạnh đồ thị nhân quả cấu trúc dựa trên kết quả giải quyết task."""
        if not os.path.exists(graph_file_path):
            # Tạo file trống mặc định nếu chưa có
            os.makedirs(os.path.dirname(graph_file_path), exist_ok=True)
            with open(graph_file_path, "w", encoding="utf-8") as f:
                json.dump({"links": []}, f)

        try:
            with open(graph_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            links = data.get("links", [])
            matched = False

            # Quét tìm cạnh nhân quả phù hợp
            for l in links:
                if l.get("symptom") == symptom and l.get("cause") == cause:
                    old_confidence = l.get("confidence", 0.5)
                    # Cập nhật tịnh tiến
                    if success:
                        new_confidence = min(0.95, old_confidence + 0.05)
                    else:
                        new_confidence = max(0.05, old_confidence - 0.05)
                    
                    l["confidence"] = round(new_confidence, 3)
                    l["context"] = context  # Lưu ngữ cảnh cập nhật
                    matched = True
                    break

            if not matched:
                # Thêm cạnh mới nếu chưa có
                links.append({
                    "symptom": symptom,
                    "cause": cause,
                    "confidence": 0.55 if success else 0.45,
                    "context": context
                })

            data["links"] = links
            with open(graph_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.info(f"CausalEvolution: Updated link '{symptom}' -> '{cause}' | Success: {success}")
            return True
        except Exception as e:
            logger.error(f"CausalEvolution: Lỗi khi tiến hóa đồ thị nhân quả: {str(e)}")
            return False
