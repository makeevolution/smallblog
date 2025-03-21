# This is the entry point to starting the whole app

import os
import re
import sys
import click
from flask_migrate import Migrate, upgrade
from sqlalchemy import create_engine
from alembic.config import Config
from alembic import command
import unittest

from app import create_app, db
from app.models import Permission, User, Role, Follow, Post
from app.factories import GenericUser, ModeratorUser, AdminUser
from app.helpers import MAX_FAKE_POSTS, MAX_FAKE_USERS, create_fake_users, create_fake_posts
from config import config

# Find the current configuration to be used for the system
usedConfiguration = os.getenv('FLASK_CONFIG') or 'default'
PORT = 5000

# Preliminary if statement to turn on test coverage engine, more information in the flask test
# decorator below.
COV = None
if (sys.gettrace() is None and (usedConfiguration in ['testing', 'development', 'default'])):
    import coverage
    # Start the coverage engine. the include option is to limit which code to analyse; otherwise it will also analyse
    # the pip packages!
    with open(".coveragerc", "w+") as f:
        coverageString = "[report] \n"
        coverageString = coverageString + "exclude_lines = \n"
        coverageString = coverageString + "\t pragma: no cover \n"
        coverageString = coverageString + "\t import \n"
        coverageString = coverageString + "\t from .* import \n"

        # Regexes for lines to exclude from consideration \n exclude_lines = \n \tpragma: no cover \ \ttest this thing"
        f.write(coverageString)
    COV = coverage.coverage(branch = True, include="app/*")
    COV.start()

# Create an instance of an application using a configuration in env var
app = create_app(usedConfiguration)
# The below variable is used by '''flask db migrate''' command i.e. when you want to create a migration script
# after updating the model. 
migrate = Migrate(app, db, render_as_batch = True)

# Nothing to do with the application, it's here just so that if we run flask shell from cmd, no imports for db, User and Role required
@app.shell_context_processor
def make_shell_context():
    print("Shell started")
    print(f"WARNING: using database " + \
            getattr(config[usedConfiguration], "SQLALCHEMY_DATABASE_URI"))
    return dict(db=db, User=User, Role=Role, Permission = Permission, Follow=Follow, Post=Post, 
                GenericUser = GenericUser, ModeratorUser = ModeratorUser, AdminUser = AdminUser)

# Coverage output not possible in debug mode, since COV.start() below starts a different
# thread that actually runs the tests. Check if debug mode is used using sys.gettrace() output.
# If debug is used, then don't need to turn on the coverage engine.

# When using flask test command (defined below), notice it uses app in its decorator. This
# means that it requires an app instance to be created before the test can be run. In this
# app instance, that's where the login_manager, etc. is initialized i.e. is run. When another
# instance is made (i.e. in setUp of each unit test), this part is not run anymore. The coverage
# engine won't see any decorators using these login_manager etc. (e.g. @login_required) if we
# start the engine after the app.create_app() statement above, making the coverage report 
# incorrect.
@app.cli.command()
def test():
    tests = unittest.TestLoader().discover('tests')
    testResult = unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()
    if testResult.wasSuccessful():
        exit(0)
    else:
        exit(1)
    
@app.cli.command()
def deploy():
    # Alembic to migrate the new database to latest version
    upgrade()
    # Create user roles in the roles table in the database, if not yet configured
    Role.insert_roles()

# My own helper command to generate a new sqlite database based on current model of db, with a corresponding migration folder.
# Similar to flask db init, but make our own so we don't depend on that framework!
@app.cli.command("init_sqlite_db")
@click.argument("db_name", required = True)
def init_sqlite_db(db_name):
    engine_for_sqlite = re.findall("(?<=\()(.*)(?=\\\)", app.extensions["migrate"].db.engine.__repr__())[0] + "\\" + db_name + ".sqlite"
    engine = create_engine(engine_for_sqlite)
    app.extensions["migrate"].db.metadata.create_all(engine)
    folder = f"{os.getcwd()}/migrations_{db_name}"
    alembic_cfg = Config(f"{folder}/alembic.ini", attributes = {"sqlalchemy.url": str(engine_for_sqlite)})
    alembic_cfg.set_main_option("sqlalchemy.url", str(engine_for_sqlite))
    command.init(alembic_cfg, directory = folder)

@app.cli.command("seed_fake_users")
@click.argument("count", required = False, default = MAX_FAKE_USERS)
def seed_fake_users(count):
    create_fake_users(count)

@app.cli.command("seed_fake_posts")
@click.argument("count", required = False, default = MAX_FAKE_POSTS)
def seed_fake_posts(count):
    create_fake_posts(count)

@app.cli.command("clear_data")
def clear_data():
    """Remove all data from all tables in the database."""
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        print(f"Clearing data from table {table.name}...")
        db.session.execute(table.delete())
    db.session.commit()
    print("All data has been cleared from the database.")

if __name__=="__main__":
    app.run(port=PORT)
