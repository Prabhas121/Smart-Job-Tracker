/**
 * Smart Job Application Intelligence Dashboard
 * Frontend Application Controller (Vanilla JS + Chart.js)
 */

// Application State
const state = {
  currentTab: "overview",
  uploadedFilename: null,
  directoryPage: 1,
  directoryPerPage: 10,
  directoryStatus: "All",
  directorySearch: "",
  charts: {}
};

// DOM Content Loaded Handler
document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initEventListeners();
  loadDashboardSummary();
  loadModelInfo();
});

// ==========================================
// 1. Navigation & Tab Switching
// ==========================================
function initNavigation() {
  const navButtons = document.querySelectorAll(".sidebar-nav .nav-item");
  navButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const tabId = btn.getAttribute("data-tab");
      switchTab(tabId);
    });
  });
}

function switchTab(tabId) {
  state.currentTab = tabId;

  // Update navigation button active state
  document.querySelectorAll(".sidebar-nav .nav-item").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-tab") === tabId);
  });

  // Update tab pane active state
  document.querySelectorAll(".tab-pane").forEach(pane => {
    pane.classList.remove("active");
  });
  const activePane = document.getElementById(`tab-${tabId}`);
  if (activePane) activePane.classList.add("active");

  // Update topbar title
  const titles = {
    "overview": { title: "Recruitment Overview", sub: "Real-time candidate metrics and predictive intelligence" },
    "dataset": { title: "Dataset Management", sub: "Upload, audit, validate, and bulk-import recruitment data into MongoDB" },
    "add-candidate": { title: "Add Candidate", sub: "Manual candidate entry with PyMongo insert_one()" },
    "directory": { title: "Candidate Directory", sub: "Search, filter, and manage applicant outcomes with update_one()" },
    "analytics": { title: "Recruitment Analytics", sub: "Live MongoDB multi-stage aggregation pipelines ($match, $group, $sort)" },
    "prediction": { title: "ML Hiring Prediction", sub: "Random Forest hiring classifier, evaluation metrics, and inference" }
  };

  const meta = titles[tabId] || titles.overview;
  document.getElementById("page-title").textContent = meta.title;
  document.getElementById("page-subtitle").textContent = meta.sub;

  // Load specific tab data when activated
  if (tabId === "overview") loadDashboardSummary();
  if (tabId === "dataset") loadImportHistory();
  if (tabId === "directory") loadCandidateDirectory();
  if (tabId === "analytics") loadRecruitmentAnalytics();
  if (tabId === "prediction") loadModelInfo();
}

// Global Notification Helper
function showNotification(message, type = "info") {
  const box = document.getElementById("notification-box");
  const text = document.getElementById("notification-text");
  box.className = `notification ${type}`;
  text.textContent = message;
  box.classList.remove("hidden");

  // Auto-dismiss after 6 seconds
  setTimeout(() => {
    closeNotification();
  }, 6000);
}

function closeNotification() {
  document.getElementById("notification-box").classList.add("hidden");
}

// ==========================================
// 2. Global Event Listeners
// ==========================================
function initEventListeners() {
  // Global refresh button
  document.getElementById("btn-refresh").addEventListener("click", () => {
    showNotification("Refreshing data from MongoDB...", "info");
    loadDashboardSummary();
    if (state.currentTab === "directory") loadCandidateDirectory();
    if (state.currentTab === "analytics") loadRecruitmentAnalytics();
    if (state.currentTab === "dataset") loadImportHistory();
  });

  // CSV file input change
  const fileInput = document.getElementById("csv-file-input");
  fileInput.addEventListener("change", handleCsvSelection);

  // Drag and drop events
  const dropzone = document.getElementById("dropzone");
  dropzone.addEventListener("dragover", e => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });
  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });
  dropzone.addEventListener("drop", e => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length) {
      fileInput.files = e.dataTransfer.files;
      handleCsvSelection();
    }
  });

  // Quick import bundled dataset button
  document.getElementById("btn-quick-import").addEventListener("click", () => {
    triggerBulkImport(null);
  });

  // Bulk import button
  document.getElementById("btn-execute-bulk-import").addEventListener("click", () => {
    triggerBulkImport(state.uploadedFilename);
  });

  // Add Candidate Form Submit
  document.getElementById("form-add-candidate").addEventListener("submit", handleAddCandidate);

  // Prediction Form Submit
  document.getElementById("form-prediction").addEventListener("submit", handlePredictCandidate);

  // Retrain Model Button
  document.getElementById("btn-retrain-model").addEventListener("click", handleRetrainModel);

  // Directory Search and Status Filter
  document.getElementById("dir-search-input").addEventListener("input", debounce(e => {
    state.directorySearch = e.target.value.trim();
    state.directoryPage = 1;
    loadCandidateDirectory();
  }, 350));

  document.getElementById("dir-status-filter").addEventListener("change", e => {
    state.directoryStatus = e.target.value;
    state.directoryPage = 1;
    loadCandidateDirectory();
  });

  // Pagination buttons
  document.getElementById("btn-page-prev").addEventListener("click", () => {
    if (state.directoryPage > 1) {
      state.directoryPage--;
      loadCandidateDirectory();
    }
  });

  document.getElementById("btn-page-next").addEventListener("click", () => {
    state.directoryPage++;
    loadCandidateDirectory();
  });
}

// ==========================================
// 3. Overview Page Controller
// ==========================================
async function loadDashboardSummary() {
  try {
    const res = await fetch("/api/dashboard/summary");
    const json = await res.json();
    if (!json.success) throw new Error(json.error || "Failed to load summary");

    const d = json.data;
    document.getElementById("kpi-total").textContent = d.total_candidates.toLocaleString();
    document.getElementById("kpi-selected").textContent = d.selected_count.toLocaleString();
    document.getElementById("kpi-rejected").textContent = d.rejected_count.toLocaleString();
    document.getElementById("kpi-pending").textContent = d.pending_count.toLocaleString();
    document.getElementById("kpi-rate").textContent = `${d.selection_rate}%`;

    // Render Recent Candidates Table
    renderRecentCandidates(d.recent_candidates);

    // Render Overview Charts
    renderOverviewCharts(d);

  } catch (err) {
    console.error("Dashboard summary error:", err);
    showNotification(`Error loading dashboard: ${err.message}`, "error");
  }
}

function renderRecentCandidates(candidates) {
  const tbody = document.getElementById("overview-recent-tbody");
  if (!candidates || candidates.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted py-4">No candidates in MongoDB yet. Use Dataset Management to import data.</td></tr>`;
    return;
  }

  tbody.innerHTML = candidates.map(c => `
    <tr>
      <td><strong>${c.candidate_id || "-"}</strong></td>
      <td>${c.candidate_name || "Applicant"}</td>
      <td>${c.education_label || `Level ${c.education_level}`}</td>
      <td>${c.experience_years} yrs</td>
      <td>${c.interview_score}/100</td>
      <td>${c.skill_score}/100</td>
      <td>${getStatusBadge(c.status)}</td>
      <td><span class="badge badge-subtle">${c.source || "db"}</span></td>
      <td class="text-muted">${c.created_at || "-"}</td>
    </tr>
  `).join("");
}

function renderOverviewCharts(data) {
  // Chart 1: Outcome Distribution
  const ctxOutcome = document.getElementById("chartOutcomeOverview").getContext("2d");
  if (state.charts.overviewOutcome) state.charts.overviewOutcome.destroy();

  state.charts.overviewOutcome = new Chart(ctxOutcome, {
    type: "doughnut",
    data: {
      labels: ["Selected / Hired", "Rejected", "Pending Review"],
      datasets: [{
        data: [data.selected_count, data.rejected_count, data.pending_count],
        backgroundColor: ["#10b981", "#ef4444", "#f59e0b"],
        borderWidth: 2,
        borderColor: "#ffffff"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "bottom" }
      }
    }
  });

  // Chart 2: Strategy Overview
  fetchStrategyForOverview();
}

async function fetchStrategyForOverview() {
  try {
    const res = await fetch("/api/analytics/strategy-efficiency");
    const json = await res.json();
    if (!json.success || !json.data) return;

    const strategies = json.data;
    const labels = strategies.map(s => s.strategy_label.split(" (")[0]);
    const selectedCounts = strategies.map(s => s.selected_count);
    const rejectedCounts = strategies.map(s => s.rejected_count);

    const ctx = document.getElementById("chartStrategyOverview").getContext("2d");
    if (state.charts.overviewStrategy) state.charts.overviewStrategy.destroy();

    state.charts.overviewStrategy = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          { label: "Selected", data: selectedCounts, backgroundColor: "#10b981", borderRadius: 4 },
          { label: "Rejected", data: rejectedCounts, backgroundColor: "#cbd5e1", borderRadius: 4 }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { stacked: true },
          y: { stacked: true, beginAtZero: true }
        },
        plugins: {
          legend: { position: "bottom" }
        }
      }
    });
  } catch (e) {
    console.error("Strategy overview fetch failed:", e);
  }
}

// ==========================================
// 4. Dataset Management Page Controller
// ==========================================
async function handleCsvSelection() {
  const fileInput = document.getElementById("csv-file-input");
  if (!fileInput.files || fileInput.files.length === 0) return;

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);

  showNotification(`Auditing and validating '${file.name}'...`, "info");

  try {
    const res = await fetch("/api/dataset/upload", {
      method: "POST",
      body: formData
    });
    const json = await res.json();
    if (!json.success) throw new Error(json.error || "Upload inspection failed");

    const d = json.data;
    state.uploadedFilename = d.filename;

    // Display audit results
    document.getElementById("audit-filename").textContent = d.original_name;
    document.getElementById("audit-rows").textContent = d.total_rows.toLocaleString();
    document.getElementById("audit-cols").textContent = d.total_columns;
    document.getElementById("audit-missing").textContent = d.missing_values_count;
    document.getElementById("audit-duplicates").textContent = d.csv_duplicates_count;
    document.getElementById("audit-valid").textContent = d.valid_records_count.toLocaleString();
    document.getElementById("audit-invalid").textContent = d.invalid_records_count.toLocaleString();

    const auditBadge = document.getElementById("audit-badge");
    if (d.is_schema_valid) {
      auditBadge.textContent = "Schema Validated";
      auditBadge.className = "badge badge-success";
    } else {
      auditBadge.textContent = `Missing Columns: ${d.missing_required_fields.join(", ")}`;
      auditBadge.className = "badge badge-danger";
    }

    // Render Preview Table
    renderDatasetPreview(d.columns, d.preview_rows);

    document.getElementById("dataset-inspection-box").classList.remove("hidden");
    showNotification(`Audit complete: ${d.valid_records_count} valid candidate records ready for MongoDB bulk insert.`, "success");

  } catch (err) {
    console.error("CSV upload error:", err);
    showNotification(`CSV validation failed: ${err.message}`, "error");
  }
}

function renderDatasetPreview(columns, rows) {
  const thead = document.getElementById("preview-thead");
  const tbody = document.getElementById("preview-tbody");

  thead.innerHTML = `<tr>${columns.map(c => `<th>${c}</th>`).join("")}</tr>`;

  if (!rows || rows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="${columns.length}" class="text-center text-muted">No rows to preview</td></tr>`;
    return;
  }

  tbody.innerHTML = rows.map(r => `
    <tr>${columns.map(c => `<td>${r[c] !== undefined ? r[c] : ""}</td>`).join("")}</tr>
  `).join("");
}

async function triggerBulkImport(filename) {
  showNotification("Executing MongoDB bulk insertion via PyMongo insert_many()...", "info");

  try {
    const res = await fetch("/api/dataset/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: filename })
    });
    const json = await res.json();
    if (!json.success) throw new Error(json.error || "Bulk import failed");

    const s = json.import_summary;
    showNotification(
      `Success: ${s.inserted_count} new candidate documents inserted into MongoDB via insert_many(). ${s.skipped_duplicates} duplicates safely skipped.`,
      "success"
    );

    // Refresh history and overview KPIs
    loadImportHistory();
    loadDashboardSummary();

  } catch (err) {
    console.error("Bulk import error:", err);
    showNotification(`Import failed: ${err.message}`, "error");
  }
}

async function loadImportHistory() {
  try {
    const res = await fetch("/api/dataset/history");
    const json = await res.json();
    if (!json.success) return;

    const tbody = document.getElementById("import-history-tbody");
    if (!json.data || json.data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4">No import logs recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = json.data.map(h => `
      <tr>
        <td><strong>${h.source_file}</strong></td>
        <td>${h.imported_at}</td>
        <td>${h.total_rows.toLocaleString()}</td>
        <td class="text-green font-weight-bold">+${h.inserted_count.toLocaleString()}</td>
        <td class="text-muted">${h.skipped_duplicates.toLocaleString()} skipped</td>
        <td>${h.invalid_records || 0}</td>
        <td><span class="badge badge-success">${h.status}</span></td>
      </tr>
    `).join("");

  } catch (e) {
    console.error("Failed to load import history:", e);
  }
}

// ==========================================
// 5. Add Candidate Controller
// ==========================================
async function handleAddCandidate(e) {
  e.preventDefault();

  const payload = {
    candidate_name: document.getElementById("add-name").value.trim(),
    candidate_id: document.getElementById("add-id").value.trim(),
    Age: parseInt(document.getElementById("add-age").value),
    Gender: parseInt(document.getElementById("add-gender").value),
    EducationLevel: parseInt(document.getElementById("add-education").value),
    ExperienceYears: parseFloat(document.getElementById("add-experience").value),
    PreviousCompanies: parseInt(document.getElementById("add-companies").value),
    DistanceFromCompany: parseFloat(document.getElementById("add-distance").value),
    InterviewScore: parseFloat(document.getElementById("add-interview").value),
    SkillScore: parseFloat(document.getElementById("add-skill").value),
    PersonalityScore: parseFloat(document.getElementById("add-personality").value),
    RecruitmentStrategy: parseInt(document.getElementById("add-strategy").value),
    status: document.getElementById("add-status").value
  };

  showNotification("Inserting candidate document via insert_one()...", "info");

  try {
    const res = await fetch("/api/candidates", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const json = await res.json();
    if (!json.success) throw new Error(json.message || json.error || "Failed to insert candidate");

    showNotification(`Candidate '${json.candidate.candidate_name}' (${json.candidate.candidate_id}) saved to MongoDB via insert_one()!`, "success");

    // Reset form
    document.getElementById("form-add-candidate").reset();
    document.getElementById("add-status").value = "Pending";

    // Refresh overview stats
    loadDashboardSummary();

  } catch (err) {
    console.error("Add candidate error:", err);
    showNotification(`Failed to add candidate: ${err.message}`, "error");
  }
}

// ==========================================
// 6. Candidate Directory & Update Outcome
// ==========================================
async function loadCandidateDirectory() {
  const tbody = document.getElementById("directory-tbody");
  tbody.innerHTML = `<tr><td colspan="11" class="text-center text-muted py-4">Fetching candidates from MongoDB...</td></tr>`;

  try {
    const params = new URLSearchParams({
      page: state.directoryPage,
      per_page: state.directoryPerPage,
      status: state.directoryStatus,
      search: state.directorySearch
    });

    const res = await fetch(`/api/candidates?${params.toString()}`);
    const json = await res.json();
    if (!json.success) throw new Error(json.error || "Failed to fetch candidates");

    const candidates = json.data;
    const pag = json.pagination;

    // Update pagination badges
    document.getElementById("pagination-current-page").textContent = `${pag.page} / ${pag.total_pages}`;
    document.getElementById("pagination-info").textContent = `Showing ${(pag.page - 1) * pag.per_page + 1} - ${Math.min(pag.page * pag.per_page, pag.total_records)} of ${pag.total_records} candidates`;

    document.getElementById("btn-page-prev").disabled = pag.page <= 1;
    document.getElementById("btn-page-next").disabled = pag.page >= pag.total_pages;

    if (!candidates || candidates.length === 0) {
      tbody.innerHTML = `<tr><td colspan="11" class="text-center text-muted py-4">No candidates matching current criteria.</td></tr>`;
      return;
    }

    tbody.innerHTML = candidates.map(c => `
      <tr>
        <td><strong>${c.candidate_id || "-"}</strong></td>
        <td>${c.candidate_name || "Applicant"}</td>
        <td>${c.education_label || `Level ${c.education_level}`}</td>
        <td>${c.experience_years} yrs</td>
        <td>${c.interview_score}</td>
        <td>${c.skill_score}</td>
        <td>${c.personality_score}</td>
        <td><span class="badge badge-subtle">${c.strategy_label ? c.strategy_label.split(" (")[0] : `Strategy ${c.recruitment_strategy}`}</span></td>
        <td>${getStatusBadge(c.status)}</td>
        <td><small class="text-muted">${c.source || "db"}</small></td>
        <td>
          ${c.status === "Pending" ? `
            <div class="btn-group-sm">
              <button class="btn btn-sm btn-outline text-green" title="Mark Selected (update_one)" onclick="updateCandidateStatus('${c.candidate_id}', 'Selected')">&#10003; Select</button>
              <button class="btn btn-sm btn-outline text-red" title="Mark Rejected (update_one)" onclick="updateCandidateStatus('${c.candidate_id}', 'Rejected')">&times; Reject</button>
            </div>
          ` : `
            <span class="text-muted"><small>Finalized</small></span>
          `}
        </td>
      </tr>
    `).join("");

  } catch (err) {
    console.error("Directory error:", err);
    tbody.innerHTML = `<tr><td colspan="11" class="text-center text-red py-4">Error loading directory: ${err.message}</td></tr>`;
  }
}

async function updateCandidateStatus(candidateId, newStatus) {
  try {
    const res = await fetch(`/api/candidates/${candidateId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });
    const json = await res.json();
    if (!json.success) throw new Error(json.error || "Update failed");

    showNotification(`Candidate ${candidateId} updated to ${newStatus} using update_one()! Now eligible for ML retraining.`, "success");
    loadCandidateDirectory();
    loadDashboardSummary();

  } catch (err) {
    showNotification(`Failed to update candidate: ${err.message}`, "error");
  }
}

// ==========================================
// 7. Recruitment Analytics Page Controller
// ==========================================
async function loadRecruitmentAnalytics() {
  try {
    const res = await fetch("/api/analytics/overview");
    const json = await res.json();
    if (!json.success) throw new Error(json.error || "Failed to run aggregation pipelines");

    const { outcomes, strategies, experience_tiers } = json.data;

    // Chart: Pipeline 1 Outcome Averages
    renderAnalyticsOutcomeChart(outcomes);

    // Chart: Pipeline 2 Strategy Efficiency
    renderAnalyticsStrategyChart(strategies);

    // Table: Pipeline 3 Experience Tiers
    renderAnalyticsTiersTable(experience_tiers);

  } catch (err) {
    console.error("Analytics pipeline error:", err);
    showNotification(`Failed to run MongoDB pipelines: ${err.message}`, "error");
  }
}

function renderAnalyticsOutcomeChart(outcomes) {
  const ctx = document.getElementById("chartAnalyticsOutcome").getContext("2d");
  if (state.charts.analyticsOutcome) state.charts.analyticsOutcome.destroy();

  const labels = outcomes.map(o => o.status);
  const interviewScores = outcomes.map(o => o.avg_interview_score);
  const skillScores = outcomes.map(o => o.avg_skill_score);
  const personalityScores = outcomes.map(o => o.avg_personality_score);

  state.charts.analyticsOutcome = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        { label: "Avg Interview Score", data: interviewScores, backgroundColor: "#4f46e5", borderRadius: 4 },
        { label: "Avg Skill Score", data: skillScores, backgroundColor: "#10b981", borderRadius: 4 },
        { label: "Avg Personality Score", data: personalityScores, backgroundColor: "#f59e0b", borderRadius: 4 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { beginAtZero: true, max: 100 }
      },
      plugins: {
        legend: { position: "bottom" }
      }
    }
  });
}

function renderAnalyticsStrategyChart(strategies) {
  const ctx = document.getElementById("chartAnalyticsStrategy").getContext("2d");
  if (state.charts.analyticsStrategy) state.charts.analyticsStrategy.destroy();

  const labels = strategies.map(s => s.strategy_label.split(" (")[0]);
  const rates = strategies.map(s => s.selection_rate);
  const volumes = strategies.map(s => s.total_candidates);

  state.charts.analyticsStrategy = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          type: "bar",
          label: "Selection Rate (%)",
          data: rates,
          backgroundColor: "#7c3aed",
          borderRadius: 4,
          yAxisID: "yRate"
        },
        {
          type: "line",
          label: "Candidate Volume",
          data: volumes,
          borderColor: "#2563eb",
          backgroundColor: "#2563eb",
          tension: 0.2,
          yAxisID: "yVol"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        yRate: { type: "linear", position: "left", beginAtZero: true, max: 100, title: { display: true, text: "Selection %" } },
        yVol: { type: "linear", position: "right", beginAtZero: true, grid: { drawOnChartArea: false }, title: { display: true, text: "Candidates" } }
      },
      plugins: {
        legend: { position: "bottom" }
      }
    }
  });
}

function renderAnalyticsTiersTable(tiers) {
  const tbody = document.getElementById("analytics-tiers-tbody");
  if (!tiers || tiers.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted py-4">No tier records found.</td></tr>`;
    return;
  }

  tbody.innerHTML = tiers.map(t => `
    <tr>
      <td><strong>${t.tier}</strong></td>
      <td>${t.total_candidates.toLocaleString()}</td>
      <td class="text-green">${t.selected_count.toLocaleString()}</td>
      <td class="text-red">${t.rejected_count.toLocaleString()}</td>
      <td class="text-amber">${t.pending_count || 0}</td>
      <td><strong>${t.selection_rate}%</strong></td>
      <td>${t.avg_interview_score}/100</td>
      <td>${t.avg_skill_score}/100</td>
    </tr>
  `).join("");
}

// ==========================================
// 8. ML Hiring Prediction Page Controller
// ==========================================
async function loadModelInfo() {
  try {
    const res = await fetch("/api/prediction/model-info");
    const json = await res.json();
    if (!json.success || !json.active_model) return;

    const m = json.active_model;
    const metrics = m.metrics || {};

    document.getElementById("model-version-badge").textContent = `Version ${m.version || "v1.0.0"}`;
    document.getElementById("metric-accuracy").textContent = metrics.accuracy_pct ? `${metrics.accuracy_pct}%` : "--%";
    document.getElementById("metric-precision").textContent = metrics.precision !== undefined ? metrics.precision : "--";
    document.getElementById("metric-recall").textContent = metrics.recall !== undefined ? metrics.recall : "--";
    document.getElementById("metric-f1").textContent = metrics.f1_score !== undefined ? metrics.f1_score : "--";
    document.getElementById("metric-roc").textContent = metrics.roc_auc !== undefined ? metrics.roc_auc : "--";

    // Confusion Matrix cells
    if (metrics.confusion_matrix) {
      const cm = metrics.confusion_matrix;
      document.getElementById("cm-tn").innerHTML = `${cm.true_negatives} <span class="cm-tag">True Neg</span>`;
      document.getElementById("cm-fp").innerHTML = `${cm.false_positives} <span class="cm-tag">False Pos</span>`;
      document.getElementById("cm-fn").innerHTML = `${cm.false_negatives} <span class="cm-tag">False Neg</span>`;
      document.getElementById("cm-tp").innerHTML = `${cm.true_positives} <span class="cm-tag">True Pos</span>`;
    }

    // Feature Importances Horizontal Bar Chart
    if (m.feature_importances) {
      renderFeatureImportanceChart(m.feature_importances);
    }

  } catch (err) {
    console.error("Failed to load model info:", err);
  }
}

function renderFeatureImportanceChart(importances) {
  const ctx = document.getElementById("chartFeatureImportances").getContext("2d");
  if (state.charts.featureImportance) state.charts.featureImportance.destroy();

  const labels = Object.keys(importances);
  const values = Object.values(importances).map(v => Math.round(v * 1000) / 10); // percentage

  state.charts.featureImportance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Importance Weight (%)",
        data: values,
        backgroundColor: "#6366f1",
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { beginAtZero: true, max: 40 }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}

async function handlePredictCandidate(e) {
  e.preventDefault();

  const payload = {
    candidate_name: document.getElementById("pred-name").value.trim() || "Applicant",
    EducationLevel: parseInt(document.getElementById("pred-education").value),
    ExperienceYears: parseFloat(document.getElementById("pred-experience").value),
    PreviousCompanies: parseInt(document.getElementById("pred-companies").value),
    DistanceFromCompany: parseFloat(document.getElementById("pred-distance").value),
    InterviewScore: parseFloat(document.getElementById("pred-interview").value),
    SkillScore: parseFloat(document.getElementById("pred-skill").value),
    PersonalityScore: parseFloat(document.getElementById("pred-personality").value),
    RecruitmentStrategy: parseInt(document.getElementById("pred-strategy").value)
  };

  showNotification("Evaluating candidate attributes with Random Forest model...", "info");

  try {
    const res = await fetch("/api/prediction/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const json = await res.json();
    if (!json.success) throw new Error(json.error || "Prediction request failed");

    const d = json.data;
    const isSelected = d.predicted_outcome === "Selected";

    document.getElementById("res-candidate-name").textContent = d.candidate_name;
    document.getElementById("res-model-tag").textContent = `Evaluated with ${d.model_algorithm} (${d.model_version})`;

    const badge = document.getElementById("res-outcome-badge");
    badge.textContent = d.predicted_outcome;
    badge.className = `result-badge ${isSelected ? "badge-selected" : "badge-rejected"}`;

    document.getElementById("res-prob-pct").textContent = `${d.selection_probability_pct}%`;
    const fill = document.getElementById("res-progress-fill");
    fill.style.width = `${d.selection_probability_pct}%`;
    fill.className = `progress-bar-fill ${isSelected ? "fill-green" : "fill-red"}`;

    document.getElementById("res-confidence").textContent = `${d.confidence_score}%`;

    // Key factors
    const list = document.getElementById("res-factors-list");
    if (d.key_factors && d.key_factors.length > 0) {
      list.innerHTML = d.key_factors.map(f => `<li>${f}</li>`).join("");
      document.getElementById("res-factors-box").classList.remove("hidden");
    } else {
      document.getElementById("res-factors-box").classList.add("hidden");
    }

    document.getElementById("res-disclaimer-text").textContent = d.disclaimer;
    document.getElementById("prediction-result-box").classList.remove("hidden");

    showNotification(`Inference complete: Candidate predicted '${d.predicted_outcome}' with ${d.confidence_score}% confidence.`, "success");

  } catch (err) {
    console.error("Prediction error:", err);
    showNotification(`Prediction failed: ${err.message}`, "error");
  }
}

async function handleRetrainModel() {
  if (!confirm("Retrain the Random Forest model on all currently verified candidate records in MongoDB?")) return;

  showNotification("Retraining Random Forest Classifier on MongoDB records...", "info");

  try {
    const res = await fetch("/api/prediction/train", {
      method: "POST"
    });
    const json = await res.json();
    if (!json.success) throw new Error(json.error || "Retraining failed");

    showNotification(`Model retraining complete: ${json.data.version} saved with ${json.data.metrics.accuracy_pct}% accuracy!`, "success");
    loadModelInfo();

  } catch (err) {
    console.error("Retrain error:", err);
    showNotification(`Retraining failed: ${err.message}`, "error");
  }
}

// ==========================================
// Helper Utilities
// ==========================================
function getStatusBadge(status) {
  if (status === "Selected") return `<span class="badge badge-success">&#10003; Selected</span>`;
  if (status === "Rejected") return `<span class="badge badge-danger">&times; Rejected</span>`;
  return `<span class="badge badge-warning">&#9679; Pending</span>`;
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
