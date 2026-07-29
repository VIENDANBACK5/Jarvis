import argparse
import sys
import logging
from backend.runtime.agent_runtime import AgentRuntime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_cli():
    parser = argparse.ArgumentParser(description="Jarvis Autonomous Software Engineering Agent CLI Tool")
    parser.add_argument("--repo", type=str, required=True, help="Path to the target repository")
    parser.add_argument("--task", type=str, required=True, help="Task description or issue to resolve")
    parser.add_argument("--max-steps", type=int, default=5, help="Maximum execution iterations")
    parser.add_argument("--budget", type=int, default=50000, help="Maximum token budget")

    args = parser.parse_args()

    print("\n========================================================")
    print("[JARVIS] AUTONOMOUS ENGINEERING AGENT (Level 9.0 CLI)")
    print("========================================================")
    print(f"[REPO] Target Repository : {args.repo}")
    print(f"[TASK] Task Goal          : {args.task}")
    print("--------------------------------------------------------\n")

    print("[JARVIS] Initializing Mission Controller & Docker Sandbox...")
    runtime = AgentRuntime(storage_dir=".")

    task_id = f"TASK-{abs(hash(args.task)) % 10000:04d}"
    
    print(f"[JARVIS] Executing Autonomous Mission [{task_id}]...\n")
    result = runtime.execute_mission(
        task_id=task_id,
        task_goal=args.task,
        repo_path=args.repo,
        max_iterations=args.max_steps
    )

    print("\n--------------------------------------------------------")
    print("[SUMMARY] MISSION EXECUTION SUMMARY")
    print("--------------------------------------------------------")
    print(f"Status        : {result['status']}")
    print(f"Review        : {result['review_status']}")
    print(f"Reward Score  : {result['reward']}")
    print(f"Events Logged : {result['events_count']}")
    print("========================================================\n")


if __name__ == "__main__":
    run_cli()
