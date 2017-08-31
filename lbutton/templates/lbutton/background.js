if(typeof(browser) === 'undefined') {
	var browser = chrome;
}

browser.browserAction.onClicked.addListener(function(tab) {
	browser.storage.sync.get({
		action_url: "{{ button_url|escapejs }}",
		action_mode: {{ button_mode }}
	}, function(items) {
		let buttonUrl = items.action_url;
		if (buttonUrl.startsWith('javascript:')) {
            let code = decodeURI(buttonUrl.replace(/^javascript:/, ''));
            if(!code.endsWith(';')) {
                code += ';';
            }
            browser.tabs.executeScript({
                    "code": "let url = " + code + " if(url) { window.document.location=url; }"
            });
        } else if(buttonUrl.startsWith('data:')) {
            if (settings.new_tab) {
                browser.tabs.executeScript({
                    "code": "window.open('" + buttonUrl.replace(/'/g, "\\';") + "');"
                });
            } else {
                browser.tabs.executeScript({
                    "code": "window.document.location='" + buttonUrl.replace(/'/g, "\\'") + "';"
                });
            }
        } else {
            if (settings.new_tab) {
                browser.tabs.create({url: buttonUrl});
            } else {
                browser.tabs.update({url: buttonUrl});
            }
        }
	});
});