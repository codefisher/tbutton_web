
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from codefisher_apps.extension_downloads.models import ExtensionDownload
from django.db.models import F

def installed(request, mode, version):
    tbutton = get_object_or_404(ExtensionDownload, version=version, group__identifier='{03B08592-E5B4-45ff-A0BE-C1D975458688}')
    template_name = "tbutton/%s.html" % mode
    compatibility = [(settings.MOZ_APP_NAMES.get(compat.app_id), compat.min_version, compat.max_version)
                              for compat in tbutton.compatibility.all() if compat.app_id in settings.MOZ_APP_NAMES]
    compatibility.sort()
    def previous_notes(release):
        while release.previous_release and release.previous_release.release_notes:
            release = release.previous_release
            yield release
    return render(request, template_name, {"tbutton": tbutton, "previous": previous_notes(tbutton), "compatibility": compatibility})

def homepage(request):
    tbutton = ExtensionDownload.objects.select_related('group').get(group__identifier='{03B08592-E5B4-45ff-A0BE-C1D975458688}', group__latest=F('pk'))
    compatibility = [(settings.MOZ_APP_NAMES.get(compat.app_id), compat.min_version, compat.max_version)
                              for compat in tbutton.compatibility.all() if compat.app_id in settings.MOZ_APP_NAMES]
    compatibility.sort()
    return render(request, "tbutton/index.html", {"tbutton": tbutton, "compatibility": compatibility, "title": "Toolbar Buttons %s" % tbutton.version})
