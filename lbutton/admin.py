from django.contrib import admin
from tbutton_web.lbutton.models import LinkButtonDownload, LinkButton

class DownloadSessionAdmin(admin.ModelAdmin):
    list_display = ['time', 'title', 'link']
admin.site.register(LinkButtonDownload, DownloadSessionAdmin)

class LinkButtonAdmin(admin.ModelAdmin):
    list_display = ['name', 'url']
    readonly_fields=('downloads',)
admin.site.register(LinkButton, LinkButtonAdmin)