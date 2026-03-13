// API Base URLs
const AUTH_API = '/api/auth';
const VIDEO_API = '/api/videos';

// Token management
function getToken() {
    return localStorage.getItem('fiapx_token');
}

function setToken(token) {
    localStorage.setItem('fiapx_token', token);
}

function clearToken() {
    localStorage.removeItem('fiapx_token');
    localStorage.removeItem('fiapx_username');
}

function getAuthHeaders() {
    return { 'Authorization': 'Bearer ' + getToken() };
}

// Check if user is logged in on page load
window.addEventListener('load', function() {
    if (getToken()) {
        showApp();
    }
});

// Auth functions
function showLogin() {
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('register-form').style.display = 'none';
}

function showRegister() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
}

function showApp() {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('app-screen').style.display = 'flex';
    document.getElementById('username-display').textContent =
        localStorage.getItem('fiapx_username') || 'Usuário';
}

function showLoginScreen() {
    document.getElementById('login-screen').style.display = 'flex';
    document.getElementById('app-screen').style.display = 'none';
}

async function doLogin() {
    var username = document.getElementById('login-username').value;
    var password = document.getElementById('login-password').value;
    var errorDiv = document.getElementById('login-error');
    errorDiv.style.display = 'none';

    if (!username || !password) {
        errorDiv.textContent = 'Preencha todos os campos';
        errorDiv.style.display = 'block';
        return;
    }

    try {
        var formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        var response = await fetch(AUTH_API + '/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        var data = await response.json();

        if (response.ok) {
            setToken(data.access_token);
            localStorage.setItem('fiapx_username', username);
            showApp();
        } else {
            errorDiv.textContent = data.detail || 'Erro ao fazer login';
            errorDiv.style.display = 'block';
        }
    } catch (err) {
        errorDiv.textContent = 'Erro de conexão: ' + err.message;
        errorDiv.style.display = 'block';
    }
}

async function doRegister() {
    var username = document.getElementById('reg-username').value;
    var email = document.getElementById('reg-email').value;
    var password = document.getElementById('reg-password').value;
    var errorDiv = document.getElementById('register-error');
    var successDiv = document.getElementById('register-success');
    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';

    if (!username || !email || !password) {
        errorDiv.textContent = 'Preencha todos os campos';
        errorDiv.style.display = 'block';
        return;
    }

    try {
        var response = await fetch(AUTH_API + '/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username, email: email, password: password })
        });

        var data = await response.json();

        if (response.ok) {
            successDiv.textContent = 'Registro realizado! Faça login.';
            successDiv.style.display = 'block';
            setTimeout(showLogin, 2000);
        } else {
            errorDiv.textContent = data.detail || 'Erro ao registrar';
            errorDiv.style.display = 'block';
        }
    } catch (err) {
        errorDiv.textContent = 'Erro de conexão: ' + err.message;
        errorDiv.style.display = 'block';
    }
}

function doLogout() {
    clearToken();
    showLoginScreen();
}

// Tab navigation
function showTab(tabName) {
    var contents = document.querySelectorAll('.tab-content');
    contents.forEach(function(content) { content.classList.remove('active'); });

    var buttons = document.querySelectorAll('.nav-btn');
    buttons.forEach(function(btn) { btn.classList.remove('active'); });

    document.getElementById(tabName).classList.add('active');
    event.currentTarget.classList.add('active');

    if (tabName === 'history') {
        loadHistory();
    }
}

// Upload logic - supports multiple files
document.getElementById('fileElem').addEventListener('change', function(e) {
    var files = e.target.files;
    if (files.length > 0) {
        for (var i = 0; i < files.length; i++) {
            uploadVideo(files[i]);
        }
    }
});

function uploadVideo(file) {
    var progressDiv = document.getElementById('upload-progress');
    progressDiv.style.display = 'block';

    var itemId = 'upload-' + Date.now() + '-' + Math.random().toString(36).substr(2, 5);
    var itemHTML = '<div class="upload-item" id="' + itemId + '">' +
        '<span>' + file.name + '</span>' +
        '<span class="badge processing">Enviando...</span></div>';
    progressDiv.innerHTML += itemHTML;

    var formData = new FormData();
    formData.append('file', file);

    fetch(VIDEO_API + '/upload', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: formData
    })
    .then(function(response) { return response.json().then(function(data) { return { ok: response.ok, data: data }; }); })
    .then(function(result) {
        var item = document.getElementById(itemId);
        if (result.ok) {
            item.querySelector('.badge').className = 'badge completed';
            item.querySelector('.badge').textContent = 'Enviado!';
        } else {
            item.querySelector('.badge').className = 'badge error';
            item.querySelector('.badge').textContent = 'Erro';
        }
    })
    .catch(function(err) {
        var item = document.getElementById(itemId);
        if (item) {
            item.querySelector('.badge').className = 'badge error';
            item.querySelector('.badge').textContent = 'Erro';
        }
    });
}

// History
function loadHistory() {
    var tbody = document.getElementById('history-body');
    tbody.innerHTML = '<tr><td colspan="4">Carregando...</td></tr>';

    fetch(VIDEO_API + '/videos', {
        headers: getAuthHeaders()
    })
    .then(function(res) {
        if (res.status === 401) {
            clearToken();
            showLoginScreen();
            return [];
        }
        return res.json();
    })
    .then(function(videos) {
        tbody.innerHTML = '';
        if (!videos || videos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4">Nenhum vídeo encontrado.</td></tr>';
            return;
        }
        videos.forEach(function(video) {
            var tr = document.createElement('tr');
            var statusClass = video.status || 'uploaded';
            var statusText = {
                'uploaded': 'Enviado',
                'queued': 'Na Fila',
                'processing': 'Processando',
                'completed': 'Concluído',
                'error': 'Erro'
            }[statusClass] || statusClass;

            var size = video.file_size ? formatFileSize(video.file_size) : '-';
            var date = video.created_at ? new Date(video.created_at).toLocaleString('pt-BR') : '-';

            tr.innerHTML =
                '<td>' + video.original_filename + '</td>' +
                '<td><span class="badge ' + statusClass + '">' + statusText + '</span></td>' +
                '<td>' + date + '</td>' +
                '<td>' + size + '</td>';
            tbody.appendChild(tr);
        });
    });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    var k = 1024;
    var sizes = ['B', 'KB', 'MB', 'GB'];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Auto-refresh history every 10 seconds when on history tab
setInterval(function() {
    if (document.getElementById('history').classList.contains('active')) {
        loadHistory();
    }
}, 10000);
