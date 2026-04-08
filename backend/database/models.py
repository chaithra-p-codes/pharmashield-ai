from .db import db

class Interaction(db.Model):
    __tablename__ = 'interactions'

    id             = db.Column(db.Integer, primary_key=True)
    drug1          = db.Column(db.String(100), nullable=False)
    drug2          = db.Column(db.String(100), nullable=False)
    severity       = db.Column(db.String(20),  nullable=False)
    effect         = db.Column(db.Text,        nullable=False)
    recommendation = db.Column(db.Text,        nullable=False)

    def to_dict(self):
        return {
            "drug1":          self.drug1,
            "drug2":          self.drug2,
            "severity":       self.severity,
            "effect":         self.effect,
            "recommendation": self.recommendation
        }


class Medicine(db.Model):
    __tablename__ = 'medicines'

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def to_dict(self):
        return {"name": self.name}


class SideEffect(db.Model):
    __tablename__ = 'side_effects'

    id       = db.Column(db.Integer, primary_key=True)
    medicine = db.Column(db.String(100), nullable=False)
    effect   = db.Column(db.String(200), nullable=False)


class Alternative(db.Model):
    __tablename__ = 'alternatives'

    id          = db.Column(db.Integer, primary_key=True)
    medicine    = db.Column(db.String(100), nullable=False)
    alternative = db.Column(db.String(100), nullable=False)
