import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  BackendUnavailableError,
  checkBackendHealth,
  submitGoal,
} from "./api";
import type { BackendStatus, RunPreview } from "./api";

type RunStatus = "idle" | "submitting" | "ready" | "error";

const placeholderStages = [
  "Goal intake",
  "Task planning",
  "Agent dispatch",
  "Result review",
  "Final synthesis",
];

export default function App() {
  const [goal, setGoal] = useState("");
  const [status, setStatus] = useState<RunStatus>("idle");
  const [backendStatus, setBackendStatus] =
    useState<BackendStatus>("checking");
  const [run, setRun] = useState<RunPreview | null>(null);
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

    try {
      const result = await submitGoal(goal.trim());
      setRun(result);
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
                {status === "submitting" ? "Starting run" : "Start preview run"}
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
      </section>
    </main>
  );
}
