const API_BASE = "/api/v1";
const state = { project: "", activity: "", projectData: null, activityData: null };

const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? "—").replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[char]));
const enc = (value) => encodeURIComponent(value);

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body?.error?.message || `Request failed (${response.status})`);
  return body;
}

function setStatus(message = "", isError = false) {
  const banner = $("#global-status");
  banner.textContent = message;
  banner.hidden = !message;
  banner.classList.toggle("error", isError);
}

function showDashboard(show) { $("#dashboard").hidden = !show; $("#empty-state").hidden = show; }
function formatDate(value) { if (!value) return "No date"; const date = new Date(value); return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" }); }
function trendBadge(trend) { const labels = { improving: "Improving", stalled: "Stalled", declining: "Declining", insufficient_data: "Insufficient data" }; const tone = trend === "improving" ? "good" : trend === "declining" ? "bad" : trend === "stalled" ? "warn" : "neutral"; return `<span class="badge ${tone}">${esc(labels[trend] || trend)}</span>`; }
function riskBadge(level) { const tone = level === "high" ? "bad" : level === "medium" ? "warn" : level === "low" ? "good" : "neutral"; return `<span class="badge ${tone}">${esc(level || "No data")} risk</span>`; }
function empty(message) { return `<div class="empty-inline">${esc(message)}</div>`; }

async function loadProjects(preferred = "") {
  const result = await api("/projects");
  const select = $("#project-select");
  select.innerHTML = `<option value="">Select a project</option>${result.projects.map((project) => `<option value="${esc(project)}">${esc(project)}</option>`).join("")}`;
  const next = result.projects.includes(preferred) ? preferred : result.projects[0] || "";
  select.value = next;
  if (next) await loadProjectData(next); else showDashboard(false);
}

async function loadProjectData(project) {
  state.project = project; state.activity = ""; showDashboard(true); setStatus("Loading project intelligence…");
  try {
    const p = enc(project);
    const [trends, risks, insights, schedule, scheduleHistory, issueHistory] = await Promise.all([
      api(`/projects/${p}/trends`), api(`/projects/${p}/risks`), api(`/projects/${p}/insights`), api(`/projects/${p}/schedule-impact`), api(`/projects/${p}/schedule-impact/history`), api(`/projects/${p}/issues/history`),
    ]);
    state.projectData = { trends, risks, insights, schedule, scheduleHistory, issueHistory };
    renderProject();
    const activityNames = trends.map((item) => item.activity_name);
    state.activity = activityNames[0] || "";
    $("#activity-select").value = state.activity;
    await loadActivityData(state.activity);
    setStatus("");
  } catch (error) { setStatus(error.message, true); showDashboard(false); }
}

function renderProject() {
  const { trends, risks, insights, scheduleHistory, issueHistory } = state.projectData;
  const activities = trends.length; const observedRisks = risks.filter((risk) => risk.risk_level !== "insufficient_data" && risk.risk_score > 0).length;
  const scheduleObservations = scheduleHistory.activities.reduce((sum, activity) => sum + activity.observations.length, 0);
  const issueObservations = issueHistory.activities.reduce((sum, activity) => sum + activity.observations.length, 0);
  $("#metrics").innerHTML = [["Activities", activities, "tracked in this project"], ["Risk signals", observedRisks, "activities with observed risk"], ["Delay observations", scheduleObservations, "reported schedule events"], ["Issue observations", issueObservations, "traceable issue records"]].map(([label, value, caption]) => `<div class="metric-card"><div class="metric-label">${label}</div><div class="metric-value">${value}</div><div class="metric-caption">${caption}</div></div>`).join("");
  $("#activity-select").innerHTML = trends.map((trend) => `<option value="${esc(trend.activity_name)}">${esc(trend.activity_name)}</option>`).join("");
  $("#activity-table").innerHTML = trends.length ? trends.map((trend) => { const risk = risks.find((item) => item.activity_name === trend.activity_name); const latest = trend.last_progress; return `<tr data-activity="${esc(trend.activity_name)}"><td><div class="activity-name">${esc(trend.activity_name)}</div><div class="subtle">${trend.snapshot_count} report${trend.snapshot_count === 1 ? "" : "s"}</div></td><td><div class="progress-cell"><strong>${latest == null ? "—" : `${latest}%`}</strong><span class="progress-track"><span class="progress-fill" style="width:${Math.max(0, Math.min(100, latest || 0))}%"></span></span></div></td><td>${trendBadge(trend.trend)}</td><td>${riskBadge(risk?.risk_level)}</td><td><span class="subtle">History available</span></td></tr>`; }).join("") : `<tr><td colspan="5">${empty("No activity history returned for this project.")}</td></tr>`;
  $("#schedule-table").innerHTML = state.projectData.schedule.activities.length ? state.projectData.schedule.activities.map((item) => `<tr data-activity="${esc(item.activity_name)}"><td class="activity-name">${esc(item.activity_name)}</td><td>${item.latest_delay_hours == null ? "—" : `${item.latest_delay_hours} hrs`}</td><td>${esc(item.latest_delay_reason || "No reason recorded")}</td><td>${item.delay_observation_count}</td><td>${trendBadge(item.progress_trend)}</td></tr>`).join("") : `<tr><td colspan="5">${empty("No observed schedule impact returned.")}</td></tr>`;
  const insightActivities = insights.activities || [];
  $("#insights").innerHTML = insightActivities.flatMap((activity) => activity.findings.map((finding) => `<article class="insight-card"><span class="badge ${finding.priority === "high" ? "bad" : finding.priority === "medium" ? "warn" : "good"}">${esc(finding.priority)} priority</span><h3>${esc(finding.title)}</h3><p>${esc(finding.explanation)}</p><p class="recommendation"><strong>Recommendation:</strong><br />${esc(finding.recommendation || "Review the underlying evidence.")}</p><p class="subtle">${esc(activity.activity_name)} · ${activity.risk_score} risk score</p></article>`)).join("") || empty("No explainable findings were returned for this project.");
}

async function loadActivityData(activity) {
  if (!activity) { renderActivityEmpty(); return; }
  state.activity = activity; $("#selected-activity-title").textContent = activity; $("#progress-detail").innerHTML = `<div class="loading-line">Loading activity evidence…</div>`;
  try {
    const p = enc(state.project); const a = enc(activity);
    const [history, trend, risk, insight, schedule, scheduleHistory, issueHistory] = await Promise.all([
      api(`/projects/${p}/activities/${a}/history`), api(`/projects/${p}/activities/${a}/trend`), api(`/projects/${p}/activities/${a}/risk`), api(`/projects/${p}/activities/${a}/insight`), api(`/projects/${p}/activities/${a}/schedule-impact`), api(`/projects/${p}/activities/${a}/schedule-impact/history`), api(`/projects/${p}/activities/${a}/issues/history`),
    ]);
    state.activityData = { history, trend, risk, insight, schedule, scheduleHistory, issueHistory }; renderActivity();
  } catch (error) { setStatus(error.message, true); renderActivityEmpty("Activity detail could not be loaded."); }
}

function renderActivity() {
  const { history, trend, risk, insight, schedule, scheduleHistory, issueHistory } = state.activityData;
  $("#progress-detail").innerHTML = `<div class="risk-score"><div class="score">${trend.last_progress == null ? "—" : `${trend.last_progress}%`}</div><div><strong>Latest observed progress</strong><div class="risk-copy">${trend.snapshot_count} snapshot${trend.snapshot_count === 1 ? "" : "s"} · ${trend.average_velocity_per_day == null ? "Velocity unavailable" : `${trend.average_velocity_per_day.toFixed(1)} points/day`}</div></div>${trendBadge(trend.trend)}</div><div class="snapshot-list">${history.snapshots.map((snapshot, index) => `<div class="snapshot"><div class="date">${esc(formatDate(snapshot.report_date))}</div><div><strong>${snapshot.progress_percentage == null ? "No progress value" : `${snapshot.progress_percentage}% progress`}</strong><div class="subtle">Submission #${snapshot.submission_order}${snapshot.status ? ` · ${esc(snapshot.status)}` : ""}</div></div><div class="delta">${index ? `${trend.progress_deltas[index - 1] >= 0 ? "+" : ""}${trend.progress_deltas[index - 1]} pts` : "Baseline"}</div></div>`).join("") || empty("No progress snapshots returned.")}</div>`;
  $("#risk-detail").innerHTML = `<div class="risk-score"><div class="score">${risk.risk_score}</div><div><strong>${riskBadge(risk.risk_level)}</strong><div class="risk-copy">Rule-based observed-risk score<br />not a probability or prediction</div></div></div>${risk.risk_signals.length ? `<ul class="signal-list">${risk.risk_signals.map((signal) => `<li>${esc(signal)}</li>`).join("")}</ul>` : empty("No risk signals observed.")}`;
  $("#insights").innerHTML = insight.findings.length ? insight.findings.map((finding) => `<article class="insight-card"><span class="badge ${finding.priority === "high" ? "bad" : finding.priority === "medium" ? "warn" : "good"}">${esc(finding.priority)} priority</span><h3>${esc(finding.title)}</h3><p>${esc(finding.explanation)}</p>${finding.factual_evidence.length ? `<p><strong>Evidence:</strong><br />${finding.factual_evidence.map(esc).join("<br />")}</p>` : ""}<p class="recommendation"><strong>Recommendation:</strong><br />${esc(finding.recommendation || "Review the underlying evidence.")}</p></article>`).join("") : empty(insight.data_note || "No explainable findings for this activity.");
  $("#impact-detail").innerHTML = `<p class="eyebrow">SELECTED ACTIVITY</p><h3>${esc(schedule.activity_name)}</h3><div class="impact-number">${schedule.latest_delay_hours == null ? "—" : `${schedule.latest_delay_hours} hrs`}</div><p>${esc(schedule.summary)}</p>${schedule.latest_delay_reason ? `<p><strong>Latest reason</strong><br />${esc(schedule.latest_delay_reason)}</p>` : ""}${schedule.repeated_delay_reasons.length ? `<p><strong>Repeated reasons</strong><br />${schedule.repeated_delay_reasons.map(esc).join("<br />")}</p>` : ""}`;
  $("#schedule-evidence").innerHTML = renderProjectScheduleEvidence(state.projectData.scheduleHistory, scheduleHistory); $("#issue-evidence").innerHTML = renderProjectIssueEvidence(state.projectData.issueHistory, issueHistory);
}

function renderScheduleEvidence(observations, compact = false) { return observations.length ? observations.map((item) => `<div class="timeline-item"><div class="timeline-meta"><span>${esc(formatDate(item.report_date))}</span><span>Submission #${item.submission_order}</span></div><strong>${item.delay_hours == null ? "Delay reason recorded" : `${item.delay_hours} hours observed`}</strong>${item.delay_reason ? `<div class="subtle">${esc(item.delay_reason)}</div>` : ""}</div>`).join("") : empty(compact ? "No delay evidence for this activity." : "No delay evidence returned."); }
function renderIssueEvidence(observations, compact = false) { return observations.length ? observations.map((item) => `<div class="timeline-item"><div class="timeline-meta"><span>${esc(formatDate(item.report_date))}</span><span>Submission #${item.submission_order}</span></div><strong>${esc(item.issue)}</strong></div>`).join("") : empty(compact ? "No issue evidence for this activity." : "No issue evidence returned."); }
function renderProjectScheduleEvidence(projectHistory, activityHistory) { const projectItems = projectHistory.activities.flatMap((activity) => activity.observations.map((item) => ({ ...item, activity_name: activity.activity_name }))); return `<div class="evidence-group"><div class="evidence-group-title">Project evidence <span>${projectItems.length} observation${projectItems.length === 1 ? "" : "s"}</span></div>${projectItems.length ? projectItems.map((item) => `<div class="timeline-item"><div class="timeline-meta"><span>${esc(formatDate(item.report_date))}</span><span>Submission #${item.submission_order}</span></div><strong>${esc(item.activity_name)} · ${item.delay_hours == null ? "Reason recorded" : `${item.delay_hours} hours`}</strong><div class="subtle">${esc(item.delay_reason || "No reason recorded")}</div></div>`).join("") : empty("No project delay evidence returned.")}</div><div class="evidence-group"><div class="evidence-group-title">Selected activity <span>${activityHistory.observations.length} observation${activityHistory.observations.length === 1 ? "" : "s"}</span></div>${renderScheduleEvidence(activityHistory.observations, true)}</div>`; }
function renderProjectIssueEvidence(projectHistory, activityHistory) { const projectItems = projectHistory.activities.flatMap((activity) => activity.observations.map((item) => ({ ...item, activity_name: activity.activity_name }))); return `<div class="evidence-group"><div class="evidence-group-title">Project evidence <span>${projectItems.length} observation${projectItems.length === 1 ? "" : "s"}</span></div>${projectItems.length ? projectItems.map((item) => `<div class="timeline-item"><div class="timeline-meta"><span>${esc(formatDate(item.report_date))}</span><span>Submission #${item.submission_order}</span></div><strong>${esc(item.activity_name)} · ${esc(item.issue)}</strong></div>`).join("") : empty("No project issue evidence returned.")}</div><div class="evidence-group"><div class="evidence-group-title">Selected activity <span>${activityHistory.observations.length} observation${activityHistory.observations.length === 1 ? "" : "s"}</span></div>${renderIssueEvidence(activityHistory.observations, true)}</div>`; }
function renderActivityEmpty(message = "Select an activity to explore its analysis.") { $("#progress-detail").innerHTML = empty(message); $("#risk-detail").innerHTML = empty(message); $("#impact-detail").innerHTML = empty(message); $("#schedule-evidence").innerHTML = empty(message); $("#issue-evidence").innerHTML = empty(message); }

async function uploadFile(file) {
  const status = $("#upload-status"); status.hidden = false; status.className = "upload-status"; status.textContent = `Processing ${file.name}…`;
  const formData = new FormData(); formData.append("file", file);
  try { const result = await api("/upload", { method: "POST", body: formData }); status.textContent = `${result.original_filename} processed successfully. Refreshing project intelligence…`; closeUpload(); await loadProjects(); }
  catch (error) { status.className = "upload-status error"; status.textContent = error.message; }
}

function closeUpload() { $("#upload-modal").hidden = true; $("#file-input").value = ""; $("#upload-status").hidden = true; }
$("#project-select").addEventListener("change", (event) => loadProjectData(event.target.value)); $("#activity-select").addEventListener("change", (event) => loadActivityData(event.target.value)); $("#refresh-button").addEventListener("click", () => loadProjects(state.project)); $("#upload-trigger").addEventListener("click", () => { $("#upload-modal").hidden = false; }); $("#empty-upload-trigger").addEventListener("click", () => { $("#upload-modal").hidden = false; }); $("#upload-close").addEventListener("click", closeUpload); $("#file-input").addEventListener("change", (event) => event.target.files[0] && uploadFile(event.target.files[0]));
$("#drop-zone").addEventListener("dragover", (event) => { event.preventDefault(); $("#drop-zone").classList.add("dragging"); }); $("#drop-zone").addEventListener("dragleave", () => $("#drop-zone").classList.remove("dragging")); $("#drop-zone").addEventListener("drop", (event) => { event.preventDefault(); $("#drop-zone").classList.remove("dragging"); const file = event.dataTransfer.files[0]; if (file) uploadFile(file); });
document.addEventListener("click", (event) => { const row = event.target.closest("tr[data-activity]"); if (!row) return; const activity = row.dataset.activity; $("#activity-select").value = activity; loadActivityData(activity); window.scrollTo({ top: $("#progress-panel").offsetTop - 20, behavior: "smooth" }); });
loadProjects().catch((error) => setStatus(error.message, true));
