const BASE = (import.meta.env?.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");
const TOKEN_KEY = "mindtrack.token";

export const tokenStore = {
  get: () => { try { return localStorage.getItem(TOKEN_KEY); } catch { return null; } },
  set: (t) => { try { localStorage.setItem(TOKEN_KEY, t); } catch { /* storage unavailable */ } },
  clear: () => { try { localStorage.removeItem(TOKEN_KEY); } catch { /* storage unavailable */ } },
};

export class ApiError extends Error {
  constructor(message, status) { super(message); this.status = status; }
}

// FastAPI returns {detail: "text"} or {detail: [{loc, msg}, ...]} for validation errors.
export function detailToMessage(detail) {
  if (!detail) return null;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => {
      const field = Array.isArray(d.loc) ? d.loc.filter((x) => x !== "body").join(".") : "";
      const msg = String(d.msg || "").replace(/^Value error, /, "");
      return field ? `${field}: ${msg}` : msg;
    }).join(" · ");
  }
  return null;
}

let onUnauthorized = () => {};
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn; };

async function request(method, path, body, { auth = true } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const token = tokenStore.get();
  if (auth && token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(BASE + path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  } catch {
    throw new ApiError(`Can't reach the server at ${BASE}. Is the backend running?`, 0);
  }
  let data = null;
  try { data = await res.json(); } catch { /* empty body */ }
  if (!res.ok) {
    if (res.status === 401 && auth) onUnauthorized();
    throw new ApiError(detailToMessage(data?.detail) || `Request failed (${res.status})`, res.status);
  }
  return data;
}

export const api = {
  register: (b) => request("POST", "/auth/register", b, { auth: false }),
  login: (b) => request("POST", "/auth/login", b, { auth: false }),
  profile: () => request("GET", "/profile"),
  updateExam: (b) => request("PUT", "/profile/exam", b),
  questions: () => request("GET", "/questions"),
  globalInsights: () => request("GET", "/insights/global"),
  submitCheckin: (answers) => request("POST", "/checkins", { answers }),
  today: () => request("GET", "/checkins/today"),
  history: (days = 14) => request("GET", `/checkins/history?days=${days}`),
  weekly: (end) => request("GET", "/reports/weekly" + (end ? `?end=${end}` : "")),
};
