from django.contrib import admin
from tbutton_web.lbutton.models import LinkButtonDownload, LinkButton, LinkButtonBuild

class DownloadSessionAdmin(admin.ModelAdmin):
    list_display = ['time', 'title', 'link']
admin.site.register(LinkButtonDownload, DownloadSessionAdmin)

class LinkButtonBuildAdmin(admin.ModelAdmin):
    list_display = ['time', 'link_button']
admin.site.register(LinkButtonBuild, LinkButtonBuildAdmin)

class LinkButtonAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'downloads']
    readonly_fields=('downloads',)
admin.site.register(LinkButton, LinkButtonAdmin)