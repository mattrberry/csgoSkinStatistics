let elements;

function getWearFromFloat(floatValue) {
  const float = parseFloat(floatValue);
  if (float < 0.07) return "Factory New";
  if (float < 0.15) return "Minimal Wear";
  if (float < 0.38) return "Field-Tested";
  if (float < 0.45) return "Well-Worn";
  return "Battle-Scarred";
}

function getRarityFromNumber(rarityNumber) {
  const rarities = [
    "Default",
    "Consumer Grade",
    "Industrial Grade",
    "Mil-Spec",
    "Restricted",
    "Classified",
    "Covert",
    "Contraband"
  ];
  return rarities[rarityNumber] || "Unknown";
}

function display(iteminfo, loadTime) {
  stopLoading();
  
  if (iteminfo.error) {
    handleError(iteminfo.error);
    return;
  }
  
  try {
    elements.itemName.innerHTML = `${iteminfo.weapon} | ${iteminfo.skin} <span class="pop">${iteminfo.special}</span>`;
    elements.itemName.classList.remove("knife");
    if (iteminfo.isKnife) {
      elements.itemName.classList.add("knife");
    }
    elements.itemPaintwear.innerHTML = iteminfo.paintwear;
    elements.itemWear.innerHTML = getWearFromFloat(iteminfo.paintwear);
    elements.itemRarity.innerHTML = getRarityFromNumber(iteminfo.rarity);
    elements.itemItemid.innerHTML = iteminfo.itemid;
    elements.itemPaintseed.innerHTML = iteminfo.paintseed;
    elements.status.innerHTML = `Loaded in ${loadTime} seconds`;
    elements.stattrakIndicator.classList.remove("yes");
    if (iteminfo.stattrak) {
      elements.stattrakIndicator.classList.add("yes");
    }

    if (iteminfo.s && iteminfo.s !== 0) {
      elements.inspectButton.href = `steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20S${iteminfo.s}A${iteminfo.a}D${iteminfo.d}`;
    } else if (iteminfo.m && iteminfo.m !== 0) {
      elements.inspectButton.href = `steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M${iteminfo.m}A${iteminfo.a}D${iteminfo.d}`;
    } else {
      elements.inspectButton.href = "#";
    }
  } catch (e) {
    handleError("An error occurred while displaying the item data");
  }
}

function resetFields() {
  elements.itemName.innerHTML = "-";
  elements.itemName.classList.remove("knife");
  elements.itemPaintwear.innerHTML = "-";
  elements.itemWear.innerHTML = "-";
  elements.itemRarity.innerHTML = "-";
  elements.itemItemid.innerHTML = "-";
  elements.itemPaintseed.innerHTML = "-";
  elements.status.innerHTML = "";
  elements.stattrakIndicator.classList.remove("yes");
  elements.inspectButton.href = "#";
  elements.errorDisplay.style.display = "none";
}

function startLoading() {
  elements.itemName.parentElement.classList.add("loading");
  elements.itemPaintwear.parentElement.classList.add("loading");
  elements.itemWear.parentElement.classList.add("loading");
  elements.itemRarity.parentElement.classList.add("loading");
  elements.itemItemid.parentElement.classList.add("loading");
  elements.itemPaintseed.parentElement.classList.add("loading");
}

function stopLoading() {
  elements.itemName.parentElement.classList.remove("loading");
  elements.itemPaintwear.parentElement.classList.remove("loading");
  elements.itemWear.parentElement.classList.remove("loading");
  elements.itemRarity.parentElement.classList.remove("loading");
  elements.itemItemid.parentElement.classList.remove("loading");
  elements.itemPaintseed.parentElement.classList.remove("loading");
}

function handleError(errorMessage) {
  resetFields();
  elements.errorDisplay.innerHTML = errorMessage;
  elements.errorDisplay.style.display = "block";
}

window.addEventListener("load", function () {
  elements = {
    itemName: document.getElementById("item_name"),
    itemPaintwear: document.getElementById("item_paintwear"),
    itemWear: document.getElementById("item_wear"),
    itemRarity: document.getElementById("item_rarity"),
    itemItemid: document.getElementById("item_itemid"),
    itemPaintseed: document.getElementById("item_paintseed"),
    status: document.getElementById("status"),
    stattrakIndicator: document.getElementById("stattrak-indicator"),
    inspectButton: document.getElementById("inspect_button"),
    textbox: document.getElementById("textbox"),
    button: document.getElementById("button"),
    errorDisplay: document.getElementById("error-display"),
  };

  elements.textbox.addEventListener("keydown", function (event) {
    if (event.code === "Enter") {
      event.preventDefault();
      elements.button.click();
    }
  });

  elements.button.addEventListener("click", function (element) {
    element.target.blur();

    const input = elements.textbox.value;
    try {
      const [match, type, paramType, paramA, paramD] = input.match(
        /([SM])(\d+)A(\d+)D(\d+)$/
      );
      const requestData = {
        s: type === "S" ? paramType : "0",
        m: type === "S" ? "0" : paramType,
        a: paramA,
        d: paramD,
      };

      elements.textbox.value = match;
      window.location.hash = match;

      resetFields();
      post(requestData);
    } catch (e) {
      elements.textbox.value = "Not a valid inspect link";
    }
  });

  if (window.location.hash) {
    const hashURL = window.location.hash.substring(1);
    elements.textbox.value = hashURL;
    elements.button.click();
  } else {
    post({
      s: "76561198261551396",
      m: "0",
      a: "19621162652",
      d: "13871278417611896371",
    });
  }
});

function post(requestData) {
  startLoading();
  const start = performance.now();
  fetch(`/api?${new URLSearchParams(requestData)}`)
    .then((response) => response.json())
    .then((iteminfo) =>
      display(iteminfo, ((performance.now() - start) / 1000).toFixed(2))
    );
}
