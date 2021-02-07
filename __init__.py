from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from sqlalchemy.sql import desc
from flask import Flask, jsonify
from datetime import timedelta
from flask import Response
import json
from cryptography.fernet import Fernet

import os
root_path = os.path.dirname(os.path.realpath(__file__))

class Cryptography:
    def __init__(self, public_key):
        self.public_key = public_key

    def decrypt_pubkey(self):
        try:
            with open(f"/{os.path.dirname(os.path.realpath(__file__))}/WPK.key") as key:
                private_key = Fernet(key.readline().encode('utf-8'))
                string = private_key.decrypt(self.public_key.encode("utf-8"))
                return string.decode("utf-8")
        except Exception as decrypt_error:
            return decrypt_error

app = Flask(__name__)
with open(f"/{os.path.dirname(os.path.realpath(__file__))}/config.json") as config:
    config = json.load(config)

sql_server = Cryptography(config['sql-connection'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = sql_server.decrypt_pubkey()

db = SQLAlchemy(app)

# transaction SQL table
class transaction_audit(db.Model):
    txid            = db.Column(db.String(125), primary_key=True)
    transacted      = db.Column(db.String(125), unique=False)
    total_workers   = db.Column(db.String(125), unique=False)
    timestamp       = db.Column(db.String(125), unique=False)

class fath_team_stats(db.Model):
    wus             = db.Column(db.String(125), primary_key=True)
    rank            = db.Column(db.String(125), unique=False)
    active_50       = db.Column(db.String(125), unique=False)
    lastupdate      = db.Column(db.String(125), unique=False)

class fath_team_stats_detailed(db.Model):
    rank                 = db.Column(db.String(125), primary_key=True)
    active_users         = db.Column(db.String(125), unique=False)
    total_users          = db.Column(db.String(125), unique=False)
    change_rank_24hr     = db.Column(db.String(125), unique=False)
    points_24hr_avg      = db.Column(db.String(125), unique=False)
    points_last_24hr     = db.Column(db.String(125), unique=False)
    points_update        = db.Column(db.String(125), unique=False)
    points_today         = db.Column(db.String(125), unique=False)
    points_week          = db.Column(db.String(125), unique=False)
    timestamp            = db.Column(db.String(125), unique=False)

@app.route('/')
def index():
    team_stats = fath_team_stats.query.order_by(fath_team_stats.lastupdate.desc()).first()
    team_stats_detailed = fath_team_stats_detailed.query.order_by(fath_team_stats_detailed.timestamp.desc()).first()

    # Team stats (used to calculate the different between the last
    stats = fath_team_stats.query.with_entities(
            fath_team_stats.lastupdate.distinct().label("lastupdate"),  # 0
            fath_team_stats.wus,                                        # 1
            fath_team_stats.rank,                                       # 2
            fath_team_stats.active_50                                   # 3
    )\
        .order_by(fath_team_stats.lastupdate.desc())\
        .limit(2)\
        .all()

    detailed_stats = fath_team_stats_detailed.query.with_entities(
            fath_team_stats_detailed.timestamp.distinct().label("timestamp"),  # 0
            fath_team_stats_detailed.active_users                              # 1
    )\
        .order_by(fath_team_stats_detailed.timestamp.desc())\
        .limit(2)\
        .all()

    wus_diff = stats[0][1] - stats[1][1]
    active_user_diff = detailed_stats[0][1] - detailed_stats[1][1]

    # Dates
    timestamp = transaction_audit.query.order_by(transaction_audit.timestamp.desc()).first()
    yesterday = timestamp.timestamp - timedelta(days=1)

    # All transactions that have happened in the last 24hrs
    _24hr_txs = transaction_audit.query.filter(
                transaction_audit.timestamp > yesterday
                    ).order_by(
                        transaction_audit.timestamp.desc())

    # Calculate 24hrs volume (to be changes into sqlalchemy query)
    n = 0
    for i in _24hr_txs:
        n = n + i.transacted

    # Total amount of BitGreen distributed since the beginning
    total_distributed = transaction_audit.query.with_entities(
                        func.sum(transaction_audit.transacted).label("total")
                                ).first()

    return render_template("index.html",
                           sum='{0:,.2f}'.format(n),
                           transacted='{0:,.2f}'.format(total_distributed.total),
                           work_units='{:,}'.format(team_stats.wus),
                           wus_diff = wus_diff,
                           active_workers=team_stats_detailed.active_users,
                           active_workers_diff=active_user_diff
    )

@app.route('/folding')
def transactions():
    '''
    Populates transactions.html with data

    Returns:
         The last 24hrs of transactions carried out by the controller.
    '''
    team_stats = fath_team_stats.query.order_by(fath_team_stats.lastupdate.desc()).first()
    team_stats_detailed = fath_team_stats_detailed.query.order_by(fath_team_stats_detailed.timestamp.desc()).first()

    # Total amount of BitGreen distributed since the beginning
    total_distributed = transaction_audit.query.with_entities(
                        func.sum(transaction_audit.transacted).label("total")
                                ).first()

    # Team stats (used to calculate the different between the last
    stats = fath_team_stats.query.with_entities(
            fath_team_stats.lastupdate.distinct().label("lastupdate"),  # 0
            fath_team_stats.wus,                                        # 1
            fath_team_stats.rank,                                       # 2
            fath_team_stats.active_50                                   # 3
    )\
        .order_by(fath_team_stats.lastupdate.desc())\
        .limit(2)\
        .all()

    detailed_stats = fath_team_stats_detailed.query.with_entities(
            fath_team_stats_detailed.timestamp.distinct().label("timestamp"),  # 0
            fath_team_stats_detailed.active_users                              # 1
    )\
        .order_by(fath_team_stats_detailed.timestamp.desc())\
        .limit(2)\
        .all()


    rank_diff = stats[1][2] - stats[0][2]
    wus_diff = stats[0][1] - stats[1][1]
    active_user_diff = detailed_stats[0][1] - detailed_stats[1][1]

    # Dates
    timestamp = transaction_audit.query.order_by(transaction_audit.timestamp.desc()).first()
    yesterday = timestamp.timestamp - timedelta(days=1)

    # All transactions that have happened in the last 24hrs
    _24hr_txs = transaction_audit.query.filter(
                transaction_audit.timestamp > yesterday
                    ).order_by(
                        transaction_audit.timestamp.desc())

    # Calculate 24hrs volume (to be changes into sqlalchemy query)
    n = 0
    for i in _24hr_txs:
        n = n + i.transacted

    return render_template("folding.html",
                           wallet_txs=_24hr_txs,
                           sum='{0:,.2f}'.format(n),
                           work_units='{:,}'.format(team_stats.wus),
                           team_rank=team_stats.rank,
                           transacted='{0:,.2f}'.format(total_distributed.total),
                           rank_diff=rank_diff,
                           wus_diff=wus_diff,
                           active_workers=team_stats_detailed.active_users,
                           active_workers_diff=active_user_diff
                           )

@app.route('/help')
def help():
    return render_template("help.html")

@app.route('/faq')
def faq():
    return render_template("faq.html")


## Generate .CSV outout for user to download
@app.route('/fah_transactions_7Days.csv')
def generate_7days_csv():
    '''
    Generate .csv file for user to download

    Returns:
         The last 7 days of transactions carried out by the controller.
    '''
    def generate():
        latest_timestamp = transaction_audit.query.order_by(transaction_audit.timestamp.desc()).first()
        yesterday = latest_timestamp.timestamp - timedelta(days=7)

        _7day_txs = transaction_audit.query.filter(transaction_audit.timestamp > yesterday).order_by(
            transaction_audit.timestamp.desc())

        yield ','.join(['txid', 'transacted', 'total_workers', 'timestamp']) + '\n'

        for row in _7day_txs:
            yield ','.join([str(row.txid), str(row.transacted), str(row.total_workers), str(row.timestamp)]) + '\n'
    return Response(generate(), mimetype='text/csv')

@app.route('/fah_transactions_14Days.csv')
def generate_14days_csv():
    '''
    Generate .csv file for user to download

    Returns:
         The last 7 days of transactions carried out by the controller.
    '''
    def generate():
        latest_timestamp = transaction_audit.query.order_by(transaction_audit.timestamp.desc()).first()
        yesterday = latest_timestamp.timestamp - timedelta(days=14)

        _14day_txs = transaction_audit.query.filter(transaction_audit.timestamp > yesterday).order_by(
            transaction_audit.timestamp.desc())

        yield ','.join(['txid', 'transacted', 'total_workers', 'timestamp']) + '\n'

        for row in _14day_txs:
            yield ','.join([str(row.txid), str(row.transacted), str(row.total_workers), str(row.timestamp)]) + '\n'
    return Response(generate(), mimetype='text/csv')

@app.route('/fah_transactions_1Month.csv')
def generate_1month_csv():
    '''
    Generate .csv file for user to download

    Returns:
         The last 31 days of transactions carried out by the controller.
    '''
    def generate():
        latest_timestamp = transaction_audit.query.order_by(transaction_audit.timestamp.desc()).first()
        yesterday = latest_timestamp.timestamp - timedelta(days=31)

        _1month_txs = transaction_audit.query.filter(transaction_audit.timestamp > yesterday).order_by(transaction_audit.timestamp.desc())

        yield ','.join(['txid', 'transacted', 'total_workers', 'timestamp']) + '\n'

        for row in _1month_txs:
            yield ','.join([str(row.txid), str(row.transacted), str(row.total_workers), str(row.timestamp)]) + '\n'
    return Response(generate(), mimetype='text/csv')

if __name__ == '__main__':


    # Method to be implemented into the back-end which will deprecate the use of psycopg2
    # in favor of flask_sqlalchemy.
    # > postgresql://USERNAME:PASSWORD@SQLSERVER:5432/DATABASE

    app.run(host='0.0.0.0')
