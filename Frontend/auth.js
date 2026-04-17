const API_URL = "http://localhost:5000";

async function handleRegister() {
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;

    if (!username || !email || !password) {
        alert("Please fill in all fields");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();
        if (response.ok) {
            alert("Registration successful! Please login.");
            toggleAuth('login');
        } else {
            alert(data.error || "Registration failed");
        }
    } catch (err) {
        alert("Error connecting to server");
    }
}

async function handleLogin() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    if (!username || !password) {
        alert("Please fill in all fields");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();
        if (response.ok) {
            localStorage.setItem('isLoggedIn', 'true');
            localStorage.setItem('username', data.username);
            window.location.href = "dashboard.html";
        } else {
            alert(data.error || "Login failed");
        }
    } catch (err) {
        alert("Error connecting to server");
    }
}

function checkAuth() {
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    const username = localStorage.getItem('username');
    
    if (!isLoggedIn && window.location.pathname.includes('dashboard.html')) {
        window.location.href = "index.html";
    }

    if (isLoggedIn && username) {
        const userDisplay = document.getElementById('userDisplay');
        if (userDisplay) {
            userDisplay.innerText = `Welcome, ${username}`;
        }
    }
}

function checkAuthStatus() {
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    if (isLoggedIn) {
        document.querySelectorAll('.auth-links').forEach(el => el.style.display = 'none');
        document.querySelector('.dashboard-link').style.display = 'block';
    }
}

function logout() {
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('username');
    window.location.href = "index.html";
}
