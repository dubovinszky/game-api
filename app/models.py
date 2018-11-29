from app import db
import datetime


class Team(db.Model):
    __tablename__ = "team"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nfc_id = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, nfc_id, name):
        self.nfc_id = nfc_id
        self.name = name

    def save(self):
        db.session.add(self)
        db.session.commit()


class Catch(db.Model):
    __tablename__ = "catch"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    catched_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    currently_held = db.Column(db.Boolean())
    timer_started_at = db.Column(db.DateTime)

    def __init__(self, team_id, currently_held=True):
        self.team_id = team_id
        self.currently_held = currently_held

    def save(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def update(cls, _id, **kwargs):
        catch = Catch.query.filter_by(id=_id).first()

        for k, v in kwargs.items():
            setattr(catch, k, v)
        db.session.commit()
        return catch
