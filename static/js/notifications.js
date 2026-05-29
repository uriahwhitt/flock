var POLL_INTERVAL = 30000;

function pollNotifications() {
    fetch('/notifications/unread_count', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        var badge = document.getElementById('notif-badge');
        if (badge) {
            if (data.count > 0) {
                badge.textContent = data.count;
            } else {
                badge.textContent = '';
            }
        }
    })
    .catch(function(err) {
        // silent failure
    });
}

pollNotifications();
setInterval(pollNotifications, POLL_INTERVAL);
