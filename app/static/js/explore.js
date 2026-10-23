import { createCollapsible } from "./filters.js";

const grid = document.getElementById("explore-grid");
const statusMessage = document.getElementById("explore-status");
const searchInput = document.getElementById("explore-search");
const sortSelect = document.getElementById("explore-sort");
const seasonInput = document.getElementById("explore-season-count");
const episodeInput = document.getElementById("explore-episode-count");
const tagsContainer = document.getElementById("explore-tags");
const clearButton = document.getElementById("explore-clear");
const moreButton = document.getElementById("explore-more");
const sentinel = document.getElementById("explore-sentinel");
const yearRoot = document.getElementById("explore-year-root");

const REGIONS = {
    BR: {
        name: "Brasil",
        flag: "/static/icons/flags/br.svg",
    },
    NL: {
        name: "Nederland",
        flag: "/static/icons/flags/nl.svg",
    },
    US: {
        name: "United States",
        flag: "/static/icons/flags/us.svg",
    },
    UK: {
        name: "United Kingdom",
        flag: "/static/icons/flags/uk.svg",
    },
};

const PAGE_SIZE = 25;

let page = 1;
let loading = false;
let finished = false;
let searchTimeout = null;


/* =========================================================
   CARDS
   ========================================================= */

function renderRegions(regions) {
    return `
    <div class="card-regions">
      ${regions
            .map((region) => {
                const data = REGIONS[region];

                if (!data) {
                    return `<span>${region}</span>`;
                }

                return `
            <img
              src="${data.flag}"
              alt="${data.name}"
              title="${data.name}"
              class="card-region-flag"
            >
          `;
            })
            .join("")}
    </div>
  `;
}

function card(anime) {
    const region = anime.regions.includes("US")
        ? "US"
        : anime.regions[0];

    const imageHtml = anime.card_image
        ? `
      <img
        src="${anime.card_image}"
        alt=""
        loading="lazy"
      >
    `
        : `<div class="fallback"></div>`;

    const maturityBadge = anime.maturity_icon
        ? `
      <div class="maturity-badge">
        <img
          src="${anime.maturity_icon}"
          alt="${anime.maturity_label || ""}"
        >
      </div>
    `
        : "";

    return `
    <a
      class="card"
      href="/anime/${encodeURIComponent(anime.id)}?region=${encodeURIComponent(region)}"
    >
      <div class="image-wrap">
        ${imageHtml}
        ${maturityBadge}
      </div>

      <div>
        <h2>${anime.title}</h2>

        <span>
          ${anime.year || "—"} · ★ ${anime.rating ?? "—"}
        </span>

        ${renderRegions(anime.regions)}
      </div>
    </a>
  `;
}


/* =========================================================
   TAGS
   ========================================================= */

function renderOptions(values, container) {
    container.innerHTML = values
        .map(
            (value) => `
        <button
          type="button"
          class="filter-option"
          data-value="${value}"
        >
          ${value}
        </button>
      `
        )
        .join("");
}

function getSelectedValues(container) {
    return [
        ...container.querySelectorAll(
            ".filter-option.selected"
        ),
    ].map(
        (option) => option.dataset.value
    );
}

function getSelectedYears() {
    const yearSelect =
        document.getElementById("explore-year");

    if (!yearSelect) {
        return [];
    }

    return [
        ...yearSelect.selectedOptions,
    ]
        .map((option) => option.value)
        .filter(Boolean);
}


/* =========================================================
   FILTERS
   ========================================================= */

async function loadFilters() {
    const response = await fetch(
        "/api/explore/filters"
    );

    if (!response.ok) {
        throw new Error(
            `HTTP ${response.status}`
        );
    }

    const filters = await response.json();

    const yearWrapper = createCollapsible(
        "year_wrap",
        "Ano",
        filters.years,
        {
            multiple: true,
            emptyLabel: "Sem filtro",
        }
    );

    yearRoot.innerHTML = "";
    yearRoot.appendChild(yearWrapper);

    const yearSelect =
        yearWrapper.querySelector("select");

    yearSelect.id = "explore-year";

    yearSelect.addEventListener(
        "change",
        resetResults
    );

    renderOptions(
        filters.tags,
        tagsContainer
    );
}


/* =========================================================
   QUERY
   ========================================================= */

function buildParams() {
    const params = new URLSearchParams();

    const query = searchInput.value.trim();

    if (query) {
        params.set("q", query);
    }

    if (sortSelect.value) {
        params.set(
            "sort",
            sortSelect.value
        );
    }

    for (const year of getSelectedYears()) {
        params.append(
            "year",
            year
        );
    }

    for (
        const tag of getSelectedValues(
            tagsContainer
        )
    ) {
        params.append(
            "tags",
            tag
        );
    }

    if (seasonInput.value !== "") {
        params.set(
            "season_count_min",
            seasonInput.value
        );
    }

    if (episodeInput.value !== "") {
        params.set(
            "episode_count_min",
            episodeInput.value
        );
    }

    params.set(
        "page",
        page
    );

    params.set(
        "page_size",
        PAGE_SIZE
    );

    return params;
}


/* =========================================================
   RESULTS
   ========================================================= */

function updateStatus(total) {
    statusMessage.textContent =
        `${total.toLocaleString("pt-BR")} anime(s) encontrado(s).`;
}

function updateMoreButton(hasNextPage) {
    finished = !hasNextPage;
    moreButton.hidden = !hasNextPage;
    moreButton.disabled = loading;
}

async function load({ reset = false } = {}) {
    if (
        loading ||
        (!reset && finished)
    ) {
        return;
    }

    if (reset) {
        page = 1;
        finished = false;
        grid.innerHTML = "";
    }

    loading = true;
    moreButton.disabled = true;

    if (reset) {
        statusMessage.textContent =
            "Carregando…";
    }

    try {
        const params = buildParams();

        const response = await fetch(
            `/api/explore?${params.toString()}`
        );

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        const data = await response.json();

        if (
            reset &&
            data.items.length === 0
        ) {
            statusMessage.textContent =
                "Nenhum anime encontrado.";

            updateMoreButton(false);
            return;
        }

        grid.insertAdjacentHTML(
            "beforeend",
            data.items
                .map(card)
                .join("")
        );

        updateStatus(
            data.pagination.total_items
        );

        updateMoreButton(
            data.pagination.has_next_page
        );

        page += 1;
    } catch (error) {
        console.error(
            "Erro ao carregar catálogo:",
            error
        );

        if (reset) {
            statusMessage.textContent =
                "Não foi possível carregar o catálogo.";
        }
    } finally {
        loading = false;
        moreButton.disabled = false;
    }
}

function resetResults() {
    load({
        reset: true,
    });
}


/* =========================================================
   EVENTS
   ========================================================= */

searchInput.addEventListener(
    "input",
    () => {
        clearTimeout(
            searchTimeout
        );

        searchTimeout =
            setTimeout(
                resetResults,
                300
            );
    }
);

sortSelect.addEventListener(
    "change",
    resetResults
);

seasonInput.addEventListener(
    "change",
    resetResults
);

episodeInput.addEventListener(
    "change",
    resetResults
);

tagsContainer.addEventListener(
    "click",
    (event) => {
        const option =
            event.target.closest(
                ".filter-option"
            );

        if (!option) {
            return;
        }

        option.classList.toggle(
            "selected"
        );

        resetResults();
    }
);


/* =========================================================
   CLEAR
   ========================================================= */

clearButton.addEventListener(
    "click",
    () => {
        searchInput.value = "";
        sortSelect.value = "relevance";

        const yearSelect =
            document.getElementById(
                "explore-year"
            );

        if (yearSelect) {
            [...yearSelect.options].forEach(
                (option) => {
                    option.selected = false;
                }
            );
        }

        seasonInput.value = "";
        episodeInput.value = "";

        tagsContainer
            .querySelectorAll(
                ".filter-option.selected"
            )
            .forEach(
                (option) => {
                    option.classList.remove(
                        "selected"
                    );
                }
            );

        yearRoot
            .querySelectorAll(
                ".collapsible"
            )
            .forEach(
                (container) => {
                    container.classList.remove(
                        "has-selection"
                    );

                    container
                        ._updateSelectionIndicator?.();
                }
            );

        resetResults();
    }
);


/* =========================================================
   LOAD MORE
   ========================================================= */

moreButton.addEventListener(
    "click",
    () => load()
);


/* =========================================================
   INFINITE SCROLL
   ========================================================= */

const observer =
    new IntersectionObserver(
        (entries) => {
            for (
                const entry of entries
            ) {
                if (
                    entry.isIntersecting &&
                    !loading &&
                    !finished
                ) {
                    load();
                }
            }
        },
        {
            root: null,
            rootMargin: "600px",
            threshold: 0,
        }
    );

observer.observe(sentinel);


/* =========================================================
   INITIALIZATION
   ========================================================= */

async function initialize() {
    try {
        await loadFilters();

        await load({
            reset: true,
        });
    } catch (error) {
        console.error(
            "Erro ao inicializar Explore:",
            error
        );

        statusMessage.textContent =
            "Não foi possível carregar os filtros.";
    }
}

initialize();