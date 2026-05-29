document.addEventListener('DOMContentLoaded', function() {
    initLikeButtons();
    initFollowButtons();
});

function initLikeButtons() {
    var likeBtns = document.querySelectorAll('.like-btn');
    likeBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            var postId = btn.dataset.postId;
            toggleLike(postId, btn);
        });
    });
}

function toggleLike(postId, btn) {
    fetch('/feed/post/' + postId + '/like', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({})
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        var countEl = document.querySelector('.like-count-' + postId);
        if (countEl) {
            countEl.textContent = data.like_count;
        }
        if (data.liked) {
            btn.classList.add('liked');
        } else {
            btn.classList.remove('liked');
        }
    })
    .catch(function(err) {
        console.error('Like failed:', err);
    });
}

function initFollowButtons() {
    var followBtns = document.querySelectorAll('.follow-btn');
    followBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            var username = btn.dataset.username;
            toggleFollow(username, btn);
        });
    });
}

function toggleFollow(username, btn) {
    fetch('/profile/' + username + '/follow', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({})
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        btn.textContent = data.following ? 'Unfollow' : 'Follow';
        var followerCountEls = document.querySelectorAll('.follower-count');
        followerCountEls.forEach(function(el) {
            el.textContent = data.follower_count;
        });
    })
    .catch(function(err) {
        console.error('Follow failed:', err);
    });
}
