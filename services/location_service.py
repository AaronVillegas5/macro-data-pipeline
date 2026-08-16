from db.models import Location


def get_or_create_location(db, name, country, region, lat, lon):
    location = db.query(Location).filter(Location.latitude == lat, Location.longitude == lon).first()
    # If already exists
    if location:
        return location

    location = Location(name=name, country=country, region=region, latitude=lat, longitude=lon)

    db.add(location)
    db.commit()
    db.refresh(location)

    return location
