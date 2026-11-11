
from flask import request, jsonify
from sqlalchemy import Column, Integer, String, DateTime, func
from werkzeug.security import generate_password_hash

# Modelos desenvolvidos por João Pedro
from modelos import Base, Usuario


# =========================
# MODELO DE SUGESTÕES
# =========================

class Sugestao(Base):
    __tablename__ = "sugestoes"

    id = Column(Integer, primary_key=True)
    tipo = Column(String(30), nullable=False)
    categoria = Column(String(100), nullable=False)
    mensagem = Column(String(1000), nullable=False)
    criada_em = Column(DateTime, server_default=func.now())


# =========================
# CADASTRO E SUGESTÕES
# =========================

def registrar_rotas(app, Session):

    # =========================
    # CADASTRAR USUÁRIO
    # =========================

    @app.route("/usuarios", methods=["POST"])
    def cadastrar_usuario():

        dados = request.get_json(silent=True) or {}

        nome = dados.get("nome", "").strip()
        email = dados.get("email", "").strip().lower()
        senha = dados.get("senha", "")

        if not nome or not email or not senha:
            return jsonify({
                "mensagem": "Preencha todos os campos!"
            }), 400

        if len(nome) > 80:
            return jsonify({
                "mensagem": "O nome deve ter no máximo 80 caracteres."
            }), 400

        if len(senha) < 6:
            return jsonify({
                "mensagem": "A senha deve possuir pelo menos 6 caracteres."
            }), 400

        s = Session()

        try:
            usuario_existente = s.query(Usuario).filter_by(
                email=email
            ).first()

            if usuario_existente:
                return jsonify({
                    "mensagem": "Este e-mail já está cadastrado!"
                }), 409

            novo_usuario = Usuario(
                nome=nome,
                email=email,
                senha_hash=generate_password_hash(senha),
                tipo="usuario"
            )

            s.add(novo_usuario)
            s.commit()

            return jsonify({
                "mensagem": "Conta criada com sucesso!",
                "id": novo_usuario.id
            }), 201

        except Exception:
            s.rollback()

            return jsonify({
                "mensagem": "Não foi possível realizar o cadastro."
            }), 500

        finally:
            s.close()


    # =========================
    # ENVIAR SUGESTÃO OU RECLAMAÇÃO
    # =========================

    @app.route("/sugestoes", methods=["POST"])
    def cadastrar_sugestao():

        dados = request.get_json(silent=True) or {}

        tipo = dados.get("tipo", "").strip()
        categoria = dados.get("categoria", "").strip()
        mensagem = dados.get("mensagem", "").strip()

        if not tipo or not categoria or not mensagem:
            return jsonify({
                "mensagem": "Preencha todos os campos!"
            }), 400

        if tipo not in ["Sugestão", "Reclamação"]:
            return jsonify({
                "mensagem": "Tipo de mensagem inválido!"
            }), 400

        if len(mensagem) > 1000:
            return jsonify({
                "mensagem": "A mensagem deve ter no máximo 1000 caracteres."
            }), 400

        s = Session()

        try:
            nova_sugestao = Sugestao(
                tipo=tipo,
                categoria=categoria,
                mensagem=mensagem
            )

            s.add(nova_sugestao)
            s.commit()

            return jsonify({
                "mensagem": "Mensagem enviada com sucesso!",
                "id": nova_sugestao.id
            }), 201

        except Exception:
            s.rollback()

            return jsonify({
                "mensagem": "Não foi possível enviar sua mensagem."
            }), 500

        finally:
            s.close()
