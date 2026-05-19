import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  BackendUnavailableError,
  checkBackendHealth,
  fetchRunDetail,
  submitGoal,
} from "./api";
import type { BackendStatus, RunDetail, RunPreview } from "./api";

type RunStatus = "idle" | "submitting" | "ready" | "error";

const placeholderStages = [
  "Goal intake",
  "Task planning",
  "Agent dispatch",
  "Result review",
  "Final synthesis",
];

const demoGoal =
  "Review the sample workspace app and plan a small change that adds a visible health status, implementation notes, QA checks, and documentation.";

export default function App() {
  const [goal, setGoal] = useState(demoGoal);
  const [status, setStatus] = useState<RunStatus>("idle");
  const [backendStatus, setBackendStatus] =
    useState<BackendStatus>("checking");
  const [run, setRun] = useState<RunPreview | null>(null);
  const [runDetail, setRunDetail] = useState<RunDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canSubmit =
    goal.trim().length > 0 &&
    status !== "submitting" &&
    backendStatus === "available";

  async function verifyBackend() {
    setBackendStatus("checking");

    try {
      await checkBackendHealth();
      setBackendStatus("available");
    } catch {
      setBackendStatus("unavailable");
    }
  }

  useEffect(() => {
    let cancelled = false;

    async function verifyBackendOnMount() {
      try {
        await checkBackendHealth();
        if (!cancelled) setBackendStatus("available");
      } catch {
        if (!cancelled) setBackendStatus("unavailable");
      }
    }

    void verifyBackendOnMount();

    return () => {
      cancelled = true;
    };
  }, []);

  const statusLabel = useMemo(() => {
    if (status === "submitting") return "Starting";
    if (status === "ready") return "Preview ready";
    if (status === "error") return "Needs attention";
    return "Waiting";
  }, [status]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!canSubmit) return;

    setStatus("submitting");
    setError(null);
    setRun(null);
    setRunDetail(null);

    try {
      const result = await submitGoal(goal.trim());
      const detail = await fetchRunDetail(result.runId);
      setRun(result);
      setRunDetail(detail);
      setStatus("ready");
    } catch (submitError) {
      setStatus("error");
      setError(
        submitError instanceof BackendUnavailableError
          ? "Start the Ligent backend, then try again."
          : submitError instanceof Error
          ? submitError.message
          : "Ligent could not start this run.",
      );
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Ligent Desktop</p>
            <h1>Local agent controller</h1>
          </div>
          <div className="topbar-status">
            <div className={`backend-pill backend-${backendStatus}`}>
              Backend {backendStatus}
            </div>
            <div className={`status-pill status-${status}`}>{statusLabel}</div>
          </div>
        </header>

        <div className="run-layout">
          <section className="goal-pane" aria-labelledby="goal-title">
            <div className="section-heading">
              <p className="eyebrow">New run</p>
              <h2 id="goal-title">Describe the software task</h2>
            </div>

            <form onSubmit={handleSubmit} className="goal-form">
              <label htmlFor="goal">Goal</label>
              <textarea
                id="goal"
                value={goal}
                onChange={(event) => setGoal(event.target.value)}
                placeholder="Example: add a FastAPI health endpoint and show its status in the desktop app"
                rows={8}
              />
              <button type="submit" disabled={!canSubmit}>
                {status === "submitting" ? "Running demo" : "Run local demo"}
              </button>
            </form>

            {backendStatus === "unavailable" ? (
              <p className="error-message">
                Backend unavailable. Run <code>npm run backend:dev</code> from
                the project root, then{" "}
                <button
                  className="inline-action"
                  type="button"
                  onClick={() => void verifyBackend()}
                >
                  check again
                </button>
                .
              </p>
            ) : null}
            {error ? <p className="error-message">{error}</p> : null}
          </section>

          <section className="progress-pane" aria-labelledby="progress-title">
            <div className="section-heading">
              <p className="eyebrow">Run status</p>
              <h2 id="progress-title">Controller preview</h2>
            </div>

            <ol className="stage-list">
              {placeholderStages.map((stage, index) => (
                <li key={stage} className={run || index === 0 ? "active" : ""}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  {stage}
                </li>
              ))}
            </ol>

            <div className="result-panel">
              <p className="eyebrow">Result</p>
              {run ? (
                <>
                  <h3>{run.summary}</h3>
                  <dl>
                    <div>
                      <dt>Run ID</dt>
                      <dd>{run.runId}</dd>
                    </div>
                    <div>
                      <dt>Status</dt>
                      <dd>{run.status}</dd>
                    </div>
                    <div>
                      <dt>Next</dt>
                      <dd>{run.nextStep}</dd>
                    </div>
                    <div>
                      <dt>Agents</dt>
                      <dd>{run.assignedAgents.join(", ")}</dd>
                    </div>
                    <div>
                      <dt>Created</dt>
                      <dd>{new Date(run.createdAt).toLocaleString()}</dd>
                    </div>
                  </dl>
                </>
              ) : (
                <p className="muted">
                  Submit a goal to verify the desktop to backend path.
                </p>
              )}
            </div>
          </section>
        </div>

        {runDetail ? (
          <section className="detail-pane" aria-labelledby="detail-title">
            <div className="section-heading">
              <p className="eyebrow">Persisted run</p>
              <h2 id="detail-title">Agent outputs and decisions</h2>
            </div>

            <div className="task-board">
              {runDetail.tasks.map((task) => (
                <article key={task.id} className="task-row">
                  <div>
                    <p className="task-agent">
                      {task.assignedAgent ?? "unassigned"} - {task.status}
                    </p>
                    <h3>{task.title}</h3>
                    <p>{task.description}</p>
                  </div>
                  <div className="task-output">
                    {task.results.map((result) => (
                      <div key={`${task.id}-${result.agent}`}>
                        <p className="output-title">
                          {result.agent} output -{" "}
                          {Math.round(result.confidence * 100)}%
                        </p>
                        <p>{formatResult(result.result)}</p>
                        {result.evidence.length > 0 ? (
                          <p className="evidence">
                            Evidence: {result.evidence.join(", ")}
                          </p>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </article>
              ))}
            </div>

            <div className="decision-strip">
              <section>
                <p className="eyebrow">Decisions</p>
                {runDetail.decisions.map((decision) => (
                  <div key={decision.id} className="decision-item">
                    <h3>{decision.summary}</h3>
                    <p>{decision.reason}</p>
                    <p className="evidence">Chosen: {decision.chosenOption}</p>
                  </div>
                ))}
              </section>
              <section>
                <p className="eyebrow">Final</p>
                <h3>{runDetail.finalSummary}</h3>
                <p className="muted">
                  Conflicts:{" "}
                  {runDetail.conflicts.length > 0
                    ? runDetail.conflicts
                        .map((conflict) => conflict.summary)
                        .join(", ")
                    : "none recorded"}
                  .
                </p>
              </section>
            </div>
          </section>
        ) : null}
      </section>
    </main>
  );
}

function formatResult(result: Record<string, unknown>) {
  const recommendation = result.recommendation;
  if (typeof recommendation === "string") return recommendation;

  const summary = result.summary;
  if (typeof summary === "string") return summary;

  return JSON.stringify(result);
}
