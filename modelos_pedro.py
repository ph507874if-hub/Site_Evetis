
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Date, Boolean
)
from sqlalchemy.orm import relationship

# Aproveita as classes já desenvolvidas por João Pedro
from modelos import Base, Usuario, Admin


class Evento(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(String(300))
    data = Column(Date, nullable=False)
    local = Column(String(150), nullable=False)

    # Um administrador pode cadastrar vários eventos
    admin_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False
    )
    admin = relationship("Admin")

    # Um evento pode possuir várias inscrições
    inscricoes = relationship(
        "Inscricao",
        back_populates="evento"
    )


class Inscricao(Base):
    __tablename__ = "inscricoes"

    id = Column(Integer, primary_key=True)
    data_inscricao = Column(Date, nullable=False)
    presente = Column(Boolean, nullable=False, default=False)

    # Cada inscrição pertence a um usuário
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False
    )
    usuario = relationship("Usuario")

    # Cada inscrição está ligada a um evento
    evento_id = Column(
        Integer,
        ForeignKey("eventos.id"),
        nullable=False
    )
    evento = relationship(
        "Evento",
        back_populates="inscricoes"
    )

    # Uma inscrição pode ter um certificado
    certificacao = relationship(
        "Certificacao",
        back_populates="inscricao",
        uselist=False
    )


class Certificacao(Base):
    __tablename__ = "certificacoes"

    id = Column(Integer, primary_key=True)
    codigo = Column(
        String(50),
        unique=True,
        nullable=False
    )
    data_emissao = Column(Date, nullable=False)

    # O certificado pertence a uma inscrição
    inscricao_id = Column(
        Integer,
        ForeignKey("inscricoes.id"),
        unique=True,
        nullable=False
    )
    inscricao = relationship(
        "Inscricao",
        back_populates="certificacao"
    )
