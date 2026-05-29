document.addEventListener('DOMContentLoaded', function() {
    var submitBtn = document.getElementById('submit-comment');
    if (submitBtn) {
        submitBtn.addEventListener('click', function() {
            var postId = submitBtn.dataset.postId;
            var input = document.getElementById('comment-input');
            var content = input.value.trim();
            if (!content) return;

            submitComment(postId, content, input);
        });
    }
});

function submitComment(postId, content, inputEl) {
    fetch('/feed/post/' + postId + '/comment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ content: content })
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.error) {
            console.error('Comment error:', data.error);
            return;
        }
        var commentContainer = document.getElementById('comments-list');
        commentContainer.innerHTML = commentContainer.innerHTML + `<div class="comment">${data.content}</div>`;
        inputEl.value = '';
    })
    .catch(function(err) {
        console.error('Comment failed:', err);
    });
}
