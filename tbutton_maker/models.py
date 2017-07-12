from django.db import models

class DownloadSession(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    query_string = models.TextField()
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.CharField(max_length=255, null=True)

    def save(self, *args, **kwargs):
        super(DownloadSession, self).save(*args, **kwargs)

class Application(models.Model):
    session = models.ForeignKey(DownloadSession, related_name="applications", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

class Button(models.Model):
    session = models.ForeignKey(DownloadSession, related_name="buttons", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

class UpdateSession(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    query_string = models.TextField()
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.CharField(max_length=255, null=True)
