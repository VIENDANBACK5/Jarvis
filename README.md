<div align="center">

# 🤖 Jarvis: Autonomous Software Development Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: 145/145 Passed](https://img.shields.io/badge/Tests-145%2F145%20Passed-brightgreen.svg)]()
[![Architecture: Agent Core](https://img.shields.io/badge/Architecture-Real--Core%20%7C%20Claude--Code--Style-purple.svg)]()

*An open-source, production-ready autonomous AI software engineer capable of modifying real codebases, running shell commands, executing test suites, and interacting via CLI and Web Studio UI.*

[Quick Start](#-quickstart) • [Web Studio](#-web-studio-ui) • [Architecture](#-architecture) • [Tools & Safety](#-real-tools--safety-gate) • [Benchmarks](#-evaluation--benchmarks)

---

</div>

## 📖 Overview

**Jarvis** is an autonomous software development system engineered to solve complex engineering tasks end-to-end. Built on a modular architecture inspired by **Claude Code** and **OpenHands**, Jarvis bridges high-level reasoning with execution on local filesystems and shell environments.

Unlike simulated agent frameworks, Jarvis features a **Real Agent Core (`backend/core/`)** that reads real source files, executes actual shell commands, computes unified diffs for code edits, and enforces fine-grained user permission gating.

---

## ✨ Core Features

- ⚡ **Real Agent Core Execution Loop**: Multi-turn tool execution loop operating on physical disks and native shells.
- 🛡️ **Interactive Safety & Permission Gate**: Human-in-the-loop permission manager (`Allow Once`, `Always Allow`, `Deny`) with live **Diff Previews** for file edits and command validation.
- 💻 **Dual Front-End Interface**:
  - **CLI REPL (Claude Code Style)**: High-speed streaming terminal interface with syntax highlighting and token usage telemetry.
  - **Web Studio UI**: Single-Page Web Studio with live File Tree, token streaming, tool call cards, and permission modal.
- 🧠 **Adaptive Thinking Engine**: Dynamically calculates task complexity vectors (`files_changed`, `dependency_depth`, `failing_tests`, `architectural_risk`) and allocates token, tool, and reflection budgets accordingly.
- 🎭 **Cloud & Local Multi-LLM Routing**:
  - **Planning & Requirement Reasoning**: `GPT-4o` / `Claude 3.5 Sonnet`
  - **Code Editing & Review**: `Claude 3.5 Sonnet`
  - **Long Document RAG & Context**: `Gemini 1.5 Pro`
  - **Local Offline Execution**: `Qwen-2.5-Coder:7b/32b`, `DeepSeek-R1`, `Llama-3.3` via Ollama / vLLM.

---

## 🏗 System Architecture

```text
                                  User Interfaces
                        ┌────────────────┴────────────────┐
                        ▼                                 ▼
           Interactive CLI REPL                  Web Studio Single-Page UI
           (scripts/jarvis.ps1)                 (http://localhost:8000/ui/)
                        │                                 │
                        └────────────────┬────────────────┘
                                         ▼
                            FastAPI Server & WebSocket Gateway
                                   (/api/v1/agent & /ws)
                                         │
                                         ▼
                           Real Agent Core (backend/core/)
                                         │
    ┌────────────────────────────────────┼────────────────────────────────────┐
    ▼                                    ▼                                    ▼
Permission Broker                  Agent Loop Engine             Adaptive Thinking Engine
(Diff Preview Gate)               (Async Multi-Turn)            (Complexity & Budget Control)
    │                                    │                                    │
    ▼                                    ▼                                    ▼
Real Workspace Tools               LLM Backend Router            Multi-Model Providers
(read, write, edit,               (Unified Provider-Neutral)    (OpenAI, Anthropic, Gemini,
 bash, glob, grep, todo)                                          Ollama, vLLM)
```

---

## 🛠 Real Tools & Safety Gate

Jarvis comes equipped with 8 workspace-level execution tools:

| Tool Name | Type | Description | Safety Mode |
| :--- | :---: | :--- | :---: |
| `read_file` | Read | Reads real workspace files line-by-line with line numbers (`cat -n`). | Auto-Allowed |
| `write_file` | Write | Creates new files or overwrites existing files safely. | Requires Approval |
| `edit_file` | Edit | Applies precise target-string replacements with line diff previews. | Requires Approval |
| `bash` | Shell | Executes PowerShell or Bash commands in the workspace environment. | Requires Approval |
| `glob` | Search | Finds files matching glob patterns across the workspace tree. | Auto-Allowed |
| `grep` | Search | Performs Ripgrep / Regex pattern searches across project files. | Auto-Allowed |
| `todo` | State | Tracks task progress and status (`pending`, `in_progress`, `completed`). | Auto-Allowed |
| `registry` | System | Exports OpenAPI JSON Schemas for LLM Function Calling dispatch. | Internal |

---

## 🚀 Quickstart

### Prerequisites
- Python 3.10 or higher
- Git
- Docker (Optional, for containerized isolation)

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/mxrvs/Jarvis.git
cd Jarvis

# Set up virtual environment
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
# Cloud Providers
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AQ.Ab8...

# Local Ollama Provider (Optional)
OLLAMA_BASE_URL=http://localhost:11434/v1
```

---

## 💻 Usage

### Option A: Interactive Terminal REPL (Claude Code Style)

Run Jarvis directly in your terminal to work on the current repository:

```powershell
# Interactive REPL Session
.\scripts\jarvis.ps1

# Or run a single task non-interactively:
python -m backend.cli.agent_cli --print "Implement a Fibonacci function in utils.py and run pytest"
```

### Option B: Web Studio UI (OpenHands Style)

Start the Jarvis FastAPI backend:

```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

Open your browser and navigate to:
👉 **[http://localhost:8000/ui/](http://localhost:8000/ui/)**

Features included in the Web Studio:
- Live Workspace File Tree
- Real-time Prose & Thinking Token Streaming
- Interactive Permission Requests with Code Diffs
- Session State Persistence & Interrupt Controls

---

## 🧪 Evaluation & Verification

Jarvis includes a comprehensive unit and integration test suite covering tool execution, permission brokers, adaptive complexity routing, and agent turn loops.

Run the test suite:

```bash
pytest
```

```text
======================= 145 passed, 1 warning in 20.09s =======================
```

---

## 📂 Repository Structure

```text
Jarvis/
├── backend/
│   ├── core/                    # Real Agent Core (Claude Code Architecture)
│   │   ├── agent.py             # Main Turn Execution Loop Engine
│   │   ├── session.py           # Session State & Token Cost Accounting
│   │   ├── permissions.py       # Permission Broker & Diff Preview Gate
│   │   ├── prompt.py            # Dynamic Workspace System Prompt Builder
│   │   ├── events.py            # Event Stream Taxonomy (CLI & Web UI)
│   │   ├── llm/                 # Unified Provider-Neutral LLM Backends
│   │   └── tools/               # 8 Real Workspace & Shell Execution Tools
│   ├── api/                     # FastAPI & WebSocket Endpoints
│   ├── cli/                     # Interactive Terminal REPL Interface
│   ├── static/                  # Web Studio Single-Page Web App
│   ├── models/                  # Adaptive Thinking Engine & Complexity Vectors
│   └── services/llm/            # Multi-Model Router & Escalation Services
├── scripts/                     # Launcher scripts (jarvis.cmd, jarvis.ps1)
├── tests/                       # Complete Test Suite (145 tests)
└── docs/                        # Architecture & Quickstart Documentation
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).