from datetime import datetime
from flask import current_app, flash, jsonify, make_response, render_template, render_template_string, request, session, redirect, url_for, abort
from flask_login import current_user, login_required
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
# the below imports the blueprint called "main" from __init__.py
from . import main
from .forms import EditProfileAdminForm, EditProfileForm, PostForm, CommentForm
from .. import db
from ..models import Permission, Role, User, Post, Comment, Vote
from ..decorators import admin_required, permission_required

@main.route('/', methods=["GET","POST"])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        post = Post(title = form.title.data, body = form.text.data, author = current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for("main.index"))
    page = request.args.get('page', 1, type=int)
    # type=int is so that if 'page' is not an integer, the default value 1 is returned
    only_following_posts = False
    if current_user.is_authenticated:
        only_following_posts = bool(request.cookies.get('only_following_posts', ''))
    if only_following_posts:
        query = current_user.following_posts
    else:
        query = Post.query
    pagination: "flask_sqlalchemy.Pagination" = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config["BLOGGING_POSTS_PER_PAGE"],
        error_out = False
    )
    # all() is now replaced with paginate() method.
    # error_out sets what happens if page that is out of range is returned. If True, we go to 404 page,
    # if false, it will return an empty list.
    # desc() orders the column entry in descending order
    posts = pagination.items
    return render_template("index.html",
                            current_time = datetime.utcnow(),
                            form = form,
                            posts = posts,
                            only_following_posts = only_following_posts,
                            pagination = pagination)

# /all and /following routes sets whether the posts to be shown is all or just those
# of the users the currently logged in user follows. The set_cookie option makes it
# so that the browser of the user remembers the choice.

@main.route('/all')
@login_required
def show_all():
    response = make_response(redirect(url_for('main.index')))
    response.set_cookie('only_following_posts', '', max_age = 60*60*24*30) # 30 days
    return response

@main.route('/following')
@login_required
def show_following():
    response = make_response(redirect(url_for('main.index')))
    response.set_cookie('only_following_posts', '1', max_age = 60*60*24*30) # 30 days
    return response

@main.route('/user/<username>')
def user(username):
    user = db.session.query(User).filter_by(username = username).first()
    if user is None:
        flash(f"User {username} not found")
        abort(404)    
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template("user.html", user = user, posts = posts)

@main.route("/edit_profile", methods=["GET","POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
       current_user.name = form.name.data
       current_user.location = form.location.data
       current_user.about_me = form.about_me.data
       db.session.add(current_user)
       db.session.commit()
       flash("Your profile has been successfully updated!")
       return redirect(url_for("main.user", username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template("edit_profile.html", form=form)

@main.route("/edit_profile/<int:id>", methods=["GET","POST"])
@login_required
@admin_required
def edit_profile_admin(id):
    user = db.session.query(User).get_or_404(id)
    form = EditProfileAdminForm(user)
    if form.validate_on_submit():
       #try using update instead of session commit
       user.name = form.name.data
       user.location = form.location.data
       user.about_me = form.about_me.data
       user.username = form.username.data
       user.email = form.email.data
       user.confirmed = form.confirmed.data 
       user.role = db.session.query(Role).get(form.role.data)
       db.session.add(user)
       db.session.commit()
       flash(f"Profile has been successfully updated!")
       return redirect(url_for("main.user", username=db.session.query(User).get(id)))
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    form.username.data = user.username
    form.email.data = user.email
    form.confirmed.data = user.confirmed
    # to set the initial value of the role choice, pass in the id of the role in the db,
    # since in the SelectField, the role is identified by its id
    form.role.data = user.role_id
    return render_template("edit_profile.html", form=form, user=user)

@main.route('/admin')
@login_required
@admin_required
def for_admins_only():
    return "For Administrators only!"

@main.route('/post/<int:id>', methods=["GET","POST"])
def post(id):
    post = db.session.query(Post).get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(author = current_user._get_current_object(), post = post, body = form.text.data)
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('main.post', id = post.id))
    page = request.args.get('page', 1, type=int)
    pagination: "flask_sqlalchemy.Pagination" = post.comments.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config["BLOGGING_POSTS_PER_PAGE"],
        error_out = False
    ) 
    comments = pagination.items
    return render_template('post.html',
                            posts = [post], 
                            form=form,
                            comments = comments,
                            pagination = pagination)

@main.route('/edit/<int:id>', methods=["GET","POST"])
def edit_post(id):
    # first check if the person have edit permissions (only admin and the user himself)
    # next get the post 
    # next edit the post
    # finally push
    post = db.session.query(Post).get_or_404(id)
    if (post.author != current_user) and (not current_user.can(Permission.ADMIN)):
        abort(403)
    form = PostForm()
    newTitle = form.title.data
    newText = form.text.data # Post to be edited is displayed first
    form.text.data = post.body
    # form.validate_on_submit() will return false if not all DataRequired fields
    # are filled in! Make sure you add them too when making unit tests.
    if form.validate_on_submit():
        post.body = newText
        post.title = newTitle
        db.session.add(post)
        db.session.commit()
        return redirect(url_for("main.post", id = post.id))
    return render_template("edit_post.html", form = form)

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    # get the user to be followed
    user = db.session.query(User).filter_by(username = username).first()
    # make sure the user is valid
    if not user:
        flash("Invalid user input!")
        return redirect(url_for("main.index"))
    # make sure the current user is not already following the user
    if not user.is_followed_by(current_user):
        # follow the user
        current_user.follow(user)
        db.session.add(user)
        db.session.commit()
        flash("You are now following this user")
    else:
        flash("You are already following this user!")
    return redirect(url_for("main.user", username=user.username))

@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    # get the user to be unfollowed
    user = db.session.query(User).filter_by(username = username).first()
    # make sure the user is valid
    if not user:
        flash("Invalid user input!")
        return redirect(url_for("main.index"))
    # make sure the current user is already following the user
    if user.is_followed_by(current_user):
        # unfollow the user
        current_user.unfollow(user)
        db.session.add(user)
        db.session.commit()
        flash("You have unfollowed this user")
    else:
        flash("You are already not following this user!")
    return redirect(url_for("main.user", username=user.username))

@main.route("/followers/<username>")
def followers(username: str):
    # return all followers of the user
    # also give pagination because there are many users!
    if username is None:
        flash("Invalid user input!")
        return redirect(url_for("main.index"))
    followersAsFollowInstance = db.session.query(User).filter_by(username=username).first().followers
    page = request.args.get('page', 1, type=int)
    pagination: "flask_sqlalchemy.Pagination" = followersAsFollowInstance.paginate(
        page, per_page=current_app.config["BLOGGING_POSTS_PER_PAGE"],
        error_out = False
    )
    followersCurrentPage = pagination.items
    fols = [{"username": followerAsFollowInstance.follower.username,
            "timestamp": followerAsFollowInstance.timestamp,
            "last_seen": followerAsFollowInstance.follower.last_seen,
            "about_me": followerAsFollowInstance.follower.about_me,
            "gravatar": followerAsFollowInstance.follower.gravatar(size=40)}
            for followerAsFollowInstance in followersCurrentPage]
    return render_template("followers.html", 
                            fols = fols,  
                            page = page,
                            username = username,
                            pagination = pagination,
                            title = "followers",
                            endpoint = "main.followers")

@main.route("/followings/<username>")
def followings(username: str):
    # return all followers of the user
    # also give pagination because there are many users!
    if username is None:
        flash("Invalid user input!")
        return redirect(url_for("main.index"))
    followingsAsFollowInstance = db.session.query(User).filter_by(username=username).first().following
    page = request.args.get('page', 1, type=int)
    pagination: "flask_sqlalchemy.Pagination" = followingsAsFollowInstance.paginate(
        page, per_page=current_app.config["BLOGGING_POSTS_PER_PAGE"],
        error_out = False
    )
    followingsCurrentPage = pagination.items
    fols = [{"username": followingAsFollowInstance.following.username,
            "timestamp": followingAsFollowInstance.timestamp,
            "last_seen": followingAsFollowInstance.following.last_seen,
            "about_me": followingAsFollowInstance.following.about_me,
            "gravatar": followingAsFollowInstance.following.gravatar(size=40)}
            for followingAsFollowInstance in followingsCurrentPage]
    return render_template("followers.html", 
                            fols = fols,  
                            page = page,
                            username = username,
                            pagination = pagination,
                            title = "followings",
                            endpoint = "main.followings")

@main.route("/moderate")
@login_required
@permission_required(Permission.MODERATE)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination: "flask_sqlalchemy.Pagination" = db.session.query(Comment).\
                                                order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config["BLOGGING_POSTS_PER_PAGE"],
        error_out = False
    ) 
    comments = pagination.items
    return render_template("moderate.html", comments = comments, pagination = pagination)

@main.route("/moderate/enable/<int:id>")
@login_required
@permission_required(Permission.MODERATE)
def moderate_enable(id):
    comment = db.session.query(Comment).get(id)
    comment.disabled = 0
    db.session.add(comment)
    db.session.commit()
    return redirect(request.referrer or url_for("main.index"))


@main.route("/moderate/disable/<int:id>")
@login_required
@permission_required(Permission.MODERATE)
def moderate_disable(id):
    comment = db.session.query(Comment).get(id)
    comment.disabled = 1
    db.session.add(comment)
    db.session.commit()
    return redirect(request.referrer or url_for("main.index"))

@main.route("/vote", methods=["GET","PUT"])
def vote():
    data = request.json
    post_id = int(data["post_id"])
    voter_id = int(data["voter_id"])
    current_vote = int(data["iter"])
    if current_vote not in [-1,1]:
        raise Exception("vote_type is not supported! Is definition changed in javascript side?")
    current_vote = True if current_vote == 1 else False
    # If instance of vote exists, and the new vote is opposite of current vote, update the vote type.
    vote_instance = db.session.query(Vote).filter(and_(Vote.post_id == post_id, Vote.voter_id == voter_id)).all()
    if len(vote_instance) > 1:
        raise Exception("something is wrong in vote database! There can't be multiple vote instances for the same post and voter!")
    if vote_instance:
        vote_instance = vote_instance[0]
        if current_vote != vote_instance.vote_type:
            vote_instance.vote_type = current_vote
            db.session.add(vote_instance)
        else:
            db.session.delete(vote_instance)
    else:
        if current_vote:
            new_vote = Vote(post_id = post_id, voter_id = voter_id, vote_type = True)
        else:
            new_vote = Vote(post_id = post_id, voter_id = voter_id, vote_type = False)
        db.session.add(new_vote)
    try:
        db.session.commit()
    except (SQLAlchemyError, DBAPIError) as e:
        db.session.rollback()
        raise Exception("Error in database operation") from e
    no_of_votes = db.session.query(Post).get_or_404(post_id).net_votes
    return jsonify({"votes":no_of_votes})