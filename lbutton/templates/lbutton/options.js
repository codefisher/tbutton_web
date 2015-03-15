// Saves options to chrome.storage
function save_options() {
  var mode = document.getElementById('mode').value;
  var url = document.getElementById('url').value;
  chrome.storage.sync.set({
    action_url: url,
    action_mode: mode
  }, function() {
    // Update status to let user know options were saved.
    var status = document.getElementById('status');
    status.textContent = 'Options saved.';
    setTimeout(function() {
      status.textContent = '';
    }, 750);
  });
}

function restore_options() {
  chrome.storage.sync.get({
    action_url: "{{ button_url|escapejs }}",
    action_mode: {{ button_mode }}
  }, function(items) {
    if(items.action_mode == 0) {
        items.action_mode = 2;
    }
    document.getElementById('mode').value = items.action_mode;
    document.getElementById('url').value = items.action_url;
  });
}
document.addEventListener('DOMContentLoaded', restore_options);
document.getElementById('save').addEventListener('click',
    save_options);