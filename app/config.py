import re
from .models import NewsStory
from flask import Response, render_template, url_for
import subprocess


def is_blocked_user_agent(user_agent):
    blocked_patterns = [r"BadBot", r"MaliciousCrawler", r"Scrapy", r"curl", r"Wget"]
    for pattern in blocked_patterns:
        try:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return True
        except Exception as e:
            print("Error checking pattern:", e)
            return False
    return True


def get_default_rss_feed():
    stories = NewsStory.query.order_by(NewsStory.submission_date.desc()).limit(20).all()
    rss_xml = render_template("rss_feed.xml", stories=stories)

    return rss_xml


def get_param_rss_feed(keyword):
    try:
        search_results = []
        news_templates_path = "/opt/eyes/app/templates/news"
        search_pattern = f"ls -1 {news_templates_path} | grep -E {keyword}"

        output = subprocess.check_output(
            search_pattern, shell=True, stderr=subprocess.DEVNULL
        )
        filenames = output.decode("utf-8").splitlines()
        for filename in filenames:
            story = NewsStory.query.filter_by(filename=filename).first()
            if story:
                search_results.append(story)
    except Exception as e:
        search_results = (
            NewsStory.query.order_by(NewsStory.submission_date.desc()).limit(20).all()
        )
        rss_xml = render_template("rss_feed.xml", stories=search_results)
        return rss_xml

    rss_xml = render_template("rss_feed.xml", stories=search_results)
    return rss_xml
