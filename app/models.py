from . import db

class ReceivedStory(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    contact_info = db.Column(db.String(1024), nullable=False)
    submission_date = db.Column(db.DateTime, default=db.func.now())
    images = db.relationship('ReceivedImages', backref='story', lazy=True, cascade="all, delete-orphan")

class ReceivedImages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(1024), nullable=True)
    story_id = db.Column(db.Integer, db.ForeignKey('received_story.id'), nullable=False)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    web_user_id = db.Column(db.Integer, db.ForeignKey('web_user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    user = db.relationship('WebUser', backref=db.backref('chat_messages', lazy=True))


class WebUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(1024), nullable=False) 
    email = db.Column(db.String(1024), nullable=False)
    user_image = db.Column(db.String(1024), nullable=True)
    chat_story_comments = db.relationship('StoryComments', cascade="all, delete-orphan", backref='user', lazy=True)
    

class StoryComments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    web_user_id = db.Column(db.Integer, db.ForeignKey('web_user.id'), nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('news_story.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1024), unique=True, nullable=False)

class NewsletterSubscribers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(1024), unique=True, nullable=False)

class NewsStory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(1024), nullable=False)
    title = db.Column(db.String(1024), nullable=False)
    author = db.Column(db.String(1024))
    web_user_id = db.Column(db.Integer, db.ForeignKey('web_user.id'), nullable=False)
    submission_date = db.Column(db.DateTime, default=db.func.now())
    
    short_description = db.Column(db.Text)
    first_part = db.Column(db.Text)
    second_part = db.Column(db.Text)

    first_image = db.Column(db.String(1024))
    second_image = db.Column(db.String(1024))
    embedded_url = db.Column(db.String(1024))
    keywords = db.Column(db.String(1024))

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    category = db.relationship('Category', backref=db.backref('stories', lazy=True))
    web_user = db.relationship('WebUser', backref=db.backref('news_stories', lazy=True))
    user_story_comments = db.relationship('StoryComments', cascade="all, delete-orphan", backref='news_story', lazy=True)
    