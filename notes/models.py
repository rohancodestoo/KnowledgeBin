from django.db import models
from django.contrib.auth.models import User

class Tag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=50)

    class Meta:
        unique_together = ('user', 'name')

    def __str__(self):
        return self.name

class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    image_url = models.URLField(blank=True, null=True, max_length=500)
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='notes')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_trash = models.BooleanField(default=False)

    def __str__(self):
        return self.title