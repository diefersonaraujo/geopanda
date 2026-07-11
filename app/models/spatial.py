from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.orm import declarative_base
from geoalchemy2 import Geometry

Base = declarative_base()


class Regiao(Base):
    __tablename__ = "regioes"
    id = Column(Integer, primary_key=True)
    codigo_ibge = Column(String(2), unique=True)
    nome = Column(String(100))
    geom = Column(Geometry("MULTIPOLYGON", srid=4674))


class Estado(Base):
    __tablename__ = "estados"
    id = Column(Integer, primary_key=True)
    codigo_ibge = Column(String(2), unique=True)
    nome = Column(String(100))
    uf = Column(String(2))
    regiao_codigo = Column(String(2))
    area_km2 = Column(Float)
    geom = Column(Geometry("MULTIPOLYGON", srid=4674))


class Mesorregiao(Base):
    __tablename__ = "mesorregioes"
    id = Column(Integer, primary_key=True)
    codigo_ibge = Column(String(4), unique=True)
    nome = Column(String(200))
    estado_codigo = Column(String(2))
    area_km2 = Column(Float)
    geom = Column(Geometry("MULTIPOLYGON", srid=4674))


class Microrregiao(Base):
    __tablename__ = "microrregioes"
    id = Column(Integer, primary_key=True)
    codigo_ibge = Column(String(5), unique=True)
    nome = Column(String(200))
    mesorregiao_codigo = Column(String(4))
    area_km2 = Column(Float)
    geom = Column(Geometry("MULTIPOLYGON", srid=4674))


class Municipio(Base):
    __tablename__ = "municipios"
    id = Column(Integer, primary_key=True)
    codigo_ibge = Column(String(7), unique=True)
    nome = Column(String(200))
    estado_codigo = Column(String(2))
    mesorregiao_codigo = Column(String(4))
    microrregiao_codigo = Column(String(5))
    area_km2 = Column(Float)
    populacao = Column(Integer)
    ddd = Column(String(2))
    geom = Column(Geometry("MULTIPOLYGON", srid=4674))


class SetorCensitario(Base):
    __tablename__ = "setores_censitarios"
    id = Column(Integer, primary_key=True)
    codigo_ibge = Column(String(15), unique=True)
    municipio_codigo = Column(String(7))
    codigo_estado = Column(String(2))
    nome = Column(Text)
    populacao = Column(Integer)
    domicilios = Column(Integer)
    area_km2 = Column(Float)
    geom = Column(Geometry("POLYGON", srid=4674))
