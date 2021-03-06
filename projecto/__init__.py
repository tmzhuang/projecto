from __future__ import absolute_import
import os

from flask import Flask, render_template, redirect, url_for
from flask.ext.login import current_user

from .blueprints import blueprints
from .extensions import login_manager, register_assets, partials
from .models import File
from settings import APP_FOLDER, STATIC_FOLDER, TEMPLATES_FOLDER, API, LOADED_MODULES

app = Flask(__name__, static_folder=STATIC_FOLDER, template_folder=TEMPLATES_FOLDER)
app.config.from_pyfile(os.path.join(APP_FOLDER, "settings.py"))

# Login management
login_manager.setup_app(app)

# Seasurf initializations
from .extensions import csrf
csrf.init_app(app)

# Database shit
# TODO: this needs to be made better.
File.FILES_FOLDER = app.config["FILES_FOLDER"]


# App stuff
@app.before_request
def before_request():
  app.jinja_env.globals["partials"] = partials()
  app.jinja_env.globals["SERVER_MODE"] = app.config["SERVER_MODE"]


# Here are just the pages.
@app.route("/")
def main():
  return render_template("main.html")


@app.route("/features")
def features():
  return render_template("features.html")


@app.route("/licenses")
def licenses():
  return render_template("licenses.html")


@app.route("/app/")
def mainapp():
  if not current_user.is_authenticated():
    return redirect(url_for("main"))

  new_user_name = current_user._get_current_object().__class__.name.default()
  return render_template("app.html", change_name=current_user.name==new_user_name)


# register blueprints automatically.
for blueprint, meta in blueprints:
  app.register_blueprint(blueprint, **meta)

# register API modules
api_route_base = __import__(API, globals(), locals(), "route_base").route_base
for module in LOADED_MODULES:
  api_module = __import__(API + "." + module + ".api", globals(), locals(), ["blueprints", "meta"])
  meta = api_module.meta
  meta["url_prefix"] = api_route_base + meta["url_prefix"]
  app.register_blueprint(api_module.blueprint, **meta)

# asset stuffs
# needs to be after all the blueprints are registered.
register_assets(app)
