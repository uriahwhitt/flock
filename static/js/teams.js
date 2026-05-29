document.addEventListener('DOMContentLoaded', function() {
    var joinBtn = document.querySelector('.join-btn');
    if (joinBtn) {
        joinBtn.addEventListener('click', function() {
            var slug = joinBtn.dataset.slug;
            toggleJoin(slug, joinBtn);
        });
    }
});

function toggleJoin(slug, btn) {
    var formData = new FormData();
    formData.append('slug', slug);

    fetch('/teams/' + slug + '/join', {
        method: 'POST',
        body: formData
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        btn.textContent = data.member ? 'Leave' : 'Join';
        var memberCountEl = document.querySelector('.member-count');
        if (memberCountEl) {
            memberCountEl.textContent = data.member_count + ' members';
        }
    })
    .catch(function(err) {
        console.error('Join failed:', err);
    });
}
