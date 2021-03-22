# BBC But Happy

BBC But Happy is a news feed of BBC articles, but only the happy ones. The app scrapes 23 different RSS feeds, runs sentiment analysis on every article, and returns only the ones that exude positivity.

## General Overview
BBC But Happy is built in Django and uses Beautiful Soup for the web scraping, Google's Natural Language API for the sentiment analysis, and Celery for the task queue. Within the bbc_but_happy/celery.py file, you can see that Celery is scheduled to execute the scrape_bbc task every 15 minutes. This task, which can be found in the scraper/tasks.py file, is the first in a chain of tasks that scrape the RSS feeds, extract the individual articles, clean the text, run sentiment analysis on said text, and create instances of the Article model. These instances also include the information seen on the feed — title, section, pubdate, and a ~100 character preview of the article. The actual filtering of articles takes place within the bbc_but_happy/views.py file.

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python manage.py runserver
```

Please note that this cannot be run without Google Cloud credentials, which come in the form of a json file and need to be saved to the scraper folder. Secret key and database credentials have also been removed from the bbc_but_happy/settings.py file.

### Dependencies
```bash
beautifulsoup4
celery
google-cloud-language
```
