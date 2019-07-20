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
    likers=db.relationship("User", secondary=likes_table)
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


@app.route("/success")
def success():
    if "user_logged_in" not in session:
        flash("Please Log In")
        return redirect("/")

    user_logged_in=User.query.get(session['user_logged_in']['id'])

    return render_template("success.html")


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
        return redirect("/success")
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
        return redirect("/success")
    else:
        flash("Login Invaild")
        return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)