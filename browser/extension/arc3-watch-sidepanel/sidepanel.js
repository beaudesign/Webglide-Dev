const STORAGE_KEY = "watchOrigin";

function normalizeOrigin(raw) {
  try {
    const u = new URL(raw.trim());
    return u.origin + "/";
  } catch {
    return "http://127.0.0.1:8765/";
  }
}

async function loadOrigin() {
  const { [STORAGE_KEY]: stored } = await chrome.storage.local.get(STORAGE_KEY);
  if (typeof stored === "string" && stored) {
    return normalizeOrigin(stored);
  }
  return "http://127.0.0.1:8765/";
}

async function saveOrigin(value) {
  const normalized = normalizeOrigin(value);
  await chrome.storage.local.set({ [STORAGE_KEY]: normalized });
  return normalized;
}

async function init() {
  const input = document.getElementById("origin");
  const iframe = document.getElementById("panel");
  const apply = document.getElementById("apply");

  input.value = await loadOrigin();
  iframe.src = new URL("/", input.value).href;

  apply.addEventListener("click", async () => {
    const o = await saveOrigin(input.value);
    input.value = o;
    iframe.src = new URL("/", o).href;
  });
}

init();
