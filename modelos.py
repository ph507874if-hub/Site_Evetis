from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    idade = Column(Integer)
    tipo = Column(String(20), nullable=False, default="usuario")

    __mapper_args__ = {
        "polymorphic_on": tipo,
        "polymorphic_identity": "usuario"
    }


class Admin(Usuario):
    __mapper_args__ = {
        "polymorphic_identity": "admin"
    }


usuario = Usuario(
    nome="João",
    email="joao@email.com",
    idade=25,

)

admin = Admin(
    nome="Maria",
    email="maria@email.com",
    idade=30,

)