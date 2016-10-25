$(document).ready(function() {
    $("#textbox").keydown(function(e){
	if(e.which === 13){
            $("#button").focus();
	}
    });
    
    $("#button").click(function() {
	$(this).blur();
	
	$("#display").animate({
	    'padding-top': "100%"
	}, "slow", "swing");
	$("#loading").show();
	
	var box = $("#textbox").val();
	var username = box;
	var findid = "none";
	
	if (box.match(/([SM])(\d+)A(\d+)D(\d+)$/)) {
	    box = box.match(/([SM])(\d+)A(\d+)D(\d+)$/)[0];
	    username = box.match(/([SM])(\d+)A(\d+)D(\d+)$/)[2];
	    findid = box.match(/([SM])(\d+)A(\d+)D(\d+)$/)[3];
	} else if (box.match(/(profiles\/)(\w+)/) || !isNaN(box)) {
	    box = box.match(/(profiles\/)(\w+)/) ? box.match(/(profiles\/)(\w+)/)[2] : box;
	    username = box;
	} else if (box.match(/(partner.)(\w+)/)) {
	    box = "7656" + (parseInt(box.match(/(partner.)(\w+)/)[2]) + 1197960265728);
	    username = box;
	} else {
	    var vanity;
	    if (box.match(/(id\/)(\w+)/)) {
		box = box.match(/(id\/)(\w+)/)[2];
		username = box;
	    }
	}
	
	var requestData = {input: box, id: username, itemid: findid};
	
	document.getElementById('textbox').value = box;
	location.hash = box;
	
	function display(data, loadTime) {
	    $("#container").animate({
		'padding-top': 5,
	    }, "slow", "swing");
	    
	    $("#display").animate({
		'padding-top': "0px"
	    }, "slow", "swing");
	    
	    $("#loading").hide();
	    document.getElementById('display').innerHTML = data;
	    
	    $("#display").append("<div style=\"text-align:center;\">Loaded in " + loadTime + " seconds</div>");
	    //$("#display").append("<div style=\"text-align:center;\"><a tabindex=\"-1\" target=\"_blank\" href=\"https://steamcommunity.com/tradeoffer/new/?partner=301285668&token=yWbzVo_6\" style=\"color:#01B7A6\">Donate :)</a></div>");
	}
	
	var start = performance.now();
	$.post("/displayInventory", requestData).done(function (data) {
	    display(data, ((performance.now()- start)/1000).toFixed(2));
	});
    })
    
    if (window.location.hash) {
	var hashURL = window.location.hash.substring(1);
	document.getElementById('textbox').value = hashURL;
	$("#button")[0].click();
    }
});
