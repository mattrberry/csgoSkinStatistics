function display(iteminfo, loadTime) {
  try {
    document.getElementById(
      "item_name"
    ).innerHTML = `${iteminfo.weapon} | ${iteminfo.skin} <span class="pop">${iteminfo.special}</span>`;
    document.getElementById("item_name").classList.remove("knife");
    if (iteminfo.isKnife) {
      document.getElementById("item_name").classList.add("knife");
    }
    document.getElementById("item_paintwear").innerHTML = iteminfo.paintwear;
    document.getElementById("item_itemid").innerHTML = iteminfo.itemid;
    document.getElementById("item_paintseed").innerHTML = iteminfo.paintseed;
    document.getElementById(
      "status"
    ).innerHTML = `Loaded in ${loadTime} seconds`;
    document.getElementById("stattrak-indicator").classList.remove("yes");
    if (iteminfo.stattrak) {
      document.getElementById("stattrak-indicator").classList.add("yes");
    }
  } catch (e) {
    document.getElementById("item_name").innerHTML = "-";
    document.getElementById("item_name").classList.remove("knife");
    document.getElementById("item_paintwear").innerHTML = "-";
    document.getElementById("item_itemid").innerHTML = "-";
    document.getElementById("item_paintseed").innerHTML = "-";
    document.getElementById("stattrak-indicator").classList.remove("yes");
    document.getElementById("status").innerHTML = data;
  }
}

window.addEventListener("load", function () {
  document
    .getElementById("textbox")
    .addEventListener("keydown", function (event) {
      if (event.code === "Enter") {
        event.preventDefault();
        document.getElementById("button").click();
      }
    });

  document
    .getElementById("button")
    .addEventListener("click", function (element) {
      element.target.blur();

      const input = document.getElementById("textbox").value;
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

        document.getElementById("textbox").value = match;
        window.location.hash = match;

        post(requestData);
      } catch (e) {
        document.getElementById("textbox").value = "Not a valid inspect link";
      }
    });

  if (window.location.hash) {
    const hashURL = window.location.hash.substring(1);
    document.getElementById("textbox").value = hashURL;
    document.getElementById("button").click();
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
  const start = performance.now();
  fetch(`/api?${new URLSearchParams(requestData)}`)
    .then((response) => response.json())
    .then((iteminfo) => display(iteminfo, ((performance.now() - start) / 1000).toFixed(2)));
}
