"""Forma que debe tener el cuerpo (JSON) de cada solicitud.

Si el cliente manda algo distinto, FastAPI responde 422 antes de tocar la base.
"""
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class Entrada(BaseModel):
    # extra="forbid": un campo que no existe en la tabla también es un 422
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class UsuarioEntrada(Entrada):
    nombre: str = Field(min_length=2, max_length=100, examples=["Ana Torres"])
    email: str = Field(max_length=150, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
                       examples=["ana.torres@foro.com"])


class TemaEntrada(Entrada):
    nombre: str = Field(min_length=2, max_length=100, examples=["JavaScript"])
    descripcion: Optional[str] = Field(default=None, max_length=255)


class EtiquetaEntrada(Entrada):
    nombre: str = Field(min_length=2, max_length=50, examples=["fastapi"])


class PreguntaEntrada(Entrada):
    id_usuario: int = Field(gt=0)
    id_tema: int = Field(gt=0)
    titulo: str = Field(min_length=5, max_length=200)
    contenido: str = Field(min_length=5)
    etiquetas: list[int] = Field(default=[], description="ids de las etiquetas de la pregunta")


class ComentarioEntrada(Entrada):
    id_usuario: int = Field(gt=0)
    id_pregunta: int = Field(gt=0)
    id_comentario_padre: Optional[int] = Field(default=None, gt=0,
                                               description="id del comentario al que responde, o null")
    contenido: str = Field(min_length=2)


class VotoEntrada(Entrada):
    id_usuario: int = Field(gt=0)
    valor: Literal[1, -1] = Field(description="1 a favor, -1 en contra")
