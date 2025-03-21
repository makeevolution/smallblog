'''This script is used to help developing the blog further. These are meant to be used
by importing in a flask shell session'''
from flask import current_app
from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
import logging
from app import db
from app.models import User, Role, Post

MAX_FAKE_USERS = 100
MAX_FAKE_POSTS = 100

def create_fake_users(count=MAX_FAKE_USERS):
    """Create fake users and add them to the database."""
    fake = Faker()
    i = 0
    if User.query.count() >= MAX_FAKE_USERS:
        logging.warning(f"There are already {MAX_FAKE_USERS} users in the database, not creating more")
        return
    while i < count:
        u = User(email=fake.email(),
                 username=fake.user_name(),
                 password='password',
                 confirmed=True,
                 name=fake.name(),
                 location=fake.city(),
                 about_me=fake.text(),
                 member_since=fake.past_date())
        db.session.add(u)
        i += 1
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        """IntegrityError occurs if the email or username to be added already
        exists. If so, it will retry generating another fake email."""

def create_fake_posts(count=MAX_FAKE_POSTS):
    """Create fake posts and assign them to random users."""
    fake = Faker()
    if Post.query.count() >= MAX_FAKE_POSTS:
        logging.warning(f"There are already {MAX_FAKE_POSTS} posts in the database, not creating more")
        return
    user_count = User.query.count()
    for _ in range(count):
        u = db.session.query(User).offset(randint(0, user_count - 1)).first()
        p = Post(title=fake.text(),
                 body=fake.text(),
                 timestamp=fake.past_date(),
                 author=u)
        db.session.add(p)
    db.session.commit()

def reset_user_roles():
    """Reset all users to the default User role, except the admin."""
    for user in db.session.query(User).all():
        if user is None:
            continue
        if user.email == current_app.get("BLOGGING_ADMIN"):
            user.role = Role.query.filter_by(name="Administrator").first()
        else:
            user.role = Role.query.filter_by(default=True).first()
        db.session.add(user)
    db.session.commit()
