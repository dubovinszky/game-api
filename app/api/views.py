import datetime
from flask import Blueprint, make_response, request, jsonify
from app.models import Catch, Team
from app import db

api = Blueprint('api', __name__)

sql = """
    WITH working_seconds AS (
    SELECT
        work_second
    FROM
        (SELECT
            generate_series(timestamp :from,
                            timestamp :to,
                            '1 second')
        as work_second) t
    WHERE
        extract(isodow from work_second) < 6
        and cast(work_second as time) between time '8:00' and time '23:59'
)

SELECT
    count(*) AS elapsed_hrs
FROM
    working_seconds
WHERE
    work_second BETWEEN :from AND :to
"""


def _make_response(json):
    resp = jsonify(json)
    resp.headers.add_header('Access-Control-Allow-Origin', '*')
    return resp


@api.route('/where', methods=['GET'])
def where():
    now = datetime.datetime.now()
    if now.weekday() > 4 or now.hour < 9 or now.hour >= 16:
        return _make_response({'team_name': None, 'time': None})

    first_catch_date = datetime.datetime(now.year, now.month, now.day, 8, 0)
    current_catch = Catch.query \
        .filter(Catch.currently_held.is_(True)) \
        .filter(Catch.timer_started_at > first_catch_date).first()
    if current_catch:
        team = Team.query.filter_by(id=current_catch.team_id).first()
        catch_time = now - current_catch.timer_started_at
        return _make_response({
            'team_name': team.name,
            'time': str(catch_time).split('.')[0]})
    else:
        alone_time = now - first_catch_date
        return _make_response({
            'team_name': None,
            'time': str(alone_time).split('.')[0]})


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
        .filter(Catch.team_id == team.id) \
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
    # team = Team.query.filter_by(nfc_id=nfc_id).first()
    # catch = Catch.query.filter(Catch.team_id == team.id) \
    #     .filter(Catch.currently_held.is_(True)).first()
    # if catch:
    #     res = db.session.execute(sql, {
    #         'from': catch.timer_started_at,
    #         'to': datetime.datetime.utcnow()})
    #     return str(datetime.timedelta(seconds=res.first()[0] * 60))
    return 'do nothin'


@api.route('/add_team', methods=['POST'])
def add_team():
    """{"nfc_id": nfc_id, "name": name}"""
    team = Team(nfc_id=request.json['nfc_id'], name=request.json['name'])
    team.save()

    return make_response('ok', 200)
