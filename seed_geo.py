from app import create_app
from models import db, Country, Governorates, Directorate

app = create_app()

def seed_data():
    with app.app_context():
        # Insert Country: Yemen
        yemen = Country.query.filter_by(Country_Name="اليمن").first()
        if not yemen:
            yemen = Country(Country_Name="اليمن")
            db.session.add(yemen)
            db.session.commit()
            
        # Governorates of Yemen
        govs = ["أمانة العاصمة", "صنعاء", "عدن", "تعز", "الحديدة", "إب", "حضرموت"]
        for g in govs:
            gov = Governorates.query.filter_by(G_Name=g, CountryID=yemen.CountryID).first()
            if not gov:
                gov = Governorates(G_Name=g, CountryID=yemen.CountryID)
                db.session.add(gov)
        db.session.commit()

        # Add some directorates for Sanaa (أمانة العاصمة)
        sanaa = Governorates.query.filter_by(G_Name="أمانة العاصمة").first()
        if sanaa:
            dirs = ["السبعين", "الوحدة", "الصافية", "التحرير", "الثورة", "شعوب", "معين", "بني الحارث"]
            for d in dirs:
                dir_obj = Directorate.query.filter_by(Disc_Name=d, G_ID=sanaa.G_ID).first()
                if not dir_obj:
                    db.session.add(Directorate(Disc_Name=d, G_ID=sanaa.G_ID))
            db.session.commit()
            
        print("Data seeded successfully!")

if __name__ == '__main__':
    seed_data()
