"""Blog Deployment"""
import os
import datetime
import secrets
from typing import List
from functools import wraps
from flask import Flask, redirect, render_template, url_for, flash, request, session, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
import bleach
from bleach.css_sanitizer import CSSSanitizer
from flask_bcrypt import Bcrypt
from flask_login import UserMixin, LoginManager, fresh_login_required, login_required, login_fresh, login_user, logout_user, current_user
from flask_gravatar import Gravatar
from dotenv import dotenv_values
from forms import RegiterForm, CommentForm, AddPost, LoginForm, ChangePassword


# config = {
#     **dotenv_values(".env.secrets")
# }

# app_key = config["secret_key"]


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DB_URI", "sqlite:///posts.db")

db = SQLAlchemy(app)
bt5 = Bootstrap5(app)
bcrypt = Bcrypt(app)
ckeditor = CKEditor(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.refresh_view = "login"
gravatar = Gravatar(app, size=50, rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=True,
                    use_ssl=False,
                    base_url=None)


@login_manager.user_loader
def load_user(token):
    """User loader callback"""
    return db.session.get(User, token)


def admin_only(function):
    """Admin only function"""
    @wraps(function)
    def wrapper_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return function(*args, **kwargs)
    return wrapper_function


class User(db.Model, UserMixin):
    """User Class"""

    def generate_username(self):
        """Generate and check if username exists in the database"""
        username = secrets.token_hex()
        check_username = db.session.query(
            User).filter_by(username=username).first()
        if check_username:
            while username == check_username.username:
                username = secrets.token_hex()
        self.username = username
        return self.username

    def generate_token(self):
        """Generate and check token if token exists in the database"""
        token = secrets.token_hex()
        check_token = db.session.query(User).filter_by(token=token).first()
        if check_token:
            while token == check_token.token:
                token = secrets.token_hex()
        self.token = token
        return self.token

    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(
        String, default=generate_token, unique=True, nullable=False)
    date_created: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now, nullable=False)
    date_updated: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=True)
    email: Mapped[str] = mapped_column(
        String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    username: Mapped[str] = mapped_column(
        String(250), default=generate_username, nullable=False)
    first_name: Mapped[str] = mapped_column(String(250), nullable=False)
    last_name: Mapped[str] = mapped_column(String(250), nullable=False)
    birth_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    comments: Mapped[List["Comment"]] = relationship(
        back_populates="comment_author", cascade="all, delete-orphan")
    posts: Mapped[List["BlogPost"]] = relationship(
        back_populates="uploader", cascade="all, delete-orphan")

    @hybrid_property
    def full_name(self):
        """Hybrid property full name attribute"""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<name: {self.full_name}>"


class BlogPost(db.Model):
    """Blogpost Class"""
    __tablename__ = "blog_post"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # foreign key means getting data outside this table
    uploader_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"))
    # back populate means you are getting the data from the parent table, this is child table.
    uploader: Mapped["User"] = relationship(
        back_populates="posts")
    article_author: Mapped[str] = mapped_column(String(250), nullable=False)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=True)
    date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False)
    edit_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    source_url: Mapped[str] = mapped_column(String, nullable=True)
    comments: Mapped[List["Comment"]] = relationship(
        back_populates="parent_post", cascade="all, delete-orphan")

    def to_dict(self):
        """Turn values to dict"""
        dictionary = {}
        for column in self.__table__.columns:
            dictionary[column.name] = getattr(self, column.name)
        return dictionary

    # def strip_invalid_html(self, body):
    #     """For development"""

    def __repr__(self) -> str:
        return f"<Title: {self.title}, Uploader: {self.uploader}>"


class Comment(db.Model):
    """Comments Class"""
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=True)
    date_created: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False)
    date_edited: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=True)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"))
    comment_author: Mapped["User"] = relationship(
        back_populates="comments")
    post_id: Mapped[int] = mapped_column(
        ForeignKey("blog_post.id", ondelete="CASCADE"))
    parent_post: Mapped["BlogPost"] = relationship(
        back_populates="comments")
    post_like: Mapped[List["Likes"]] = relationship(
        back_populates="parent_comment", cascade="all, delete-orphan")


class Likes(db.Model):
    """Likes table"""
    __tablename__ = "likes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comment_id: Mapped[int] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"))
    parent_comment: Mapped["Comment"] = relationship(
        back_populates="post_like")


with app.app_context():
    db.create_all()


def get_data():
    """Get all the BlogPost data from the database"""
    all_blogpost_data = db.session.query(BlogPost).order_by(BlogPost.id).all()

    # Display data in reverse, displays on 10 items.
    latest_posts = all_blogpost_data[::-1][0:10]
    return latest_posts, all_blogpost_data


def post_per_page(all_data):
    """To get how many pages are needed to display in the pagination"""
    total_posts_count = len(all_data)
    divisible = total_posts_count % 10
    if divisible == 0 and total_posts_count != 0:
        number_of_pages = int(total_posts_count/10) - 1
    else:
        number_of_pages = round(int(total_posts_count/10))
    return number_of_pages


def strip_invalid_html(content):
    """For cleaning user input"""
    css_sanitizer = CSSSanitizer(allowed_css_properties=[
                                 'color', 'height', 'width'])

    allowed_tags = ['a', 'abbr', 'acronym', 'address', 'b', 'div', 'dl', 'dt',
                    'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img',
                    'li', 'ol', 'p', 'pre', 'q', 's', 'small', 'strike',
                    'span', 'sub', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th',
                    'thead', 'tr', 'tt', 'u', 'ul', 'strong', 'wbr']

    allowed_attrs = {
        'a': ['href', 'target', 'title'],
        'img': ['src', 'alt', 'width', 'height', 'style'],
        '*': ['style']
    }

    cleaned = bleach.clean(content,
                           tags=allowed_tags,
                           attributes=allowed_attrs,
                           strip=True,
                           css_sanitizer=css_sanitizer)
    return cleaned


@app.route("/")
def index():
    """Home page of the website"""
    session["url"] = "/"
    all_data = get_data()
    posts_data = all_data[1]
    data = all_data[0]
    # For testing-------------------------------------------------
    # one_post = db.session.query(BlogPost).filter_by(id=2).first()
    # print(one_post.uploader_id, one_post.uploader.email)
    # one_user = db.session.query(User).filter_by(id=2).scalar()
    # posts = [i for i in one_user.posts]
    # print(posts)
    # -------------------------------------------------------------
    current_page = 0  # Pagination
    pages = post_per_page(posts_data)  # Pagination
    background_url = r"static/assets/img/home-bg.jpg"
    return render_template("index.html", posts=data,
                           page=pages, current_page=current_page,
                           copyRight=datetime.datetime.now().strftime("%Y"),
                           today=datetime.datetime.now().strftime("%B %d, %Y"),
                           bg=background_url)


@app.route("/signup", methods=["POST", "GET"])
def signup():
    """Signup page"""
    bg = r"/static/home-bg-copy.jpg"
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegiterForm()
    if request.method == "POST":
        if form.validate_on_submit():
            check = db.session.query(User).filter_by(
                email=form.email.data).first()
            if check is None:
                new_user = User(
                    first_name=form.first_name.data.strip().capitalize(),
                    last_name=form.last_name.data.strip().capitalize(),
                    birth_date=form.birth_date.data,
                    email=form.email.data.strip(),
                    password=bcrypt.generate_password_hash(
                        form.password.data.strip()).decode("utf-8"),
                    # token=User.generate_token(),
                    # username=User.generate_username()
                )
                db.session.add(new_user)
                db.session.commit()
                login_user(user=new_user, remember=True)
                # if current_user.is_authenticated:
                #     print(current_user.name)
                return redirect(url_for("index"))
            else:
                flash("Email already exists")
                return redirect(url_for("login"))
        flash("Incomplete Entry")
    return render_template("signup.html", form=form, bg=bg,
                           copyRight=datetime.datetime.now().strftime("%Y"))


@app.route('/login', methods=["POST", "GET"])
def login():
    """Log in to account"""
    bg = r"/static/home-bg-copy.jpg"
    if login_fresh():
        return redirect(url_for('index'))
    login_form = LoginForm()
    if request.method == "POST":
        if login_form.validate_on_submit():
            user_check = db.session.query(User).filter_by(
                email=login_form.email.data).first()
            if user_check:
                if bcrypt.check_password_hash(user_check.password, login_form.password.data):
                    login_user(user=user_check, remember=True)
                    # Gets the input value of #next_url in the "login.html" for the code below.
                    next_url = request.form.get("next")
                    if not next_url:
                        next_url = session["url"]
                    # Using the code above, the url is redirected to next or secret.
                    # This is implemented to directly redirect the user
                    # to desired endpoint that needs fresh login.
                    return redirect(next_url or url_for("index"))
                flash("Invalid Username or Password")
            else:
                flash("Email not found, create an account to log in.")
                return redirect(url_for("signup"))
    return render_template("login.html", form=login_form, bg=bg,
                           copyRight=datetime.datetime.now().strftime("%Y"))


@app.route("/posts/<int:page>", methods=["POST", "GET"])
def posts(page):
    """Posts Page"""
    session["url"] = f"posts/{page}"
    bg_url = r"/static/home-bg-copy.jpg"
    all_data = get_data()
    total_posts = all_data[1]
    if len(total_posts) > 10:
        # For displaying the data in reverse, displays 10 items only.
        data = total_posts[0:-10*page][::-1][:10]

        pages = post_per_page(total_posts)  # Pagination

        return render_template("index.html", posts=data,
                               copyRight=datetime.datetime.now().strftime("%Y"),
                               bg=bg_url, page=pages, current_page=page,
                               today=datetime.datetime.now().strftime("%B %d, %Y"))
    return redirect(url_for("index"))


@app.route("/new-post", methods=["POST", "GET"])
@fresh_login_required
def new_post():
    """Add New Post Page"""
    message = "New Post"
    background_url = r"/static/home-bg-copy.jpg"
    new_post_form = AddPost()
    if new_post_form.validate_on_submit():
        # uploader = db.session.query(User).filter_by(id=current_user.id).first()
        new_blog_post = BlogPost(
            uploader_id=current_user.id,
            title=new_post_form.blog_title.data,
            subtitle=new_post_form.blog_subtitle.data,
            date=datetime.datetime.now(),
            article_author=new_post_form.blog_author.data,
            img_url=new_post_form.blog_img_url.data,  # update this to also upload an image
            source_url=new_post_form.source_link.data,
            body=strip_invalid_html(new_post_form.blog_content.data)
        )
        db.session.add(new_blog_post)
        db.session.commit()
        # The commentted code below is for redirecting
        # to the current user's latest post, not yet working.
        # latest_post=db.session.query(BlogPost).filter_by(uploader_id=current_user.id).order_by(BlogPost.id).first()
        # print(latest_post.id)
        return redirect(url_for("index"))
    return render_template("new_post.html", form=new_post_form,
                           message=message, bg=background_url,
                           copyRight=datetime.datetime.now().strftime("%Y"))


@app.route("/post/<int:number>", methods=["GET", "POST"])
def get_post(number):
    """Get individual post"""
    session["url"] = f"post/{number}"
    data = db.session.get(BlogPost, number)
    if data is not None:
        comment_form = CommentForm()
        if request.method == "POST":
            if current_user.is_authenticated:
                if comment_form.validate_on_submit():
                    new_comment = Comment(
                        text=strip_invalid_html(comment_form.text.data),
                        author_id=current_user.id,
                        post_id=data.id,
                        date_created=datetime.datetime.now()
                        # Create a route for editing the comment that is a copy of this route.
                    )
                    db.session.add(new_comment)
                    db.session.commit()
                    return redirect(url_for("get_post", number=number))
                return redirect(url_for("get_post", number=number))
            flash("Log in to post comment")
            return redirect(url_for("login", next=f"post/{number}"))
        next_post = [idx.id for idx in get_data()[1]]
        background_url = data.img_url
        return render_template("post.html", post=data, bg=background_url,
                               next_item=next_post, form=comment_form,
                               copyRight=datetime.datetime.now().strftime("%Y"))
    return redirect(url_for("index"))


@app.route("/edit-post/<int:number>", methods=["POST", "GET"])
@fresh_login_required
def edit_post(number):
    """Edit a post"""
    message = "Edit Post"
    data = db.session.get(BlogPost, number)
    background_url = data.img_url
    edit_post_form = AddPost(
        blog_title=data.title,
        blog_subtitle=data.subtitle,
        blog_author=data.article_author,
        blog_img_url=data.img_url,
        source_link=data.source_url,
        blog_content=data.body
    )
    if number:
        state = True
    if request.method == "POST" and edit_post_form.validate_on_submit():
        data.title = edit_post_form.blog_title.data
        data.subtitle = edit_post_form.blog_subtitle.data
        data.article_author = edit_post_form.blog_author.data
        data.img_url = edit_post_form.blog_img_url.data
        data.body = strip_invalid_html(edit_post_form.blog_content.data)
        data.edit_date = datetime.datetime.now()
        data.source_url = edit_post_form.source_link.data
        db.session.commit()
        return redirect(url_for("get_post", number=number))
    return render_template("new_post.html", form=edit_post_form,
                           message=message, bg=background_url,
                           state=state, number=number, copyRight=datetime.datetime.now().strftime("%Y"))


@app.route('/delete-post/<int:number>', methods=["GET"])
@fresh_login_required
def delete_post(number):
    """Delete page"""
    post = db.session.get(BlogPost, number)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("index"))


@app.route('/delete-comment/<int:number>')
@fresh_login_required
def delete_comment(number):
    """For Deleting comment"""
    pass


@app.route('/form-entry', methods=["POST", "GET"])
@login_required
def form_entry():
    """Form entry"""
    session["url"] = f"/{request.endpoint}"
    background_url = r"static/assets/img/contact-bg.jpg"
    if request.method == "POST":
        name = current_user.name
        email = current_user.email
        message = request.form["message"]
        phone_number = request.form.get("phoneNumber")

        body = f"""Name:{name}\nEmail:{email}\nPhone number:{phone_number}\nMessage:{message}."""
        print(body)
        response = "Your message is sent."
        return render_template("contact.html", message=response,
                               bg=background_url, copyRight=datetime.datetime.now().strftime("%Y"))
    return redirect("contact")


@app.route("/logout")
@login_required
def logout():
    """Log out user"""
    logout_user()
    return redirect(session["url"] or url_for("index"))


@app.route('/aboutme')
def aboutme():
    """About me page"""
    session["url"] = f"/{request.endpoint}"
    print(session["url"])
    background_url = r"static/assets/img/about-bg.jpg"
    return render_template("aboutme.html", bg=background_url, copyRight=datetime.datetime.now().strftime("%Y"))


@app.route("/new-password", methods=["POST", "GET"])
@fresh_login_required
def new_password():
    """Changing the password function"""
    session["url"] = f"/{request.endpoint}"
    change_form = ChangePassword()
    if request.method == "POST" and change_form.validate_on_submit():
        user = db.session.query(User).filter_by(id=current_user.id).first()
        if user and bcrypt.check_password_hash(user.password, change_form.current_password.data):
            user.password = bcrypt.generate_password_hash(
                change_form.new_password.data.strip(), 10).decode("utf-8")
            user.token = secrets.token_hex()
            user.date_updated = datetime.datetime.now()
            db.session.commit()
            return redirect(url_for('index'))
        flash("Incorrect Current Password")
    if change_form.errors:
        for error, message in change_form.errors.items():
            flash(message[0])
    return render_template("new_password.html", form=change_form,
                           copyRight=datetime.datetime.now().strftime("%Y"))


@app.route("/new-username/<username>", methods=["POST", "GET"])
@fresh_login_required
def change_username(username):
    """Route for changing username"""
    # if current_user.is_authenticated and current_user.username == username:
    if current_user.is_authenticated:
        user = db.session.query(User).filter_by(id=current_user.id).first()
        user.username = username
        db.session.commit()
        # print(user.id)
        # print(current_user.id)
    return redirect(url_for("index"))


@app.route("/delete-account")
@fresh_login_required
def delete_account():
    """Delete the current user's account in the database"""
    remove = db.session.get(User, current_user.id)
    db.session.delete(remove)
    db.session.commit()
    return redirect(url_for("index"))


@app.route('/contact')
@login_required
def contact():
    """Contact page"""
    session["url"] = f"/{request.endpoint}"
    background_url = r"static/assets/img/contact-bg.jpg"
    message = "Contact Me"
    return render_template("contact.html", bg=background_url,
                           message=message, copyRight=datetime.datetime.now().strftime("%Y"))


@app.route("/secrets")
@admin_only
def secret():
    """Route for the admin to accesc the database"""
    # TODO: Create a database access for the admin account.
    return "Welcome to Secrets"


@app.errorhandler(404)
def page_not_found(error):
    """For displaying error page"""
    bg = r"/static/home-bg-copy.jpg"
    return render_template("error_page.html", error=error, bg=bg,
                           copyRight=datetime.datetime.now().strftime("%Y")), 404


if __name__ == "__main__":
    app.run(debug=False)
