from django.db import models

class Article(models.Model):
    guid = models.CharField(max_length=1024, unique=True)
    title = models.CharField(max_length=512)
    pub_date = models.DateTimeField(blank=True)
    section = models.CharField(max_length=256, blank=True)
    teaser = models.CharField(max_length=256, blank=True)
    source = models.CharField(max_length=512, default='', blank=True)
    article_length = models.IntegerField(default=0)
    sentiment_score = models.FloatField(default=0)
    sentiment_magnitude = models.FloatField(default=0)
    scraped_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class LatestArticles(SingletonModel):
    article_list = models.TextField(null=False, default='{ }')

    def __str__(self):
        return self.article_list