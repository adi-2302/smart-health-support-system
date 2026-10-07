const KEY = "mindtrack.theme"; // "light" | "dark" | "system"

export function getTheme() {
  try { return localStorage.getItem(KEY) || "system"; } catch { return "system"; }
}

export function setTheme(mode) {
  try { localStorage.setItem(KEY, mode); } catch { /* storage unavailable */ }
  applyTheme(mode);
}

function applyTheme(mode) {
  const root = document.documentElement;
  if (mode === "system") root.removeAttribute("data-theme");
  else root.setAttribute("data-theme", mode);
}

export function initTheme() { applyTheme(getTheme()); }
