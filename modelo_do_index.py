
from flask import request, jsonify

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Usuario(Base):

    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    nome = Column(String(80), nullable=False)
    email = Column(String(254), nullable=False, unique=True, index=True)
    senha_hash = Column(String(255), nullable=False)
    tipo = Column(String(20), nullable=False, default="usuario")

class Evento(Base):

    __tablename__ = "eventos"
    id = Column(Integer, primary_key=True)
    nome = Column(String(80), nullable=False)
    categoria = Column(String(50), nullable=False, default="Outros")
    descricao = Column(String(500), nullable=False)
    data = Column(Date, nullable=False)
    local = Column(String(100), nullable=False)
    admin_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False
    )

class Inscricao(Base):

    __tablename__ = "inscricoes"
    __table_args__ = (
        UniqueConstraint("usuario_id", "evento_id"),
    )
    id = Column(Integer, primary_key=True)
    data_inscricao = Column(Date, nullable=False)
    presente = Column(Boolean, nullable=False, default=False)

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

class Certificacao(Base):

    __tablename__ = "certificacoes"
    id = Column(Integer, primary_key=True)
    codigo = Column(String(50), unique=True, nullable=False)
    data_emissao = Column(Date, nullable=False)

    inscricao_id = Column(
        Integer,
        ForeignKey("inscricoes.id"),
        unique=True,
        nullable=False
    )

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


def registrar_rotas(app, Session):

    @app.route("/usuarios", methods=["POST"])
    def cadastrar_usuario():
        return jsonify({
            "mensagem": (
                "Cadastro temporariamente indisponível enquanto "
                "o MySQL é configurado."
            )
        }), 503

    @app.route("/login", methods=["POST"])
    def login():
        return jsonify({
            "mensagem": (
                "Login temporariamente indisponível enquanto "
                "o MySQL é configurado."
            )
        }), 503

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
