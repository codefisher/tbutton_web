import zipfile
import io
import os

from django.contrib import admin
from tbutton_web.lbutton.models import LinkButtonDownload, LinkButton, LinkButtonBuild
from tbutton_web.lbutton.views import write_webextension_files, write_crx_files, get_version
from django.contrib.sites.models import Site
from django.urls import reverse
from django.conf import settings


def create_output(button_obj):
    output = io.BytesIO()
    xpi = zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED)
    xpi.write(button_obj.icon_16.path, "icon-16.png")
    xpi.write(button_obj.icon_24.path, "icon-24.png")
    xpi.write(button_obj.icon_32.path, "icon.png")
    return output, xpi

def create_firefox(button_obj, data):
    output, xpi = create_output(button_obj)
    result = write_webextension_files(data, xpi, output)
    if result:
        output = result
    file_name =  button_obj.extension_id + '.xpi'
    path = os.path.join(settings.MEDIA_ROOT, 'lbutton', 'firefox')
    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, file_name), 'wb') as fp:
        fp.write(output.getvalue())
    button_obj.firefox_file = file_name

def create_chrome(button_obj, data):
    output, xpi = create_output(button_obj)
    write_crx_files(data, xpi, output)
    file_name =  button_obj.extension_id + '.zip'
    path = os.path.join(settings.MEDIA_ROOT, 'lbutton', 'chrome')
    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, file_name), 'wb') as fp:
        fp.write(output.getvalue())
    button_obj.chrome_file = file_name

class DownloadSessionAdmin(admin.ModelAdmin):
    list_display = ['time', 'title', 'link']
admin.site.register(LinkButtonDownload, DownloadSessionAdmin)

class LinkButtonBuildAdmin(admin.ModelAdmin):
    list_display = ['time', 'link_button']
admin.site.register(LinkButtonBuild, LinkButtonBuildAdmin)

class LinkButtonAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'downloads']
    readonly_fields=('downloads','firefox_file', 'chrome_file', 'version')

    def save_model(self, request, button_obj, form, change):
        super(LinkButtonAdmin, self).save_model(request, button_obj, form, change)
        extension_uuid = "lbutton-{}@codefisher.org".format(button_obj.extension_id)
        domain = Site.objects.get_current().domain
        data = {
            "version": get_version(button_obj.version),
            "button_id": button_obj.chrome_name,
            "button_url": button_obj.url,
            "description": button_obj.description,
            "button_mode": int(request.GET.get("open-method", 0)),
            "chrome_name": button_obj.chrome_name,
            "extension_uuid": extension_uuid,
            "name": button_obj.name,
            "button_label": button_obj.label,
            "home_page": "https://{}{}".format(domain, reverse("lbutton-buttons")),
        }
        create_firefox(button_obj, data)
        create_chrome(button_obj, data)
        button_obj.save()

admin.site.register(LinkButton, LinkButtonAdmin)