# Jarvis Autonomous Agent — Quick Start Guide

Jarvis is a genuinely working local autonomous coding agent inspired by Claude Code. It drives a tool-use loop over real files and a real shell with user permission gating.

---

## 🚀 1. Running the Interactive CLI (Claude Code Style)

Run Jarvis in any project directory:

```powershell
# Interactive REPL session
python -m backend.cli.agent_cli --cwd .

# Or using the Windows launcher script:
.\scripts\jarvis.ps1
```

### Run a One-Shot Task:
```powershell
python -m backend.cli.agent_cli --print "Create fizzbuzz.py and run pytest"
```

---

## 🌐 2. Running the Real Web UI Studio

Start the FastAPI server:

```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

Open your browser and navigate to:
👉 **[http://localhost:8000/ui/](http://localhost:8000/ui/)**

---

## 🔒 3. Permission System & Safety

* **Read-only operations** (`read_file`, `glob`, `grep`, `todo`): Executed automatically.
* **Mutating operations** (`write_file`, `edit_file`, `bash`): Prompt the user with a preview (Diff or Command) for approval (`Allow once`, `Always allow`, or `Deny`).
