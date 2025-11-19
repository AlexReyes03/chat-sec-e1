from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    nombre_google = Column(String(255), nullable=True)
    apodo = Column(String(50), nullable=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow, nullable=False)
    foto_perfil_url = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Usuario(id={self.id}, email='{self.email}', apodo='{self.apodo}')>"

    def to_dict(self):
        """
        Convierte el modelo a diccionario
        """
        return {
            'id': self.id,
            'email': self.email,
            'google_id': self.google_id,
            'nombre_google': self.nombre_google,
            'apodo': self.apodo,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'foto_perfil_url': self.foto_perfil_url
        }
