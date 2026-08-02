from .extensions import db

class Country(db.Model):
    __tablename__ = 'Country'
    CountryID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Country_Name = db.Column(db.String(100))
    
    governorates = db.relationship('Governorates', back_populates='country', cascade='all, delete-orphan')

class Governorates(db.Model):
    __tablename__ = 'Governorates'
    G_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    G_Name = db.Column(db.String(100))
    CountryID = db.Column(db.Integer, db.ForeignKey('Country.CountryID'))
    
    country = db.relationship('Country', back_populates='governorates')
    directorates = db.relationship('Directorate', back_populates='governorate', cascade='all, delete-orphan')

class Directorate(db.Model):
    __tablename__ = 'Directorate'
    DiscID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Disc_Name = db.Column(db.String(100))
    G_ID = db.Column(db.Integer, db.ForeignKey('Governorates.G_ID'))
    
    governorate = db.relationship('Governorates', back_populates='directorates')
