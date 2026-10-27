document.querySelectorAll('[data-form-conta]').forEach((formulario) => {
    formulario.addEventListener('submit', (event) => {
        event.preventDefault();
    });
});
