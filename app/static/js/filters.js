export const opt = (value, label) => {
  const element = document.createElement("option");

  element.value = value;
  element.textContent = label;

  return element;
};


function normalizeOption(option, formatLabel) {
  if (Array.isArray(option)) {
    return {
      value: String(option[0]),
      label: String(option[1]),
    };
  }

  if (
    option &&
    typeof option === "object"
  ) {
    return {
      value: String(option.value),
      label: String(
        option.label ?? option.value
      ),
    };
  }

  const value = String(option);

  return {
    value,
    label: formatLabel
      ? formatLabel(option)
      : value,
  };
}


export function createCollapsible(
  key,
  labelText,
  options,
  opts = {}
) {
  const container =
    document.createElement("div");

  container.className =
    "collapsible";

  container.dataset.key =
    key;


  /* =========================================================
     HEADER
     ========================================================= */

  const header =
    document.createElement("button");

  header.type = "button";
  header.className =
    "collapsible-header";

  header.textContent =
    labelText;


  const caret =
    document.createElement("span");

  caret.className = "caret";

  header.appendChild(caret);


  /* =========================================================
     CONTENT
     ========================================================= */

  const content =
    document.createElement("div");

  content.className =
    "collapsible-content";


  /* =========================================================
     SELECTION INDICATOR
     ========================================================= */

  function updateSelectionIndicator() {
    let active = false;


    content
      .querySelectorAll("select")
      .forEach((select) => {
        const selected =
          [...select.selectedOptions]
            .some(
              (option) =>
                option.value !== ""
            );

        if (selected) {
          active = true;
        }
      });


    content
      .querySelectorAll("input")
      .forEach((input) => {
        if (
          input.type === "checkbox" &&
          input.checked
        ) {
          active = true;
        }

        if (
          input.type === "number" &&
          input.value
        ) {
          active = true;
        }
      });


    container.classList.toggle(
      "has-selection",
      active
    );
  }


  content.addEventListener(
    "change",
    updateSelectionIndicator
  );

  content.addEventListener(
    "input",
    updateSelectionIndicator
  );


  container._updateSelectionIndicator =
    updateSelectionIndicator;


  /* =========================================================
     CHECKBOX
     ========================================================= */

  if (opts.checkbox) {
    const label =
      document.createElement("label");

    label.className =
      "checkbox-option";


    const checkbox =
      document.createElement("input");

    checkbox.type = "checkbox";
    checkbox.id = key;
    checkbox.className =
      "native-checkbox";


    label.append(
      checkbox,
      document.createTextNode(
        " " + labelText
      )
    );


    content.appendChild(label);


    /* =========================================================
       NUMBER INPUT
       ========================================================= */

  } else if (opts.inputNumber) {
    const input =
      document.createElement("input");

    input.type = "number";
    input.id = key;


    if (opts.placeholder) {
      input.placeholder =
        opts.placeholder;
    }


    content.appendChild(input);


    /* =========================================================
       SELECT
       ========================================================= */

  } else if (options) {
    const select =
      document.createElement("select");

    select.id = key;

    select.setAttribute(
      "aria-label",
      labelText
    );


    /*
     * Without `multiple`, this is a
     * native single-select.
     *
     * With `multiple`, it becomes
     * a native multi-select.
     */
    if (opts.multiple) {
      select.multiple = true;
    }


    /*
     * Empty option.
     *
     * For a single-select this is
     * the default "no filter" value.
     */
    select.append(
      opt(
        "",
        opts.emptyLabel ||
        "Sem filtro"
      )
    );


    (options || []).forEach(
      (rawOption) => {
        const {
          value,
          label,
        } = normalizeOption(
          rawOption,
          opts.formatLabel
        );


        select.append(
          opt(
            value,
            label
          )
        );
      }
    );


    content.appendChild(
      select
    );
  }


  /* =========================================================
     TOGGLE
     ========================================================= */

  header.addEventListener(
    "click",
    (event) => {
      event.stopPropagation();

      container.classList.toggle(
        "open"
      );
    }
  );


  container.append(
    header,
    content
  );


  return container;
}