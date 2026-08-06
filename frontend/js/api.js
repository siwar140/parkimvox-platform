// Adresse de votre backend FastAPI
const API_BASE_URL = "http://127.0.0.1:8000";

function getToken() {
  return localStorage.getItem("token");
}

function saveSession(token, role, fullName) {
  localStorage.setItem("token", token);
  localStorage.setItem("role", role);
  localStorage.setItem("full_name", fullName);
}

function clearSession() {
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("full_name");
}

function requireAuth(expectedRole) {
  const token = getToken();
  const role = localStorage.getItem("role");
  if (!token || (expectedRole && role !== expectedRole)) {
    window.location.href = "login.html";
  }
}

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = options.headers || {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData) && options.body) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

  if (response.status === 401) {
    clearSession();
    window.location.href = "login.html";
    return;
  }

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    let message = "Une erreur est survenue";
    if (Array.isArray(data?.detail)) {
      message = data.detail.map(e => e.msg).join(" | ");
    } else if (typeof data?.detail === "string") {
      message = data.detail;
    }
    throw new Error(message);
  }
  return data;
}

function logout() {
  clearSession();
  window.location.href = "login.html";
}
