function showTab(tabName) {
    // Esconde todos os conteúdos
    const contents = document.querySelectorAll('.tab-content');
    contents.forEach(content => content.classList.remove('active'));

    // Remove a classe active de todos os botões
    const buttons = document.querySelectorAll('.nav-btn');
    buttons.forEach(btn => btn.classList.remove('active'));

    // Mostra o selecionado
    document.getElementById(tabName).classList.add('active');
    event.currentTarget.classList.add('active');
}

document.getElementById('fileElem').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        uploadVideo(file);
    }
});

function uploadVideo(file) {
    const formData = new FormData();
    formData.append('file', file);

    // Feedback visual simples
    const uploadBox = document.getElementById('drop-area');
    const originalContent = uploadBox.innerHTML;
    uploadBox.innerHTML = `<i class="fas fa-spinner fa-spin fa-3x"></i><p>Enviando ${file.name}...</p>`;

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert(data.message);
            // Aqui você poderia atualizar a aba de histórico automaticamente
        } else {
            alert("Erro: " + data.error);
        }
    })
    .catch(error => {
        console.error('Erro no upload:', error);
        alert("Falha na conexão com o servidor.");
    })
    .finally(() => {
        uploadBox.innerHTML = originalContent;
    });
}