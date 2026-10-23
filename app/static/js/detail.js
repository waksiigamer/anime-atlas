// detail.js — watch-later / watched buttons on the anime detail page

const $ = (id) => document.getElementById(id);

const DEFAULT_REGION = "BR";
const REGION_STORAGE_KEY = "catalog_region";

function getCurrentRegion() {
  return localStorage.getItem(REGION_STORAGE_KEY) || DEFAULT_REGION;
}

async function fetchUserStatuses() {
  try {
    const region = getCurrentRegion();

    const res = await fetch(
      `/api/user/anime?region=${encodeURIComponent(region)}`
    );

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    return await res.json();
  } catch (err) {
    console.error("detail.js: failed to load user statuses", err);
    return [];
  }
}

function setButtonState(button, active) {
  if (!button) return;

  button.classList.toggle("active", !!active);
  button.setAttribute("aria-pressed", active ? "true" : "false");
}

/*
  UI logic:
  - only one status should be active at a time (watched OR watch_later)
  - clicking an active button removes the status
  - clicking an inactive button sets that status
*/

async function setStatusOnServer(animeId, status) {
  if (!status) {
    const res = await fetch(
      `/api/user/anime/${encodeURIComponent(animeId)}`,
      {
        method: "DELETE",
      }
    );

    if (!res.ok) {
      throw new Error(`DELETE failed: ${res.status}`);
    }

    return null;
  }

  const res = await fetch("/api/user/anime", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      anime_id: animeId,
      status,
    }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`POST failed: ${res.status} ${text}`);
  }

  return status;
}

async function initDetailActions() {
  const detail = document.getElementById("detail");

  if (!detail) {
    console.warn(
      "detail.js: #detail wrapper not found, skipping detail actions"
    );
    return;
  }

  const animeId = detail.dataset.animeId;

  if (!animeId) {
    console.warn(
      "detail.js: anime id missing in data-anime-id"
    );
    return;
  }

  const watchedBtn = $("watched-btn");
  const watchLaterBtn = $("watch-later-btn");

  if (!watchedBtn || !watchLaterBtn) {
    console.warn(
      "detail.js: action buttons missing"
    );
    return;
  }

  // Load user statuses for the currently selected catalog.
  try {
    const statuses = await fetchUserStatuses();

    const myStatus = statuses.find(
      (s) => String(s.anime_id) === String(animeId)
    );

    const statusValue = myStatus?.status || null;

    setButtonState(
      watchedBtn,
      statusValue === "watched"
    );

    setButtonState(
      watchLaterBtn,
      statusValue === "watch_later"
    );
  } catch (err) {
    console.error(
      "detail.js: error setting initial states",
      err
    );
  }

  async function toggleStatus(targetBtn, actionValue) {
    const isActive = targetBtn.classList.contains("active");

    const newStatus = isActive
      ? null
      : actionValue;

    // Optimistic UI
    setButtonState(
      watchedBtn,
      newStatus === "watched"
    );

    setButtonState(
      watchLaterBtn,
      newStatus === "watch_later"
    );

    try {
      await setStatusOnServer(
        animeId,
        newStatus
      );
    } catch (err) {
      console.error(
        "detail.js: failed to update status",
        err
      );

      // Revert UI by refetching the current status.
      try {
        const statuses = await fetchUserStatuses();

        const myStatus = statuses.find(
          (s) =>
            String(s.anime_id) === String(animeId)
        );

        const statusValue =
          myStatus?.status || null;

        setButtonState(
          watchedBtn,
          statusValue === "watched"
        );

        setButtonState(
          watchLaterBtn,
          statusValue === "watch_later"
        );
      } catch (e) {
        setButtonState(watchedBtn, false);
        setButtonState(watchLaterBtn, false);
      }
    }
  }

  watchedBtn.addEventListener("click", (e) => {
    e.preventDefault();
    toggleStatus(watchedBtn, "watched");
  });

  watchLaterBtn.addEventListener("click", (e) => {
    e.preventDefault();
    toggleStatus(
      watchLaterBtn,
      "watch_later"
    );
  });
}

// Run on DOM ready
if (document.readyState === "loading") {
  document.addEventListener(
    "DOMContentLoaded",
    initDetailActions
  );
} else {
  initDetailActions();
}