import os
import smtplib
from datetime import date
from functools import wraps
from random import randint

from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

from KEYS import email, password
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm, ContactForm, VerifyForm, ForgetPassword, \
    NewPassword
from send_email import SendOTP

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
ckeditor = CKEditor(app)
Bootstrap(app)

# CONNECT TO DB
# for develop locally
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///blog.db")
# for server
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

# Gravatar
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# CONFIGURE TABLES

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    # ***************Parent Relationship*************#
    comments = relationship("Comment", back_populates="parent_post")


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    # *******Add parent relationship*******#
    # "comment_author" refers to the comment_author property in the Comment class.
    comments = relationship("Comment", back_populates="comment_author")

    # TODO-1 add methods for quick access
    # @staticmethod
    # def search_by_email(user_email):
    #     user = User.query.filter_by(email=user_email).first()
    #     return user if user else False


class Comment(db.Model):
    # __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    # *******Add child relationship*******#
    # "users.id" The users refers to the tablename of the Users class.
    # "comments" refers to the comments property in the User class.
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    comment_author = relationship("User", back_populates="comments")

    # ***************Child Relationship*************#
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    comment = db.Column(db.Text, nullable=False)


db.create_all()


# Create admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = None
        try:
            current_user_id = current_user.id
        except Exception as e:
            print(e)
        finally:
            # If id is not 1 then return abort with 403 error
            if current_user_id != 1:
                return abort(403)
            # Otherwise continue with the route function
            return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts, )


@app.route('/register', methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if request.method == "POST" and form.validate_on_submit():
        user_email = request.form.get("email")

        user = User.query.filter_by(email=user_email).first()
        if user:
            flash("You've already signed up with this email, login instead.")
            return redirect(url_for('login'))
        else:
            name = request.form.get("name")
            user_password = request.form.get("password")
            hashed_password = generate_password_hash(password=user_password, method='pbkdf2:sha256', salt_length=8)

            return redirect(url_for('verify_otp', name=name, user_email=user_email, user_password=hashed_password))

    return render_template("register.html", form=form)


@app.route('/login', methods=["POST", "GET"])
def login():
    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        user_email = request.form.get("email")
        user_password = request.form.get("password")

        all_users = User.query.all()
        for user in all_users:
            if user.email == user_email:
                if check_password_hash(user.password, user_password):
                    login_user(user)
                    return redirect(url_for('get_all_posts'))
                else:
                    flash("The password doesn't match, Please try again.")
        flash("The email doesn't exits, Please try again.")

    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["POST", "GET"])
def show_post(post_id):
    form = CommentForm()
    requested_post = BlogPost.query.get(post_id)

    if request.method == "POST" and form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register for comment.")
            return redirect(url_for('login'))

        comment = request.form.get("comment")
        # user_id = current_user.id
        new_comment = Comment(comment=comment, author_id=current_user.id, post_id=post_id)
        print(new_comment.comment, new_comment.author_id, new_comment.post_id)
        db.session.add(new_comment)
        db.session.commit()
        return redirect((url_for('show_post', post_id=post_id)))

    return render_template("post.html", post=requested_post, form=form, User=User)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/new-post", methods=["POST", "GET"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if request.method == "POST" and form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user.name,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, )


@app.route("/edit-post/<int:post_id>", methods=["POST", "GET"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body
    )
    if request.method == "POST" and edit_form.validate_on_submit():
        post_to_update = BlogPost.query.filter_by(id=post_id).first()
        post_to_update.title = request.form.get("title")
        post_to_update.subtitle = request.form.get("subtitle")
        post_to_update.img_url = request.form.get("img_url")
        post_to_update.body = request.form.get("body")
        db.session.commit()

        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, is_edit=True)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/delete-comment/<int:comment_id>")
@admin_only
def delete_comment(comment_id):
    print(comment_id)
    comment_to_delete = Comment.query.get(comment_id)
    print(comment_to_delete)
    db.session.delete(comment_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()

    if request.method == "POST" and form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register for contact.")
            return redirect(url_for('login'))

        name = request.form.get("name")
        user_email = request.form.get("email")
        phone_number = request.form.get("phone_number")
        message = request.form.get("message")
        with smtplib.SMTP("smtp.gmail.com") as connection:
            connection.starttls()
            connection.login(user=email, password=password)
            connection.sendmail(from_addr=email, to_addrs="rajkar921@gmail.com",
                                msg=f"Subject:Contact\n\nName: {name}\nEmail: {user_email}"
                                    f"\nphone_number: {phone_number}\nmessage: {message}")
        return redirect(url_for('success'))

    return render_template("contact.html", form=form)


@app.route('/success')
@login_required
def success():
    return render_template('success.html')


otp = None


# TODO-3 refactor verify-user code
@app.route('/verify-otp/<name>/<user_email>/<user_password>', methods=["GET", "POST"])
def verify_otp(name, user_email, user_password):
    global otp
    form = VerifyForm()

    if request.method == "GET":
        flash(f"An OTP is send to your email ({user_email}) address.")
        otp = randint(123456, 987654)
        send_otp = SendOTP(user_name=name, user_email=user_email, otp=otp)
        send_otp.register_msgBody()
        send_otp.send_otp()

    if request.method == "POST" and form.validate_on_submit():
        enter_otp = int(request.form.get("otp"))
        if enter_otp == otp:
            new_user = User(name=name, email=user_email, password=user_password)
            db.session.add(new_user)
            db.session.commit()

            # This line will authenticate the user with Flask-Login
            login_user(new_user)
            return redirect(url_for('get_all_posts'))
        else:
            flash("OTP mismatched, another OTP send to your email address.")
            return redirect(url_for('verify_otp', name=name, user_email=user_email, user_password=user_password))

    return render_template("email-verification.html", form=form)


# TODO-2 refactor forget-password code
@app.route('/forget-password', methods=["POST", "GET"])
def forgot_password():
    form = ForgetPassword()

    if request.method == "POST" and form.validate_on_submit():
        user_email = request.form.get("email")
        user_data = User.query.filter_by(email=user_email).first()
        if user_data:
            flash("An OTP send to your email address.")
            return redirect(url_for('verify_user_otp', name=user_data.name, user_email=user_data.email))
        else:
            flash("No account link with this email ! Please check your email.")

    return render_template('forgot-password.html', form=form)


@app.route('/verify-otp/<name>/<user_email>', methods=["POST", "GET"])
def verify_user_otp(name, user_email):
    global otp
    form = VerifyForm()

    if request.method == "GET":
        otp = randint(123456, 987654)
        otp_send = SendOTP(user_name=name, user_email=user_email, otp=otp)
        otp_send.forgot_password_msgBody()
        otp_send.send_otp()

    if request.method == "POST" and form.validate_on_submit():
        user_otp = int(request.form.get("otp"))
        if user_otp == otp:
            print(user_otp, otp)
            flash("Enter your new password, and note it in your dairy.")
            return redirect(url_for('reset_password', user_email=user_email))
        else:
            flash("Wrong credentials provided, Please try again !")
            return redirect(url_for('login'))

    return render_template("forgot-password.html", form=form)


@app.route('/reset-password/<user_email>', methods=["POST", "GET"])
def reset_password(user_email):
    form = NewPassword()
    if request.method == "POST" and form.validate_on_submit():
        new_password = request.form.get("password")
        user = User.query.filter_by(email=user_email).first()
        user.password = generate_password_hash(password=new_password, method="pbkdf2:sha256", salt_length=8)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('forgot-password.html', form=form)


@app.route('/robots.txt')
def robots():
    return render_template('robots.html')


# TODO-4 add category
# TODO-5 add spider for scrap data through worldwide
# TODO-6 each profile has an separate user profile
# TODO-7 admin can see user list, and also can delete users, can create test accounts.

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
    # for local env and testing
    # app.run(debug=True)
