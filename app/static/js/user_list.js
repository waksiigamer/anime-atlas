const grid = document.getElementById("grid");
const statusMessage = document.getElementById("status");
const currentListStatus = window.USER_LIST_STATUS || "";

const DEFAULT_REGION = "BR";
const REGION_STORAGE_KEY = "catalog_region";

const urlRegion = new URLSearchParams(location.search).get("region");

let currentRegion =
  urlRegion ||
  localStorage.getItem(REGION_STORAGE_KEY) ||
  DEFAULT_REGION;

localStorage.setItem(REGION_STORAGE_KEY, currentRegion);

grid.addEventListener("click", async (event) => {
  const button = event.target.closest(".card-action");

  if (!button) return;

  event.preventDefault();
  event.stopPropagation();

  const animeId = button.dataset.animeId;
  const newStatus = button.dataset.action;
  const cardElement = button.closest(".card");

  // Remover status
  if (button.classList.contains("active")) {
    try {
      const response = await fetch(
        `/api/user/anime/${encodeURIComponent(animeId)}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      if (currentListStatus) {
        cardElement.remove();
      } else {
        cardElement
          .querySelectorAll(".card-action")
          .forEach((action) => action.classList.remove("active"));
      }
    } catch (error) {
      console.error("Erro ao remover status:", error);
    }

    return;
  }

  // Definir novo status
  try {
    const response = await fetch("/api/user/anime", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        anime_id: animeId,
        status: newStatus,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    if (currentListStatus && newStatus !== currentListStatus) {
      cardElement.remove();
      return;
    }

    cardElement
      .querySelectorAll(".card-action")
      .forEach((action) => action.classList.remove("active"));

    button.classList.add("active");
  } catch (error) {
    console.error("Erro ao salvar status:", error);
  }
});

async function loadLibrary(status = "") {
  statusMessage.textContent = "Carregando…";
  grid.innerHTML = "";

  try {
    const region = getCurrentRegion();

    const params = new URLSearchParams();
    params.set("region", region);

    if (status) {
      params.set("status", status);
    }

    const response = await fetch(
      `/api/user/anime?${params.toString()}`
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const animes = await response.json();

    if (!animes.length) {
      statusMessage.textContent =
        "Nenhum anime nesta lista.";
      return;
    }

    grid.innerHTML = animes.map(card).join("");
    statusMessage.textContent = "";
  } catch (error) {
    console.error(
      "Erro ao carregar biblioteca:",
      error
    );

    statusMessage.textContent =
      "Não foi possível carregar sua biblioteca.";
  }
}

function card(anime) {
  const region = getCurrentRegion();

  const imageHtml = anime.card_image
    ? `<img src="${anime.card_image}" alt="">`
    : '<div class="fallback"></div>';

  const badge = anime.maturity_icon
    ? `<div class="maturity-badge">
         <img
           src="${anime.maturity_icon}"
           alt="${anime.maturity_label || ""}"
         >
       </div>`
    : "";

  const actions = `
    <div class="card-actions">
      <button
        type="button"
        class="card-action ${anime.status === "watched" ? "active" : ""
    }"
        data-action="watched"
        data-anime-id="${anime.id}"
        title="Marcar como assistido"
        aria-label="Marcar como assistido"
      >✓</button>

      <button
        type="button"
        class="card-action ${anime.status === "watch_later" ? "active" : ""
    }"
        data-action="watch_later"
        data-anime-id="${anime.id}"
        title="Adicionar à lista de assistir mais tarde"
        aria-label="Adicionar à lista de assistir mais tarde"
      >🔖</button>
    </div>
  `;

  return `
    <a
      class="card"
      href="/anime/${anime.id}?region=${encodeURIComponent(region)}"
    >
      <div class="image-wrap">
        ${imageHtml}
        ${badge}
        ${actions}
      </div>

      <div>
        <h2>${anime.title}</h2>
        <span>
          ${anime.year || "—"} · ★ ${anime.rating ?? "—"}
        </span>
        <p class="tag">
          ${(anime.genres || []).slice(0, 3).join(" · ")}
        </p>
      </div>
    </a>
  `;
}

loadLibrary(window.USER_LIST_STATUS);