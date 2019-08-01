import os
from flask import Flask, render_template, redirect, request, session, flash
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy			
from flask_migrate import Migrate
from sqlalchemy.sql import func	
import re

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///BrightIdeas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db=SQLAlchemy(app)
migrate=Migrate(app, db)

bcrypt=Bcrypt(app)
app.secret_key = "Group_Project_Coding_Dojo_2019"

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

likes_table=db.Table('likes',
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column('created_at', db.DateTime, server_default=func.now())
)

followers_table=db.Table('followers',
    db.Column("follower_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("followed_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("created_at", db.DateTime, server_default=func.now())
)

class User(db.Model):
    __tablename__ = "users"
    id=db.Column(db.Integer, primary_key=True)
    first_name=db.Column(db.String(255))
    last_name=db.Column(db.String(255))
    email=db.Column(db.String(255))
    password_hash=db.Column(db.String(255))
    liked_posts=db.relationship("Post", secondary=likes_table)
    followers=db.relationship("User", 
        secondary=followers_table, 
        primaryjoin=id==followers_table.c.followed_id, 
        secondaryjoin=id==followers_table.c.follower_id,
        backref="following")
    created_at=db.Column(db.DateTime, server_default=func.now())
    updated_at=db.Column(db.DateTime, server_default=func.now(),onupdate=func.now())

    def full_name(self):
        return "{} {}".format(self.first_name, self.last_name)

    @classmethod
    def add_user(cls,data):
        new_user = cls(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            password_hash=bcrypt.generate_password_hash(data['password'])
        )
        db.session.add(new_user)
        db.session.commit()
        return new_user

    @classmethod
    def reg_errors(cls, form_data):
        errors=[]
        if len(form_data['first_name'])<2:
            errors.append("First name must be longer")
        if len(form_data['last_name'])<2:
            errors.append("Last name must be longer")
        if not EMAIL_REGEX.match(form_data['email']):
            errors.append("Email Address is invalid")
        if form_data['password'] != request.form['c_password']:
            errors.append("Passwords do not match")
        if len(form_data['password']) < 8:
            errors.append("Password must be longer than 8 characters")
        return errors

    @classmethod
    def register_user(cls, form_data):
        errors = cls.reg_errors(form_data)
        valid = len(errors)==0
        data = cls.add_user(form_data) if valid else errors
        return {
            "status": "good" if valid else "bad",
            "data": data
        }


class Post(db.Model):
    __tablename__="posts"
    id=db.Column(db.Integer, primary_key=True)
    message=db.Column(db.String(255))
    author_id=db.Column(db.Integer,db.ForeignKey("users.id"))
    author=db.relationship("User", backref="posts", cascade="all")
    likers=db.relationship("User", secondary=likes_table, cascade="all")
    created_at=db.Column(db.DateTime, server_default=func.now())
    updated_at=db.Column(db.DateTime, server_default=func.now(),onupdate=func.now())

    @classmethod
    def add_new_post(cls,post):
        db.session.add(post)
        db.session.commit()
        return post
    
    def age(self):
        return self.created_at
        return age


class Follow(db.Model):
    __tablename__="follows"
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("users.id"))
    user=db.relationship("User",backref="likes", cascade="all")
    user_id=db.Column(db.Integer, db.ForeignKey("users.id"))
    user=db.relationship("User",backref="likes", cascade="all")
    created_at=db.Column(db.DateTime, server_default=func.now())



@app.route("/")
def index():
    return render_template("index.html")


@app.route("/bright_ideas")
def bright_ideas():
    if "user_logged_in" not in session:
        flash("Please Log In")
        return redirect("/")

    user_logged_in=User.query.get(session['user_logged_in']['id'])
    approved_users_ids = [user.id for user in user_logged_in.following] + [user_logged_in.id]
    all_posts=Post.query.all()
    # one_post=Post.query.get(1)
    # totalLikes = (db.session.query(func.count(likes_table.user_id).label("# people"))
    # .group_by(likes_table.post_id)).all()
    # print(totalLikes)
    # print("post")
    # print(len(one_post.likers))
    
    return render_template("bright_ideas.html", posts=all_posts)


@app.route("/register", methods=["POST"])
def register():
    result=User.register_user(request.form)
    if result['status']=="good":
        user=result['data']
        session['user_logged_in'] = {
            "id": user.id,
            "first": user.first_name,
            "last": user.last_name
        }
        return redirect("/bright_ideas")
    else:
        errors=result['data']
        for error in errors:
            flash(error)
        return redirect("/")

@app.route("/login", methods=['POST'])
def login():
    user=User.query.filter_by(email=request.form['email']).first()
    valid = True if bcrypt.check_password_hash(user.password_hash, request.form['password']) else False
    
    if valid:
        session['user_logged_in'] = {
            "id": user.id,
            "first": user.first_name,
            "last": user.last_name
        }
        return redirect("/bright_ideas")
    else:
        flash("Login Invaild")
        return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

#add a post-WORKED
@app.route("/add_post", methods=["GET", "POST"])
def add_post():


    new_post = Post(
        message = request.form["message"],
        author_id = int(session['user_logged_in']['id'])

    )
    db.session.add(new_post)
    db.session.commit()
    return redirect("/bright_ideas")


#like a post-WORKED
@app.route("/posts/<post_id>/like", methods=["POST"])
def add_like(post_id):
    print("got to the like route", post_id)
    liked_post= Post.query.get(post_id)
    liker=User.query.get(session['user_logged_in']['id'])
    print(liked_post, liker)
    # liker.liked_posts.append(liked_post)
    liked_post.likers.append(liker)
    db.session.commit()
    return redirect("/bright_ideas")

#DELETE route is working - but route is breaking if it is liked, if it is not liked than it is getting deleted
@app.route("/posts/<post_id>/delete", methods=['POST'])
def delete_post(post_id):
    if "user_logged_in" not in session:
        flash("Please Log In")
        return redirect("/")
    post_being_deleted=Post.query.get(post_id)
    posts_author=post_being_deleted.author
    posts_author.posts.remove(post_being_deleted)
    db.session.delete(post_being_deleted)
    db.session.commit()
    return redirect("/bright_ideas")
    # print(post_id)
    # deleter = User.query.get(session['user_logged_in']['id'])
    # post_being_deleted=Post.query.get(post_id)
    # print(deleter)
    # print(type(post_being_deleted))
    # if len (post_being_deleted.likers) > 0:
    #     post_being_deleted.likers.clear()
    #     # db.session.commit()
    # # post_being_deleted.likers.clear()
    # # post_being_deleted.likers.remove(deleter)
    # # posts_author=post_being_deleted.author
    # # print(posts_author)
    # # deleter.posts.remove(post_being_deleted)
    # # posts_author.posts.remove(post_being_deleted)
    
    # # db.session.commit()
    # # db.session.delete(post_being_deleted)
    # db.session.commit()
    return redirect("/bright_ideas")

#Edit Post WORKING but login user should be able to edit their own post not other users
@app.route("/posts/<post_id>/edit")
def show_edit(post_id):
    if "user_logged_in" not in session:
        flash("Please Log In")
        return redirect("/")
    post=Post.query.get(post_id)
    return render_template("edit.html", post=post)

#Update post working but login user should be able to update their own post not other users
@app.route("/posts/<post_id>/update", methods=["POST"])
def update_post(post_id):
    if "user_logged_in" not in session:
        flash("Please Log In")
        return redirect("/")
    editer=User.query.get(session['user_logged_in']['id'])
    post=Post.query.get(post_id)
    if len(request.form['post'])>0:
        post.message=request.form['post']
        db.session.commit()
        return redirect("/bright_ideas")
    else:
        flash("Field cannot be empty!")
        return render_template("edit.html", post=post)

#User Profile - should show user first & last name, email and Number of post and number of likes by the user
@app.route("/users/<id>", methods=["GET"])
def user_profile(id):
    user_profile = User.query.get(id)
    numlikes = len(user_profile.liked_posts)
    # db.session.query(User).join(liked_posts).filter(liked_posts.user_id==id).count()
    # print(type)
    # print(numlikes, "This is a number of like")
    # count = 0
    # for like in numlikes:
    #     count = count+1
    # numlikesis = count
    numposts = Post.query.filter(Post.author_id == id).count()
    # print(numposts, "This is a number of post")
    # count2 = 0
    # for post in numposts:
    #     count2 = count2+1
    # numpostsis = count2
    return render_template("user_profile.html", user_profile=user_profile, numlikes = numlikes, numposts=numposts)

#Follow Users- Worked
@app.route("/follow/<user_id>")
def follow_user(user_id):
    if "user_logged_in" not in session:
        flash("Please Log In")
        return redirect("/")
    logged_in_user=User.query.get(session['user_logged_in']['id'])
    followed_user=User.query.get(user_id)
    followed_user.followers.append(logged_in_user)
    db.session.commit()
    return redirect("/success")

#Succes Route-for Follow Route
@app.route("/success")
def successful_follow():
    if "user_logged_in" not in session:
        flash("Please Log In")
        return redirect("/")
    return render_template("success.html")

# Like Status- this route will show the user names who have liked a certain post -WORKED
@app.route("/brightideas/<post_id>", methods=["GET"])
def like_status(post_id):
    post = Post.query.get(int (post_id))
    print(post.likers)
    return render_template("like_status.html", post=post)

# Ajax Route
@app.route("/email", methods=['POST'])
def email_check(email):
    found = False
    user_email = User.query.filter_by(email)
    result = user_email
    if result:
        found = True
    return render_template('partials/email.html', found=found)

if __name__ == "__main__":
    app.run(debug=True)