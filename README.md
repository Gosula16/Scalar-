---
title: Smart Support Env
emoji: "\U0001F6A8"
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
pinned: false
tags:
  - openenv
---

# Smart Support Env

`smart-support-env` is a realistic OpenEnv benchmark for customer support agents. Instead of a toy chatbot, it simulates three real workflows that support teams handle every day:

1. `basic_greeting` (easy): onboard a new user and guide them to CSV import.
2. `medium_resolution` (medium): recover access during a password reset failure.
3. `advanced_escalation` (hard): collect billing evidence and escalate a duplicate charge safely.

The environment is deterministic, multi-step, and reward-shaped so agents get partial credit for doing the right work in the right order.

## Why this is useful

This benchmark is designed for evaluating agents that must:

- communicate professionally with a customer,
- choose the correct next operational step,
- avoid unsafe promises,
- escalate only when policy requires it,
- finish the ticket within a limited step budget.

## OpenEnv surface

The server exposes the standard interaction pattern:

- `POST /reset`
- `POST /step`
- `GET /state`
- `GET /tasks`
- `GET /health`

### Reset request

```json
{
  "task_name": "medium_resolution"
}
```

### Step request

```json
{
  "action": {
    "action_type": "resolve",
    "content": "Use the newest reset link in a fresh browser tab.",
    "confidence": 0.92,
    "resolution_code": null
  }
}
```

## Typed models

### Action

- `action_type`: `greet | empathize | ask_clarifying_question | troubleshoot | resolve | escalate | close_ticket | update_status`
- `content`: customer-facing response text
- `confidence`: `0.0` to `1.0`
- `resolution_code`: optional internal escalation or resolution code

### Observation

- `task_name`
- `task_difficulty`
- `task_title`
- `instructions`
- `current_ticket`
- `conversation_history`
- `status`
- `step_count`
- `remaining_steps`
- `latest_customer_message`
- `available_actions`

### Reward

- `value`: net reward for the step
- `progress`: progress credit earned
- `penalty`: deductions for unsafe or low-quality actions
- `explanation`: human-readable explanation
- `grader_score`: current normalized score in the `0.0` to `1.0` range

## Reward design

Each task is a sequence of objectives. The agent earns progress only when it completes the next objective with:

- the right action type,
- the required support details,
- the correct escalation code when one is required.

The environment also penalizes:

- repeating the same action,
- missing critical details,
- unsafe handling in the billing dispute workflow.

That gives dense feedback through the trajectory instead of a single binary result.

## Graders

Every task has a deterministic grader in `graders/` that returns a score between `0.0` and `1.0`.

- Easy: objective completion plus clean closure
- Medium: objective completion, closure quality, and unsafe-action penalties
- Hard: objective completion, correct escalation outcome, and stronger safety penalties

## Local setup

```bash
cd smart-support-env
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Run the API:

```bash
uv run server
```

Or, if you are not using `uv`:

```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

Example calls:

```bash
curl http://localhost:8000/tasks
curl -X POST http://localhost:8000/reset -H "Content-Type: application/json" -d "{\"task_name\":\"basic_greeting\"}"
curl http://localhost:8000/state
```

## Baseline inference

The required baseline script is [`inference.py`](/D:/Scalar/smart-support-env/inference.py).

It supports two modes:

- LLM mode when `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN` are set.
- Heuristic mode when those variables are missing, which is useful for local smoke testing.

Environment variables:

- `ENV_BASE_URL`: environment server URL, defaults to `http://localhost:8000`
- `API_BASE_URL`: OpenAI-compatible model endpoint
- `MODEL_NAME`: model identifier
- `HF_TOKEN`: Hugging Face or API token

Create your local secret file from the example:

```bash
copy .env.example .env
```

Then edit `.env` and place your real key there. The project ignores `.env` in Git, and `inference.py` automatically loads it with `python-dotenv`.

Run it:

```bash
python inference.py
```

## Docker and Hugging Face Spaces

Build locally:

```bash
docker build -t smart-support-env .
docker run -p 8000:8000 smart-support-env
```

For Hugging Face Spaces:

1. Create a Docker Space.
2. Push this repository.
3. Set `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN` as Space secrets if you want the LLM baseline to run there.

The container serves the app on port `8000`.

## Project structure

```text
smart-support-env/
  client.py
  support_models.py
  openenv.yaml
  inference.py
  Dockerfile
  requirements.txt
  server/
  tasks/
  graders/
```

## Expected baseline behavior

The heuristic baseline should complete all three tasks successfully and produce near-perfect scores locally. The LLM baseline should be reproducible because it uses deterministic prompts and `temperature=0`.
