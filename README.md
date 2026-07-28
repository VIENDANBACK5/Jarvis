# 🤖 AI Agent Template (FastAPI + LangGraph)

Template dự án hoàn chỉnh để xây dựng AI Agent sử dụng LangGraph và FastAPI backend. Thích hợp làm nền tảng (boilerplate) cho các ứng dụng AI Agent khác nhau.

## 📁 Cấu trúc dự án

```
├── src/
│   ├── agents/          # 🧠 Định nghĩa LangGraph Agent
│   │   ├── graph.py     #    State Graph (nodes + edges)
│   │   ├── state.py     #    State schema (TypedDict)
│   │   ├── nodes/       #    Các Node xử lý logic
│   │   └── tools/       #    Công cụ của Agent (@tool)
│   ├── api/             # 🌐 FastAPI Backend
│   │   └── routes.py    #    API endpoints
│   ├── models/          # 📋 Pydantic schemas (Data validation)
│   ├── services/        # 🔧 Logic dịch vụ (LLM service, etc.)
│   ├── config.py        # ⚙️ Pydantic Settings (Quản lý biến môi trường)
│   └── main.py          # 🚀 Cổng chạy ứng dụng (App entrypoint)
├── tests/               # 🧪 Bộ kiểm thử (pytest)
├── docs/                # 📖 Tài liệu dự án & Kiến trúc
├── eval/                # 📊 Đánh giá chất lượng Agent
├── scripts/             # 🔌 Các script cấu hình nhanh
│   └── setup.sh         #    Script cài đặt môi trường tự động
├── Dockerfile           # 🐳 Dockerfile đa tầng (Multi-stage build)
├── docker-compose.yml   # 🐙 Docker Compose cấu hình dịch vụ
└── requirements.txt     # 📦 Dependencies của dự án
```

## ⚡ Bắt đầu nhanh (Quick Start)

### 1. Cài đặt môi trường
Chạy script setup tự động (dành cho Linux/macOS):
```bash
bash scripts/setup.sh
```
Hoặc cài đặt thủ công:
```bash
# Tạo môi trường ảo
python -m venv .venv
source .venv/bin/activate  # Trên Windows: .venv\Scripts\activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường
Sao chép `.env.example` thành `.env` và điền các API key của bạn:
```bash
cp .env.example .env
```

### 3. Chạy Development Server
```bash
uvicorn src.main:app --reload --port 8000
```
Truy cập Swagger UI tại: `http://localhost:8000/docs` để kiểm tra các API endpoints.

## 🛠 Tech Stack

| Thành phần | Công nghệ sử dụng |
|---|---|
| **AI Agent** | LangGraph + LangChain |
| **Backend** | FastAPI + Uvicorn |
| **LLM** | OpenAI GPT-4o / GPT-4o-mini (hoặc các provider khác) |
| **Database** | SQLite (Development) / PostgreSQL (Production) |
| **DevOps** | Docker + Docker Compose |
| **Testing** | Pytest |

## 🔗 Tài liệu tham khảo
* Tài liệu thiết kế kiến trúc: [ARCHITECTURE.md](ARCHITECTURE.md)
* Cẩm nang hướng dẫn kỹ thuật chi tiết: [docs/guide/](docs/guide/)
