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

const DEFAULT_REGION = "BR";
const REGION_STORAGE_KEY = "catalog_region";

const regionButton = document.getElementById("region-selector");
const regionModal = document.getElementById("region-modal");
const regionOptions = document.getElementById("region-options");
const regionClose = document.getElementById("region-modal-close");

function getCurrentRegion() {
    return (
        new URLSearchParams(window.location.search).get("region") ||
        localStorage.getItem(REGION_STORAGE_KEY) ||
        DEFAULT_REGION
    );
}

function updateRegionButton() {
    const region = REGIONS[getCurrentRegion()] || REGIONS[DEFAULT_REGION];

    regionButton.innerHTML = `
        <img src="${region.flag}" alt="${region.name}">
    `;
    regionButton.title = region.name;
}

function openRegionModal() {
    const currentRegion = getCurrentRegion();

    regionOptions.innerHTML = Object.entries(REGIONS)
        .map(([code, region]) => `
            <button
                type="button"
                class="region-option ${code === currentRegion ? "selected" : ""
            }"
                data-region="${code}"
            >
                <span class="region-option-flag">
                    <img src="${region.flag}" alt="">
                </span>

                <span class="region-option-name">
                    ${region.name}
                </span>
            </button>
        `)
        .join("");

    regionModal.hidden = false;
}

function closeRegionModal() {
    regionModal.hidden = true;
}

function selectRegion(region) {
    if (!REGIONS[region]) {
        return;
    }

    localStorage.setItem(
        REGION_STORAGE_KEY,
        region
    );

    const url = new URL(window.location.href);

    url.searchParams.set("region", region);

    window.location.href = url.toString();
}

regionButton.addEventListener(
    "click",
    openRegionModal
);

regionClose.addEventListener(
    "click",
    closeRegionModal
);

regionModal
    .querySelector(".region-modal-backdrop")
    .addEventListener(
        "click",
        closeRegionModal
    );

regionOptions.addEventListener(
    "click",
    (event) => {
        const option = event.target.closest(
            ".region-option"
        );

        if (!option) {
            return;
        }

        selectRegion(
            option.dataset.region
        );
    }
);

document.addEventListener(
    "keydown",
    (event) => {
        if (
            event.key === "Escape" &&
            !regionModal.hidden
        ) {
            closeRegionModal();
        }
    }
);

updateRegionButton();