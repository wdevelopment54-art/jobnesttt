// JobNest main JavaScript - Vanilla JS only

document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss flash messages
    setTimeout(function () {
        document.querySelectorAll('.alert').forEach(function (el) {
            var alert = bootstrap.Alert.getOrCreateInstance(el);
            if (alert) setTimeout(function () { alert.close(); }, 5000);
        });
    }, 5000);

    // Confirm dialogs for destructive actions
    document.querySelectorAll('[data-confirm]').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            if (!confirm(btn.getAttribute('data-confirm'))) {
                e.preventDefault();
            }
        });
    });

    // Image preview
    document.querySelectorAll('input[type="file"][data-preview]').forEach(function (input) {
        input.addEventListener('change', function () {
            var target = document.querySelector(input.getAttribute('data-preview'));
            if (target && input.files && input.files[0]) {
                var reader = new FileReader();
                reader.onload = function (e) { target.src = e.target.result; target.style.display = 'block'; };
                reader.readAsDataURL(input.files[0]);
            }
        });
    });

    // Bookmark toggle (save job) - handled via form submit, no JS needed
    // Mobile navbar active link highlight
    var path = window.location.pathname;
    document.querySelectorAll('.navbar-nav .nav-link').forEach(function (link) {
        if (link.getAttribute('href') === path) {
            link.classList.add('active');
        }
    });

    // Password strength indicator
    var pw = document.querySelector('input[type="password"][data-strength]');
    if (pw) {
        var meter = document.createElement('div');
        meter.className = 'progress mt-2';
        meter.innerHTML = '<div class="progress-bar" style="width:0%"></div>';
        pw.parentNode.appendChild(meter);
        pw.addEventListener('input', function () {
            var val = pw.value;
            var score = 0;
            if (val.length >= 8) score++;
            if (/[A-Z]/.test(val)) score++;
            if (/[a-z]/.test(val)) score++;
            if (/\d/.test(val)) score++;
            if (/[^A-Za-z0-9]/.test(val)) score++;
            var pct = (score / 5) * 100;
            var bar = meter.querySelector('.progress-bar');
            bar.style.width = pct + '%';
            bar.style.background = pct < 40 ? '#dc2626' : pct < 80 ? '#f59e0b' : '#16a34a';
        });
    }
});
