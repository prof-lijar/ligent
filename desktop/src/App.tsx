import { FormEvent, useMemo, useState } from "react";
import { submitGoal } from "./tauri";

type RunStatus = "idle" | "submitting" | "ready" | "error";

type RunPreview = {
  runId: string;
  status: string;
  summary: string;
  nextStep: string;
};

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
  const [run, setRun] = useState<RunPreview | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = goal.trim().length > 0 && status !== "submitting";

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
        submitError instanceof Error
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
          <div className={`status-pill status-${status}`}>{statusLabel}</div>
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
                  </dl>
                </>
              ) : (
                <p className="muted">
                  Submit a goal to verify the desktop shell and command path.
                </p>
              )}
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}
