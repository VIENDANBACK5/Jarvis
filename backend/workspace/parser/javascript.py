import re
from typing import List, Dict, Any, Optional


class JavaScriptSymbolParser:
    """Bộ phân tích cú pháp ký hiệu JavaScript cơ bản dùng Regex."""

    def __init__(self):
        # Pattern tìm class: class Name
        self.class_pat = re.compile(r'^\s*(?:export\s+)?class\s+(\w+)')
        
        # Pattern tìm function: function name(...), async function name(...)
        self.func_pat = re.compile(r'^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(')
        
        # Pattern tìm arrow function: const name = (...) =>, let name = async(...) =>
        self.arrow_pat = re.compile(r'^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(.*?\)\s*=>')

    def parse_code(self, code: str) -> List[Dict[str, Any]]:
        symbols = []
        lines = code.splitlines()

        for idx, line in enumerate(lines, 1):
            # 1. Tìm Class
            class_match = self.class_pat.match(line)
            if class_match:
                symbols.append({
                    "name": class_match.group(1),
                    "type": "class",
                    "start_line": idx,
                    "end_line": idx,
                    "docstring": "",
                    "parent": None
                })
                continue

            # 2. Tìm Function tiêu chuẩn
            func_match = self.func_pat.match(line)
            if func_match:
                symbols.append({
                    "name": func_match.group(1),
                    "type": "function",
                    "start_line": idx,
                    "end_line": idx,
                    "docstring": "",
                    "parent": None
                })
                continue

            # 3. Tìm Arrow Function
            arrow_match = self.arrow_pat.match(line)
            if arrow_match:
                symbols.append({
                    "name": arrow_match.group(1),
                    "type": "function",
                    "start_line": idx,
                    "end_line": idx,
                    "docstring": "",
                    "parent": None
                })

        return symbols

    def parse_imports(self, code: str) -> List[str]:
        """Trích xuất danh sách các module được import trong file JavaScript/TypeScript."""
        imports = []
        # Match standard ES6 imports: import ... from 'module' or import 'module'
        es6_import = re.compile(r'(?:import\s+(?:.*?\s+from\s+)?[\'"](.*?)[\'"])|(?:import\s+[\'"](.*?)[\'"])')
        # Match CommonJS require: require('module')
        cjs_require = re.compile(r'require\s*\(\s*[\'"](.*?)[\'"]\s*\)')
        
        for line in code.splitlines():
            m1 = es6_import.search(line)
            if m1:
                val = m1.group(1) or m1.group(2)
                if val:
                    imports.append(val)
                continue
                
            m2 = cjs_require.search(line)
            if m2:
                val = m2.group(1)
                if val:
                    imports.append(val)
        return imports
