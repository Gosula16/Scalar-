#!/usr/bin/env python3
"""Baseline inference script for Smart Support Env."""

import json
import os
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:8000")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
BENCHMARK = os.getenv("SMART_SUPPORT_BENCHMARK", "smart_support_env")
MAX_STEPS = 8
TEMPERATURE = 0.0
MAX_TOKENS = 250
SUCCESS_SCORE_THRESHOLD = 0.6


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(
    step: int,
    action: str,
    reward: float,
    done: bool,
    error: Optional[str],
) -> None:
    error_value = error if error else "null"
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} "
        f"done={str(done).lower()} error={error_value}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{reward:.2f}" for reward in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


def build_prompt(observation: Dict) -> str:
    ticket = observation["current_ticket"]
    history_lines = [
        f"{turn['speaker'].title()}: {turn['message']}"
        for turn in observation["conversation_history"]
    ]
    history = "\n".join(history_lines)
    return f"""
You are a high-quality SaaS customer support agent.

Task: {observation['task_title']} ({observation['task_difficulty']})
Instructions: {observation['instructions']}
Ticket category: {ticket['category']}
Priority: {ticket['priority']}
Account tier: {ticket['account_tier']}
Customer sentiment: {ticket['sentiment']}
Customer description: {ticket['description']}
Latest customer message: {observation['latest_customer_message']}

Conversation so far:
{history}

Return only valid JSON with this shape:
{{
  "action_type": "greet|empathize|ask_clarifying_question|troubleshoot|resolve|escalate|close_ticket|update_status",
  "content": "one concise but helpful reply",
  "confidence": 0.0,
  "resolution_code": null
}}
""".strip()


def heuristic_action(task_name: str, step_count: int) -> Dict:
    plans: Dict[str, List[Dict]] = {
        "basic_greeting": [
            {
                "action_type": "greet",
                "content": "Welcome to support, and thanks for reaching out. I can help you import your first file.",
                "confidence": 0.93,
                "resolution_code": None,
            },
            {
                "action_type": "resolve",
                "content": "From the dashboard, open the Data section and choose Import to upload your CSV.",
                "confidence": 0.95,
                "resolution_code": None,
            },
            {
                "action_type": "close_ticket",
                "content": "If the import template helps, you can use it now, and support is here if you need anything else.",
                "confidence": 0.90,
                "resolution_code": None,
            },
        ],
        "medium_resolution": [
            {
                "action_type": "empathize",
                "content": "I understand the time pressure before your demo, and I will help you get access back quickly.",
                "confidence": 0.90,
                "resolution_code": None,
            },
            {
                "action_type": "ask_clarifying_question",
                "content": "Please request the latest reset email and open only the newest email link.",
                "confidence": 0.88,
                "resolution_code": None,
            },
            {
                "action_type": "resolve",
                "content": "Use the newest reset link in a fresh browser tab so the browser does not reuse an older expired token.",
                "confidence": 0.93,
                "resolution_code": None,
            },
            {
                "action_type": "close_ticket",
                "content": "You can bookmark the login page, and if the issue returns support can help right away.",
                "confidence": 0.85,
                "resolution_code": None,
            },
        ],
        "advanced_escalation": [
            {
                "action_type": "empathize",
                "content": "I understand the impact of this double billing issue and will treat it as a priority billing case.",
                "confidence": 0.91,
                "resolution_code": None,
            },
            {
                "action_type": "ask_clarifying_question",
                "content": "Please send the invoice IDs and the timestamp for each charge so billing can verify the duplicate transaction.",
                "confidence": 0.90,
                "resolution_code": None,
            },
            {
                "action_type": "update_status",
                "content": "Our billing operations team will review the evidence and confirm the duplicate charge status after review.",
                "confidence": 0.87,
                "resolution_code": None,
            },
            {
                "action_type": "escalate",
                "content": "I am escalating this duplicate charge case to billing operations for immediate review.",
                "confidence": 0.95,
                "resolution_code": "BILLING_DUPLICATE_CHARGE",
            },
            {
                "action_type": "close_ticket",
                "content": "Your case reference is CASE-9912, and billing will update you within 24 hours.",
                "confidence": 0.88,
                "resolution_code": None,
            },
        ],
    }
    task_plan = plans[task_name]
    return task_plan[min(step_count, len(task_plan) - 1)]


def get_model_action(client: OpenAI, observation: Dict) -> Dict:
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": build_prompt(observation)}],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
    raw_content = (completion.choices[0].message.content or "").strip()
    return json.loads(raw_content or "{}")


def post_json(path: str, payload: Dict) -> Dict:
    response = requests.post(f"{ENV_BASE_URL}{path}", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def format_action(action: Dict) -> str:
    return action.get("action_type", "unknown")


def run_task(task_name: str, client: Optional[OpenAI]) -> None:
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME if client else "heuristic-baseline")

    try:
        reset_result = post_json("/reset", {"task_name": task_name})
        observation = reset_result["observation"]
        done = bool(reset_result.get("done", False))

        for step in range(1, MAX_STEPS + 1):
            if done:
                break

            action = heuristic_action(task_name, observation["step_count"]) if client is None else get_model_action(client, observation)

            step_result = post_json("/step", {"action": action})
            observation = step_result["observation"]
            reward = float(step_result.get("reward") or 0.0)
            done = bool(step_result.get("done", False))
            error = observation.get("metadata", {}).get("last_action_error")

            rewards.append(reward)
            steps_taken = step

            log_step(
                step=step,
                action=format_action(action),
                reward=reward,
                done=done,
                error=error,
            )

            if done:
                break

        score = float(observation.get("grader_score", 0.0))
        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


def main() -> None:
    client: Optional[OpenAI] = None
    if HF_TOKEN:
        client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    for task_name in ["basic_greeting", "medium_resolution", "advanced_escalation"]:
        run_task(task_name, client)


if __name__ == "__main__":
    main()
