/* ============================================================
   API Client — all fetch calls go through here
   ============================================================ */

const API_BASE = "";

function getToken() {
  return localStorage.getItem("vet_token");
}

function getUser() {
  try { return JSON.parse(localStorage.getItem("vet_user") || "null"); } catch { return null; }
}

function logout() {
  localStorage.removeItem("vet_token");
  localStorage.removeItem("vet_user");
  window.location.href = "/";
}

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const resp = await fetch(API_BASE + path, { ...options, headers });

  if (resp.status === 401) { logout(); throw new Error("Session expired"); }

  if (!resp.ok) {
    let msg = `HTTP ${resp.status}`;
    try { const j = await resp.json(); msg = j.detail || msg; } catch {}
    throw new Error(msg);
  }

  if (resp.status === 204) return null;
  const ct = resp.headers.get("content-type") || "";
  if (ct.includes("application/json")) return resp.json();
  return resp.blob();
}

const API = {
  // Auth
  login: (username, password) => {
    const form = new URLSearchParams({ username, password });
    return fetch("/api/auth/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    }).then(r => { if (!r.ok) throw new Error("Invalid credentials"); return r.json(); });
  },
  me: () => apiFetch("/api/auth/me"),

  // Users
  listUsers: () => apiFetch("/api/users"),
  createUser: d => apiFetch("/api/users", { method: "POST", body: JSON.stringify(d) }),
  updateUser: (id, d) => apiFetch(`/api/users/${id}`, { method: "PUT", body: JSON.stringify(d) }),
  deleteUser: id => apiFetch(`/api/users/${id}`, { method: "DELETE" }),

  // Patients
  listPatients: q => apiFetch(`/api/patients${q ? "?q=" + encodeURIComponent(q) : ""}`),
  getPatient: id => apiFetch(`/api/patients/${id}`),
  createPatient: d => apiFetch("/api/patients", { method: "POST", body: JSON.stringify(d) }),
  updatePatient: (id, d) => apiFetch(`/api/patients/${id}`, { method: "PUT", body: JSON.stringify(d) }),
  deletePatient: id => apiFetch(`/api/patients/${id}`, { method: "DELETE" }),

  // Records
  listRecords: params => {
    const qs = new URLSearchParams(params || {}).toString();
    return apiFetch(`/api/records${qs ? "?" + qs : ""}`);
  },
  getRecord: id => apiFetch(`/api/records/${id}`),
  createRecord: d => apiFetch("/api/records", { method: "POST", body: JSON.stringify(d) }),
  updateRecord: (id, d) => apiFetch(`/api/records/${id}`, { method: "PUT", body: JSON.stringify(d) }),
  deleteRecord: id => apiFetch(`/api/records/${id}`, { method: "DELETE" }),

  // Drugs
  listDrugs: rid => apiFetch(`/api/records/${rid}/drugs`),
  addDrug: (rid, d) => apiFetch(`/api/records/${rid}/drugs`, { method: "POST", body: JSON.stringify(d) }),
  updateDrug: (rid, id, d) => apiFetch(`/api/records/${rid}/drugs/${id}`, { method: "PUT", body: JSON.stringify(d) }),
  deleteDrug: (rid, id) => apiFetch(`/api/records/${rid}/drugs/${id}`, { method: "DELETE" }),

  // Monitoring
  listMonitoring: rid => apiFetch(`/api/records/${rid}/monitoring`),
  addMonitoring: (rid, d) => apiFetch(`/api/records/${rid}/monitoring`, { method: "POST", body: JSON.stringify(d) }),
  updateMonitoring: (rid, id, d) => apiFetch(`/api/records/${rid}/monitoring/${id}`, { method: "PUT", body: JSON.stringify(d) }),
  deleteMonitoring: (rid, id) => apiFetch(`/api/records/${rid}/monitoring/${id}`, { method: "DELETE" }),

  // Fluids
  listFluids: rid => apiFetch(`/api/records/${rid}/fluids`),
  addFluid: (rid, d) => apiFetch(`/api/records/${rid}/fluids`, { method: "POST", body: JSON.stringify(d) }),
  updateFluid: (rid, id, d) => apiFetch(`/api/records/${rid}/fluids/${id}`, { method: "PUT", body: JSON.stringify(d) }),
  deleteFluid: (rid, id) => apiFetch(`/api/records/${rid}/fluids/${id}`, { method: "DELETE" }),

  // Emergency
  listEmergency: rid => apiFetch(`/api/records/${rid}/emergency`),
  addEmergency: (rid, d) => apiFetch(`/api/records/${rid}/emergency`, { method: "POST", body: JSON.stringify(d) }),
  updateEmergency: (rid, id, d) => apiFetch(`/api/records/${rid}/emergency/${id}`, { method: "PUT", body: JSON.stringify(d) }),
  deleteEmergency: (rid, id) => apiFetch(`/api/records/${rid}/emergency/${id}`, { method: "DELETE" }),

  // Procedures
  listProcedures: rid => apiFetch(`/api/records/${rid}/procedures`),
  addProcedure: (rid, d) => apiFetch(`/api/records/${rid}/procedures`, { method: "POST", body: JSON.stringify(d) }),
  updateProcedure: (rid, id, d) => apiFetch(`/api/records/${rid}/procedures/${id}`, { method: "PUT", body: JSON.stringify(d) }),
  deleteProcedure: (rid, id) => apiFetch(`/api/records/${rid}/procedures/${id}`, { method: "DELETE" }),

  // Export
  exportPDF: rid => apiFetch(`/api/export/${rid}/pdf`),
  exportDOCX: rid => apiFetch(`/api/export/${rid}/docx`),

  // OR Bookings
  upsertBooking: (rid, d) => apiFetch(`/api/records/${rid}/booking`, { method: "POST", body: JSON.stringify(d) }),
  deleteBooking: rid => apiFetch(`/api/records/${rid}/booking`, { method: "DELETE" }),
  listBookings: params => {
    const qs = new URLSearchParams(params || {}).toString();
    return apiFetch(`/api/bookings${qs ? "?" + qs : ""}`);
  },
  checkSchedule: params => {
    const qs = new URLSearchParams(params || {}).toString();
    return apiFetch(`/api/schedule/check${qs ? "?" + qs : ""}`);
  },

  // Procedure Templates
  listTemplates: () => apiFetch("/api/procedure-templates"),
  createTemplate: d => apiFetch("/api/procedure-templates", { method: "POST", body: JSON.stringify(d) }),
  deleteTemplate: id => apiFetch(`/api/procedure-templates/${id}`, { method: "DELETE" }),

  // Procedure Images
  uploadImage: (rid, file) => {
    const token = getToken();
    const form = new FormData();
    form.append("file", file);
    return fetch(`/api/records/${rid}/images`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}` },
      body: form,
    }).then(async r => {
      if (!r.ok) { const j = await r.json().catch(() => ({})); throw new Error(j.detail || "Upload failed"); }
      return r.json();
    });
  },
  listImages: rid => apiFetch(`/api/records/${rid}/images`),
  updateImage: (rid, iid, params) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/api/records/${rid}/images/${iid}?${qs}`, { method: "PUT" });
  },
  deleteImage: (rid, iid) => apiFetch(`/api/records/${rid}/images/${iid}`, { method: "DELETE" }),
  imageUrl: (rid, filename) => `/api/images/${rid}/${filename}?token=${getToken()}`,

  // Drug Presets
  listDrugPresets: () => apiFetch("/api/drug-presets"),
  createDrugPreset: d => apiFetch("/api/drug-presets", { method: "POST", body: JSON.stringify(d) }),
  updateDrugPreset: (id, d) => apiFetch(`/api/drug-presets/${id}`, { method: "PUT", body: JSON.stringify(d) }),
  deleteDrugPreset: id => apiFetch(`/api/drug-presets/${id}`, { method: "DELETE" }),

  // Surgeon Duty Schedule
  listDuties: params => {
    const qs = new URLSearchParams(params || {}).toString();
    return apiFetch(`/api/duties${qs ? "?" + qs : ""}`);
  },
  createDuty: d => apiFetch("/api/duties", { method: "POST", body: JSON.stringify(d) }),
  updateDuty: (id, d) => apiFetch(`/api/duties/${id}`, { method: "PUT", body: JSON.stringify(d) }),
  deleteDuty: (id, scope) => {
    const qs = scope ? `?scope=${encodeURIComponent(scope)}` : "";
    return apiFetch(`/api/duties/${id}${qs}`, { method: "DELETE" });
  },
};

/* ── Toast notifications ────────────────────────────────── */
function toast(msg, type = "success", duration = 3500) {
  const icons = { success: "✓", error: "✗", warning: "⚠", info: "ℹ" };
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `<span style="font-size:1.1rem">${icons[type] || "ℹ"}</span><span>${msg}</span>`;
  container.appendChild(el);
  setTimeout(() => { el.style.opacity = "0"; el.style.transition = "opacity 0.3s"; setTimeout(() => el.remove(), 300); }, duration);
}

/* ── Helpers ────────────────────────────────────────────── */

// Server returns UTC naive datetimes without 'Z'. Force UTC parsing by appending 'Z'.
function _asUTC(iso) {
  if (!iso) return null;
  const hasZone = iso.endsWith("Z") || /[+-]\d{2}:\d{2}$/.test(iso);
  const d = new Date(hasZone ? iso : iso + "Z");
  return isNaN(d.getTime()) ? null : d;
}

function nowLocalDT() {
  const d = new Date();
  const pad = n => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function nowLocalTime() {
  const d = new Date();
  return d.toTimeString().slice(0, 5);
}

function formatDT(iso) {
  if (!iso) return "";
  try {
    const d = _asUTC(iso);
    if (!d) return iso;
    return d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  } catch { return iso; }
}

function formatDate(iso) {
  if (!iso) return "";
  try {
    const d = _asUTC(iso);
    if (!d) return iso;
    return d.toLocaleDateString("en-GB");
  } catch { return iso; }
}

function isoToLocalDT(iso) {
  if (!iso) return "";
  try {
    const d = _asUTC(iso);
    if (!d) return "";
    const pad = n => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  } catch { return ""; }
}

function localDTtoISO(local) {
  if (!local) return null;
  try { return new Date(local).toISOString(); } catch { return null; }
}

function calcDose(weight, dose, conc) {
  const w = parseFloat(weight), d = parseFloat(dose), c = parseFloat(conc);
  if (!w || !d) return { totalDose: null, volume: null };
  const totalDose = w * d;
  const volume = c ? totalDose / c : null;
  return { totalDose, volume };
}

function secondsToHMS(sec) {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/* ── Auth guard ─────────────────────────────────────────── */
function requireAuth() {
  if (!getToken()) { window.location.href = "/"; return false; }
  return true;
}

/* ── Dark mode ──────────────────────────────────────────── */
function initTheme() {
  const saved = localStorage.getItem("vet_theme") || "light";
  document.documentElement.setAttribute("data-theme", saved);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("vet_theme", next);
}

/* ── Sidebar toggle ─────────────────────────────────────── */
function initSidebar() {
  const toggle = document.getElementById("sidebar-toggle");
  const sidebar = document.getElementById("sidebar");
  if (!toggle || !sidebar) return;
  toggle.addEventListener("click", () => sidebar.classList.toggle("open"));
  document.addEventListener("click", e => {
    if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
      sidebar.classList.remove("open");
    }
  });
}

/* ── Modal helpers ──────────────────────────────────────── */
function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove("hidden");
}

function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add("hidden");
}

initTheme();
