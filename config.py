import os
basedir = os.path.abspath(os.path.dirname(__file__))

# Base class contains settings common to all configurations
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in \
        ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    BLOGGING_MAIL_SUBJECT_PREFIX = '[Blogging]'
    BLOGGING_MAIL_SENDER = 'Blogging Admin <blogging@example.com>'
    BLOGGING_ADMIN = os.environ.get('BLOGGING_ADMIN') or "aldohasibuan1@gmail.com"
    SQLALCHEMY_TRACK_MODIFICATIONS = True 
    BLOGGING_POSTS_PER_PAGE = 5
    NAMING_CONVENTION = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
    }
    # This class can be used to allow the application to customize is configurations.
    # e.g. all the config above can optionally be set here, for example:
    # app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', 'false')
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///'
    # Disable csrf check at every post request carrying a form
    WTF_CSRF_ENABLED = False
    # Disable csrf check at every post request to the endpoint
    #https://stackoverflow.com/questions/38624060/flask-disable-csrf-in-unittest
    WTF_CSRF_METHODS= []

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')

class CustomdbConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'testnew.sqlite')

class DockerConfig(ProductionConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'testnew.sqlite')

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        import logging
        from logging import FileHandler
        # Create handler that logs all logging to stderr.
        # Docker will expose all logging to stderr through docker logs command.
        file_handler = FileHandler("logs_prod.log", 'a', 'utf-16')
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'customdb': CustomdbConfig,

    'default': DevelopmentConfig
}
