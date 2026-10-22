from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
from uuid import uuid4
# Modelos desenvolvidos por João Pedro
from modelos import Base, Usuario, Admin
# Modelos desenvolvidos por você
from modelos_eventos import Evento, Inscricao, Certificacao

app = Flask(__name__)
CORS(app)

# =========================
# BANCO DE DADOS
# =========================

engine = create_engine("sqlite:///database.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# =========================
# ROTAS PARA SERVIR HTML
# =========================

@app.route("/")
def index():
    return jsonify({
        "mensagem": "API do Sistema de Eventos funcionando!"
    })


# Se você criar páginas HTML, pode seguir este padrão:
# @app.route("/eventos.html")
# def pagina_eventos():
#     return send_from_directory(".", "eventos.html")


# =========================
# EVENTOS
# =========================

@app.route("/eventos", methods=["GET"])
def get_eventos():
    s = Session()
    eventos = s.query(Evento).order_by(Evento.data).all()

    return jsonify([
        {
            "id": e.id,
            "nome": e.nome,
            "descricao": e.descricao,
            "data": e.data.isoformat(),
            "local": e.local,
            "admin_id": e.admin_id
        }
        for e in eventos
    ])

@app.route("/eventos/<int:id>", methods=["GET"])
def get_evento_unico(id):
    s = Session()
    evento = s.get(Evento, id)

    if not evento:
        return jsonify({"mensagem": "Evento não encontrado!"}), 404

    return jsonify({
        "id": evento.id,
        "nome": evento.nome,
        "descricao": evento.descricao,
        "data": evento.data.isoformat(),
        "local": evento.local,
        "admin_id": evento.admin_id
    })

@app.route("/eventos", methods=["POST"])
def add_evento():
    s = Session()
    data = request.json

    if not data:
        return jsonify({"mensagem": "Envie os dados do evento!"}), 400

    campos = ["nome", "data", "local", "admin_id"]
    if any(campo not in data or data[campo] in (None, "") for campo in campos):
        return jsonify({
            "mensagem": "Informe nome, data, local e admin_id."
        }), 400

    administrador = s.get(Admin, data["admin_id"])
    if not administrador:
        return jsonify({"mensagem": "Administrador não encontrado!"}), 404

    try:
        data_evento = date.fromisoformat(data["data"])
    except (ValueError, TypeError):
        return jsonify({
            "mensagem": "Data inválida! Use o formato AAAA-MM-DD."
        }), 400

    evento = Evento(
        nome=data["nome"],
        descricao=data.get("descricao", ""),
        data=data_evento,
        local=data["local"],
        admin_id=administrador.id
    )

    s.add(evento)
    s.commit()

    return jsonify({
        "mensagem": "Evento cadastrado com sucesso!",
        "id": evento.id
    }), 201


@app.route("/eventos/<int:id>", methods=["PUT"])
def atualizar_evento(id):
    s = Session()
    evento = s.get(Evento, id)

    if not evento:
        return jsonify({"mensagem": "Evento não encontrado!"}), 404

    data = request.json
    if not data:
        return jsonify({"mensagem": "Envie os dados do evento!"}), 400

    try:
        if "nome" in data:
            evento.nome = data["nome"]
        if "descricao" in data:
            evento.descricao = data["descricao"]
        if "data" in data:
            evento.data = date.fromisoformat(data["data"])
        if "local" in data:
            evento.local = data["local"]
        if "admin_id" in data:
            administrador = s.get(Admin, data["admin_id"])
            if not administrador:
                return jsonify({"mensagem": "Administrador não encontrado!"}), 404
            evento.admin_id = administrador.id
    except (ValueError, TypeError):
        return jsonify({
            "mensagem": "Data inválida! Use o formato AAAA-MM-DD."
        }), 400

    s.commit()
    return jsonify({"mensagem": "Evento atualizado com sucesso!"})


@app.route("/eventos/<int:id>", methods=["DELETE"])
def deletar_evento(id):
    s = Session()
    evento = s.get(Evento, id)

    if not evento:
        return jsonify({"mensagem": "Evento não encontrado!"}), 404

    if s.query(Inscricao).filter_by(evento_id=id).first():
        return jsonify({
            "mensagem": "Não é possível excluir um evento que possui inscrições."
        }), 409

    s.delete(evento)
    s.commit()

    return jsonify({"mensagem": "Evento deletado com sucesso!"})


# =========================
# INSCRIÇÕES
# =========================

@app.route("/inscricoes", methods=["GET"])
def get_inscricoes():
    s = Session()
    inscricoes = s.query(Inscricao).all()

    return jsonify([
        {
            "id": i.id,
            "usuario_id": i.usuario_id,
            "evento_id": i.evento_id,
            "data_inscricao": i.data_inscricao.isoformat(),
            "presente": i.presente
        }
        for i in inscricoes
    ])


@app.route("/inscricoes/<int:id>", methods=["GET"])
def get_inscricao_unica(id):
    s = Session()
    inscricao = s.get(Inscricao, id)

    if not inscricao:
        return jsonify({"mensagem": "Inscrição não encontrada!"}), 404

    return jsonify({
        "id": inscricao.id,
        "usuario_id": inscricao.usuario_id,
        "evento_id": inscricao.evento_id,
        "data_inscricao": inscricao.data_inscricao.isoformat(),
        "presente": inscricao.presente
    })


@app.route("/inscricoes", methods=["POST"])
def add_inscricao():
    s = Session()
    data = request.json

    if not data or "usuario_id" not in data or "evento_id" not in data:
        return jsonify({
            "mensagem": "Informe usuario_id e evento_id."
        }), 400

    usuario = s.get(Usuario, data["usuario_id"])
    if not usuario:
        return jsonify({"mensagem": "Usuário não encontrado!"}), 404

    evento = s.get(Evento, data["evento_id"])
    if not evento:
        return jsonify({"mensagem": "Evento não encontrado!"}), 404

    if evento.data < date.today():
        return jsonify({
            "mensagem": "Não é possível se inscrever em um evento encerrado."
        }), 400

    inscricao_existente = s.query(Inscricao).filter_by(
        usuario_id=usuario.id,
        evento_id=evento.id
    ).first()

    if inscricao_existente:
        return jsonify({
            "mensagem": "Este usuário já está inscrito neste evento!"
        }), 409

    inscricao = Inscricao(
        usuario_id=usuario.id,
        evento_id=evento.id,
        data_inscricao=date.today(),
        presente=False
    )

    s.add(inscricao)
    s.commit()

    return jsonify({
        "mensagem": "Inscrição realizada com sucesso!",
        "id": inscricao.id
    }), 201


# =========================
# CONFIRMAR PRESENÇA
# =========================

@app.route("/inscricoes/<int:id>/presenca", methods=["PUT"])
def confirmar_presenca(id):
    s = Session()
    inscricao = s.get(Inscricao, id)

    if not inscricao:
        return jsonify({"mensagem": "Inscrição não encontrada!"}), 404

    data = request.json or {}
    if data.get("presente") is not True:
        return jsonify({
            "mensagem": "Envie presente: true para confirmar a presença."
        }), 400

    inscricao.presente = True
    s.commit()

    return jsonify({
        "mensagem": "Presença confirmada com sucesso!",
        "inscricao_id": inscricao.id,
        "presente": inscricao.presente
    })


# =========================
# CERTIFICADOS
# =========================

@app.route("/certificacoes", methods=["GET"])
def get_certificacoes():
    s = Session()
    certificados = s.query(Certificacao).all()

    return jsonify([
        {
            "id": c.id,
            "codigo": c.codigo,
            "data_emissao": c.data_emissao.isoformat(),
            "inscricao_id": c.inscricao_id
        }
        for c in certificados
    ])


@app.route("/certificacoes/<string:codigo>", methods=["GET"])
def get_certificado_unico(codigo):
    s = Session()
    certificado = s.query(Certificacao).filter_by(
        codigo=codigo.upper()
    ).first()

    if not certificado:
        return jsonify({"mensagem": "Certificado não encontrado!"}), 404

    inscricao = s.get(Inscricao, certificado.inscricao_id)
    evento = s.get(Evento, inscricao.evento_id)
    usuario = s.get(Usuario, inscricao.usuario_id)

    return jsonify({
        "id": certificado.id,
        "codigo": certificado.codigo,
        "data_emissao": certificado.data_emissao.isoformat(),
        "usuario": usuario.nome,
        "evento": evento.nome,
        "data_evento": evento.data.isoformat(),
        "inscricao_id": inscricao.id
    })


@app.route("/certificacoes/emitir", methods=["POST"])
def emitir_certificados():
    s = Session()
    inscricoes = s.query(Inscricao).all()
    emitidos = []

    for inscricao in inscricoes:
        evento = s.get(Evento, inscricao.evento_id)

        # Só emite se o evento terminou e a presença foi confirmada
        if not evento or evento.data >= date.today() or not inscricao.presente:
            continue

        # Não cria um segundo certificado para a mesma inscrição
        certificado_existente = s.query(Certificacao).filter_by(
            inscricao_id=inscricao.id
        ).first()

        if certificado_existente:
            continue

        certificado = Certificacao(
            codigo=uuid4().hex[:12].upper(),
            data_emissao=date.today(),
            inscricao_id=inscricao.id
        )

        s.add(certificado)
        s.flush()

        emitidos.append({
            "id": certificado.id,
            "codigo": certificado.codigo,
            "inscricao_id": inscricao.id,
            "usuario_id": inscricao.usuario_id,
            "evento_id": inscricao.evento_id
        })

    s.commit()

    return jsonify({
        "mensagem": "Processamento de certificados concluído!",
        "quantidade_emitida": len(emitidos),
        "certificados": emitidos
    })


@app.route("/usuarios/<int:id>/certificacoes", methods=["GET"])
def get_certificados_usuario(id):
    s = Session()
    usuario = s.get(Usuario, id)

    if not usuario:
        return jsonify({"mensagem": "Usuário não encontrado!"}), 404

    inscricoes = s.query(Inscricao).filter_by(usuario_id=id).all()
    resultado = []

    for inscricao in inscricoes:
        certificado = s.query(Certificacao).filter_by(
            inscricao_id=inscricao.id
        ).first()

        if certificado:
            evento = s.get(Evento, inscricao.evento_id)
            resultado.append({
                "codigo": certificado.codigo,
                "data_emissao": certificado.data_emissao.isoformat(),
                "evento": evento.nome
            })

    return jsonify(resultado)


# =========================
# INICIAR SERVIDOR
# =========================

if __name__ == "__main__":
    app.run(debug=True)
