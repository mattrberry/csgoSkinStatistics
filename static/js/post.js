function display(data, loadTime) {
    try {
        iteminfo = JSON.parse(data.split("'").join("\""));

        document.getElementById('item_name').innerHTML = iteminfo.name + " <span class=\"pop\">" + iteminfo.special + "</span>";
        document.getElementById('item_paintwear').innerHTML = iteminfo.paintwear;
        document.getElementById('item_itemid').innerHTML = iteminfo.itemid;
        document.getElementById('item_paintseed').innerHTML = iteminfo.paintseed;
        document.getElementById('status').innerHTML = "Loaded in " + loadTime + " seconds";
    } catch (e) {
        document.getElementById('item_name').innerHTML = "-";
        document.getElementById('item_paintwear').innerHTML = '-';
        document.getElementById('item_itemid').innerHTML = '-';
        document.getElementById('item_paintseed').innerHTML = '-';
        document.getElementById('status').innerHTML = data;
    }
}

$(document).ready(function() {
    $("#textbox").keydown(function(e){
        if(e.which === 13){
            $("#button").focus();
        }
    });

    $("#button").click(function() {
        $(this).blur();

        var box = $("#textbox").val();

        try {
            var match = box.match(/([SM])(\d+)A(\d+)D(\d+)$/);
            box = match[0];
            type = match[1];
            var requestData = {
                s: type === 'S' ? match[2] : '0',
                a: match[3],
                d: match[4],
                m: type === 'S' ? '0' : match[2]
            }

            document.getElementById('textbox').value = box;
            location.hash = box;

            post(requestData);
        } catch (e) {
            document.getElementById('display').innerHTML = "<p>Not a valid inspect link</p>";
        }
    })


    if (window.location.hash) {
        var hashURL = window.location.hash.substring(1);
        document.getElementById('textbox').value = hashURL;
    } else {
        document.getElementById('textbox').value = "S76561198261551396A9716592909D9549395284300371856";
    }

    ping();
    setInterval(ping, 30000);

    document.getElementById('button').click();
});

function post(requestData) {
    var start = performance.now();
    $.post("/displayInventory", requestData).done(function (data) {
        display(data, ((performance.now()- start)/1000).toFixed(2));
    });
}

function ping() {
    var start = performance.now();
    $.post("/ping", "ping").done(function (response) {
        if (response == "pong") {
            document.getElementById('ping').innerHTML = "Ping:" + Math.floor((performance.now() - start)).toString() + 'ms';
        }
    });
}
