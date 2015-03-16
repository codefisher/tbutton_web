
import urlparse
import base64
import zipfile
import io
import hashlib
import os
import urllib
import time
import json
import tempfile

from array import array
from subprocess import Popen, PIPE

from PIL import Image

from django.db import models
from django.contrib.sites.models import Site
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.http import HttpResponse, QueryDict
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.utils.encoding import force_str
from django.core.paginator import Paginator, InvalidPage, EmptyPage

from codefisher_apps.favicon_getter.views import get_sized_icons
from mozbutton_sdk.builder.app_versions import get_app_versions
from tbutton_web.lbutton.models import LinkButtonDownload, LinkButton, LinkButtonBuild

VERSION = "1.1.0"

def index(request, template_name="lbutton/index.html"):
    data = {
        "icon_range": range(1,11),
    }
    return render(request, template_name, data)

def create(request):
    if request.method == 'POST':
        url = request.POST.get("url")
        parsed_url = urlparse.urlparse(url)
        if parsed_url[0] == "":
            url = "http://" + url
        elif parsed_url[0] not in ["http", "https", "ftp", "ftps", "javascript", "file"]:
            redirect(reverse('lbutton-custom'))
        button_id = "lbutton-%s-%s" % (hashlib.md5(url).hexdigest(), time.strftime("%y%m%d"))
        icon_type = request.POST.get("icon-type")
        icon_data = {}
        if icon_type == "default":
            icon_name = request.POST.get("default-icon")
            if not icon_name in ["www-%s" % i for i in range(1,11)]:
                icon_name = "www-1"
            for size in [16, 24, 32]:
                icon_path = os.path.join(settings.BASE_DIR, settings.DEFAULT_LINK_ICONS, '%s-%s.png' % (icon_name, size))
                if os.path.exists(icon_path):
                    with open(icon_path) as fp:
                        icon_data["icon-%s" % size] = base64.encodestring(fp.read())
        elif icon_type == "favicon":
            icons = get_sized_icons(url, [16, 24, 32])
            if icons is None:
                return redirect(reverse('lbutton-custom'))
            for size in [16, 24, 32]:
                value = io.BytesIO()
                icons[size].save(value, "png")
                icon_data["icon-%s" % size] = base64.b64encode(value.getvalue())
                value.close()
        elif icon_type == "custom":
            have = []
            for size in [16, 24, 32]:
                if "icon-%s" % size in request.FILES:
                    have.append("icon-%s" % size)
                    icon_data["icon-%s" % size] = base64.encodestring("".join(c for c in request.FILES["icon-%s" % size].chunks()))
            if len(have) == 0:
                return redirect(reverse('lbutton-custom'))
            elif len(have) != 3:
                for size in [16, 24, 32]:
                    if "icon-%s" % size not in have:
                        imagefile  = io.BytesIO("".join(c for c in request.FILES[have[-1]].chunks()))
                        im = Image.open(imagefile)
                        im = im.resize((size, size), Image.BICUBIC)
                        png = io.BytesIO()
                        im.save(png, format='PNG')
                        imagefile.close()
                        icon_data["icon-%s" % size] = base64.encodestring(png.getvalue())
        else:
            return redirect(reverse('lbutton-custom'))
        button_mode = request.POST.get("open-method", "0")
        if button_mode.isdigit():
            button_mode = int(button_mode)
        else:
            button_mode = 0
        data = {
            "icon_type": icon_type,
            "icon_name": request.POST.get("default-icon"),
            "button_id": button_id,
            "button_url": url,
            "button_mode": button_mode,
            "chrome_name": button_id,
            "extension_uuid": "%s@codefisher.org" % button_id,
            "name": force_str(request.POST.get("title")),
            "button_label": force_str(request.POST.get("label")),
            "button_tooltip": force_str(request.POST.get("tooltip")),
            "offer-download": request.POST.get("offer-download") == "true",
        }
        if "chrome" in request.POST:
            data["chrome"] = True
        data.update(icon_data)
        url_data = urllib.urlencode(data)
        key = 'lbytton-%s' % hashlib.sha1(url_data).hexdigest()
        cache.set(key, url_data, 3*60*60)
        request.session["lbutton-key"] = key
        download_session = LinkButtonDownload(query_string=request.POST.urlencode(), link=url, title=request.POST.get("label"))
        download_session.save()
        return build(request, data)
    else:
        if request.session.get("lbutton-key"):
            # this means they have already requested it, but firefox kill the request
            # because our site did not have permissions to install an addon
            # it then restarts the request, as a GET, without the POST data
            # so if we have saved data, we use it
            data = QueryDict(cache.get(request.session.get("lbutton-key")))
            del request.session['lbutton-key']
            return build(request, data)
        else:
            return redirect(reverse('lbutton-custom'))

def make(request):
    return build(request, request.GET)

def create_update_url(request, data, domain, url_name):
    update_query = QueryDict("").copy()
    update_query.update(data)
    for key in ['offer-download', 'icon-16', 'icon-24', 'icon-32']:
        if key in update_query:
            del update_query[key]
    if "chrome" in request.GET:
        return "https://%s%s?%s" % (domain, reverse(url_name), update_query.urlencode())
    app_data = {
        "item_id": "%ITEM_ID%",
        "item_version": "%ITEM_VERSION%",
        "item_maxapversion": "%ITEM_MAXAPPVERSION%",
        "app_version": "%APP_VERSION%",
    }
    extra_query = "&".join("%s=%s" % (key, value) for key, value in app_data.items())
    return "https://%s%s?%s&%s" % (domain, reverse(url_name), update_query.urlencode(), extra_query)

def build(request, input_data):
    data = dict(input_data.items())
    if 'button_mode' not in data:
        data['button_mode'] = 0
    data["version"] = VERSION
    domain = Site.objects.get_current().domain
    icon_type = data.get("icon_type", "custom")
    if icon_type != "custom":
        data["update_url"] = create_update_url(request, data, domain, "lbutton-update")
        if "icon-16" not in data:
            if icon_type == "favicon":
                icons = get_sized_icons(data["button_url"], [16, 24, 32])
                if icons is None:
                    icon_type = "default"
                else:
                    for size in [16, 24, 32]:
                        value = io.BytesIO()
                        icons[size].save(value, "png")
                        data["icon-%s" % size] = base64.b64encode(value.getvalue())
                        value.close()
            if icon_type == "default":
                icon_name = data["icon_name"]
                if not icon_name in ["www-%s" % i for i in range(1,11)]:
                    icon_name = "www-1"
                for size in [16, 24, 32]:
                    icon_path = os.path.join(settings.DEFAULT_LINK_ICONS, '%s-%s.png' % (icon_name, size))
                    if os.path.exists(icon_path):
                        with open(icon_path) as fp:
                            data["icon-%s" % size] = base64.encodestring(fp.read())
    data.update({
        "home_page": "https://%s%s" % (domain, reverse("lbutton-custom")),
        # firefox max version number
        "max_version": get_app_versions().get("{ec8030f7-c20a-464f-9b0e-13a3a9e97384}", "35.0"),
    })
    output = io.BytesIO()
    xpi = zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED)
    for name in ["icon-16", "icon-24", "icon-32"]:
        file_name = name if name != "icon-32" else "icon"
        icon_data = data[name]
        xpi.writestr("%s.png" % file_name, base64.b64decode(icon_data))
    if "chrome" in input_data:
        output = write_crx_files(data, xpi, output)
    else:
        write_xpi_files(data, xpi)
        xpi.close()
    return get_xpi_response(data.get('offer-download'), data, output, "chrome" not in  input_data)

def get_entries_for_page(paginator, page):
    try:
        page = int(page)
    except ValueError:
        page = 1
    try:
        return paginator.page(page)
    except (EmptyPage, InvalidPage) as e:
        raise e # this must be handeled
    
def buttons(request, page=1):
    entries_list = LinkButton.objects.all().order_by('featured', 'downloads')
    paginator = Paginator(entries_list, 10)
    try:
        entries = get_entries_for_page(paginator, page)
    except (EmptyPage, InvalidPage):
        if page != 1:
            return redirect(reverse("lbutton-buttons", kwargs={"page": paginator.num_pages}))
    data =  {
        "link_button": entries_list[0],
        "entries": entries,
        "title": "Link Buttons",
    }
    return render(request, 'lbutton/buttons.html' , data)

def button(request, button):
    button_obj = get_object_or_404(LinkButton, extension_id=button)
    data = {
        "button": button_obj,
        "title": button_obj.name,
    }
    return render(request, 'lbutton/button.html' , data)

def button_update(request):
    max_version = get_app_versions().get("{ec8030f7-c20a-464f-9b0e-13a3a9e97384}", "38.*")
    button = request.GET.get('button', '')
    domain = Site.objects.get_current().domain
    data = {
        "version": VERSION,
        "max_version": max_version,
        "update_url":"https://%s%s?%s" % (domain, reverse("lbutton-button-make", kwargs={"button": button}),
                request.GET.urlencode()),
        "extension_uuid": request.GET.get("extension_uuid")
    }
    if "chrome" in request.GET:
        return render(request, "lbutton/update.xml", data, content_type="application/xml")
    else:
        return render(request, "lbutton/update.rdf", data, content_type="application/xml+rdf")


def write_xpi_files(data, xpi):
    for template in ["button.css", "button.js", "button.xul", "chrome.manifest", "install.rdf", "option_window.xul", "option.xul"]:
        xpi.writestr(template, render_to_string(os.path.join("lbutton", template), data).encode("utf-8"))
    xpi.writestr(os.path.join("defaults", "preferences", "link.js"), render_to_string(os.path.join("lbutton", "preferences.js"), data).encode("utf-8"))


def build_id(pub_key_der):
    sha = hashlib.sha256(pub_key_der).hexdigest()
    prefix = sha[:32]
    reencoded = []
    ord_a = ord('a')
    for old_char in prefix:
        code = int(old_char, 16)
        new_char = chr(ord_a + code)
        reencoded.append(new_char)
    return "".join(reencoded)

def write_crx_files(data, xpi, input):
    _, pem = tempfile.mkstemp()
    Popen(["openssl", "genrsa", "-out", pem, "2048"], stdout=PIPE).stdout.read()
    xpi.write(pem, "key.pem")
    # Convert the PEM key to DER (and extract the public form) for inclusion in the CRX header
    derkey = Popen(["openssl", "rsa", "-pubout", "-inform", "PEM", "-outform", "DER", "-in", pem], stdout=PIPE).stdout.read()

    manifest = {
        "name": data["name"],
         "description": data.get("description", "A Customized Link Toolbar Button."),
         "version": VERSION,
         "icons": {
              "128": "icon.png",
              "24": "icon-24.png",
              "16": "icon-16.png",
         },
         "update_url": data["update_url"] + "&extension_uuid=" + build_id(derkey),
         "background": {
             "scripts": ["background.js"]
         },
         "permissions": [
             "tabs", "http://*/*", "https://*/*", "storage"
         ],
         "browser_action": {
             "default_title": data["button_tooltip"],
             "default_icon": "icon-16.png",
         },
         "options_page": "options.html",
         "options_ui": {
              "page": "options.html",
              "chrome_style": True,
         },
         "manifest_version": 2
    }
    for template in ["background.js", "options.js", "options.html"]:
        xpi.writestr(template, render_to_string(os.path.join("lbutton", template), data).encode("utf-8"))
    xpi.writestr("manifest.json", json.dumps(manifest, indent=4, separators=(',', ': ')))
    xpi.close()

    value = input.getvalue()
    _, input_file = tempfile.mkstemp()
    with open(input_file, "w") as fp:
        fp.write(value)
    
    # Sign the zip file with the private key in PEM format
    signature = Popen(["openssl", "sha1", "-sign", pem, input_file], stdout=PIPE).stdout.read()
    os.remove(input_file)
    os.remove(pem)
    output = io.BytesIO()
    output.write("Cr24")
    header = array("i")
    header.append(2)
    header.append(len(derkey))
    header.append(len(signature))
    output.write(header.tostring())
    output.write(derkey)
    output.write(signature)
    output.write(value)
    return output
    
def get_xpi_response(offer_download, data, output, firefox=True,):
    data["file_type"] = "xpi" if firefox else "crx"
    if offer_download or not firefox:
        response = HttpResponse(output.getvalue(), content_type="application/octet-stream")
        response['Content-Disposition'] = 'attachment; filename=%(button_id)s.%(file_type)s' % data
    else:
        content_type = "application/x-xpinstall" if firefox else "application/x-chrome-extension"
        response = HttpResponse(output.getvalue(), content_type=content_type)
        response['Content-Disposition'] = 'filename=%(button_id)s.%(file_type)s' % data
    return response

def button_make(request, button):
    button_obj = get_object_or_404(LinkButton, extension_id=button)
    LinkButton.objects.filter(pk=button_obj.pk).update(downloads=models.F('downloads') + 1)
    extension_uuid = "lbutton-%s-%s@codefisher.org" % (button_obj.extension_id, time.strftime("%y%m%d"))
    offer_download = request.GET.get("offer-download") == "true"
    domain = Site.objects.get_current().domain
    request.GET.update({"button": button})
    data = {
        "version": VERSION,
        "button_id": button_obj.chrome_name,
        "button_url": button_obj.url,
        "description": button_obj.description,
        "button_mode": int(request.GET.get("open-method", 0)),
        "chrome_name": button_obj.chrome_name,
        "extension_uuid": extension_uuid,
        "name": button_obj.name,
        "button_label": button_obj.label,
        "button_tooltip": button_obj.tooltip,
        "home_page": "https://%s%s" % (domain, reverse("lbutton-buttons")),
        "max_version": get_app_versions().get("{ec8030f7-c20a-464f-9b0e-13a3a9e97384}", "38.0"),
        "update_url": create_update_url(request, request.GET, domain, "lbutton-button-update")
    }
    output = io.BytesIO()
    xpi = zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED)
    xpi.write(button_obj.icon_16.path, "icon-16.png")
    xpi.write(button_obj.icon_24.path, "icon-24.png")
    xpi.write(button_obj.icon_32.path, "icon.png")
    if "chrome" in request.GET:
        output = write_crx_files(data, xpi, output)
    else:
        write_xpi_files(data, xpi)
        xpi.close()
    session = LinkButtonBuild(link_button=button_obj)
    session.save()
    return get_xpi_response(offer_download, data, output, "chrome" not in request.GET)
        
def update(request):
    max_version = get_app_versions().get("{ec8030f7-c20a-464f-9b0e-13a3a9e97384}", "38.*")
    domain = Site.objects.get_current().domain
    data = {
        "version": VERSION,
        "max_version": max_version,
        "update_url":"https://%s%s?%s" % (domain, reverse("lbutton-make"),
                request.GET.urlencode()),
        "extension_uuid": request.GET.get("extension_uuid")
    }
    if "chrome" in request.GET:
        return render(request, "lbutton/update.xml", data, content_type="application/xml")
    else:
        return render(request, "lbutton/update.rdf", data, content_type="application/xml+rdf")

def update_legacy(request):
    return HttpResponse('') # we deleted the data, so now we can't do more :(

@csrf_exempt
def favicons(request):
    if not request.POST.get("url"):
        return HttpResponse("fail")
    url = request.POST.get("url")
    parsed_url = urlparse.urlparse(url)
    if parsed_url[0] == "":
        url = "http://" + url
    elif parsed_url[0] not in ["http", "https", "ftp", "ftps", "javascript", "file"]:
        return HttpResponse("fail")
    sizes = (16, 24, 32)
    icons = get_sized_icons(url, sizes)
    if icons is None:
        return HttpResponse("fail")
    tags = []
    for size in sizes:
        value = io.BytesIO()
        icons[size].save(value, "png")
        data = "data:image/png;base64," + base64.b64encode(value.getvalue())
        value.close()
        tags.append('<img src="%s" width="%s" height="%s" alt="">' % (data, size, size))
    return HttpResponse("\n".join(tags))
