from django.contrib import admin
from tbutton_web.lbutton.models import LinkButtonDownload, LinkButton

class DownloadSessionAdmin(admin.ModelAdmin):
    list_display = ['time', 'title', 'link']
admin.site.register(LinkButtonDownload, DownloadSessionAdmin)