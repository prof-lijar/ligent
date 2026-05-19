use serde::Serialize;

#[derive(Serialize)]
struct RunPreview {
    #[serde(rename = "runId")]
    run_id: String,
    status: String,
    summary: String,
    #[serde(rename = "nextStep")]
    next_step: String,
}

#[tauri::command]
fn submit_goal(goal: String) -> RunPreview {
    let goal_preview: String = goal.chars().take(96).collect();

    RunPreview {
        run_id: "preview-local".to_string(),
        status: "queued".to_string(),
        summary: "Desktop shell accepted the goal.".to_string(),
        next_step: format!("Backend orchestration will handle: {goal_preview}"),
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![submit_goal])
        .run(tauri::generate_context!())
        .expect("failed to run Ligent desktop shell");
}
