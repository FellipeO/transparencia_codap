from . import db
from sqlalchemy.orm import relationship

class Lancamento(db.Model):
    __tablename__ = 'lancamentos'

    nCodLanc = db.Column(db.BigInteger, primary_key=True)
    nCodCC = db.Column(db.BigInteger)
    cObs = db.Column(db.String(255))
    nValorLanc = db.Column(db.Float)
    dDtLanc = db.Column(db.DateTime)
    cNatureza = db.Column(db.String(1))
    nCodCliente = db.Column(db.BigInteger, db.ForeignKey('clientes.codigo_cliente_omie'))
    nCodCCDestino = db.Column(db.BigInteger, nullable=True)

    cliente = relationship('Clientes', backref='lancamentos')

    def __repr__(self):
        return f'<Lancamento {self.nCodLanc}>'

class Pessoas(db.Model):
    __tablename__ = 'pessoas'

    email = db.Column(db.String(255), primary_key=True, nullable=False)
    nome = db.Column(db.String(255), nullable=False)
    cargo = db.Column(db.String(100), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(50), nullable=False)
    data_admissao = db.Column(db.Date, nullable=False)
    aniversario = db.Column(db.Date, nullable=False)
    genero = db.Column(db.String(50), nullable=False)
    etnia = db.Column(db.String(50), nullable=False)
    linkedin = db.Column(db.String(255))
    instagram = db.Column(db.String(255))
    twitter = db.Column(db.String(255))
    frase = db.Column(db.String(255))
    
class Clientes(db.Model):
    __tablename__='clientes'

    codigo_cliente_omie = db.Column(db.BigInteger, primary_key=True)
    nome_fantasia = db.Column(db.String(255))
    razao_social = db.Column(db.String(255))
    cnpj_cpf = db.Column(db.String(20))

class GrupoUsuario(db.Model):
    __tablename__ = 'grupos_usuarios'
    
    email = db.Column(db.String(255), primary_key=True)
    grupo = db.Column(db.Enum('super_admin', 'diretor', 'assessor'))

    def __repr__(self):
        return f'<GrupoUsuario {self.email}, {self.grupo}>'
    
class EstatutoSocial(db.Model):
    __tablename__ = 'estatuto_social'
    versao = db.Column(db.Integer, primary_key=True)
    vigencia_inicio = db.Column(db.Date)
    vigencia_fim = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum('aprovado', 'registrado'))
    texto = db.Column(db.Text)
    hash = db.Column(db.String(64))

    def __repr__(self):
        return f'<EstatutoSocial Versão {self.versao}>'
    
class AquisicoesAlienacoes(db.Model):
    __tablename__ = 'aquisicoes_alienacoes'
    versao = db.Column(db.Integer, primary_key=True)
    vigencia_inicio = db.Column(db.Date)
    vigencia_fim = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum('aprovado', 'registrado'))
    texto = db.Column(db.Text)
    hash = db.Column(db.String(64))

    def __repr__(self):
        return f'<AquisicoesAlienacoes Versão {self.versao}>'
    
class OportunidadesInvestimento(db.Model):
    __tablename__ = 'oportunidades_investimento'
    versao = db.Column(db.Integer, primary_key=True)
    vigencia_inicio = db.Column(db.Date)
    vigencia_fim = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum('aprovado', 'registrado'))
    texto = db.Column(db.Text)
    hash = db.Column(db.String(64))

    def __repr__(self):
        return f'<OportunidadesInvestimento Versão {self.versao}>'