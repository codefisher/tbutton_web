if(typeof(browser) === 'undefined') {
	var browser = chrome;
}

browser.browserAction.onClicked.addListener(function(tab) {
	browser.storage.sync.get({
		action_url: "{{ button_url|escapejs }}",
		action_mode: {{ button_mode }}
	}, function(items) {
		if(items.action_mode == 1) {
			browser.tabs.create({url : items.action_url}, function(tab) {});
		} else {
			browser.tabs.update(tab.id, {url: items.action_url});
		}
	});	
});