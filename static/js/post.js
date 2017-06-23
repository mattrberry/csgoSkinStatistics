function display(data, loadTime) {
    iteminfo = JSON.parse(data.split("'").join("\""));

    document.getElementById('item_name').innerHTML = iteminfo.name + " <span class=\"pop\">" + iteminfo.special + "</span>";
    document.getElementById('item_paintwear').innerHTML = iteminfo.paintwear;

    document.getElementById('display').innerHTML = "<div style=\"text-align:center;\">Loaded in " + loadTime + " seconds</div><br><br>";
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

    document.getElementById('textbox').value = "S76561198261551396A9067619073D14604201839850564398";
    document.getElementById('button').click();

    if (window.location.hash) {
        var hashURL = window.location.hash.substring(1);
        document.getElementById('textbox').value = hashURL;
        $("#button")[0].click();
    }
});

function post(requestData) {
    var start = performance.now();
    $.post("/displayInventory", requestData).done(function (data) {
        display(data, ((performance.now()- start)/1000).toFixed(2));
    });
}
