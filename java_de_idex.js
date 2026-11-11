
const API_URL = "http://127.0.0.1:5000";

let eventos = [];
let modoLogin = false;
let minhasMensagens = [];

const usuarioId = () => localStorage.getItem("usuarioId");
const usuarioNome = () => localStorage.getItem("usuarioNome");
const usuarioTipo = () => localStorage.getItem("usuarioTipo");


// ==========================================
// FUNÇÃO PARA CONVERSAR COM O PYTHON
// ==========================================

async function requisicao(url, opcoes = {}) {

    const resposta = await fetch(`${API_URL}${url}`, opcoes);

    const dados = await resposta.json();

    if (!resposta.ok) {
        throw new Error(dados.mensagem || "Erro na operação.");
    }

    return dados;
}


// ==========================================
// NOTIFICAÇÕES
// ==========================================

function notificar(mensagem) {

    const notificacao = document.getElementById("notificacao");

    notificacao.textContent = mensagem;
    notificacao.classList.add("ativo");

    setTimeout(() => {
        notificacao.classList.remove("ativo");
    }, 3000);
}


// ==========================================
// MODAL DE CADASTRO E LOGIN
// ==========================================

const modalConta = document.getElementById("modal-conta");
const formularioConta = document.getElementById("form-conta");

function abrirConta(login = false) {

    modoLogin = login;

    document.getElementById("titulo-conta").textContent =
        login ? "Entrar na conta" : "Criar conta";

    document.getElementById("enviar-conta").textContent =
        login ? "Entrar" : "Criar conta";

    document.getElementById("campo-nome").style.display =
        login ? "none" : "block";

    document.getElementById("nome").required = !login;

    document.getElementById("senha").autocomplete =
        login ? "current-password" : "new-password";

    document.getElementById("alternar-conta").textContent =
        login ? "Criar uma conta" : "Já tenho conta";

    document.getElementById("mensagem-conta").textContent =
        login
            ? "Informe seu e-mail e sua senha."
            : "Preencha os dados para criar sua conta.";

    modalConta.showModal();
}

document.getElementById("btn-login").onclick = () => {
    abrirConta(true);
};

document.getElementById("btn-cadastro").onclick = () => {
    abrirConta(false);
};

document.getElementById("fechar-conta").onclick = () => {
    modalConta.close();
};

document.getElementById("alternar-conta").onclick = () => {
    abrirConta(!modoLogin);
};


// ==========================================
// MOSTRAR E ESCONDER SENHA
// ==========================================

document.querySelectorAll(".mostrar-senha").forEach(botao => {

    botao.addEventListener("click", () => {

        const campo = document.getElementById(
            botao.dataset.alvo
        );

        if (campo.type === "password") {

            campo.type = "text";
            botao.textContent = "Ocultar";

        } else {

            campo.type = "password";
            botao.textContent = "Mostrar";

        }

    });

});


// ==========================================
// CADASTRO E LOGIN
// ==========================================

formularioConta.addEventListener("submit", async event => {

    event.preventDefault();

    const nome = document.getElementById("nome").value.trim();

    const email = document.getElementById("email").value.trim();

    const senha = document.getElementById("senha").value;

    const mensagem = document.getElementById("mensagem-conta");

    const botao = document.getElementById("enviar-conta");

    botao.disabled = true;
    mensagem.textContent = "Processando...";

    try {

        const dados = await requisicao(
            modoLogin ? "/login" : "/usuarios",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(
                    modoLogin
                        ? { email, senha }
                        : { nome, email, senha }
                )
            }
        );

        if (modoLogin) {

            localStorage.setItem("usuarioId", dados.id);

            localStorage.setItem("usuarioNome", dados.nome);

            localStorage.setItem("usuarioTipo", dados.tipo);

            modalConta.close();

            formularioConta.reset();

            atualizarUsuario();

            carregarPerfil();

            carregarEventos();

            carregarInscricoes();

            notificar("Login realizado com sucesso!");

        } else {

            mensagem.textContent = dados.mensagem;

            formularioConta.reset();

            notificar("Conta criada com sucesso!");

            abrirConta(true);

        }

    } catch (erro) {

        mensagem.textContent = erro.message;

    } finally {

        botao.disabled = false;

    }

});


// ==========================================
// ATUALIZAR ÁREA DO USUÁRIO
// ==========================================

function atualizarUsuario() {

    const area = document.getElementById("area-usuario");

    const botaoCriar = document.getElementById("btn-criar-evento");

    if (!usuarioId()) {

        area.innerHTML = `
            <button id="btn-login" class="btn btn-outline">
                Entrar
            </button>

            <button id="btn-cadastro" class="btn btn-primary">
                Criar conta
            </button>
        `;

        document.getElementById("btn-login").onclick =
            () => abrirConta(true);

        document.getElementById("btn-cadastro").onclick =
            () => abrirConta(false);

        botaoCriar.style.display = "none";

        return;
    }

    area.innerHTML = `
        <span>Olá, ${escapar(usuarioNome())}</span>

        <button id="btn-sair" class="btn btn-outline">
            Sair
        </button>
    `;

    document.getElementById("btn-sair").onclick = sair;

    botaoCriar.style.display =
        usuarioTipo() === "admin" ? "inline-block" : "none";
}


// ==========================================
// SAIR DA CONTA
// ==========================================

function sair() {

    localStorage.removeItem("usuarioId");
    localStorage.removeItem("usuarioNome");
    localStorage.removeItem("usuarioTipo");

    atualizarUsuario();

    carregarPerfil();

    carregarInscricoes();

    notificar("Você saiu da sua conta.");

}


// ==========================================
// PROTEGER TEXTO EXIBIDO NA PÁGINA
// ==========================================

function escapar(texto) {

    return String(texto ?? "").replace(/[&<>"']/g, caractere => ({

        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"

    })[caractere]);

}


// ==========================================
// CARREGAR EVENTOS
// ==========================================

async function carregarEventos() {

    try {

        eventos = await requisicao("/eventos");

        filtrarEventos();

    } catch (erro) {

        notificar(erro.message);

    }

}


// ==========================================
// PESQUISAR E FILTRAR EVENTOS
// ==========================================

function filtrarEventos() {

    const pesquisa = document.getElementById("pesquisa")
        .value.toLowerCase();

    const categoria = document.getElementById("filtro-categoria")
        .value;

    const encontrados = eventos.filter(evento => {

        const nome = evento.nome.toLowerCase();

        const correspondeNome = nome.includes(pesquisa);

        const correspondeCategoria =
            categoria === "Todas" ||
            evento.categoria === categoria;

        return correspondeNome && correspondeCategoria;

    });

    const lista = document.getElementById("lista-eventos");

    const mensagem = document.getElementById("sem-eventos");

    mensagem.classList.toggle("hidden", encontrados.length > 0);

    lista.innerHTML = encontrados.map(evento => `

        <article class="evento-card">

            <span>${escapar(evento.categoria || "Outros")}</span>

            <h3>${escapar(evento.nome)}</h3>

            <p>${escapar(evento.descricao)}</p>

            <p>📅 ${escapar(evento.data)}</p>

            <p>📍 ${escapar(evento.local)}</p>

            <button class="btn btn-primary"
                onclick="inscrever(${Number(evento.id)})">

                Participar

            </button>

            <button class="btn btn-outline"
                onclick="abrirAvaliacao(${Number(evento.id)})">

                Avaliar evento

            </button>

        </article>

    `).join("");

}

document.getElementById("pesquisa").addEventListener(
    "input", filtrarEventos
);

document.getElementById("filtro-categoria").addEventListener(
    "change", filtrarEventos
);


// ==========================================
// CRIAR EVENTO
// ==========================================

const modalEvento = document.getElementById("modal-evento");

const formularioEvento = document.getElementById("form-evento");

function abrirEvento() {

    if (!usuarioId()) {

        notificar("Entre na sua conta primeiro.");

        abrirConta(true);

        return;
    }

    if (usuarioTipo() !== "admin") {

        notificar("Somente administradores podem criar eventos.");

        return;
    }

    modalEvento.showModal();

}

document.getElementById("btn-criar-evento").onclick =
    abrirEvento;

document.getElementById("btn-criar-evento-final").onclick =
    abrirEvento;

document.getElementById("fechar-evento").onclick = () => {
    modalEvento.close();
};

document.getElementById("cancelar-evento").onclick = () => {
    modalEvento.close();
};


// ==========================================
// PUBLICAR EVENTO
// ==========================================

formularioEvento.addEventListener("submit", async event => {

    event.preventDefault();

    if (!usuarioId() || usuarioTipo() !== "admin") {

        notificar("Acesso permitido somente para administradores.");

        return;
    }

    const dados = {

        nome: formularioEvento.elements.nome.value.trim(),

        categoria: formularioEvento.elements.categoria.value,

        data: formularioEvento.elements.data.value,

        local: formularioEvento.elements.local.value.trim(),

        descricao: formularioEvento.elements.descricao.value.trim(),

        admin_id: Number(usuarioId())

    };

    try {

        const resposta = await requisicao("/eventos", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(dados)

        });

        formularioEvento.reset();

        modalEvento.close();

        notificar(resposta.mensagem);

        carregarEventos();

    } catch (erro) {

        notificar(erro.message);

    }

});


// ==========================================
// REALIZAR INSCRIÇÃO
// ==========================================

async function inscrever(eventoId) {

    if (!usuarioId()) {

        notificar("Entre na sua conta para se inscrever.");

        abrirConta(true);

        return;
    }

    try {

        const dados = await requisicao("/inscricoes", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                usuario_id: Number(usuarioId()),

                evento_id: eventoId

            })

        });

        notificar(dados.mensagem);

        carregarInscricoes();

    } catch (erro) {

        notificar(erro.message);

    }

}


// ==========================================
// MINHAS INSCRIÇÕES
// ==========================================

async function carregarInscricoes() {

    const lista = document.getElementById("lista-inscricoes");

    const vazio = document.getElementById("sem-inscricoes");

    if (!usuarioId()) {

        lista.innerHTML = "";

        vazio.textContent =
            "Entre na sua conta para visualizar suas inscrições.";

        vazio.style.display = "block";

        return;
    }

    try {

        const inscricoes = await requisicao("/inscricoes");

        const minhas = inscricoes.filter(i =>
            i.usuario_id === Number(usuarioId())
        );

        vazio.style.display = minhas.length ? "none" : "block";

        vazio.textContent = "Você ainda não possui inscrições.";

        lista.innerHTML = minhas.map(i => {

            const evento = eventos.find(e => e.id === i.evento_id);

            return `

                <article class="painel">

                    <h3>${escapar(evento?.nome || "Evento")}</h3>

                    <p>Data da inscrição: ${escapar(i.data_inscricao)}</p>

                    <p>Presença:
                        ${i.presente ? "Confirmada" : "Pendente"}
                    </p>

                </article>

            `;

        }).join("");

    } catch (erro) {

        notificar(erro.message);

    }

}


// ==========================================
// PERFIL DO USUÁRIO
// ==========================================

function carregarPerfil() {

    const painel = document.getElementById("conteudo-perfil");

    if (!usuarioId()) {

        painel.innerHTML = `
            <p>Você precisa entrar para acessar seu perfil.</p>
        `;

        return;
    }

    painel.innerHTML = `

        <h3>${escapar(usuarioNome())}</h3>

        <p>ID: ${escapar(usuarioId())}</p>

        <p>Tipo de conta: ${escapar(usuarioTipo())}</p>

        <button class="btn btn-outline" onclick="sair()">
            Sair da conta
        </button>

    `;

}


// ==========================================
// RECLAMAÇÕES E SUGESTÕES
// ==========================================

const formularioReclamacao =
    document.getElementById("form-reclamacao");

formularioReclamacao.addEventListener("submit", async event => {

    event.preventDefault();

    const tipo = document.getElementById("tipo-reclamacao").value;

    const mensagem = document.getElementById("texto-reclamacao")
        .value.trim();

    if (!usuarioId()) {

        notificar("Entre na sua conta para enviar uma mensagem.");

        abrirConta(true);

        return;
    }

    try {

        const dados = await requisicao("/sugestoes", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                tipo: tipo,

                categoria: "Geral",

                mensagem: mensagem,

                usuario_id: Number(usuarioId())

            })

        });

        minhasMensagens.push({

            tipo: tipo,

            mensagem: mensagem

        });

        mostrarMinhasMensagens();

        formularioReclamacao.reset();

        notificar(dados.mensagem);

    } catch (erro) {

        notificar(erro.message);

    }

});


// ==========================================
// MOSTRAR MINHAS MENSAGENS
// ==========================================

function mostrarMinhasMensagens() {

    const lista = document.getElementById("lista-reclamacoes");

    lista.innerHTML = minhasMensagens.map(mensagem => `

        <article class="painel">

            <strong>${escapar(mensagem.tipo)}</strong>

            <p>${escapar(mensagem.mensagem)}</p>

        </article>

    `).join("");

}


// ==========================================
// AVALIAÇÕES DE EVENTOS
// ==========================================

const modalAvaliacao =
    document.getElementById("modal-avaliacao");

const formularioAvaliacao =
    document.getElementById("form-avaliacao");

function abrirAvaliacao(eventoId) {

    if (!usuarioId()) {

        notificar("Entre na sua conta para avaliar.");

        abrirConta(true);

        return;
    }

    document.getElementById("avaliacao-evento-id").value =
        eventoId;

    modalAvaliacao.showModal();

}

document.getElementById("fechar-avaliacao").onclick = () => {
    modalAvaliacao.close();
};


formularioAvaliacao.addEventListener("submit", async event => {

    event.preventDefault();

    const eventoId = Number(
        document.getElementById("avaliacao-evento-id").value
    );

    const nota = Number(
        document.getElementById("nota-avaliacao").value
    );

    const comentario = document.getElementById(
        "comentario-avaliacao"
    ).value.trim();

    try {

        const dados = await requisicao("/avaliacoes", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                usuario_id: Number(usuarioId()),

                evento_id: eventoId,

                nota: nota,

                comentario: comentario

            })

        });

        formularioAvaliacao.reset();

        modalAvaliacao.close();

        notificar(dados.mensagem);

    } catch (erro) {

        notificar(erro.message);

    }

});


// ==========================================
// INICIALIZAÇÃO
// ==========================================

atualizarUsuario();

carregarEventos();

carregarPerfil();

carregarInscricoes();
