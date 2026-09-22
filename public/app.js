(function () {
    const params = new URLSearchParams(window.location.search);
    const noticeBox = document.getElementById('notice-box');

    if (params.get('created') === '1' && noticeBox) {
        noticeBox.innerHTML = '<p class="notice" role="status">Your account is ready. Log in to get started.</p>';
    }

    function getUsers() {
        try {
            return JSON.parse(localStorage.getItem('talents_users') || '[]');
        } catch {
            return [];
        }
    }

    function saveUsers(users) {
        localStorage.setItem('talents_users', JSON.stringify(users));
    }

    function getCurrentUser() {
        try {
            return JSON.parse(localStorage.getItem('talents_current_user') || 'null');
        } catch {
            return null;
        }
    }

    function setCurrentUser(user) {
        if (user) {
            localStorage.setItem('talents_current_user', JSON.stringify(user));
        } else {
            localStorage.removeItem('talents_current_user');
        }
    }

    // Signup form handler
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        signupForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const name = document.getElementById('name').value.trim();
            const email = document.getElementById('email').value.trim().toLowerCase();
            const password = document.getElementById('password').value;

            if (!name || !email || !password) {
                if (noticeBox) noticeBox.innerHTML = '<p class="notice error" role="alert">Please fill out all fields.</p>';
                return;
            }
            if (password.length < 6) {
                if (noticeBox) noticeBox.innerHTML = '<p class="notice error" role="alert">Your password must be at least 6 characters.</p>';
                return;
            }

            const users = getUsers();
            if (users.some(u => u.email === email)) {
                if (noticeBox) noticeBox.innerHTML = '<p class="notice error" role="alert">This email is already registered. Please log in.</p>';
                return;
            }

            users.push({ name, email, password });
            saveUsers(users);
            window.location.href = '/login.html?created=1';
        });
    }

    // Login form handler
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const email = document.getElementById('email').value.trim().toLowerCase();
            const password = document.getElementById('password').value;

            const users = getUsers();
            const user = users.find(u => u.email === email && u.password === password);

            if (!user) {
                if (noticeBox) noticeBox.innerHTML = '<p class="notice error" role="alert">Invalid email or password.</p>';
                return;
            }

            setCurrentUser({ name: user.name, email: user.email });
            window.location.href = '/dashboard.html';
        });
    }

    // Dashboard handler
    const dashboardAvatar = document.getElementById('user-avatar');
    if (dashboardAvatar) {
        const user = getCurrentUser();
        if (!user) {
            window.location.href = '/login.html';
            return;
        }
        document.getElementById('user-name').textContent = user.name;
        document.getElementById('user-email').textContent = user.email;
        dashboardAvatar.textContent = (user.name[0] || 'U').toUpperCase();

        const logoutForm = document.getElementById('logout-form');
        if (logoutForm) {
            logoutForm.addEventListener('submit', function (e) {
                e.preventDefault();
                setCurrentUser(null);
                window.location.href = '/login.html';
            });
        }
    }

    // Forgot password handler
    const forgotForm = document.getElementById('forgot-form');
    if (forgotForm) {
        forgotForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const email = document.getElementById('email').value.trim().toLowerCase();
            const users = getUsers();
            const exists = users.some(u => u.email === email);

            if (noticeBox) {
                if (exists) {
                    noticeBox.innerHTML = '<p class="notice" role="status">Reset link generated (demo mode: no email sent).</p>';
                } else {
                    noticeBox.innerHTML = '<p class="notice error" role="alert">No account found with that email.</p>';
                }
            }
        });
    }
})();
