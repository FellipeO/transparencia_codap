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
