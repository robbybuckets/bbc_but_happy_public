from django.shortcuts import render
from django.views import generic
from django.db.models import Q

from scraper.models import Article

class BBCFeedView(generic.ListView):
    template_name = 'home.html'
    context_object_name = 'articles'
    paginate_by = 6

    # queryset for Article objects.
    # note: filtering takes place here rather than
    # through the template to keep pagination consistent
    def get_queryset(self):
        articles = Article.objects.all()
        happy_articles = articles.exclude(
                sentiment_score__lt=.2
            ).exclude(
                article_length__lt=100
            ).exclude(
                guid__contains='/sport/'
            ).exclude(
                title__icontains='scotland\'s papers'
            ).filter(
                Q(article_length__lte=800) | Q(sentiment_magnitude__gte=5)
            ).order_by(
                '-pub_date'
            )
        return happy_articles