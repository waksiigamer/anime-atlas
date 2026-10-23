import { opt, createCollapsible } from "./filters.js";

const DEFAULT_REGION = "BR";
const REGION_STORAGE_KEY = "catalog_region";

const urlRegion = new URLSearchParams(location.search).get("region");

let currentRegion =
  urlRegion ||
  localStorage.getItem(REGION_STORAGE_KEY) ||
  DEFAULT_REGION;

localStorage.setItem(REGION_STORAGE_KEY, currentRegion);

let resetting = false;

const $ = (id) => document.getElementById(id);

const grid = $("grid");

const userStatuses = new Map();

let page = 1;
let loading = false;
let userStatusesLoaded = false;


const localeLabels = {
  "pt-BR": "Português (Brasil)",
  "en-US": "Inglês",
  "de-DE": "Alemão",
  "ar-SA": "Árabe",
  "ca-ES": "Catalão",
  "zh-HK": "Chinês (Hong Kong)",
  "zh-CN": "Chinês (Simplificado)",
  "zh-TW": "Chinês (Tradicional)",
  "ko-KR": "Coreano",
  "es-419": "Espanhol (América Latina)",
  "es-ES": "Espanhol (Espanha)",
  "fr-FR": "Francês",
  "hi-IN": "Hindi",
  "nl-NL": "Holandês",
  "id-ID": "Indonésio",
  "en-IN": "Inglês (Índia)",
  "it-IT": "Italiano",
  "ja-JP": "Japonês",
  "ms-MY": "Malaio",
  "pl-PL": "Polonês",
  "pt-PT": "Português (Portugal)",
  "ru-RU": "Russo",
  "th-TH": "Tailandês",
  "ta-IN": "Tâmil",
  "te-IN": "Telugu",
  "tr-TR": "Turco",
  "vi-VN": "Vietnamita",
};

const localeLabel = (locale) =>
  localeLabels[locale] || locale;

const localePriority = {
  "pt-BR": 0,
  "en-US": 1,
};

const sortLocales = (locales) => {
  return [...(locales || [])].sort((a, b) => {
    const priorityA = localePriority[a] ?? 2;
    const priorityB = localePriority[b] ?? 2;

    if (priorityA !== priorityB) {
      return priorityA - priorityB;
    }

    return localeLabel(a).localeCompare(
      localeLabel(b),
      "pt-BR"
    );
  });
};


const FILTER_DEFINITIONS = [
  {
    key: "year",
    label: "Ano",
    type: "select",
    source: "years",
    multiple: true,
    row: "primary",
  },

  {
    key: "tags",
    label: "Tags",
    type: "select",
    source: "tags",
    multiple: true,
    row: "primary",
  },

  {
    key: "maturity_rating",
    label: "Classificação",
    type: "select",
    source: "maturity_ratings",
    multiple: true,
    row: "primary",
  },

  {
    key: "content_descriptor",
    label: "Descritor",
    type: "select",
    source: "content_descriptors",
    multiple: true,
    row: "primary",
  },

  {
    key: "audio_locale",
    label: "Áudio",
    type: "select",
    source: "audio_locales",
    multiple: true,
    row: "primary",
    formatLabel: localeLabel,
  },

  {
    key: "subtitle_locale",
    label: "Legenda",
    type: "select",
    source: "subtitle_locales",
    multiple: true,
    row: "primary",
    formatLabel: localeLabel,
  },

  {
    key: "min_rating",
    label: "Nota mínima",
    type: "rating",
    row: "primary",
  },

  {
    key: "user_status",
    label: "Status",
    type: "single-select",
    options: [
      ["watched", "Assistidos"],
      ["watch_later", "Assistir mais tarde"],
      ["watch_later", "Larguei"],
      ["watch_later", "Assistindo"],
    ],
    row: "secondary",
  },

  {
    key: "season_count_min",
    label: "Temporadas mín.",
    type: "number",
    row: "secondary",
  },

  {
    key: "episode_count_min",
    label: "Episódios mín.",
    type: "number",
    row: "secondary",
  },

  {
    key: "sort",
    label: "Ordenar por",
    type: "single-select",
    options: [
      ["title_asc", "Título A → Z"],
      ["title_desc", "Título Z → A"],
      ["rating_desc", "Nota maior"],
      ["rating_asc", "Nota menor"],
      ["year_desc", "Ano mais recente"],
      ["year_asc", "Ano mais antigo"],
      ["recently_published", "Data Publicação"],
    ],
    row: "secondary",
  },
];


const getFilterDefinition = (key) =>
  FILTER_DEFINITIONS.find(
    (definition) => definition.key === key
  );

const getDefinitionsByRow = (row) =>
  FILTER_DEFINITIONS.filter(
    (definition) => definition.row === row
  );


grid.addEventListener("click", async (event) => {
  const button = event.target.closest(".card-action");

  if (!button) return;

  event.preventDefault();
  event.stopPropagation();

  const animeId = button.dataset.animeId;
  const status = button.dataset.action;

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

      const card = button.closest(".card");

      card.querySelectorAll(".card-action").forEach((action) => {
        action.classList.remove("active");
      });

      userStatuses.delete(animeId);
    } catch (error) {
      console.error("Erro ao remover status:", error);
    }

    return;
  }

  try {
    const response = await fetch("/api/user/anime", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        anime_id: animeId,
        status: status,
      }),
    });

    if (!response.ok) {
      const text = await response.text();

      console.error(
        "POST error:",
        text
      );

      throw new Error(
        `HTTP ${response.status}`
      );
    }

    const card = button.closest(".card");

    card
      .querySelectorAll(".card-action")
      .forEach((action) => {
        action.classList.remove("active");
      });

    button.classList.add("active");

    userStatuses.set(
      animeId,
      status
    );
  } catch (error) {
    console.error(
      "Erro ao salvar status:",
      error
    );
  }
});


const selectedValues = (select) =>
  [...select.selectedOptions]
    .map((option) => option.value)
    .filter(Boolean);


function appendSelectToQuery(
  params,
  key
) {
  const select = $(key);

  if (!select) {
    return;
  }

  if (select.multiple) {
    selectedValues(select).forEach(
      (value) => {
        params.append(key, value);
      }
    );

    return;
  }

  if (select.value) {
    params.set(
      key,
      select.value
    );
  }
}


function query() {
  const params = new URLSearchParams();

  params.set(
    "region",
    currentRegion
  );

  params.set(
    "page",
    page
  );

  const search = $("q");

  if (search?.value.trim()) {
    params.set(
      "q",
      search.value.trim()
    );
  }

  FILTER_DEFINITIONS
    .filter(
      (definition) =>
        definition.type === "select" ||
        definition.type === "rating"
    )
    .forEach(
      (definition) => {
        appendSelectToQuery(
          params,
          definition.key
        );
      }
    );

  FILTER_DEFINITIONS
    .filter(
      (definition) =>
        definition.type === "number"
    )
    .forEach(
      (definition) => {
        const input = $(
          definition.key
        );

        if (
          input &&
          input.value !== ""
        ) {
          params.set(
            definition.key,
            input.value
          );
        }
      }
    );

  const userStatus = $("user_status");

  if (userStatus?.value) {
    params.set(
      "user_status",
      userStatus.value
    );
  }

  const sort = $("sort");

  params.set(
    "sort",
    sort?.value || "relevance"
  );

  return params;
}


function card(anime) {
  const imageHtml =
    anime.card_image
      ? `<img src="${anime.card_image}" alt="">`
      : '<div class="fallback"></div>';

  const badge =
    anime.maturity_icon
      ? `
        <div class="maturity-badge">
          <img
            src="${anime.maturity_icon}"
            alt="${anime.maturity_label || ""}"
          >
        </div>
      `
      : "";

  const currentStatus =
    userStatuses.get(
      anime.id
    );

  const actions = `
    <div class="card-actions">

      <button
        type="button"
        class="card-action ${currentStatus === "watched"
      ? "active"
      : ""
    }"
        data-action="watched"
        data-anime-id="${anime.id}"
        title="Marcar como assistido"
        aria-label="Marcar como assistido"
      >✓</button>

      <button
        type="button"
        class="card-action ${currentStatus === "watch_later"
      ? "active"
      : ""
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
      href="/anime/${anime.id}?region=${encodeURIComponent(currentRegion)}"
    >

      <div class="image-wrap">
        ${imageHtml}
        ${badge}
        ${actions}
      </div>

      <div>
        <h2>${anime.title}</h2>

        <span>
          ${anime.year || "—"} · ★ ${anime.rating ?? "—"
    }
        </span>

        <p class="tag">
          ${(anime.genres || [])
      .slice(0, 3)
      .join(" · ")}
        </p>
      </div>

    </a>
  `;
}


async function load() {
  if (loading) {
    return;
  }

  if (!userStatusesLoaded) {
    await loadUserStatuses();
  }

  loading = true;

  $("status").textContent =
    "Carregando…";

  try {
    const data = await fetch(
      "/api/animes?" + query()
    ).then(
      (response) =>
        response.json()
    );

    grid.insertAdjacentHTML(
      "beforeend",
      data.items
        .map(card)
        .join("")
    );

    $("count").textContent =
      data.pagination.total_items +
      " resultados";

    $("more").hidden =
      !data.pagination.has_next_page;

    $("status").textContent =
      data.items.length
        ? ""
        : "Nenhum resultado encontrado.";

    history.replaceState(
      null,
      "",
      "?" + query()
    );
  } catch (error) {
    console.error(
      "Erro ao carregar catálogo:",
      error
    );

    $("status").textContent =
      "Não foi possível carregar o catálogo.";
  } finally {
    loading = false;
  }
}


async function loadUserStatuses() {
  try {
    const response = await fetch(
      `/api/user/anime?region=${encodeURIComponent(
        currentRegion
      )}`
    );

    if (!response.ok) {
      throw new Error(
        `HTTP ${response.status}`
      );
    }

    const items =
      await response.json();

    userStatuses.clear();

    for (const item of items) {
      userStatuses.set(
        item.anime_id,
        item.status
      );
    }

    userStatusesLoaded = true;
  } catch (error) {
    console.error(
      "Erro ao carregar status dos animes:",
      error
    );
  }
}


async function reset() {
  resetting = true;

  page = 1;

  grid.innerHTML = "";

  await loadUserStatuses();

  await load();

  setTimeout(() => {
    resetting = false;
  }, 500);
}


function appendToRow(
  element,
  row
) {
  const root =
    row === "secondary"
      ? $("secondary-root")
      : $("advanced-root");

  root.appendChild(element);
}


function createSelectFilter(
  definition,
  filters
) {
  let options =
    filters[definition.source] || [];

  if (
    definition.key === "audio_locale" ||
    definition.key === "subtitle_locale"
  ) {
    options = sortLocales(options);
  }

  const wrapper =
    createCollapsible(
      definition.key,
      definition.label,
      options,
      {
        multiple:
          definition.multiple,
        emptyLabel:
          "Sem filtro",
        formatLabel:
          definition.formatLabel,
      }
    );

  return wrapper;
}


function createYearFilter(
  definition,
  filters
) {
  const select =
    document.createElement(
      "select"
    );

  select.id =
    definition.key;

  select.setAttribute(
    "aria-label",
    definition.label
  );

  select.multiple = true;

  select.append(
    opt(
      "",
      definition.label
    )
  );

  (
    filters.years || []
  ).forEach(
    (value) => {
      select.append(
        opt(
          value,
          value
        )
      );
    }
  );

  const wrapper =
    createCollapsible(
      `${definition.key}_wrap`,
      definition.label,
      null,
      {}
    );

  wrapper
    .querySelector(
      ".collapsible-content"
    )
    .appendChild(select);

  return wrapper;
}


function createRatingFilter(
  definition
) {
  const options = [
    "3",
    "3.5",
    "4",
    "4.5",
  ];

  const select =
    document.createElement(
      "select"
    );

  select.id =
    definition.key;

  select.setAttribute(
    "aria-label",
    definition.label
  );

  select.multiple = true;
  select.size = 5;

  select.append(
    opt(
      "",
      "Sem filtro"
    )
  );

  options.forEach(
    (value) => {
      select.append(
        opt(
          value,
          `${value}+`
        )
      );
    }
  );

  select.addEventListener(
    "change",
    () => {
      const selected =
        [
          ...select.selectedOptions,
        ].find(
          (option) =>
            option.value !== ""
        );

      [
        ...select.options,
      ].forEach(
        (option) => {
          option.selected =
            option === selected;
        }
      );

      if (!selected) {
        select.options[0].selected =
          true;
      }
    }
  );

  const wrapper =
    createCollapsible(
      `${definition.key}_wrap`,
      definition.label,
      null,
      {}
    );

  wrapper
    .querySelector(
      ".collapsible-content"
    )
    .appendChild(select);

  return wrapper;
}


function createSingleSelectFilter(
  definition
) {
  const options = definition.options || [];

  const select =
    document.createElement(
      "select"
    );

  select.id =
    definition.key;

  select.setAttribute(
    "aria-label",
    definition.label
  );

  select.multiple = true;
  select.size = 5;

  select.append(
    opt(
      "",
      "Sem filtro"
    )
  );

  options.forEach(
    ([value, label]) => {
      select.append(
        opt(
          value,
          label
        )
      );
    }
  );

  const defaultValue =
    definition.defaultValue ??
    "";

  const defaultOption =
    [...select.options].find(
      (option) =>
        option.value ===
        defaultValue
    );

  if (defaultOption) {
    defaultOption.selected = true;
  }

  select.addEventListener(
    "change",
    () => {
      const selected =
        [
          ...select.selectedOptions,
        ].find(
          (option) =>
            option.value !== ""
        );

      [
        ...select.options,
      ].forEach(
        (option) => {
          option.selected =
            option === selected;
        }
      );

      if (!selected) {
        select.options[0].selected =
          true;
      }
    }
  );

  const wrapper =
    createCollapsible(
      `${definition.key}_wrap`,
      definition.label,
      null,
      {}
    );

  wrapper
    .querySelector(
      ".collapsible-content"
    )
    .appendChild(select);

  return wrapper;
}


function createNumberFilter(
  definition
) {
  const input =
    document.createElement(
      "input"
    );

  input.type = "number";

  input.id =
    definition.key;

  input.min = "0";

  input.placeholder =
    definition.key ===
      "season_count_min"
      ? "Temporadas mín."
      : "Episódios mín.";

  input.className =
    "mini-number";

  return input;
}


function createFilter(
  definition,
  filters
) {
  switch (definition.type) {
    case "select":
      return definition.key ===
        "year"
        ? createYearFilter(
          definition,
          filters
        )
        : createSelectFilter(
          definition,
          filters
        );

    case "rating":
      return createRatingFilter(
        definition
      );

    case "single-select":
      return createSingleSelectFilter(
        definition
      );

    case "number":
      return createNumberFilter(
        definition
      );

    default:
      throw new Error(
        `Tipo de filtro desconhecido: ${definition.type}`
      );
  }
}


function createFilters(filters) {
  const primaryRoot = $("advanced-root");
  const secondaryRoot = $("secondary-root");

  primaryRoot.innerHTML = "";
  secondaryRoot.innerHTML = "";

  for (const definition of FILTER_DEFINITIONS) {
    const element = createFilter(
      definition,
      filters
    );

    if (definition.row === "secondary") {
      secondaryRoot.appendChild(element);
    } else {
      primaryRoot.appendChild(element);
    }
  }

  const clearButton = $("clear");

  if (clearButton) {
    secondaryRoot.appendChild(clearButton);
  }
}


function restoreSelectFromUrl(
  key,
  url
) {
  const select = $(key);

  if (!select) {
    return;
  }

  const values =
    url.getAll(key);

  if (!values.length) {
    return;
  }

  if (select.multiple) {
    [
      ...select.options,
    ].forEach(
      (option) => {
        option.selected =
          values.includes(
            option.value
          );
      }
    );

    return;
  }

  select.value =
    values[0] || "";
}


function restoreFiltersFromUrl() {
  const url =
    new URLSearchParams(
      location.search
    );

  FILTER_DEFINITIONS
    .filter(
      (definition) =>
        definition.type ===
        "select" ||
        definition.type ===
        "rating" ||
        definition.type ===
        "single-select"
    )
    .forEach(
      (definition) => {
        restoreSelectFromUrl(
          definition.key,
          url
        );
      }
    );

  FILTER_DEFINITIONS
    .filter(
      (definition) =>
        definition.type ===
        "number"
    )
    .forEach(
      (definition) => {
        const input = $(
          definition.key
        );

        if (!input) {
          return;
        }

        input.value =
          url.get(
            definition.key
          ) || "";
      }
    );

  const search = $("q");

  if (search) {
    search.value =
      url.get("q") || "";
  }

  const sortSelect = $("sort");

  if (
    sortSelect &&
    !url.get("sort")
  ) {
    [
      ...sortSelect.options,
    ].forEach(
      (option) => {
        option.selected =
          option.value ===
          "relevance";
      }
    );
  }

  document
    .querySelectorAll(
      ".collapsible"
    )
    .forEach(
      (container) => {
        container
          ._updateSelectionIndicator
          ?.();
      }
    );
}


async function init() {
  const filters =
    await fetch(
      `/api/filters?region=${encodeURIComponent(
        currentRegion
      )}`
    ).then(
      (response) =>
        response.json()
    );

  createFilters(
    filters
  );

  restoreFiltersFromUrl();

  document
    .querySelectorAll(
      "#advanced-root select, #advanced-root input, #secondary-root select, #secondary-root input"
    )
    .forEach(
      (element) => {
        element.onchange =
          reset;
      }
    );

  await loadUserStatuses();

  await load();
}


$("clear").onclick = () => {
  document
    .querySelectorAll(
      "input, select"
    )
    .forEach(
      (element) => {
        if (
          element.type ===
          "checkbox"
        ) {
          element.checked =
            false;
        } else {
          element.value = "";
        }

        if (
          element.multiple
        ) {
          [
            ...element.options,
          ].forEach(
            (option) => {
              option.selected =
                false;
            }
          );
        }
      }
    );

  FILTER_DEFINITIONS
    .filter(
        (definition) =>
            definition.type ===
            "single-select"
    )
    .forEach(
        (definition) => {
            const select = $(
                definition.key
            );

            if (!select) {
                return;
            }

            [
                ...select.options,
            ].forEach(
                (option) => {
                    option.selected =
                        false;
                }
            );

            const emptyOption =
                [...select.options].find(
                    (option) =>
                        option.value === ""
                );

            if (emptyOption) {
                emptyOption.selected =
                    true;
            }
        }
    );

  document
    .querySelectorAll(
      ".collapsible"
    )
    .forEach(
      (container) => {
        container.classList.remove(
          "has-selection"
        );

        container
          ._updateSelectionIndicator
          ?.();
      }
    );

  reset();
};


let timer;

$("q").oninput = () => {
  clearTimeout(timer);

  timer = setTimeout(
    reset,
    300
  );
};


const moreBtn = $("more");

if (moreBtn) {
  moreBtn.onclick = () => {
    page += 1;
    load();
  };
}


function bindDynamicFilterHandlers() {
  const year =
    $("year");

  if (year) {
    year.size = 6;
  }

  document
    .querySelectorAll(
      "select, input:not(#q)"
    )
    .forEach(
      (element) => {
        element.onchange =
          reset;
      }
    );
}


function setupAutoLoad() {
  const loadMoreBtn =
    $("more");

  const gridEl =
    $("grid");

  if (
    !gridEl ||
    !loadMoreBtn
  ) {
    return;
  }

  let sentinel =
    document.getElementById(
      "scroll-sentinel"
    );

  if (!sentinel) {
    sentinel =
      document.createElement(
        "div"
      );

    sentinel.id =
      "scroll-sentinel";

    sentinel.style.width =
      "1px";

    sentinel.style.height =
      "1px";

    sentinel.style.margin =
      "0";

    sentinel.style.padding =
      "0";

    sentinel.setAttribute(
      "aria-hidden",
      "true"
    );

    gridEl.insertAdjacentElement(
      "afterend",
      sentinel
    );
  }

  const ROOT_MARGIN =
    "400px 0px";

  const THRESHOLD =
    0.1;

  const CLICK_COOLDOWN_MS =
    1000;

  let lastClickTime = 0;

  let finished = false;

  function isButtonClickable(
    btn
  ) {
    if (!btn) return false;

    if (btn.hidden) return false;

    if (btn.disabled) return false;

    const style =
      getComputedStyle(btn);

    if (
      !style ||
      style.display ===
      "none" ||
      style.visibility ===
      "hidden" ||
      parseFloat(
        style.opacity
      ) === 0
    ) {
      return false;
    }

    return true;
  }

  let io = null;

  const buttonObserver =
    new MutationObserver(() => {
      if (
        !isButtonClickable(
          loadMoreBtn
        )
      ) {
        setTimeout(() => {
          if (
            !isButtonClickable(
              loadMoreBtn
            )
          ) {
            finished = true;

            if (io) {
              io.disconnect();
            }

            buttonObserver.disconnect();

            removalObserver.disconnect();
          }
        }, 300);
      }
    });

  buttonObserver.observe(
    loadMoreBtn,
    {
      attributes: true,
      attributeFilter: [
        "hidden",
        "disabled",
        "style",
        "class",
      ],
    }
  );

  const removalObserver =
    new MutationObserver(
      (mutations) => {
        for (
          const mutation
          of mutations
        ) {
          for (
            const node
            of mutation.removedNodes
          ) {
            if (
              node ===
              loadMoreBtn
            ) {
              finished = true;

              if (io) {
                io.disconnect();
              }

              removalObserver.disconnect();

              buttonObserver.disconnect();

              return;
            }
          }
        }
      }
    );

  removalObserver.observe(
    document.body,
    {
      childList: true,
      subtree: true,
    }
  );

  const gridObserver =
    new MutationObserver(
      (mutations) => {
        const added =
          mutations.some(
            (mutation) =>
              mutation.addedNodes &&
              mutation.addedNodes
                .length > 0
          );

        if (added) {
        }
      }
    );

  gridObserver.observe(
    gridEl,
    {
      childList: true,
      subtree: false,
    }
  );

  if (
    "IntersectionObserver" in
    window
  ) {
    io =
      new IntersectionObserver(
        (entries) => {
          for (
            const entry
            of entries
          ) {
            if (
              entry.isIntersecting &&
              !loading &&
              !finished &&
              !resetting
            ) {
              const now =
                Date.now();

              if (
                now -
                lastClickTime <
                CLICK_COOLDOWN_MS
              ) {
                return;
              }

              if (
                !isButtonClickable(
                  loadMoreBtn
                )
              ) {
                return;
              }

              lastClickTime =
                now;

              try {
                loadMoreBtn.click();
              } catch (err) {
                console.warn(
                  "Auto-load: failed to click #more",
                  err
                );
              }
            }
          }
        },
        {
          root: null,
          rootMargin:
            ROOT_MARGIN,
          threshold:
            THRESHOLD,
        }
      );

    io.observe(
      sentinel
    );
  } else {
    let ticking =
      false;

    const fallbackHandler =
      () => {
        if (
          ticking ||
          loading ||
          finished ||
          resetting
        ) {
          return;
        }

        ticking = true;

        requestAnimationFrame(
          () => {
            const rect =
              sentinel.getBoundingClientRect();

            if (
              rect.top <=
              window.innerHeight +
              400
            ) {
              const now =
                Date.now();

              if (
                now -
                lastClickTime >=
                CLICK_COOLDOWN_MS &&
                isButtonClickable(
                  loadMoreBtn
                )
              ) {
                lastClickTime =
                  now;

                try {
                  loadMoreBtn.click();
                } catch (err) {
                  console.warn(
                    "Auto-load fallback click failed",
                    err
                  );
                }
              }
            }

            ticking = false;
          }
        );
      };

    window.addEventListener(
      "scroll",
      fallbackHandler,
      {
        passive: true,
      }
    );

    setTimeout(
      fallbackHandler,
      250
    );
  }
}


init().then(() => {
  bindDynamicFilterHandlers();

  document
    .querySelectorAll(
      "#advanced-root select, #advanced-root input, #secondary-root select, #secondary-root input"
    )
    .forEach(
      (element) => {
        element.onchange =
          reset;
      }
    );

  try {
    setupAutoLoad();
  } catch (err) {
    console.warn(
      "Failed to initialize auto-load:",
      err
    );
  }
});