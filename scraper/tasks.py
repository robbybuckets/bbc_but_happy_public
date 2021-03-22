# tasks
from __future__ import absolute_import, unicode_literals
from celery import Celery
from celery import app, shared_task


# scraping
import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
from django.utils.timezone import make_aware
from .models import Article, LatestArticles

# sentiment analysis
from .sentiment import analyze_text_sentiment

# TASKS
# Note: tasks are organized alphabetically below, but to 
# understand the workflow, start reading from scrape_bbc()

# BBC feeds
bbc_rss_feeds = [
    'http://feeds.bbci.co.uk/news/world/africa/rss.xml',
    'http://feeds.bbci.co.uk/news/world/asia/rss.xml',
    'http://feeds.bbci.co.uk/news/world/europe/rss.xml',
    'http://feeds.bbci.co.uk/news/world/latin_america/rss.xml',
    'http://feeds.bbci.co.uk/news/world/middle_east/rss.xml',
    'http://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml',
    'http://feeds.bbci.co.uk/news/england/rss.xml',
    'http://feeds.bbci.co.uk/news/northern_ireland/rss.xml',
    'http://feeds.bbci.co.uk/news/scotland/rss.xml',
    'http://feeds.bbci.co.uk/news/wales/rss.xml',
    'http://feeds.bbci.co.uk/news/video_and_audio/world/rss.xml',
    'http://feeds.bbci.co.uk/news/video_and_audio/uk/rss.xml',
    'http://feeds.bbci.co.uk/news/video_and_audio/business/rss.xml',
    'http://feeds.bbci.co.uk/news/video_and_audio/politics/rss.xml',
    'http://feeds.bbci.co.uk/news/video_and_audio/health/rss.xml',
    'http://feeds.bbci.co.uk/news/video_and_audio/science_and_environment/rss.xml',
    'http://feeds.bbci.co.uk/news/video_and_audio/technology/rss.xml',
    'http://feeds.bbci.co.uk/news/video_and_audio/entertainment_and_arts/rss.xml',
    'http://feeds.bbci.co.uk/news/stories/rss.xml',
    'http://feeds.bbci.co.uk/news/also_in_the_news/rss.xml',
    'http://feeds.bbci.co.uk/news/in_pictures/rss.xml',
    'http://feeds.bbci.co.uk/news/special_reports/rss.xml',
    'http://feeds.bbci.co.uk/news/have_your_say/rss.xml',
]

bbc_sections = [
    'Africa', 'Asia', 'Europe', 'Latin America', 'Middle East', 
    'US and Canada', 'England', 'Northern Ireland', 'Scotland', 
    'Wales', 'World', 'UK', 'Business', 'Politics', 'Health', 
    'Science and Environment', 'Technology', 'Entertainment and Arts', 
    'Stories', 'Also in the News', 'In Pictures', 
    'Special Reports', 'Have Your Say'
]

# analyze article
@shared_task
def analyze_article(article):
    html = requests.get(article)
    html.encoding = 'utf-8'
    soup = BeautifulSoup(html.text, 'html.parser')
    try:
        article = soup.find('article').find_all('p')
        article_text = ''
        for i in range(len(article)):
            paragraph = article[i].text
            if i <= 1 and len(paragraph) < 60 and paragraph.startswith('By'):
                continue
            elif 'Last updated on' in paragraph or \
                'From the section' in paragraph or \
                'click here' in paragraph.lower() or \
                'reporter' in paragraph.lower() and ':' in paragraph.lower() or \
                'editor' in paragraph.lower() and ':' in paragraph.lower() or \
                'all photographs subject to copyright' in paragraph.lower() or \
                'follow newsbeat on' in paragraph.lower() or \
                'you can follow' in paragraph.lower() and ('twitter' in paragraph.lower() or 'instagram' in paragraph.lower()):
                    continue
            article_text += (paragraph + ' ')
        article_text = clean_up_text(article_text)
        try:
            article_length = len(article_text)
            sentiment = analyze_text_sentiment(article_text)
            try:
                if sentiment.score < .1:
                    teaser = ''
                else:
                    teaser = create_teaser(article_text)
            except Exception as e:
                print('Failed to create teaser. See exception below.')
                print(e)
            article_data = {
                'teaser': teaser,
                'article_length': article_length,
                'sentiment_score': sentiment.score,
                'sentiment_magnitude': sentiment.magnitude
            }
            return article_data
        except Exception as e:
            print('Failed to analyze sentiment. See exception below.')
            print(e)
    except Exception as e:
        print("Could not create article text. See exception below.")
        print(e)

# remove emojis, links,  and double spaces from text
@shared_task
def clean_up_text(text):
    regrex_pattern = re.compile(pattern = "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                        "]+", flags = re.UNICODE)
    text = regrex_pattern.sub(r'',text)
    text = re.sub(r'http\S+|pic.t\S+|twitter.\S+|@\S+', '', text)
    text = ' '.join(text.split())
    return text

# create article teaser to be displayed on feed
@shared_task
def create_teaser(article_text):
    teaser = article_text[:225]
    ending_index = 225
    for i in range(len(teaser)):
        if teaser[-i] == ' ':
            ending_index = -i
            break
    teaser = teaser[:ending_index] + ' ...'
    return teaser

# filter out latest articles
@shared_task
def filter_latest_articles(article_list):
    try:
        latest_articles_obj = LatestArticles.load()
        jsonDec = json.decoder.JSONDecoder()
        latest_articles = jsonDec.decode(latest_articles_obj.article_list)
        latest_articles_update = []
        potential_new_articles = []

        for article in article_list:
            try:
                latest_articles_update.append(article['guid'])
                if article['guid'] not in latest_articles:
                    potential_new_articles.append(article)
            except Exception as e:
                print('Failed to search or append article')
                print(e)
        
        # update latest_articles with most recent scrape
        latest_articles_update = json.dumps(latest_articles_update)
        latest_articles_obj.article_list = latest_articles_update
        latest_articles_obj.save()

        return query_db_and_analyze(potential_new_articles)

    except Exception as e:
        print('Failed to filter latest articles. See exception below.')
        print(e)

# save function
@shared_task(serializer='json')
def save(new_articles):
    for article in new_articles:
        try:
            source_index = bbc_rss_feeds.index(article['source'])
            article_section = bbc_sections[source_index]
            Article.objects.create(
                guid = article['guid'],
                title = article['title'],
                pub_date = article['pub_date'],
                section = article_section,
                teaser = article['teaser'],
                source = article['source'],
                article_length = article['article_length'],
                sentiment_score = article['sentiment_score'],
                sentiment_magnitude = article['sentiment_magnitude']
            )
        except Exception as e:
            print('Failed to save object. See exception below.')
            print(e)

# scrape articles from bbc
@shared_task
def scrape_bbc():
    article_list = []

    for rss_feed in bbc_rss_feeds:
        try:
            source = rss_feed
            html = requests.get(source)
            soup = BeautifulSoup(html.text, 'html.parser')
            articles = soup.find_all('item')
            for i in articles:
                try:
                    guid = i.find('guid').text
                    title = i.find('title').text
                    pub_date_str = i.find('pubdate').text
                    pub_date_naive = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %Z')
                    pub_date = make_aware(pub_date_naive)

                    # if not in database...
                        # run sentiment analysis
                        # add to database
                    article = {
                        'guid': guid,
                        'title': title,
                        'pub_date': pub_date,
                        'source': source
                    }
                    article_list.append(article)
                except Exception as e:
                    print('Failed to scrape feed.')
                    print(e)
        except Exception as e:
            print('Failed to scrape feed.')
            print(e)

    return filter_latest_articles(article_list)


@shared_task
def query_db_and_analyze(potential_new_articles):
    if potential_new_articles:
        new_articles = []
        for article in potential_new_articles:
            try:
                already_in_database = Article.objects.filter(guid=article['guid']).exists()
                if not already_in_database:
                    article_url = article['guid']
                    article_data = analyze_article(article_url)
                    article.update(article_data)
                    new_articles.append(article)
            except Exception as e:
                print('DB query and/or sentiment analysis failed. See exception below.')
                print(e)
        return save(new_articles)
    else:
        print('No new articles to analyze')

# Run locally with below command:
# celery -A bbc_but_happy worker -B -l INFO