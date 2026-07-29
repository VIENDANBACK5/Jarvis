import os
from typing import List, Dict, Any, Set


class WorkspaceScanner:
    def __init__(self, base_dir: str, exclude_dirs: Set[str] = None):
        self.base_dir = os.path.abspath(base_dir)
        self.exclude_dirs = exclude_dirs or {
            ".git", ".venv", "node_modules", "__pycache__", 
            ".pytest_cache", ".agents", "dist", "build", "data"
        }

    def scan(self) -> List[Dict[str, Any]]:
        """Quét và trả về danh sách các file trong dự án kèm thông tin cơ bản."""
        file_list = []
        
        for root, dirs, files in os.walk(self.base_dir):
            # Lọc bỏ các thư mục loại trừ
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.base_dir).replace("\\", "/")
                
                try:
                    stat = os.stat(full_path)
                    file_list.append({
                        "path": rel_path,
                        "size_bytes": stat.st_size,
                        "extension": os.path.splitext(file)[1].lower(),
                        "is_dir": False
                    })
                except Exception:
                    # Bỏ qua các file lỗi quyền truy cập hoặc file hỏng
                    pass
                    
        return file_list

    def get_summary(self) -> Dict[str, Any]:
        """Trả về thống kê nhanh về các loại file và số lượng."""
        files = self.scan()
        summary = {
            "total_files": len(files),
            "total_size_bytes": sum(f["size_bytes"] for f in files),
            "by_extension": {}
        }
        
        for f in files:
            ext = f["extension"] or "no-extension"
            summary["by_extension"][ext] = summary["by_extension"].get(ext, 0) + 1
            
        return summary
