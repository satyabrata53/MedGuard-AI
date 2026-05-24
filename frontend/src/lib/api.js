function normalizeApiBase(value) {
  return (value || "http://localhost:8000").replace(/\/+$/, "").replace(/\/api$/i, "");
}

const API_BASE = normalizeApiBase(import.meta.env.VITE_API_BASE_URL);

async function post(path, payload = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json();
}

export const api = {
  patients: () => post("/api/patients"),
  safetyCheck: (payload) => post("/api/safety-check", payload),
  askGeneric: (payload) => post("/api/ask-generic", payload),
  askSafe: (payload) => post("/api/ask-safe", payload),
};
