
const API_URL = "http://127.0.0.1:5000";

// LISTAR EVENTOS
async function carregarEventos() {
    try {
        const resposta = await fetch(`${API_URL}/eventos`);
        const eventos = await resposta.json();

        const lista = document.getElementById("lista-eventos");

        lista.innerHTML = "";

        eventos.forEach(evento => {
            const card = document.createElement("div");

            card.className = "evento-card";

            card.innerHTML = `
                <h3>${evento.nome}</h3>
                <p>${evento.descricao || ""}</p>
                <p>Data: ${evento.data}</p>
                <p>Local: ${evento.local}</p>
                <button onclick="inscreverEvento(${evento.id})">
                    Inscrever-se
                </button>
            `;

            lista.appendChild(card);
        });

    } catch (erro) {
        console.error("Erro ao carregar eventos:", erro);
    }
}


// REALIZAR INSCRIÇÃO
async function inscreverEvento(eventoId) {
    const usuarioId = localStorage.getItem("usuarioId");

    if (!usuarioId) {
        alert("Faça login para se inscrever!");
        return;
    }

    try {
        const resposta = await fetch(`${API_URL}/inscricoes`, {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                usuario_id: Number(usuarioId),
                evento_id: eventoId
            })
        });

        const dados = await resposta.json();

        alert(dados.mensagem || dados.erro);

    } catch (erro) {
        alert("Erro ao realizar inscrição.");
    }
}


// LISTAR CERTIFICADOS DO USUÁRIO
async function carregarCertificados() {
    const usuarioId = localStorage.getItem("usuarioId");

    if (!usuarioId) {
        alert("Faça login para consultar seus certificados.");
        return;
    }

    try {
        const resposta = await fetch(
            `${API_URL}/usuarios/${usuarioId}/certificacoes`
        );

        const certificados = await resposta.json();

        const lista = document.getElementById("lista-certificados");

        lista.innerHTML = "";

        certificados.forEach(certificado => {
            const item = document.createElement("div");

            item.className = "certificado-card";

            item.innerHTML = `
                <h3>${certificado.evento}</h3>
                <p>Código: ${certificado.codigo}</p>
                <p>Data de emissão: ${certificado.data_emissao}</p>
            `;

            lista.appendChild(item);
        });

    } catch (erro) {
        console.error("Erro ao carregar certificados:", erro);
    }
}
