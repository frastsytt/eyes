from flask import (
    request,
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    jsonify,
    g,
    render_template_string,
)
from . import db
from markupsafe import escape
from .auth import requires_roles
import jwt
import os
from datetime import datetime
from sqlalchemy import text
from .models import ReceivedStory, Category, WebUser, NewsStory, StoryComments
import uuid
import re
from urllib.parse import urlparse
import json

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin")
@requires_roles("admin")
def admin():
    user = session.get("user")
    email = user.get("email")
    warning = False
    if detect_mobile_browser(request.user_agent.string):
        warning = True

    user_role = g.get("user_role", None)

    existing_user = WebUser.query.filter_by(email=email).first()
    username = render_template_string(existing_user.username)
    return render_template(
        "admin.html",
        username=username,
        title="Admin",
        warning=warning,
        admin_role=user_role,
        user_email=email,
    )


@admin_bp.route("/review/stories")
@requires_roles("admin")
def review_news():
    user_role = g.get("user_role", None)
    warning = False
    if detect_mobile_browser(request.user_agent.string):
        warning = True
    user = session.get("user")
    email = user.get("email")
    stories = ReceivedStory.query.order_by(ReceivedStory.submission_date.desc()).all()

    deleted = request.args.get("deleted")
    error = request.args.get("error")

    existing_user = WebUser.query.filter_by(email=email).first()
    return render_template(
        "adm_review_news.html",
        username=existing_user.username,
        admin_role=user_role,
        title="Review",
        stories=stories,
        user_email=email,
        deleted=deleted,
        error=error,
        warning=warning,
    )


@admin_bp.route("/delete_story", methods=["POST"])
@requires_roles("admin")
def delete_story():
    user_role = g.get("user_role", None)
    warning = False
    if detect_mobile_browser(request.user_agent.string):
        warning = True

    story_id = request.form.get("story_id")
    if not story_id:
        return redirect(url_for("admin.review_news", error=1))

    story = ReceivedStory.query.get(story_id)
    if not story:
        return redirect(url_for("admin.review_news", error=1))

    db.session.delete(story)
    db.session.commit()

    return redirect(url_for("admin.review_news", deleted=1))


@admin_bp.route("/delete_news_story", methods=["POST"])
@requires_roles("admin")
def delete_news_story():
    user_role = g.get("user_role", None)
    warning = False
    if detect_mobile_browser(request.user_agent.string):
        warning = True

    story_id = request.form.get("story_id")
    if not story_id:
        return redirect(url_for("admin.view_news", error=1))

    story = NewsStory.query.get(story_id)
    if not story:
        return redirect(url_for("admin.view_news", error=1))

    db.session.delete(story)
    db.session.commit()

    return redirect(url_for("admin.view_news", deleted=1))


def detect_mobile_browser(user_agent):
    mobile_patterns = [
        r"android",
        r"iphone",
        r"ipod",
        r"blackberry",
        r"iemobile",
        r"opera mini",
        r"mobile",
        r"windows phone",
        r"windows ce",
        r"fennec",
        r"htc",
        r"kfot",
        r"tablet",
        r"kindle",
        r"playbook",
        r"opera mobi",
        r"nintendo",
        r"playstation",
        r"symbian",
        r"webos",
        r"palm",
        r"bolt",
        r"doris",
        r"hiptop",
        r"midp",
        r"treo",
        r"up\.browser",
        r"up\.link",
        r"vodafone",
        r"wap",
        r"xda",
    ]

    for pattern in mobile_patterns:
        try:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return True
        except:
            return False
    return False


@admin_bp.route("/create/approved/story/<int:story_id>", methods=["GET", "POST"])
@requires_roles("admin")
def create_approved_story_view(story_id):
    user_role = g.get("user_role", None)
    warning = False
    if detect_mobile_browser(request.user_agent.string):
        warning = True

    user = session.get("user")
    email = user.get("email")
    story = ReceivedStory.query.get(story_id)
    if not story:
        return redirect(url_for("admin.review_news"))

    existing_user = WebUser.query.filter_by(email=user.get("email")).first()
    if not existing_user:
        return render_template("404.html"), 404

    if request.method == "GET":
        return render_template(
            "adm_create_news_from_story.html",
            username=existing_user.username,
            admin_role=user_role,
            title="Create News",
            story=story,
            user_email=email,
            warning=warning,
        )

    if request.method == "POST":
        title = request.form.get("newsTitle")
        author = request.form.get("newsAuthor")
        category = request.form.get("category")
        short_description = request.form.get("newsShortDescription")
        story1 = request.form.get("newsStoryText1")
        story2 = request.form.get("newsStoryText2")
        keywords_str = request.form.get("newsKeywords", "")
        keywords_list = [kw for kw in re.split(r"[,\s]+", keywords_str.strip()) if kw]
        video = request.form.get("newsVideoUrl")
        if not is_valid_url(video):
            video = ""

        base_image_path = "/opt/eyes/app/static/images/news"

        title_image_file = request.files.get("title_image")
        unique_identifier = str(uuid.uuid4())
        title_image_filename = f"{unique_identifier}_{title_image_file.filename}"
        title_image_filepath = os.path.join(base_image_path, title_image_filename)
        title_image_file.save(title_image_filepath)

        try:
            check_image_upload = f"file {title_image_filepath}"
            if not os.path.isfile(title_image_filepath):
                raise FileNotFoundError(f"File {title_image_filepath} not found.")
        except Exception as e:
            return render_template(
                "adm_create_news_from_story.html",
                username=existing_user.username,
                admin_role=user_role,
                title="Create News",
                story=story,
                user_email=email,
                warning=warning,
                error=1,
            )

        story_image_file = request.files.get("story_image")
        unique_identifier = str(uuid.uuid4())
        story_image_filename = f"{unique_identifier}_{story_image_file.filename}"
        story_image_filepath = os.path.join(base_image_path, story_image_filename)
        story_image_file.save(story_image_filepath)

        try:
            check_image_upload = f"file {story_image_filepath}"
            if not os.path.isfile(story_image_filepath):
                raise FileNotFoundError(f"File {story_image_filepath} not found.")
        except Exception as e:
            return render_template(
                "adm_create_news_from_story.html",
                username=existing_user.username,
                admin_role=user_role,
                title="Create News",
                story=story,
                user_email=email,
                warning=warning,
                error=1,
            )

        timestamp_to_save = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        author = author
        html_content = render_template(
            "news_template.html",
            news_title=title,
            news_title_image=title_image_filename,
            news_date=timestamp_to_save,
            news_category=category,
            news_author=author,
            news_short_description=short_description,
            news_story1=story1,
            news_story_image=story_image_filename,
            news_video_url=video,
            news_story2=story2,
            news_keywords=keywords_list,
        )

        try:
            template_stories_path = "/opt/eyes/app/templates/news"
            filename = f"{title}.html"
            file_path = os.path.join(template_stories_path, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            check_image_upload = f"file {file_path}"
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"File {file_path} not found.")

            category_element = Category.query.filter_by(name=category).first()
            if not category_element:
                return render_template("404.html"), 404

            query = text(
                """
                INSERT INTO news_story 
                    (filename, title, web_user_id, submission_date, short_description, 
                    first_part, second_part, first_image, second_image, embedded_url, keywords, category_id, author)
                VALUES 
                    (:filename, :title, :web_user_id, :submission_date, :short_description,
                    :first_part, :second_part, :first_image, :second_image, :embedded_url, :keywords, :category_id, :author)
            """
            )

            params = {
                "filename": filename,
                "title": title,
                "web_user_id": existing_user.id,
                "submission_date": timestamp_to_save,
                "short_description": short_description,
                "first_part": story1,
                "second_part": story2,
                "first_image": title_image_filename,
                "second_image": story_image_filename,
                "embedded_url": video,
                "keywords": keywords_str,
                "category_id": category_element.id,
                "author": author,  # Make sure the author is passed as a parameter
            }

            db.session.execute(query, params)
            db.session.commit()

            from .mqtt_client import client

            news_payload = json.dumps(
                {
                    "filename": filename,
                    "title": title,
                    "timestamp": timestamp_to_save,
                    "short_description": short_description,
                }
            )
            notification_topic = os.getenv("MQTT_TOPIC_NOTIFICATION_SEND")
            client.publish(notification_topic, news_payload)

            db.session.delete(story)
            db.session.commit()

        except Exception as e:
            return render_template(
                "adm_create_news_from_story.html",
                username=existing_user.username,
                admin_role=user_role,
                title="Create News",
                story=story,
                user_email=email,
                warning=warning,
                error=1,
            )

        return redirect(url_for("main.view_story", filename=filename))

    return render_template("404.html"), 404


@admin_bp.route("/create/approved/story", methods=["GET", "POST"])
@requires_roles("admin")
def create_approved_story():
    user_role = g.get("user_role", None)
    warning = False
    if detect_mobile_browser(request.user_agent.string):
        warning = True

    user = session.get("user")
    email = user.get("email")

    if request.method == "POST":
        story_id = request.form.get("story_id")
        if not story_id:
            return redirect(url_for("admin.review_news", error=1))

        story = ReceivedStory.query.get(story_id)
        if not story:
            return redirect(url_for("admin.review_news", error=1))

        return redirect(url_for("admin.create_approved_story_view", story_id=story_id))

    return render_template("404.html"), 404


@admin_bp.route("/view/news")
@requires_roles("admin")
def view_news():
    user_role = g.get("user_role", None)
    user = session.get("user")
    email = user.get("email")
    warning = False
    if detect_mobile_browser(request.user_agent.string):
        warning = True

    page = request.args.get("page", 1, type=int)
    stories = NewsStory.query.order_by(NewsStory.submission_date.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template(
        "adm_view_news.html",
        admin_role=user_role,
        title="Create News",
        stories=stories,
        warning=warning,
        user_email=email,
    )


def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)


@admin_bp.route("/create/news", methods=["GET", "POST"])
@requires_roles("admin")
def new_story():
    user_role = g.get("user_role", None)
    user = session.get("user")
    email = user.get("email")

    existing_user = WebUser.query.filter_by(email=user.get("email")).first()
    if not existing_user:
        return render_template("404.html"), 404

    warning = False
    if detect_mobile_browser(request.user_agent.string):
        warning = True

    if request.method == "GET":
        return render_template(
            "adm_create_news.html",
            username=existing_user.username,
            admin_role=user_role,
            title="Create News",
            warning=warning,
            user_email=email,
        )

    if request.method == "POST":
        title = request.form.get("newsTitle")
        author = request.form.get("newsAuthor")
        category = request.form.get("category")
        short_description = request.form.get("newsShortDescription")
        story1 = request.form.get("newsStoryText1")
        story2 = request.form.get("newsStoryText2")
        keywords_str = request.form.get("newsKeywords", "")
        keywords_list = [kw for kw in re.split(r"[,\s]+", keywords_str.strip()) if kw]
        video = request.form.get("newsVideoUrl")
        if not is_valid_url(video):
            video = ""

        base_image_path = "/opt/eyes/app/static/images/news"

        title_image_file = request.files.get("title_image")
        unique_identifier = str(uuid.uuid4())
        title_image_filename = f"{unique_identifier}_{title_image_file.filename}"
        title_image_filepath = os.path.join(base_image_path, title_image_filename)
        title_image_file.save(title_image_filepath)

        try:
            check_image_upload = f"file {title_image_filepath}"
            if not os.path.isfile(title_image_filepath):
                raise FileNotFoundError(f"File {title_image_filepath} not found.")
        except Exception as e:
            return render_template(
                "adm_create_news.html",
                username=existing_user.username,
                admin_role=user_role,
                title="Create News",
                warning=warning,
                user_email=email,
                error=1,
            )

        story_image_file = request.files.get("story_image")
        unique_identifier = str(uuid.uuid4())
        story_image_filename = f"{unique_identifier}_{story_image_file.filename}"
        story_image_filepath = os.path.join(base_image_path, story_image_filename)
        story_image_file.save(story_image_filepath)

        try:
            check_image_upload = f"file {story_image_filepath}"
            if not os.path.isfile(story_image_filepath):
                raise FileNotFoundError(f"File {story_image_filepath} not found.")
        except Exception as e:
            return render_template(
                "adm_create_news.html",
                username=existing_user.username,
                admin_role=user_role,
                title="Create News",
                warning=warning,
                user_email=email,
                error=1,
            )

        timestamp_to_save = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        author = escape(author)
        html_content = render_template(
            "news_template.html",
            news_title=title,
            news_title_image=title_image_filename,
            news_date=timestamp_to_save,
            news_category=category,
            news_author=author,
            news_short_description=short_description,
            news_story1=story1,
            news_story_image=story_image_filename,
            news_video_url=video,
            news_story2=story2,
            news_keywords=keywords_list,
        )

        try:
            template_stories_path = "/opt/eyes/app/templates/news"
            filename = f"{title}.html"
            file_path = os.path.join(template_stories_path, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            check_image_upload = f"file {file_path}"
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"File {file_path} not found.")

            category_element = Category.query.filter_by(name=category).first()
            if not category_element:
                return render_template("404.html"), 404

            query = text(
                """
                INSERT INTO news_story 
                    (filename, title, web_user_id, submission_date, short_description, 
                    first_part, second_part, first_image, second_image, embedded_url, keywords, category_id, author)
                VALUES 
                    (:filename, :title, :web_user_id, :submission_date, :short_description, 
                    :first_part, :second_part, :first_image, :second_image, :embedded_url, :keywords, :category_id, :author)
            """
            )

            params = {
                "filename": filename,
                "title": title,
                "web_user_id": existing_user.id,
                "submission_date": timestamp_to_save,
                "short_description": short_description,
                "first_part": story1,
                "second_part": story2,
                "first_image": title_image_filename,
                "second_image": story_image_filename,
                "embedded_url": video,
                "keywords": keywords_str,
                "category_id": category_element.id,
                "author": author,  # Safely bind the 'author' field as a parameter
            }

            db.session.execute(query, params)
            db.session.commit()

            from .mqtt_client import client

            news_payload = json.dumps(
                {
                    "filename": filename,
                    "title": title,
                    "timestamp": timestamp_to_save,
                    "short_description": short_description,
                }
            )
            notification_topic = os.getenv("MQTT_TOPIC_NOTIFICATION_SEND")
            client.publish(notification_topic, news_payload)

        except Exception as e:
            return render_template(
                "adm_create_news.html",
                username=existing_user.username,
                admin_role=user_role,
                title="Create News",
                warning=warning,
                user_email=email,
                error=1,
            )

        return redirect(url_for("main.view_story", filename=filename))

    return render_template("404.html"), 404
