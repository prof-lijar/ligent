import { invoke } from "@tauri-apps/api/core";

export type RunPreview = {
  runId: string;
  status: string;
  summary: string;
  nextStep: string;
};

function createBrowserPreview(goal: string): RunPreview {
  return {
    runId: `preview-${Date.now()}`,
    status: "queued",
    summary: "Desktop shell accepted the goal.",
    nextStep: `Backend orchestration will handle: ${goal.slice(0, 96)}`,
  };
}

export async function submitGoal(goal: string): Promise<RunPreview> {
  if (!window.__TAURI_INTERNALS__) {
    return createBrowserPreview(goal);
  }

  return invoke<RunPreview>("submit_goal", { goal });
}
