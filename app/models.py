from . import db
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

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

class Evento(db.Model):
    __tablename__ = 'eventos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False)
    data = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    estado = db.Column(db.String(100), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    endereco = db.Column(db.String(255), nullable=False)
    email_organizador = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

class EventoArquivo(db.Model):
    __tablename__ = 'eventos_arquivos'

    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, db.ForeignKey('eventos.id'), nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento com o evento
    evento = db.relationship('Evento', backref=db.backref('arquivos', cascade="all, delete-orphan"))

class Pessoas(db.Model):
    __tablename__ = 'pessoas'

    email = db.Column(db.String(255), primary_key=True, nullable=False)
    nome = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String, unique=True, nullable=False)
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
    hash_foto = db.Column(db.String(255), nullable=True)

    cargos = db.relationship('PessoaCargo', backref='pessoa', cascade="all, delete-orphan")
    lotacoes = db.relationship('PessoaLotacao', backref='pessoa', cascade="all, delete-orphan")

class Timeline(db.Model):
    __tablename__ = 'timeline'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), db.ForeignKey('pessoas.email'), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    tipo = db.Column(db.String(50), nullable=False)  # Ex: 'contracheque', 'reuniao'
    referencia_id = db.Column(db.Integer, db.ForeignKey('contracheques.id'), nullable=False)

    pessoa = db.relationship('Pessoas', backref='timeline')

class Contracheque(db.Model):
    __tablename__ = 'contracheques'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mes_ano = db.Column(db.String(7), nullable=False)  # Formato MM/AAAA
    email = db.Column(db.String(255), db.ForeignKey('pessoas.email'), nullable=False)
    salario_bruto = db.Column(db.Float, nullable=False)
    inss = db.Column(db.Float, nullable=False)
    imposto_renda = db.Column(db.Float, nullable=False)
    gratificacao = db.Column(db.Float, nullable=False)

    pessoa = db.relationship('Pessoas', backref='contracheques')
    timeline_entries = db.relationship(
        'Timeline', 
        cascade="all, delete-orphan", 
        backref='contracheque'
    )
    
class PessoaCargo(db.Model):
    __tablename__ = 'pessoa_cargos'

    id = db.Column(db.Integer, primary_key=True)
    pessoa_email = db.Column(db.String(255), db.ForeignKey('pessoas.email'), nullable=False)
    cargo = db.Column(db.String(100), nullable=False)

class PessoaLotacao(db.Model):
    __tablename__ = 'pessoa_lotacoes'

    id = db.Column(db.Integer, primary_key=True)
    pessoa_email = db.Column(db.String(255), db.ForeignKey('pessoas.email'), nullable=False)
    lotacao = db.Column(db.String(100), nullable=False)

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
    
class RegimentoInterno(db.Model):
    __tablename__ = 'regimento_interno'
    versao = db.Column(db.Integer, primary_key=True)
    vigencia_inicio = db.Column(db.Date)
    vigencia_fim = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum('aprovado', 'registrado'))
    texto = db.Column(db.Text)
    hash = db.Column(db.String(64))

    def __repr__(self):
        return f'<RegimentoInterno Versão {self.versao}>'