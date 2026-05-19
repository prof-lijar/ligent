const DEFAULT_BACKEND_URL = "http://127.0.0.1:8765";

export type BackendStatus = "checking" | "available" | "unavailable";

export type RunPreview = {
  runId: string;
  status: string;
  summary: string;
  nextStep: string;
  assignedAgents: string[];
  createdAt: string;
};

export type HealthResponse = {
  status: string;
  service: string;
};

export class BackendUnavailableError extends Error {
  constructor(message = "Ligent backend is not available on 127.0.0.1:8765.") {
    super(message);
    this.name = "BackendUnavailableError";
  }
}

function getBackendUrl() {
  return import.meta.env.VITE_LIGENT_BACKEND_URL ?? DEFAULT_BACKEND_URL;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${getBackendUrl()}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
  } catch {
    throw new BackendUnavailableError();
  }

  if (!response.ok) {
    throw new Error(`Ligent backend returned ${response.status}.`);
  }

  return response.json() as Promise<T>;
}

export async function checkBackendHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export async function submitGoal(goal: string): Promise<RunPreview> {
  return request<RunPreview>("/runs/preview", {
    method: "POST",
    body: JSON.stringify({ goal }),
  });
}
