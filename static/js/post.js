function display(data, loadTime) {
    iteminfo = JSON.parse(data.split("'").join("\""));
    document.getElementById('display').innerHTML = iteminfo.paintwear;

    $("#display").append("<div style=\"text-align:center;\">Loaded in " + loadTime + " seconds</div><br><br>");
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

            var start = performance.now();
            $.post("/displayInventory", requestData).done(function (data) {
                display(data, ((performance.now()- start)/1000).toFixed(2));
            });
        } catch (e) {
            document.getElementById('display').innerHTML = "<p>Not a valid inspect link</p>";
        }
    })

    if (window.location.hash) {
        var hashURL = window.location.hash.substring(1);
        document.getElementById('textbox').value = hashURL;
        $("#button")[0].click();
    }
});
