function display(data, loadTime) {
    try {
        iteminfo = JSON.parse(data);

        document.getElementById('item_name').innerHTML = iteminfo.name + " <span class=\"pop\">" + iteminfo.special + "</span>";
        document.getElementById('item_name').classList.remove('knife');
        if (isKnife(iteminfo.name)) {
            document.getElementById('item_name').classList.add('knife');
        }
        document.getElementById('item_paintwear').innerHTML = iteminfo.paintwear;
        document.getElementById('item_itemid').innerHTML = iteminfo.itemid;
        document.getElementById('item_paintseed').innerHTML = iteminfo.paintseed;
        document.getElementById('status').innerHTML = "Loaded in " + loadTime + " seconds";
        document.getElementById('stattrak-indicator').classList.remove('yes');
        document.getElementById('stattrak-indicator').classList.add(iteminfo.stattrak);
    } catch (e) {
        document.getElementById('item_name').innerHTML = "-";
        document.getElementById('item_name').classList.remove('knife');
        document.getElementById('item_paintwear').innerHTML = '-';
        document.getElementById('item_itemid').innerHTML = '-';
        document.getElementById('item_paintseed').innerHTML = '-';
        document.getElementById('stattrak-indicator').classList.remove('yes');
        document.getElementById('status').innerHTML = data;
    }
}

window.onload = function () {
    document.getElementById("textbox").addEventListener("keydown", function (event) {
        if (event.keyCode === 13) {
            event.preventDefault();
            document.getElementById("button").click();
        }
    });

    document.getElementById("button").onclick = function (element) {
        element.toElement.blur();

        var box = document.getElementById("textbox").value;
        console.log(box);

        try {
            var match = box.match(/([SM])(\d+)A(\d+)D(\d+)$/);
            box = match[0];
            type = match[1];
            var requestData = {
                s: type === 'S' ? match[2] : '0',
                a: match[3],
                d: match[4],
                m: type === 'S' ? '0' : match[2]
            };

            document.getElementById('textbox').value = box;
            location.hash = box;

            post(requestData);
        } catch (e) {
            document.getElementById('textbox').value = "Not a valid inspect link";
        }
    };

    if (window.location.hash) {
        var hashURL = window.location.hash.substring(1);
        document.getElementById('textbox').value = hashURL;
    } else {
        document.getElementById('textbox').value = "S76561198261551396A12256887280D2776544801323831695";
    }

    ping();
    setInterval(ping, 30000);

    document.getElementById('button').click();
};

function post(requestData) {
    var start = performance.now();

    var request = new XMLHttpRequest();
    request.open('POST', '/item', true);
    request.setRequestHeader('Content-type', 'application/json');
    request.onreadystatechange = function () {
        display(request.response, ((performance.now() - start) / 1000).toFixed(2));
    };

    request.send(JSON.stringify(requestData));
}

function ping() {
    var start = performance.now();

    var request = new XMLHttpRequest();
    request.open('POST', '/ping', true);
    request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    request.onreadystatechange = function () {
        if (request.readyState === XMLHttpRequest.DONE && request.status === 200 && request.response === 'pong') {
            console.log(request);
            document.getElementById('ping').innerHTML = 'Ping:' + Math.floor((performance.now() - start)).toString() + 'ms';
        }
    };

    request.send('ping');
}

var knifes = ['Bayonet', 'Butterfly Knife', 'Falchion Knife', 'Flip Knife', 'Gut Knife',
    'Huntsman Knife', 'Karambit', 'M9 Bayonet', 'Shadow Daggers', 'Bowie Knife'];

function isKnife(item_name) {
    var item_type = item_name.split(' | ')[0];
    return knifes.indexOf(item_type) > -1;
}
