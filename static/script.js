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