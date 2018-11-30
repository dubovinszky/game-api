import datetime
from flask import Blueprint, make_response, request, jsonify
from app.models import Catch, Team
from app import db

api = Blueprint('api', __name__)

sql = """
    WITH working_minutes AS (
    SELECT
        work_minute
    FROM
        (SELECT
            generate_series(timestamp :from,
                            timestamp :to,
                            '1 minute')
        as work_minute) t
    WHERE
        extract(isodow from work_minute) < 6
        and cast(work_minute as time) between time '10:00' and time '23:59'
)

SELECT
    count(*) AS elapsed_hrs
FROM
    working_minutes
WHERE
    work_minute BETWEEN :from AND :to
"""


@api.route('/where', methods=['GET'])
def where():
    current_catch = Catch.query.filter_by(currently_held=True).first()
    if current_catch:
        team = Team.query.filter_by(id=current_catch.team_id).first()
        import random
        return jsonify({'team_name': team.name,
                        'time': str(datetime.timedelta(
                            seconds=random.randint(1, 86400)))})
    else:
        return make_response('***no one has it***', 200)


@api.route('/catch/<nfc_id>', methods=['GET'])
def catch(nfc_id):
    team = Team.query.filter_by(nfc_id=nfc_id).first()
    all_catches = Catch.query.count()
    can_recatch = Catch.query \
        .filter(Catch.currently_held.is_(True)) \
        .filter(Catch.timer_started_at.isnot(None)) \
        .filter(Catch.team_id != team.id) \
        .count()
    can_skip = Catch.query \
        .filter(Catch.currently_held.is_(True)) \
        .filter(Catch.timer_started_at.is_(None)) \
        .filter(Catch.team_id != team.id) \
        .count()
    if all_catches == 0:
        catch = Catch(team_id=team.id, currently_held=True)
        catch.save()
        return 'true'
    elif can_recatch > 0:
        currently_held_by = Catch.query \
            .filter(Catch.currently_held.is_(True)).first()
        Catch.update(currently_held_by.id, currently_held=False)
        catch = Catch(team_id=team.id, currently_held=True)
        catch.save()
        return 'true'
    elif can_skip > 0:
        return 'true'
    else:
        return 'false'


@api.route('/start_timer/<nfc_id>', methods=['GET'])
def start_timer(nfc_id):
    team = Team.query.filter_by(nfc_id=nfc_id).first()
    start_timer = Catch.query.filter_by(
        team_id=team.id,
        currently_held=True,
        timer_started_at=None)
    if start_timer.count() == 1:
        Catch.update(start_timer.first().id,
                     timer_started_at=datetime.datetime.utcnow())
    else:
        return 'false'
    return 'true'


@api.route('/heartbeat/<nfc_id>', methods=['GET'])
def heartbeat(nfc_id):
    team = Team.query.filter_by(nfc_id=nfc_id).first()
    catch = Catch.query.filter(Catch.team_id == team.id) \
        .filter(Catch.currently_held.is_(True)) \
        .filter(Catch.timer_started_at.isnot(None)).first()
    if catch:
        res = db.session.execute(sql, {
            'from': catch.timer_started_at,
            'to': datetime.datetime.utcnow()})
        return str(datetime.timedelta(seconds=res.first()[0] * 60))
    return 'do nothin'


@api.route('/add_team', methods=['POST'])
def add_team():
    """{"nfc_id": nfc_id, "name": name}"""
    team = Team(nfc_id=request.json['nfc_id'], name=request.json['name'])
    team.save()

    return make_response('ok', 200)
