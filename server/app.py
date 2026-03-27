"""FastAPI application for Smart Support Env."""

from dataclasses import asdict
from typing import Any, Dict

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import HTMLResponse

try:
    from ..support_models import SmartSupportAction
    from ..tasks.catalog import TASKS
    from .environment import SmartSupportEnvironment
except ImportError:
    from server.environment import SmartSupportEnvironment
    from support_models import SmartSupportAction
    from tasks.catalog import TASKS

app = FastAPI(title="Smart Support Env", version="3.0.0")
env = SmartSupportEnvironment()


def _task_cards() -> str:
    difficulty_colors = {"easy": "#0d8a5f", "medium": "#b7791f", "hard": "#b83232"}
    cards = []
    for task_name, task in TASKS.items():
        cards.append(
            f"""
            <article class="task-card">
              <div class="task-top">
                <span class="pill" style="background:{difficulty_colors.get(task['difficulty'], '#3658d6')}">{task['difficulty'].upper()}</span>
                <span class="mono">{task_name}</span>
              </div>
              <h3>{task['title']}</h3>
              <p>{task['instructions']}</p>
              <button onclick="resetTask('{task_name}')">Reset This Task</button>
            </article>
            """
        )
    return "\n".join(cards)


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    html = f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Smart Support Env</title>
      <style>
        :root {{
          --bg: #f5efe4;
          --panel: rgba(255,255,255,0.78);
          --ink: #1e2230;
          --muted: #556070;
          --line: rgba(30,34,48,0.12);
          --brand: #1c6b57;
          --accent: #d96f32;
          --shadow: 0 16px 40px rgba(39, 45, 77, 0.12);
        }}
        * {{ box-sizing: border-box; }}
        body {{
          margin: 0;
          font-family: Georgia, "Times New Roman", serif;
          color: var(--ink);
          background:
            radial-gradient(circle at top left, rgba(217,111,50,0.18), transparent 28%),
            radial-gradient(circle at top right, rgba(28,107,87,0.16), transparent 30%),
            linear-gradient(180deg, #f8f3ea 0%, var(--bg) 100%);
        }}
        .wrap {{
          max-width: 1180px;
          margin: 0 auto;
          padding: 32px 18px 60px;
        }}
        .hero {{
          display: grid;
          grid-template-columns: 1.3fr 0.9fr;
          gap: 18px;
          margin-bottom: 20px;
        }}
        .panel {{
          background: var(--panel);
          backdrop-filter: blur(8px);
          border: 1px solid var(--line);
          border-radius: 22px;
          box-shadow: var(--shadow);
        }}
        .hero-main {{
          padding: 28px;
        }}
        .eyebrow {{
          display: inline-block;
          padding: 6px 10px;
          border-radius: 999px;
          font-size: 12px;
          letter-spacing: 0.14em;
          background: rgba(28,107,87,0.1);
          color: var(--brand);
          margin-bottom: 12px;
        }}
        h1 {{
          margin: 0 0 10px;
          font-size: clamp(36px, 5vw, 62px);
          line-height: 0.96;
          letter-spacing: -0.04em;
        }}
        .lead {{
          margin: 0 0 18px;
          font-size: 18px;
          line-height: 1.5;
          color: var(--muted);
          max-width: 54ch;
        }}
        .hero-actions, .quick-actions {{
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
        }}
        a.button, button {{
          appearance: none;
          border: 0;
          border-radius: 999px;
          padding: 11px 16px;
          font: inherit;
          cursor: pointer;
          text-decoration: none;
          transition: transform 120ms ease, opacity 120ms ease;
        }}
        a.button:hover, button:hover {{ transform: translateY(-1px); opacity: 0.96; }}
        .primary {{
          background: var(--brand);
          color: white;
        }}
        .secondary {{
          background: #fff;
          color: var(--ink);
          border: 1px solid var(--line);
        }}
        .hero-side {{
          padding: 24px;
          display: grid;
          gap: 12px;
          align-content: start;
        }}
        .stat {{
          padding: 16px;
          border-radius: 16px;
          background: rgba(255,255,255,0.82);
          border: 1px solid var(--line);
        }}
        .stat-label {{
          font-size: 12px;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: var(--muted);
        }}
        .stat-value {{
          margin-top: 8px;
          font-size: 22px;
          font-weight: 700;
        }}
        .grid {{
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 18px;
          margin-top: 18px;
        }}
        .task-grid {{
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 14px;
        }}
        .section {{
          padding: 22px;
        }}
        .section h2 {{
          margin: 0 0 12px;
          font-size: 28px;
        }}
        .section p {{
          margin: 0 0 12px;
          color: var(--muted);
        }}
        .task-card {{
          border: 1px solid var(--line);
          border-radius: 18px;
          padding: 16px;
          background: rgba(255,255,255,0.86);
          display: grid;
          gap: 10px;
        }}
        .task-card h3 {{
          margin: 0;
          font-size: 22px;
        }}
        .task-card p {{
          margin: 0;
          color: var(--muted);
          font-size: 15px;
        }}
        .task-top {{
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 8px;
        }}
        .pill {{
          color: white;
          padding: 6px 10px;
          border-radius: 999px;
          font-size: 11px;
          letter-spacing: 0.12em;
        }}
        .mono {{
          font-family: Consolas, monospace;
          font-size: 12px;
          color: var(--muted);
        }}
        .playground {{
          display: grid;
          gap: 12px;
        }}
        .row {{
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 10px;
        }}
        input, select, textarea {{
          width: 100%;
          border-radius: 14px;
          border: 1px solid var(--line);
          padding: 12px 14px;
          font: inherit;
          background: rgba(255,255,255,0.95);
        }}
        textarea {{
          min-height: 140px;
          resize: vertical;
          font-family: Consolas, monospace;
          font-size: 13px;
        }}
        pre {{
          margin: 0;
          border-radius: 18px;
          background: #19202d;
          color: #dce8f6;
          padding: 18px;
          min-height: 260px;
          overflow: auto;
          font-size: 13px;
          line-height: 1.45;
        }}
        .footer-note {{
          margin-top: 18px;
          font-size: 14px;
          color: var(--muted);
        }}
        @media (max-width: 980px) {{
          .hero, .grid, .task-grid, .row {{ grid-template-columns: 1fr; }}
        }}
      </style>
    </head>
    <body>
      <main class="wrap">
        <section class="hero">
          <div class="panel hero-main">
            <div class="eyebrow">OpenEnv Submission Dashboard</div>
            <h1>Smart Support Env</h1>
            <p class="lead">
              A reviewer-friendly interface for exploring the environment, testing the core
              API, and understanding the three graded real-world support workflows.
            </p>
            <div class="hero-actions">
              <a class="button primary" href="/docs">Open API Docs</a>
              <a class="button secondary" href="https://github.com/Gosula16/Scalar-" target="_blank" rel="noreferrer">GitHub Repo</a>
              <a class="button secondary" href="https://huggingface.co/spaces/Gosula16/smart-support-env" target="_blank" rel="noreferrer">HF Space</a>
            </div>
          </div>
          <aside class="panel hero-side">
            <div class="stat">
              <div class="stat-label">Environment Type</div>
              <div class="stat-value">Customer Support</div>
            </div>
            <div class="stat">
              <div class="stat-label">Tasks</div>
              <div class="stat-value">3 deterministic workflows</div>
            </div>
            <div class="stat">
              <div class="stat-label">Core Endpoints</div>
              <div class="stat-value">/reset /step /state /health</div>
            </div>
          </aside>
        </section>

        <section class="panel section">
          <h2>Task Overview</h2>
          <p>Each task is graded on trajectory quality, not just the final outcome. Reviewers can reset a task directly from here.</p>
          <div class="task-grid">
            {_task_cards()}
          </div>
        </section>

        <section class="grid">
          <section class="panel section">
            <h2>Quick Checks</h2>
            <p>Use the buttons below to verify the most important endpoints quickly.</p>
            <div class="quick-actions">
              <button class="primary" onclick="callJson('/health')">Check Health</button>
              <button class="secondary" onclick="callJson('/tasks')">List Tasks</button>
              <button class="secondary" onclick="callJson('/state')">Current State</button>
            </div>
            <div class="footer-note">Tip: click a task card above, then inspect state or send a custom step below.</div>
          </section>

          <section class="panel section">
            <h2>Interactive Playground</h2>
            <div class="playground">
              <div class="row">
                <select id="taskName">
                  <option value="basic_greeting">basic_greeting</option>
                  <option value="medium_resolution">medium_resolution</option>
                  <option value="advanced_escalation">advanced_escalation</option>
                </select>
                <button class="primary" onclick="resetSelectedTask()">Reset Selected Task</button>
              </div>
              <div class="row">
                <select id="actionType">
                  <option value="greet">greet</option>
                  <option value="empathize">empathize</option>
                  <option value="ask_clarifying_question">ask_clarifying_question</option>
                  <option value="troubleshoot">troubleshoot</option>
                  <option value="resolve">resolve</option>
                  <option value="escalate">escalate</option>
                  <option value="close_ticket">close_ticket</option>
                  <option value="update_status">update_status</option>
                </select>
                <input id="resolutionCode" placeholder="resolution code (optional)" />
              </div>
              <input id="actionContent" value="Welcome to support, I can help with your import workflow." />
              <div class="row">
                <input id="confidence" type="number" min="0" max="1" step="0.01" value="0.90" />
                <button class="primary" onclick="sendStep()">Send Step</button>
              </div>
            </div>
          </section>
        </section>

        <section class="panel section" style="margin-top:18px;">
          <h2>Live Response Viewer</h2>
          <p>All endpoint results appear here so judges can inspect behavior without opening browser devtools.</p>
          <pre id="output">{{"status": "ready"}}</pre>
        </section>
      </main>

      <script>
        const output = document.getElementById("output");

        function pretty(data) {{
          output.textContent = typeof data === "string" ? data : JSON.stringify(data, null, 2);
        }}

        async function callJson(path, options = undefined) {{
          try {{
            const response = await fetch(path, options);
            const text = await response.text();
            try {{
              pretty(JSON.parse(text));
            }} catch {{
              pretty(text);
            }}
          }} catch (error) {{
            pretty({{ error: String(error) }});
          }}
        }}

        async function resetTask(taskName) {{
          document.getElementById("taskName").value = taskName;
          await callJson("/reset", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ task_name: taskName }})
          }});
        }}

        async function resetSelectedTask() {{
          await resetTask(document.getElementById("taskName").value);
        }}

        async function sendStep() {{
          const payload = {{
            action: {{
              action_type: document.getElementById("actionType").value,
              content: document.getElementById("actionContent").value,
              confidence: Number(document.getElementById("confidence").value),
              resolution_code: document.getElementById("resolutionCode").value || null
            }}
          }};
          await callJson("/step", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify(payload)
          }});
        }}
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "healthy"}


@app.get("/tasks")
async def list_tasks() -> Any:
    return env.tasks()


@app.post("/reset")
async def reset(request: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    try:
        observation = env.reset(task_name=request.get("task_name", "basic_greeting"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"observation": asdict(observation), "reward": None, "done": False}


@app.post("/step")
async def step(request: Dict[str, Any]) -> Dict[str, Any]:
    try:
        action = SmartSupportAction(**request.get("action", {}))
        observation = env.step(action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "observation": asdict(observation),
        "reward": observation.reward,
        "done": observation.done,
    }


@app.get("/state")
async def state() -> Dict[str, Any]:
    try:
        return asdict(env.state)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
