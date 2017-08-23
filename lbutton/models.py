import os
from django.db import models
from django.urls import reverse
from django.conf import settings

class LinkButtonDownload(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    query_string = models.TextField()
    link = models.TextField()
    title = models.CharField(max_length=100)
    
class LinkButtonBuild(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    link_button = models.ForeignKey('LinkButton', on_delete=models.CASCADE)
    
def image_path(instance, filename):
    return ("lbutton/%s/%s" % (instance.extension_id, filename.lower()))

class LinkButton(models.Model):
    extension_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    label = models.CharField(max_length=100)
    tooltip = models.CharField(max_length=100)
    url = models.TextField()
    chrome_name = models.CharField(max_length=100)

    time = models.DateTimeField(auto_now_add=True)
    version = models.IntegerField(default=1)

    description = models.TextField(null=True, blank=True)
    downloads = models.IntegerField(default=0)
    featured = models.BooleanField(default=False)
    
    icon_16 = models.ImageField(blank=False, null=False, upload_to=image_path)
    icon_24 = models.ImageField(blank=False, null=False, upload_to=image_path)
    icon_32 = models.ImageField(blank=False, null=False, upload_to=image_path)

    firefox_path = os.path.join(settings.MEDIA_ROOT, 'lbutton', 'firefox')
    firefox_file = models.FilePathField(path=firefox_path, null=True)
    chrome_path = os.path.join(settings.MEDIA_ROOT, 'lbutton', 'chrome')
    chrome_file = models.FilePathField(path=chrome_path, null=True)
    
    def get_absolute_url(self, page=None):
        if page:
            return reverse("lbutton-buttons", kwargs={"page": page})
        return reverse("lbutton-buttons")

    def save(self, **kwargs):
        self.version += 1
        super(LinkButton, self).save(**kwargs)

    
    def __str__(self):
        return self.name