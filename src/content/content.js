var longMessages = {};
function l(key) {
	$("#m" + key).text(longMessages[key]);
}
$(function(){
	$.get("/c", function(data) {
		/* database size */
		$("#content").append("<!-- " + data["dbsize"] + " -->");
		console.log(data["dbsize"]);
		/* data types */
		var table = [
			{ name : "Bot", title : "Bots" },
			{ name : "Query", title : "Queries" },
			{ name : "Cookie", title : "Cookies" },
			{ name : "Referer", title : "Referers" },
			{ name : "Username", title : "Usernames" },
			{ name : "Password", title : "Passwords" },
			{ name : "Message", title : "Messages" },
		];
		/* go through data types and create content */
		$(table).each(function(i, type) {
			var name = type.name.toLowerCase();
			if(name in data) {
				var tbl = $("<table></table>");
				tbl.append(
					$("<tr></tr>").append("<th>Hits</th><th>" + type.name + "</th>")
				);
				var showMoreButton = false;
				var sorted = $.map(data[name], function(a, b) { return [[b, a]]; }).sort(function(a, b) { return b[1] - a[1]; });
				$.each(sorted, function(key, val) {
					var tmp = $("<td></td>");
					/* bots are shown a bit differently */
					if(name == "bot") {
						var pages = $('<span class="pages"></span>');
						if(val[0] in data["botreq"]) {
							var pageList = data["botreq"][val[0]];
							if(pageList.indexOf("r") != -1) pages.append($('<span class="rbt">robot</span>'));
							if(pageList.indexOf("i") != -1) pages.append($('<span class="html">html</span>'));
							if(pageList.indexOf("s") != -1) pages.append($('<span class="css">css</span>'));
							if(pageList.indexOf("j") != -1) pages.append($('<span class="js">js</span>'));
							if(pageList.indexOf("d") != -1) pages.append($('<span class="json">json</span>'));
							if(pageList.indexOf("l") != -1) pages.append($('<span class="red">login</span>'));
							if(pageList.indexOf("m") != -1) pages.append($('<span class="red">spam</span>'));
							if(pageList.indexOf("?") != -1) pages.append($('<span class="red">???</span>'));
						}
						tmp.append($("<span></span>").text(val[0]).append(pages));
					}
					/* messages are shown a bit differently */
					else if(name == "message") {
						var dat = JSON.parse(val[0]);
						if(dat["m"].length > 90) {
							longMessages[key] = dat["m"];
							tmp.append(
								$("<span></span>").append($('<span class="title"></span>').text(dat["t"])).append($('<span id="m' + key + '"></span>').text(dat["m"].substr(0,90)).append($('<a href="javascript:l(' + key + ')">...</a>')))
							);
						}
						else tmp.append(
								$("<span></span>").append($('<span class="title"></span>').text(dat["t"])).append($("<span></span>").text(dat["m"]))
							);
					}
					/* queries are decoded */
					else if(name == "query") {
						var query = unescape(val[0]).replace(/\+/g, ' ').split("/");
						tmp.append(
							$("<span></span>").text("/" + query.splice(1).join("/")).prepend($('<span class="host"></span>').text(query[0]))
						);
					}
					/* rest of the data types */
					else tmp.append($("<span></span>").text(val[0]));
					/* create the row */
					var row = $("<tr></tr>");
					if(key >= 15) {
						showMoreButton = true;
						row = $('<tr class="hiddenrow ' + name + 'row"></tr>');
					}
					tbl.append(
						row.append("<td>" + val[1] + "</td>").append(tmp)
					);
				});
				/* add show more and less buttons */
				if(showMoreButton) {
					tbl.append(
						$('<tr class="showrow" id="' + name + 'srow"></tr>').append(
							$('<td colspan="2"><a href="javascript:void(0)">Show more</a></td>').click(function() {
								$("." + name + "row").fadeIn();
								$("#" + name + "srow").hide();
								$("#" + name + "hrow").show();
							})
						)
					).append(
						$('<tr style="display:none" class="showrow" id="' + name + 'hrow"></tr>').append(
							$('<td colspan="2"><a href="javascript:void(0)">Show less</a></td>').click(function() {
								$("." + name + "row").fadeOut();
								$("#" + name + "hrow").hide();
								$("#" + name + "srow").show();
							})
						)
					);
				}
				$("#content").append(
					$("<div></div>").append("<h3>" + type.title + "</h3>").append(tbl)
				);
			}
		});
		/* done */
		$("#content").slideDown(1500);
		setTimeout(function(){
			/* stop the loading animation in the index html */
			stop = true;
			$("#cnvs").hide(500);
		}, 200);
	});
});
