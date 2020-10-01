from django.db import models


class Post(models.Model):
    author = models.ForeignKey('user.NetworkUser', on_delete=models.CASCADE)
    posted = models.DateTimeField(auto_now_add=True)
    edited = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=255)
    text = models.TextField()
    link = models.URLField(null=True)
    likes = models.ManyToManyField('user.NetworkUser', related_name='liked_posts')
