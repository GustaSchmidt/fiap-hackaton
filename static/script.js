// Função para trocar abas
function showTab(tabName) {
    const contents = document.querySelectorAll('.tab-content');
    contents.forEach(content => content.classList.remove('active'));

    const buttons = document.querySelectorAll('.nav-btn');
    buttons.forEach(btn => btn.classList.remove('active'));

    document.getElementById(tabName).classList.add('active');
    event.currentTarget.classList.add('active');

    if (tabName === 'history') {
        loadHistory();
    }
}

// Lógica de Upload
document.getElementById('fileElem').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        uploadVideo(file);
    }
});

function uploadVideo(file) {
    const formData = new FormData();
    formData.append('file', file);

    const uploadBox = document.getElementById('drop-area');
    const originalHTML = uploadBox.innerHTML;
    
    uploadBox.innerHTML = `<i class="fas fa-spinner fa-spin fa-3x"></i><p>Enviando para o MinIO...</p>`;

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert(data.message);
        } else {
            alert("Erro: " + data.error);
        }
    })
    .catch(err => alert("Erro na conexão: " + err))
    .finally(() => {
        uploadBox.innerHTML = originalHTML;
    });
}

// Carregar Histórico Dinamicamente
function loadHistory() {
    const tbody = document.querySelector('.data-table tbody');
    tbody.innerHTML = '<tr><td colspan="4">Carregando...</td></tr>';

    fetch('/list-videos')
        .then(res => res.json())
        .then(videos => {
            tbody.innerHTML = '';
            if (videos.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4">Nenhum vídeo encontrado.</td></tr>';
                return;
            }
            videos.forEach(video => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${video.name}</td>
                    <td><span class="badge success">Armazenado</span></td>
                    <td>${video.last_modified}</td>
                    <td><button class="btn-text">Processar</button></td>
                `;
                tbody.appendChild(tr);
            });
        });
}