
from flask import request, jsonify

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    func
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from modelos import Base, Usuario


# ==========================================
# MODELO DE SUGESTÕES E RECLAMAÇÕES
# ==========================================

class Sugestao(Base):

    __tablename__ = "sugestoes"

    id = Column(Integer, primary_key=True)

    tipo = Column(String(30), nullable=False)

    categoria = Column(String(100), nullable=False)

    mensagem = Column(String(1000), nullable=False)

    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=True
    )

    criada_em = Column(
        DateTime,
        server_default=func.now()
    )


# ==========================================
# MODELO DE AVALIAÇÕES
# ==========================================

class Avaliacao(Base):

    __tablename__ = "avaliacoes"

    id = Column(Integer, primary_key=True)

    nota = Column(Integer, nullable=False)

    comentario = Column(String(500), nullable=False)

    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False
    )

    evento_id = Column(
        Integer,
        ForeignKey("eventos.id"),
        nullable=False
    )

    criada_em = Column(
        DateTime,
        server_default=func.now()
    )


# ==========================================
# REGISTRO DAS ROTAS
# ==========================================

def registrar_rotas(app, Session):


    # ======================================
    # CADASTRAR USUÁRIO
    # ======================================

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

            existente = s.query(Usuario).filter_by(
                email=email
            ).first()

            if existente:

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

            app.logger.exception("Erro ao cadastrar usuário")

            return jsonify({
                "mensagem": "Erro ao cadastrar usuário."
            }), 500

        finally:

            s.close()


    # ======================================
    # LOGIN
    # ======================================

    @app.route("/login", methods=["POST"])
    def login():

        dados = request.get_json(silent=True) or {}

        email = dados.get("email", "").strip().lower()

        senha = dados.get("senha", "")

        if not email or not senha:

            return jsonify({
                "mensagem": "Informe e-mail e senha!"
            }), 400

        s = Session()

        try:

            usuario = s.query(Usuario).filter_by(
                email=email
            ).first()

            if not usuario:

                return jsonify({
                    "mensagem": "E-mail ou senha incorretos!"
                }), 401

            if not check_password_hash(
                usuario.senha_hash,
                senha
            ):

                return jsonify({
                    "mensagem": "E-mail ou senha incorretos!"
                }), 401

            return jsonify({

                "mensagem": "Login realizado com sucesso!",

                "id": usuario.id,

                "nome": usuario.nome,

                "tipo": usuario.tipo

            })

        finally:

            s.close()


    # ======================================
    # ENVIAR SUGESTÕES E RECLAMAÇÕES
    # ======================================

    @app.route("/sugestoes", methods=["POST"])
    def cadastrar_sugestao():

        dados = request.get_json(silent=True) or {}

        tipo = dados.get("tipo", "").strip()

        categoria = dados.get("categoria", "Geral").strip()

        mensagem = dados.get("mensagem", "").strip()

        usuario_id = dados.get("usuario_id")

        tipos_validos = [

            "Reclamação",

            "Sugestão",

            "Problema técnico",

            "Outro"

        ]

        if tipo not in tipos_validos:

            return jsonify({
                "mensagem": "Tipo de mensagem inválido!"
            }), 400

        if not mensagem:

            return jsonify({
                "mensagem": "Escreva uma mensagem!"
            }), 400

        if len(mensagem) > 1000:

            return jsonify({
                "mensagem": "Mensagem muito grande!"
            }), 400

        s = Session()

        try:

            if usuario_id is not None:

                usuario = s.get(Usuario, usuario_id)

                if not usuario:

                    return jsonify({
                        "mensagem": "Usuário não encontrado!"
                    }), 404

            nova_sugestao = Sugestao(

                tipo=tipo,

                categoria=categoria or "Geral",

                mensagem=mensagem,

                usuario_id=usuario_id

            )

            s.add(nova_sugestao)

            s.commit()

            return jsonify({

                "mensagem": "Mensagem enviada com sucesso!",

                "id": nova_sugestao.id

            }), 201

        except Exception:

            s.rollback()

            app.logger.exception("Erro ao enviar sugestão")

            return jsonify({
                "mensagem": "Erro ao enviar mensagem."
            }), 500

        finally:

            s.close()


    # ======================================
    # LISTAR SUGESTÕES DO USUÁRIO
    # ======================================

    @app.route("/usuarios/<int:id>/sugestoes", methods=["GET"])
    def listar_sugestoes_usuario(id):

        s = Session()

        try:

            usuario = s.get(Usuario, id)

            if not usuario:

                return jsonify({
                    "mensagem": "Usuário não encontrado!"
                }), 404

            sugestoes = s.query(Sugestao).filter_by(
                usuario_id=id
            ).order_by(
                Sugestao.criada_em.desc()
            ).all()

            return jsonify([

                {

                    "id": item.id,

                    "tipo": item.tipo,

                    "categoria": item.categoria,

                    "mensagem": item.mensagem,

                    "criada_em": (
                        item.criada_em.isoformat()
                        if item.criada_em else None
                    )

                }

                for item in sugestoes

            ])

        finally:

            s.close()


    # ======================================
    # AVALIAR EVENTO
    # ======================================

    @app.route("/avaliacoes", methods=["POST"])
    def cadastrar_avaliacao():

        dados = request.get_json(silent=True) or {}

        usuario_id = dados.get("usuario_id")

        evento_id = dados.get("evento_id")

        nota = dados.get("nota")

        comentario = dados.get("comentario", "").strip()

        if not usuario_id or not evento_id or nota is None or not comentario:

            return jsonify({
                "mensagem": "Preencha todos os campos!"
            }), 400

        try:

            nota = int(nota)

        except (ValueError, TypeError):

            return jsonify({
                "mensagem": "Nota inválida!"
            }), 400

        if nota < 1 or nota > 5:

            return jsonify({
                "mensagem": "A nota deve ser de 1 a 5!"
            }), 400

        if len(comentario) > 500:

            return jsonify({
                "mensagem": "Comentário muito grande!"
            }), 400

        s = Session()

        try:

            usuario = s.get(Usuario, usuario_id)

            if not usuario:

                return jsonify({
                    "mensagem": "Usuário não encontrado!"
                }), 404

            from modelos_pedro import Evento

            evento = s.get(Evento, evento_id)

            if not evento:

                return jsonify({
                    "mensagem": "Evento não encontrado!"
                }), 404

            existente = s.query(Avaliacao).filter_by(

                usuario_id=usuario_id,

                evento_id=evento_id

            ).first()

            if existente:

                return jsonify({
                    "mensagem": "Você já avaliou este evento!"
                }), 409

            avaliacao = Avaliacao(

                usuario_id=usuario_id,

                evento_id=evento_id,

                nota=nota,

                comentario=comentario

            )

            s.add(avaliacao)

            s.commit()

            return jsonify({

                "mensagem": "Avaliação enviada com sucesso!",

                "id": avaliacao.id

            }), 201

        except Exception:

            s.rollback()

            app.logger.exception("Erro ao cadastrar avaliação")

            return jsonify({
                "mensagem": "Erro ao cadastrar avaliação."
            }), 500

        finally:

            s.close()
