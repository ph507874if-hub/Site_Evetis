
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
from uuid import uuid4

# =========================
# IMPORTAÇÃO DOS MODELOS
# =========================

# Modelos desenvolvidos por João Pedro
from modelos import Base, Usuario, Admin

# Modelos de eventos, inscrições e certificações
from modelos_pedro import Evento, Inscricao, Certificacao

# Modelos de sugestões, avaliações e rotas de cadastro
from modelos_cadastro_sugestoes import (
    Sugestao,
    Avaliacao,
    registrar_rotas
)


# =========================
# CONFIGURAÇÃO DO FLASK
# =========================

app = Flask(__name__)
CORS(app)


# =========================
# BANCO DE DADOS
# =========================

engine = create_engine("sqlite:///database.db")
Session = sessionmaker(bind=engine)

# Cria as tabelas de todos os modelos importados
Base.metadata.create_all(engine)

# Registra as rotas de cadastro, login,
# sugestões, reclamações e avaliações
registrar_rotas(app, Session)


# =========================
# ROTA INICIAL
# =========================

@app.route("/")
def index():
    return jsonify({
        "mensagem": "API do Sistema de Eventos funcionando!"
    })


# =========================
# EVENTOS
# =========================

# LISTAR TODOS OS EVENTOS
@app.route("/eventos", methods=["GET"])
def get_eventos():
    s = Session()

    try:
        eventos = s.query(Evento).order_by(Evento.data).all()

        return jsonify([
            {
                "id": e.id,
                "nome": e.nome,
                "categoria": getattr(e, "categoria", "Outros"),
                "descricao": e.descricao,
                "data": e.data.isoformat(),
                "local": e.local,
                "admin_id": e.admin_id
            }
            for e in eventos
        ])

    finally:
        s.close()


# BUSCAR UM EVENTO PELO ID
@app.route("/eventos/<int:id>", methods=["GET"])
def get_evento_unico(id):
    s = Session()

    try:
        evento = s.get(Evento, id)

        if not evento:
            return jsonify({
                "mensagem": "Evento não encontrado!"
            }), 404

        return jsonify({
            "id": evento.id,
            "nome": evento.nome,
            "categoria": getattr(evento, "categoria", "Outros"),
            "descricao": evento.descricao,
            "data": evento.data.isoformat(),
            "local": evento.local,
            "admin_id": evento.admin_id
        })

    finally:
        s.close()


# CADASTRAR EVENTO
@app.route("/eventos", methods=["POST"])
def add_evento():
    s = Session()

    try:
        dados = request.get_json(silent=True)

        if not dados:
            return jsonify({
                "mensagem": "Envie os dados do evento!"
            }), 400

        campos = ["nome", "data", "local", "admin_id"]

        if any(
            campo not in dados or dados[campo] in (None, "")
            for campo in campos
        ):
            return jsonify({
                "mensagem": "Informe nome, data, local e admin_id."
            }), 400

        administrador = s.get(Admin, dados["admin_id"])

        if not administrador:
            return jsonify({
                "mensagem": "Administrador não encontrado!"
            }), 404

        try:
            data_evento = date.fromisoformat(dados["data"])

        except (ValueError, TypeError):
            return jsonify({
                "mensagem": "Data inválida! Use o formato AAAA-MM-DD."
            }), 400

        evento = Evento(
            nome=dados["nome"],
            descricao=dados.get("descricao", ""),
            data=data_evento,
            local=dados["local"],
            admin_id=administrador.id
        )

        # Salva a categoria se o modelo possuir esse campo
        if hasattr(Evento, "categoria"):
            evento.categoria = dados.get("categoria", "Outros")

        s.add(evento)
        s.commit()

        return jsonify({
            "mensagem": "Evento cadastrado com sucesso!",
            "id": evento.id
        }), 201

    except Exception as erro:
        s.rollback()
        print("Erro ao cadastrar evento:", erro)

        return jsonify({
            "mensagem": "Erro ao cadastrar evento."
        }), 500

    finally:
        s.close()


# ATUALIZAR EVENTO
@app.route("/eventos/<int:id>", methods=["PUT"])
def atualizar_evento(id):
    s = Session()

    try:
        evento = s.get(Evento, id)

        if not evento:
            return jsonify({
                "mensagem": "Evento não encontrado!"
            }), 404

        dados = request.get_json(silent=True)

        if not dados:
            return jsonify({
                "mensagem": "Envie os dados do evento!"
            }), 400

        if "nome" in dados:
            evento.nome = dados["nome"]

        if "descricao" in dados:
            evento.descricao = dados["descricao"]

        if "local" in dados:
            evento.local = dados["local"]

        if "categoria" in dados and hasattr(Evento, "categoria"):
            evento.categoria = dados["categoria"]

        if "data" in dados:
            try:
                evento.data = date.fromisoformat(dados["data"])

            except (ValueError, TypeError):
                return jsonify({
                    "mensagem": "Data inválida! Use AAAA-MM-DD."
                }), 400

        if "admin_id" in dados:
            administrador = s.get(Admin, dados["admin_id"])

            if not administrador:
                return jsonify({
                    "mensagem": "Administrador não encontrado!"
                }), 404

            evento.admin_id = administrador.id

        s.commit()

        return jsonify({
            "mensagem": "Evento atualizado com sucesso!"
        })

    except Exception as erro:
        s.rollback()
        print("Erro ao atualizar evento:", erro)

        return jsonify({
            "mensagem": "Erro ao atualizar evento."
        }), 500

    finally:
        s.close()


# DELETAR EVENTO
@app.route("/eventos/<int:id>", methods=["DELETE"])
def deletar_evento(id):
    s = Session()

    try:
        evento = s.get(Evento, id)

        if not evento:
            return jsonify({
                "mensagem": "Evento não encontrado!"
            }), 404

        inscricao = s.query(Inscricao).filter_by(
            evento_id=id
        ).first()

        if inscricao:
            return jsonify({
                "mensagem": "Não é possível excluir um evento que possui inscrições."
            }), 409

        s.delete(evento)
        s.commit()

        return jsonify({
            "mensagem": "Evento deletado com sucesso!"
        })

    except Exception as erro:
        s.rollback()
        print("Erro ao deletar evento:", erro)

        return jsonify({
            "mensagem": "Erro ao deletar evento."
        }), 500

    finally:
        s.close()


# =========================
# INSCRIÇÕES
# =========================

# LISTAR TODAS AS INSCRIÇÕES
@app.route("/inscricoes", methods=["GET"])
def get_inscricoes():
    s = Session()

    try:
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

    finally:
        s.close()


# BUSCAR UMA INSCRIÇÃO PELO ID
@app.route("/inscricoes/<int:id>", methods=["GET"])
def get_inscricao_unica(id):
    s = Session()

    try:
        inscricao = s.get(Inscricao, id)

        if not inscricao:
            return jsonify({
                "mensagem": "Inscrição não encontrada!"
            }), 404

        return jsonify({
            "id": inscricao.id,
            "usuario_id": inscricao.usuario_id,
            "evento_id": inscricao.evento_id,
            "data_inscricao": inscricao.data_inscricao.isoformat(),
            "presente": inscricao.presente
        })

    finally:
        s.close()


# REALIZAR INSCRIÇÃO
@app.route("/inscricoes", methods=["POST"])
def add_inscricao():
    s = Session()

    try:
        dados = request.get_json(silent=True)

        if (
            not dados
            or "usuario_id" not in dados
            or "evento_id" not in dados
        ):
            return jsonify({
                "mensagem": "Informe usuario_id e evento_id."
            }), 400

        usuario = s.get(Usuario, dados["usuario_id"])

        if not usuario:
            return jsonify({
                "mensagem": "Usuário não encontrado!"
            }), 404

        evento = s.get(Evento, dados["evento_id"])

        if not evento:
            return jsonify({
                "mensagem": "Evento não encontrado!"
            }), 404

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

    except Exception as erro:
        s.rollback()
        print("Erro ao realizar inscrição:", erro)

        return jsonify({
            "mensagem": "Erro ao realizar inscrição."
        }), 500

    finally:
        s.close()


# =========================
# CONFIRMAR PRESENÇA
# =========================

@app.route("/inscricoes/<int:id>/presenca", methods=["PUT"])
def confirmar_presenca(id):
    s = Session()

    try:
        inscricao = s.get(Inscricao, id)

        if not inscricao:
            return jsonify({
                "mensagem": "Inscrição não encontrada!"
            }), 404

        dados = request.get_json(silent=True) or {}

        if dados.get("presente") is not True:
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

    except Exception as erro:
        s.rollback()
        print("Erro ao confirmar presença:", erro)

        return jsonify({
            "mensagem": "Erro ao confirmar presença."
        }), 500

    finally:
        s.close()


# =========================
# CERTIFICADOS
# =========================

# LISTAR TODOS OS CERTIFICADOS
@app.route("/certificacoes", methods=["GET"])
def get_certificacoes():
    s = Session()

    try:
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

    finally:
        s.close()


# BUSCAR CERTIFICADO PELO CÓDIGO
@app.route("/certificacoes/<string:codigo>", methods=["GET"])
def get_certificado_unico(codigo):
    s = Session()

    try:
        certificado = s.query(Certificacao).filter_by(
            codigo=codigo.upper()
        ).first()

        if not certificado:
            return jsonify({
                "mensagem": "Certificado não encontrado!"
            }), 404

        inscricao = s.get(Inscricao, certificado.inscricao_id)

        if not inscricao:
            return jsonify({
                "mensagem": "Inscrição do certificado não encontrada!"
            }), 404

        evento = s.get(Evento, inscricao.evento_id)
        usuario = s.get(Usuario, inscricao.usuario_id)

        if not evento or not usuario:
            return jsonify({
                "mensagem": "Dados do certificado incompletos!"
            }), 404

        return jsonify({
            "id": certificado.id,
            "codigo": certificado.codigo,
            "data_emissao": certificado.data_emissao.isoformat(),
            "usuario": usuario.nome,
            "evento": evento.nome,
            "data_evento": evento.data.isoformat(),
            "inscricao_id": inscricao.id
        })

    finally:
        s.close()


# EMITIR CERTIFICADOS
@app.route("/certificacoes/emitir", methods=["POST"])
def emitir_certificados():
    s = Session()

    try:
        inscricoes = s.query(Inscricao).all()
        emitidos = []

        for inscricao in inscricoes:
            evento = s.get(Evento, inscricao.evento_id)

            # Só emite se o evento terminou e a presença foi confirmada
            if (
                not evento
                or evento.data >= date.today()
                or not inscricao.presente
            ):
                continue

            # Evita emitir mais de um certificado por inscrição
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

    except Exception as erro:
        s.rollback()
        print("Erro ao emitir certificados:", erro)

        return jsonify({
            "mensagem": "Erro ao emitir certificados."
        }), 500

    finally:
        s.close()


# LISTAR CERTIFICADOS DE UM USUÁRIO
@app.route("/usuarios/<int:id>/certificacoes", methods=["GET"])
def get_certificados_usuario(id):
    s = Session()

    try:
        usuario = s.get(Usuario, id)

        if not usuario:
            return jsonify({
                "mensagem": "Usuário não encontrado!"
            }), 404

        inscricoes = s.query(Inscricao).filter_by(
            usuario_id=id
        ).all()

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
                    "evento": evento.nome if evento else "Evento não encontrado"
                })

        return jsonify(resultado)

    finally:
        s.close()


# =========================
# INICIAR SERVIDOR
# =========================

if __name__ == "__main__":
    app.run(debug=True)
