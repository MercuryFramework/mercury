from .MigrationGenerator import MigrationWrapper
from .connection import connection
from sqlalchemy.ext.declarative import declarative_base
from libmercury.db import Column, Integer

b = declarative_base()
class mercury_version(b):
	__tablename__ = "mercury_version"
	id = Column(Integer(), primary_key=True)
	version = Column(Integer())

def create_mercury_table(url):
	wrapper = MigrationWrapper(url)
	wrapper.create_table("mercury_version", [
		Column("id", Integer, primary_key=True),
		Column("version", Integer)
	])

def find_mercury_table(url):
	conn = connection(url)
	base = declarative_base()
	base.metadata.reflect(conn.Engine)
	table = base.metadata.tables.get("mercury_version")
	return table

def get_version(url):
	conn = connection(url)
	m = conn.Session.query(mercury_version).first()
	return m.version

def create_version(url, version):
	conn = connection(url)
	m = mercury_version(version=version)
	conn.Session.add(m)
	conn.Session.commit()

def update_version(url, version):
	conn = connection(url)
	m = conn.Session.query(mercury_version).first()
	m.version = version 
	conn.Session.add(m)
	conn.Session.commit()
