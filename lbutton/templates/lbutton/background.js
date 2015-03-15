chrome.browserAction.onClicked.addListener(function(tab) {
	chrome.storage.sync.get({
		action_url: "{{ button_url|escapejs }}",
		action_mode: {{ button_mode }}
	}, function(items) {
		if(items.action_mode == 1) {
			chrome.tabs.create({url : items.action_url}, function(tab) {});
		} else {
			chrome.tabs.update(tab.id, {url: items.action_url});
		}
	});	
});