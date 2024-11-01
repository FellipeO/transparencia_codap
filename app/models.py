from . import db

class Lancamento(db.Model):
    __tablename__ = 'lancamentos'

    nCodLanc = db.Column(db.BigInteger, primary_key=True)
    nCodCC = db.Column(db.BigInteger)
    cObs = db.Column(db.String(255))
    nValorLanc = db.Column(db.Float)
    dDtLanc = db.Column(db.DateTime)
    cNatureza = db.Column(db.String(1))

    def __repr__(self):
        return f'<Lancamento {self.nCodLanc}>'


class GrupoUsuario(db.Model):
    __tablename__ = 'grupos_usuarios'
    
    email = db.Column(db.String(255), primary_key=True)
    grupo = db.Column(db.Enum('super_admin', 'admin', 'usuario'))

    def __repr__(self):
        return f'<GrupoUsuario {self.email}, {self.grupo}>'
    
class EstatutoSocial(db.Model):
    __tablename__ = 'estatuto_social'
    versao = db.Column(db.Integer, primary_key=True)
    vigencia_inicio = db.Column(db.Date)
    vigencia_fim = db.Column(db.Date)
    status = db.Column(db.Enum('aprovado', 'registrado'))
    texto = db.Column(db.Text)

    def __repr__(self):
        return f'<EstatutoSocial Versão {self.versao}>'