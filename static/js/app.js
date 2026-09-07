const state = {
  roster: [],
  selectedDate: "",
};

document.addEventListener("DOMContentLoaded", initializeApp);

async function initializeApp() {
  setDefaultDateAndTime();
  wireEvents();
  await loadRoster();
  await loadEntries();
}

function wireEvents() {
  document.getElementById("date").addEventListener("change", async event => {
    state.selectedDate = event.target.value;
    await loadEntries();
  });

  document.getElementById("rosterSelect").addEventListener("change", event => {
    applyRosterSelection(event.target.value);
  });

  document.getElementById("saveButton").addEventListener("click", saveEntry);
  document.getElementById("confirmButton").addEventListener("click", confirmEntries);
}

function setDefaultDateAndTime() {
  const today = new Date();
  const dateField = document.getElementById("date");
  const timeField = document.getElementById("startTime");
  if (!dateField.value) {
    dateField.value = formatLocalDate(today);
  }
  if (!timeField.value) {
    timeField.value = `${String(today.getHours()).padStart(2, "0")}:${String(today.getMinutes()).padStart(2, "0")}`;
  }
  state.selectedDate = dateField.value;
}

async function loadRoster() {
  const result = await fetchJson("/api/roster");
  state.roster = result.items || [];
  const select = document.getElementById("rosterSelect");
  select.innerHTML = '<option value="">名簿から選択</option>';
  for (const item of state.roster) {
    const option = document.createElement("option");
    option.value = item.employee_name;
    option.textContent = item.employee_name;
    option.dataset.employeeNumber = item.employee_number || "";
    select.appendChild(option);
  }
}

function applyRosterSelection(employeeName) {
  const item = state.roster.find(entry => entry.employee_name === employeeName);
  if (!item) {
    return;
  }
  document.getElementById("employeeName").value = item.employee_name;
  document.getElementById("employeeNumber").value = item.employee_number || "";
}

async function loadEntries() {
  const date = document.getElementById("date").value;
  const params = new URLSearchParams();
  if (date) {
    params.set("date", date);
  }
  const url = params.toString() ? `/api/entries?${params.toString()}` : "/api/entries";
  const result = await fetchJson(url);
  renderEntries(result.items || []);
}

function renderEntries(items) {
  const tbody = document.getElementById("entriesBody");
  const emptyState = document.getElementById("emptyState");
  tbody.innerHTML = "";
  if (!items.length) {
    emptyState.hidden = false;
    return;
  }
  emptyState.hidden = true;
  for (const item of items) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(item.date)}</td>
      <td>${escapeHtml(item.employee_number)}</td>
      <td>${escapeHtml(item.employee_name)}</td>
      <td>${escapeHtml(item.reason)}</td>
      <td>${escapeHtml(item.start_time)}</td>
      <td>${escapeHtml(item.end_time)}</td>
      <td>${escapeHtml(item.remarks)}</td>
    `;
    tbody.appendChild(tr);
  }
}

async function saveEntry() {
  const button = document.getElementById("saveButton");
  button.disabled = true;
  try {
    const payload = buildPayload();
    const result = await fetchJson("/api/entries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setMessage(result.warning ? `${result.message} ${result.warning}` : result.message, result.warning ? "warning" : "success");
    await loadEntries();
  } catch (error) {
    setMessage(error.message || "保存に失敗しました。", "error");
  } finally {
    button.disabled = false;
  }
}

async function confirmEntries() {
  const button = document.getElementById("confirmButton");
  button.disabled = true;
  try {
    const date = document.getElementById("date").value;
    const result = await fetchJson("/api/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ date }),
    });
    setMessage(`${result.message} (${result.output_file})`, "success");
  } catch (error) {
    setMessage(error.message || "Excel の生成に失敗しました。", "error");
  } finally {
    button.disabled = false;
  }
}

function buildPayload() {
  return {
    date: document.getElementById("date").value,
    employee_number: document.getElementById("employeeNumber").value,
    employee_name: document.getElementById("employeeName").value,
    reason: document.getElementById("reason").value,
    start_time: document.getElementById("startTime").value,
    end_time: document.getElementById("endTime").value,
    remarks: document.getElementById("remarks").value,
  };
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const detail = body && typeof body === "object" ? body.detail : body;
    throw new Error(detail || "Request failed");
  }
  return body;
}

function setMessage(text, kind) {
  const messageArea = document.getElementById("messageArea");
  messageArea.textContent = text || "";
  messageArea.className = `message ${kind || ""}`.trim();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatLocalDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
