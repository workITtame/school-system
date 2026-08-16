from .extensions import db

class Country(db.Model):
    __tablename__ = 'country'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    CountryID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Country_Name = db.Column(db.String(100))
    
    governorates = db.relationship('Governorates', back_populates='country', lazy=True)

class Governorates(db.Model):
    __tablename__ = 'governorates'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    G_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    G_Name = db.Column(db.String(100))
    CountryID = db.Column(db.Integer, db.ForeignKey('country.CountryID', ondelete='RESTRICT'))
    
    country = db.relationship('Country', back_populates='governorates')
    directorates = db.relationship('Directorate', back_populates='governorate', lazy=True)

class Directorate(db.Model):
    __tablename__ = 'directorate'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    DiscID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Disc_Name = db.Column(db.String(100))
    G_ID = db.Column(db.Integer, db.ForeignKey('governorates.G_ID', ondelete='RESTRICT'))
    
    governorate = db.relationship('Governorates', back_populates='directorates')
