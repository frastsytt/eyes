from flask import (
    request,
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    jsonify,
    g,
    Response,
    render_template_string,
)
from markupsafe import escape
from . import db
from .auth import requires_roles
import jwt
import os
import subprocess
from datetime import datetime
from sqlalchemy import text
from .models import (
    ReceivedStory,
    NewsStory,
    StoryComments,
    WebUser,
    NewsletterSubscribers,
    Category,
)
import uuid
from .admin import detect_mobile_browser
from .config import is_blocked_user_agent, get_param_rss_feed, get_default_rss_feed


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    if session.get("token") and session.get("user"):
        token = session["token"]
        access_token_str = token.get("access_token")
        if not access_token_str:
            return redirect(url_for("main.welcome"))
        try:
            decoded_access = jwt.decode(
                access_token_str,
                options={"verify_signature": False, "verify_exp": False},
            )
        except Exception as e:
            print("Error at decoding the token.", e)
            return redirect(url_for("main.welcome"))

        resource_access = decoded_access.get("resource_access", {})

        roles = resource_access.get(os.getenv("KEYCLOAK_CLIENT_ID"), {}).get(
            "roles", []
        )

        if "admin" in roles:
            return redirect(url_for("admin.admin"))
        elif "user" in roles:
            return redirect(url_for("main.user"))
        else:
            return redirect(url_for("main.welcome"))

        return redirect(url_for("main.welcome"))
    return redirect(url_for("main.welcome"))


@main_bp.route("/welcome")
def welcome():

    if is_blocked_user_agent(request.user_agent.string):
        source_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        print(f"Warning, malicious traffic from: {source_ip}")

    return render_template("login.html", title="Login")


@main_bp.route("/search")
@requires_roles("user", "admin")
def search():
    user_role = g.get("user_role", None)
    user = session.get("user")
    if not user:
        return render_template("404.html"), 404

    email = user.get("email")
    if not email:
        return render_template("404.html"), 404

    latest_stories = (
        NewsStory.query.order_by(NewsStory.submission_date.desc()).limit(5).all()
    )

    query_param = request.args.get("query")
    search_results = []
    search_results1 = []
    search_results2 = []
    search_results3 = []

    if query_param:
        try:
            news_templates_path = "/opt/eyes/app/templates/news"
            regex_for_search_engine = (
                f"ls -1 {news_templates_path} | grep -E {query_param}"
            )

            output = subprocess.check_output(
                regex_for_search_engine, shell=True, stderr=subprocess.DEVNULL
            )
            filenames = output.decode("utf-8").splitlines()
            for filename in filenames:
                story = NewsStory.query.filter_by(filename=filename).first()
                if story:
                    search_results1.append(story)
        except Exception as e:
            search_results1 = []

        try:
            query_db = text(
                """
                SELECT *
                FROM news_story 
                INNER JOIN category ON news_story.category_id = category.id 
                WHERE category.name LIKE :query_param
            """
            )

            # Execute the query with the parameter passed as a dictionary
            search_results2 = db.session.execute(
                query_db, {"query_param": f"%{query_param}%"}
            )

            # Commit the transaction if necessary (usually not required for SELECT)
            db.session.commit()
        except Exception as e:
            search_results2 = []

        try:
            # Use bind parameter to safely pass query_param to the SQL query
            query_db = text(
                """
                SELECT *
                FROM news_story 
                WHERE keywords LIKE :query_param
            """
            )

            # Execute the query with the parameter passed as a dictionary
            search_results3 = db.session.execute(
                query_db, {"query_param": f"%{query_param}%"}
            )

            # Commit the transaction if necessary
            db.session.commit()
        except Exception as e:
            search_results3 = []

        try:
            combined_stories = search_results1 + search_results2 + search_results3

            unique_stories_dict = {}
            for story in combined_stories:
                story_id = story.id if hasattr(story, "id") else story["id"]
                unique_stories_dict[story_id] = story
            unique_stories = list(unique_stories_dict.values())

            if len(unique_stories) < 5:
                latest_three = (
                    NewsStory.query.order_by(NewsStory.submission_date.desc())
                    .limit(3)
                    .all()
                )
                existing_ids = {
                    story.id for story in unique_stories if hasattr(story, "id")
                }
                for story in latest_three:
                    if story.id not in existing_ids:
                        unique_stories.append(story)

            for s_r in unique_stories:
                if isinstance(s_r, NewsStory):
                    search_results.append(s_r)
                else:
                    new_sr = NewsStory.query.get(s_r[0])
                    if new_sr:
                        search_results.append(new_sr)

        except Exception as e:
            search_results = (
                NewsStory.query.order_by(NewsStory.submission_date.desc())
                .limit(7)
                .all()
            )

    else:
        search_results = (
            NewsStory.query.order_by(NewsStory.submission_date.desc()).limit(7).all()
        )

    new_user = WebUser.query.filter_by(email=email).first()
    return render_template(
        "search.html",
        title="Search",
        username=new_user.username,
        admin_role=user_role,
        user_email=email,
        latest_stories=latest_stories,
        search_results=search_results,
        query_param=query_param,
    )


@main_bp.route("/home")
@requires_roles("user", "admin")
def user():
    user_role = g.get("user_role", None)
    user = session.get("user")
    if not user:
        return render_template("404.html"), 404

    email = user.get("email")
    if not email:
        return render_template("404.html"), 404

    subscribed = request.args.get("subscribed")
    uploaded = request.args.get("uploaded")

    latest_politics_story = (
        NewsStory.query.join(Category)
        .filter(Category.name == "Politics")
        .order_by(NewsStory.submission_date.desc())
        .first()
    )
    latest_economy_story = (
        NewsStory.query.join(Category)
        .filter(Category.name == "Economy")
        .order_by(NewsStory.submission_date.desc())
        .first()
    )
    latest_technology_story = (
        NewsStory.query.join(Category)
        .filter(Category.name == "Technology")
        .order_by(NewsStory.submission_date.desc())
        .first()
    )

    latest_news = (
        NewsStory.query.order_by(NewsStory.submission_date.desc()).limit(4).all()
    )

    new_user = WebUser.query.filter_by(email=email).first()
    username = escape(new_user.username)
    return render_template(
        "home.html",
        title="Home",
        username=username,
        admin_role=user_role,
        user_email=email,
        uploaded=uploaded,
        subscribed=subscribed,
        politics=latest_politics_story,
        economy=latest_economy_story,
        technology=latest_technology_story,
        latest_news=latest_news,
    )


@main_bp.route("/upload", methods=["GET", "POST"])
@requires_roles("user", "admin")
def upload():
    user_role = g.get("user_role", None)
    user = session.get("user")
    if not user:
        return render_template("404.html"), 404

    email = user.get("email")
    if not email:
        return render_template("404.html"), 404

    new_user = WebUser.query.filter_by(email=email).first()

    if request.method == "GET":
        error = request.args.get("error")
        successfully = request.args.get("error")
        return render_template(
            "upload.html",
            username=new_user.username,
            admin_role=user_role,
            title="Upload",
            user_email=email,
            error=error,
            successfully=successfully,
        )

    if request.method == "POST":
        story_text = request.form.get("storyText")
        contact_info = request.form.get("contactInfo")

        try:
            timestamp_to_save = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            query = text(
                """
                INSERT INTO received_story (content, submission_date, contact_info)
                VALUES (:content, :submission_date, :contact_info)
            """
            )

            params = {
                "content": story_text,
                "submission_date": timestamp_to_save,
                "contact_info": contact_info,  # Use parameterized value for contact_info
            }

            db.session.execute(query, params)
            db.session.commit()

            story = ReceivedStory.query.filter_by(
                content=story_text,
                contact_info=contact_info,
                submission_date=timestamp_to_save,
            ).first()

            if not story:
                return render_template(
                    "upload.html",
                    username=new_user.username,
                    admin_role=user_role,
                    title="Upload",
                    user_email=email,
                    error=1,
                )

            story_id = story.id
            images = request.files.getlist("images")
            upload_base = "/opt/eyes/app/static/images/received_stories"

            for image in images:
                if image:
                    unique_identifier = str(uuid.uuid4())
                    filename = f"{unique_identifier}_{image.filename}"
                    filepath = os.path.join(upload_base, filename)

                    image.save(filepath)

                    try:
                        if not os.path.isfile(filepath):
                            raise FileNotFoundError(f"File {filepath} not found.")
                    except Exception as e:
                        continue
                    try:
                        query = text(
                            """
                            INSERT INTO received_images (story_id, filename)
                            VALUES (:story_id, :filename)
                        """
                        )

                        params = {"story_id": story_id, "filename": filename}

                        db.session.execute(query, params)
                        db.session.commit()
                    except Exception as e:
                        continue
        except Exception as e:
            return render_template(
                "upload.html",
                username=new_user.username,
                admin_role=user_role,
                title="Upload",
                user_email=email,
                error=1,
            )

        return redirect(url_for("main.user", uploaded=1))

    return render_template("404.html"), 404


@main_bp.route("/termsandconditions")
def termsandconditions():
    warning = False
    if is_blocked_user_agent(request.user_agent.string):
        warning = True
    return render_template("termsconditions.html", title="Terms&Conditions")


@main_bp.route("/story/<filename>")
@requires_roles("user", "admin")
def view_story(filename):
    user = session.get("user")
    user_role = g.get("user_role", None)
    email = user.get("email")

    latest_three_stories = (
        NewsStory.query.order_by(NewsStory.submission_date.desc()).limit(3).all()
    )
    current_story = NewsStory.query.filter_by(filename=filename).first()
    if not current_story:
        return render_template("404.html"), 404

    story_id = current_story.id

    comments = (
        StoryComments.query.filter_by(story_id=current_story.id)
        .order_by(StoryComments.timestamp.asc())
        .all()
    )

    return_comments = []
    for com in comments:
        user = WebUser.query.filter_by(id=com.web_user_id).first()
        if not user:
            continue
        author = user.username
        new_comment = {
            "timestamp": com.timestamp,
            "author": escape(user.username),
            "content": escape(com.content),
        }
        return_comments.append(new_comment)

    new_user = WebUser.query.filter_by(email=email).first()
    return render_template(
        f"news/{filename}",
        username=new_user.username,
        admin_role=user_role,
        latest_stories=latest_three_stories,
        current_story=current_story,
        comments=return_comments,
        user_email=email,
    )


@main_bp.route("/post-comment/<int:story_id>", methods=["POST"])
@requires_roles("user", "admin")
def post_comment(story_id):
    try:
        user = session.get("user")
        current_user = WebUser.query.filter_by(email=user.get("email")).first()
        comment_text = request.form.get("commentText")
        timestamp_to_save = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        story = NewsStory.query.filter_by(id=story_id).first()

        query = text(
            """
                    INSERT INTO story_comments 
                        (web_user_id, story_id, content, timestamp)
                    VALUES 
                        (:web_user_id, :story_id, :content, :timestamp)
                """
        )

        params = {
            "web_user_id": current_user.id,
            "story_id": story_id,
            "content": comment_text,
            "timestamp": timestamp_to_save,
        }

        db.session.execute(query, params)
        db.session.commit()

        return redirect(url_for("main.view_story", filename=story.filename))
    except Exception as e:
        return render_template("500.html"), 500


@main_bp.route("/subscribe", methods=["POST"])
def subscribe_newsletter():
    subscribed = False
    try:
        warning = False
        if detect_mobile_browser(request.user_agent.string):
            warning = True
        email = request.form.get("subEmail")

        if email:
            regex_email = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
            check_email_format = f"echo {email} | grep -E {regex_email}"
            try:
                result = subprocess.run(
                    ["echo", email],  # Command: echo the email
                    stdout=subprocess.PIPE,  # Capture the output
                    stderr=subprocess.PIPE,  # Capture any errors
                )

                # Check if the result matches the regex using grep's output
                grep_result = subprocess.run(
                    ["grep", "-E", regex_email],  # Command: grep with regex
                    input=result.stdout,  # Pass the output from the previous command to grep
                    stdout=subprocess.PIPE,  # Capture the output of grep
                    stderr=subprocess.PIPE,  # Capture any errors
                )
            except Exception as e:
                print("Invalid email")
                return redirect(url_for("main.user", subscribed=False))

            query = text(
                """
                SELECT * FROM newsletter_subscribers WHERE email = :email
            """
            )

            params = {"email": email}

            result = db.session.execute(query, params).fetchone()
            if not result:
                new_subscriber = NewsletterSubscribers(email=email)
                db.session.add(new_subscriber)
                subscribed = True
            db.session.commit()
            return redirect(url_for("main.user", subscribed=subscribed))
        return redirect(url_for("main.user", subscribed=subscribed))
    except Exception as e:
        return redirect(url_for("main.user", subscribed=subscribed))


@main_bp.route("/rss/feed", methods=["GET"])
def get_rss_feed():
    query_param = request.args.get("q")

    if query_param:
        xml_rss = get_param_rss_feed(query_param)
    else:
        xml_rss = get_default_rss_feed()

    return Response(xml_rss, mimetype="application/rss+xml")
