from flask import Flask, request, render_template, redirect, session

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config.from_pyfile("../settings.py")
from flask_uwsgi_websocket import GeventWebSocket

sockets = GeventWebSocket(app)


@app.before_request
def process_request(*args, **kwargs):
    reqpath=request.path
    if reqpath == '/' or reqpath == '/login' or '/static/' or '/chpwd' in reqpath:
        return None
    else:
        if session.get('user_info'):
            return None
        return redirect('/')


@app.after_request
def process_response(response):
    request.args.get('name')
    return response


@app.errorhandler(404)
def not_found(*args, **kwargs):
    return render_template('404-not-found.html')


from .advert import blue_advert
from .assets import blue_assets
from .domain import blue_domain
from .engineer import blue_engineer
from .game import blue_game
from .gamelist import blue_gamelist
from .home import blue_home
from .image import blue_image
from .loadpage import blue_loadpage
from .script import blue_script
from .sites import blue_sites
from .video import blue_video
from .person import blue_person
from admins.adhome import blue_adhome
from admins.addomain import blue_addomain
from admins.adauthorproject import blue_adauthorproject
from admins.adsites import blue_adsites
from admins.adauthorrole import blue_adauthorrole

app.register_blueprint(blue_advert)
app.register_blueprint(blue_assets)
app.register_blueprint(blue_domain)
app.register_blueprint(blue_engineer)
app.register_blueprint(blue_game)
app.register_blueprint(blue_gamelist)
app.register_blueprint(blue_home)
app.register_blueprint(blue_image)
app.register_blueprint(blue_loadpage)
app.register_blueprint(blue_script)
app.register_blueprint(blue_sites)
app.register_blueprint(blue_video)
app.register_blueprint(blue_person)
app.register_blueprint(blue_adhome)
app.register_blueprint(blue_adsites)
app.register_blueprint(blue_adauthorproject)
app.register_blueprint(blue_addomain)
app.register_blueprint(blue_adauthorrole)
