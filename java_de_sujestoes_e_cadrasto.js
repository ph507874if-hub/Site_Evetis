
const API_URL = "http://127.0.0.1:5000";


// =========================
// CADASTRO DE USUÁRIO
// =========================

const formularioCadastro = document.querySelector("[data-form-conta]");

if (formularioCadastro) {

    formularioCadastro.addEventListener("submit", async function(event) {

        event.preventDefault();

        const nome = formularioCadastro.elements.nome.value.trim();
        const email = formularioCadastro.elements.email.value.trim();
        const senha = formularioCadastro.elements.senha.value;

        const aviso = document.querySelector(".conta-aviso");
        const botao = formularioCadastro.querySelector("button");

        aviso.textContent = "Enviando cadastro...";
        botao.disabled = true;

        try {

            const resposta = await fetch(`${API_URL}/usuarios`, {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    nome: nome,
                    email: email,
                    senha: senha
                })
            });

            const dados = await resposta.json();

            if (!resposta.ok) {
                throw new Error(dados.mensagem || "Erro ao cadastrar.");
            }

            // Guarda o ID para as funcionalidades de inscrição
            localStorage.setItem("usuarioId", dados.id);

            formularioCadastro.reset();

            aviso.textContent = dados.mensagem;

        } catch (erro) {

            aviso.textContent = erro.message;

        } finally {

            botao.disabled = false;

        }

    });

}


// =========================
// SUGESTÕES E RECLAMAÇÕES
// =========================

const formularioSugestao = document.getElementById("form-sugestao");

if (formularioSugestao) {

    formularioSugestao.addEventListener("submit", async function(event) {

        event.preventDefault();

        const tipo = formularioSugestao.elements.tipo.value;
        const categoria = formularioSugestao.elements.categoria.value;
        const mensagem = formularioSugestao.elements.mensagem.value.trim();

        const status = document.getElementById("status-sugestao");
        const botao = formularioSugestao.querySelector("button");

        status.textContent = "Enviando mensagem...";
        botao.disabled = true;

        try {

            const resposta = await fetch(`${API_URL}/sugestoes`, {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    tipo: tipo,
                    categoria: categoria,
                    mensagem: mensagem
                })
            });

            const dados = await resposta.json();

            if (!resposta.ok) {
                throw new Error(dados.mensagem || "Erro ao enviar mensagem.");
            }

            formularioSugestao.reset();

            status.textContent = dados.mensagem;

        } catch (erro) {

            status.textContent = erro.message;

        } finally {

            botao.disabled = false;

        }

    });

}
