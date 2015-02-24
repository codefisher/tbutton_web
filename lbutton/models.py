from django.db import models

class LinkButtonDownload(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    query_string = models.TextField()
    link = models.TextField()
    title = models.CharField(max_length=100)
    
def image_path(instance, filename):
    return ("lbutton/%s/%s" % (instance.user.pk, filename.lower()))


class LinkButton(models.Model):    
    extension_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    label = models.CharField(max_length=100)
    tooltip = models.CharField(max_length=100)
    url = models.TextField()
    chrome_name = models.CharField(max_length=100)
    
    icon_16 = models.ImageField(blank=False, null=False, upload_to=image_path)
    icon_24 = models.ImageField(blank=False, null=False, upload_to=image_path)
    icon_32 = models.ImageField(blank=False, null=False, upload_to=image_path)