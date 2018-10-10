import codecs
import os
import re
import io
import datetime
import hashlib
import json
import itertools
from collections import Counter, namedtuple

from django.contrib.sites.models import Site
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse, Http404, QueryDict
from django.urls import reverse
from django.db.models import Count
from django.utils.html import escape
from django.contrib import messages
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.views.decorators.csrf import csrf_exempt

from mozbutton_sdk.config.settings import config
from mozbutton_sdk.builder import button, locales, util, build
from mozbutton_sdk.builder.util import extra_update_prams
from tbutton_web.tbutton_maker.models import Application, Button, DownloadSession, UpdateSession
from codefisher_apps.extension_downloads.models import ExtensionDownload
from codefisher_apps.downloads.models import DownloadGroup

SETTINGS = dict(config)
util.apply_settings_files(SETTINGS, settings.TBUTTON_CONFIG)

ButtonDataTuple = namedtuple(
    'ButtonData', ['button_id', 'apps', 'label', 'tooltip',
                   'icons', 'description', 'folder', 'button_apps'])

class ButtonData(ButtonDataTuple):

    def is_legacy(self):
        return BUTTONS.is_legacy(self.button_id)

    def amo_page(self):
        return BUTTONS.amo_page(self.button_id)

LocaleData = namedtuple(
    'LocaleData', ['locale_code', 'name', 'native_name', 'country'])

class WebButton(button.SimpleButton):
    def __init__(self, folders, buttons, settings, applications):
        button.SimpleButton.__init__(self, folders, buttons, settings, applications)
        self._description = {}
        self._source_folder = {}
        self.hidden_buttons = {}


        for folder in folders:
            head, button_id = os.path.split(folder)
            self._source_folder[button_id] = os.path.split(head)[1]

        for folder, button_id, files in self._info:
            if "description" in files:
                with open(os.path.join(folder, "description"), "r") as fp:
                    description = fp.read().strip()
                    self._description[button_id] = description
                    if not description:
                        print("Button {} lacks description".format(button_id))
            if "hidden" in files:
                with open(os.path.join(folder, "hidden"), "r") as fp:
                    self.hidden_buttons[button_id] = fp.read().strip()
              
    def get_source_folder(self, button):
        return self._source_folder[button] 

    def description(self, button):
        if button in self._manifests and "description" in self._manifests.get(button):
            return self._manifests.get(button).get("description")
        return self._description.get(button)
    
def get_buttons_obj(extension_settings, applications="all", buttons_ids="all"):
    button_folders, buttons = util.get_button_folders(buttons_ids, extension_settings)
    for name in extension_settings.get("projects"):
        staging_button_folders, staging_buttons = util.get_button_folders(buttons_ids, extension_settings, name)
        button_folders.extend(staging_button_folders)
        buttons.extend(staging_buttons)
    return WebButton(button_folders, buttons, extension_settings, applications)
    
def create_locales():
    locale_folder, locale = util.get_locale_folders("all", SETTINGS)
    return locales.Locale(SETTINGS, locale_folder, locale)

def single_configs():
    result = {}
    path = os.path.join(SETTINGS.get('project_root'), 'configs')
    for file_name in os.listdir(path):
        with codecs.open(os.path.join(path, file_name), encoding='utf-8') as fp:
            try:
                ext_config = json.load(fp)
                if ext_config.get('amo_page'):
                    result[ext_config.get('chrome_name')] = ext_config
            except ValueError:
                pass # corrupt json file
    return result

LOCALE = create_locales()
BUTTONS = get_buttons_obj(SETTINGS)

def locale_str_getter(locale_name):
    return BUTTONS.locale_string(button_locale=LOCALE, locale_name=locale_name)

def list_buttons(request, locale_name=None,
                 applications=None, template_name='tbutton_maker/list.html'):
    data = index(request, locale_name=locale_name, applications=applications,
                 template_name=None)
    return render(request, template_name, data)

def button_key(item):
    return item[2].lower() if item[2] else ""

def get_local_data():
    locale_meta = LOCALE
    local_data = []
    for locale_code in locale_meta.locales:
        data = LocaleData(
            locale_code=locale_code,
            name=locale_meta.get_dtd_value(locale_code, 'name'),
            native_name=locale_meta.get_dtd_value(locale_code, 'native_name'),
            country=locale_meta.get_dtd_value(locale_code, 'country')
        )
        local_data.append(data)
    local_data.sort(key=button_key)
    return local_data

def get_applications(request, applications=None):
    if applications is None:
        applications = request.GET.getlist('button-application')
    else:
        if ',' in applications:
            applications = applications.split(",")
        else:
            applications = applications.split("-")
    default_apps = set(SETTINGS["applications_data"].keys())
    applications = default_apps.intersection(applications)
    if not applications:
        applications = list(default_apps)
    return applications

def get_locale_name(request, locale_name=None):
    if locale_name is None:
        locale_name = request.GET.get('button-locale')
    if locale_name not in LOCALE.locales:
        locale_name = SETTINGS.get("default_locale")
    return locale_name

def lazy_button_list(applications, locale_str):
    applications = set(applications)
    def _func():
        button_data = []
        for button_id, apps in BUTTONS.button_applications().items():
            button_apps = applications.intersection(apps)
            if button_apps and button_id not in BUTTONS.hidden_buttons:
                # TODO: we don't know if the tooltip or label has entities escaped or not.
                label = locale_str("label", button_id)
                tooltip = locale_str("tooltip", button_id) or label
                button = ButtonData(
                    button_id=button_id,
                    apps=sorted(apps),
                    label=label,
                    tooltip=tooltip,
                    icons=BUTTONS.get_icons(button_id),
                    description=BUTTONS.description(button_id),
                    folder=BUTTONS.get_source_folder(button_id),
                    button_apps=button_apps
                )
                button_data.append(button)
        button_data.sort(key=button_key)
        return button_data
    return _func

def index(request, locale_name=None, applications='browser',
          template_name='tbutton_maker/index.html'):
    locale_name = get_locale_name(request, locale_name)
    applications = get_applications(request, applications)
    locale_str = locale_str_getter(locale_name)
    button_data = lazy_button_list(applications, locale_str)
    local_data = get_local_data()
    application_data = SETTINGS.get("applications_data")
    application_names = {key: [item[0] for item in value]
                         for key, value in application_data.items()}
    data = {
        "locale": locale_name,
        "all_applications": sorted(application_data.keys()),
        "applications": applications,
        "button_data": button_data,
        "buttons": request.GET.getlist('button'),
        "application_names": application_names,
        "local_data": local_data,
        "default_icons": settings.TBUTTON_DEFAULT_ICONS,
        "add_to_toolbar": request.GET.get('add-to-toolbar'),
        "offer_download": request.GET.get('offer-download'),
        "create_toolbars": request.GET.get('create-toolbars'),
        "channel": request.GET.get('channel', 'stable'),
        "create_menu": request.GET.get('create-menu'),
        "custom_button": 'custom_button' in request.GET,
        "icon_size": request.GET.get('icon-size', 'standard'),
    }
    if template_name is None:
        return data
    data["button_data"] = (button for button in data["button_data"]() if button.folder != "webext")
    return render(request, template_name, data)

def webextensions(request):
    data = index(request, locale_name=None, applications='browser',
          template_name=None)
    data["button_data"] = (button for button in data["button_data"]() if button.amo_page())
    data["webextension"] = True
    return render(request, 'tbutton_maker/web_ext.html', data)

def buttons_page(request, button_id, locale_name=None):
    if button_id not in BUTTONS:
        raise Http404
    #try:
    locale_name = get_locale_name(request, locale_name)
    locale_str = locale_str_getter(locale_name)
    file_to_name = [(file_name, name)
                    for file_name, name in SETTINGS.get("file_to_name").items()
                    if file_name in BUTTONS.button_windows[button_id]]
    file_to_name.sort(key=lambda item: item[1].lower() if item[1] else None)
    local_data = get_local_data()
    
    days = 30
    time = datetime.datetime.now() - datetime.timedelta(days)
    inner_qs = Button.objects.filter(
        name__in=[button_id], session__time__gt=time).values('session')
    results = Button.objects.filter(
        session__in=inner_qs).exclude(name__in=[button_id])
    stats = list(results.values('name').annotate(
        downloads=Count('name')).order_by("-downloads"))[0:5]
    for stat in stats:
        stat.update({
            "label": locale_str("label", stat["name"]),
            "tooltip": locale_str("tooltip", stat["name"]),
            "icon": BUTTONS.get_icons(stat["name"]),
        })
    application_data = SETTINGS.get("applications_data")
    application_names = {key: [item[0] for item in value]
                         for key, value in application_data.items()}
    data = {
        "button": button_id,
        "apps": sorted(list(BUTTONS.button_applications()[button_id])),
        "label": locale_str("label", button_id),
        "tooltip": locale_str("tooltip", button_id),
        "icon": BUTTONS.get_icons(button_id),
        "legacy": BUTTONS.is_legacy(button_id),
        "amo_page": BUTTONS.amo_page(button_id),
        "amo_download": BUTTONS.download_url(button_id),
        "description": BUTTONS.description(button_id),
        "folder": BUTTONS.get_source_folder(button_id),
        "local_data": local_data,
        "locale": locale_name,
        "file_to_name": file_to_name,
        "related": stats,
        "application_names": application_names,
    }
    #except:
    #    raise Http404
    return render(request, "tbutton_maker/button.html", data)

def create_buttons(request, query, log_creation=True):
    buttons = migrate_buttons(query.getlist("button"))
    locale = query.get("button-locale", "all")

    extension_settings = dict(SETTINGS)
    extension_settings["buttons"] = buttons

    if not locale or query.get("include-all-locales") == "true":
        locale = "all"
        
    extension_settings["fix_meta"] = True
     
    if query.get("create-toolbars") == "true":
        if not query.get("add-to-toolbar") == "true":
            extension_settings["put_button_on_toolbar"] = True
        extension_settings["include_toolbars"] = -1
    else:
        extension_settings["include_toolbars"] = 0

    if query.get("create-menu") == "true":
        extension_settings["menuitems"] = "all"
        if len(buttons) == 1:
            extension_settings["menu_placement"] = "tools"

    extension_settings["locale"] = "all" # always include everything
    applications = get_applications(request)
    extension_settings["applications"] = applications
    update_query = query.copy()
    update_query.setlist('button-application', applications)
    update_query.setlist('button', buttons)
    update_query["locale"] = locale
    allowed_options = {
        "button-application", "locale", "button", "create-menu",
        "create-toolbars", "icon-size", "channel"}
    remove_keys = []
    for key in update_query.keys():
        if key not in allowed_options:
            remove_keys.append(key) # can't modify the keys inside the loop
    for key in remove_keys:
        del update_query[key]
    extra_query = extra_update_prams()
    icons_size = settings.TBUTTON_ICON_SET_SIZES.get(
        settings.TBUTTON_DEFAULT_ICONS).get(query.get("icon-size"))
    if icons_size:
        extension_settings["icon_size"] = icons_size
    button_hash = hashlib.md5("_".join(sorted(buttons)).encode('utf-8')).hexdigest()
    chrome_name = "toolbar-button-" + button_hash[0:10]
    extension_settings["chrome_name"] = chrome_name
    extension_settings["extension_id"] = button_hash + "@button.codefisher.org"
    '''update_url = "https://{domain}{path}?{query}&amp;{extra_query}"
    extension_settings["update_url"] = update_url.format(
        domain=Site.objects.get_current().domain,
        path=reverse("tbutton-update"),
        query=escape(update_query.urlencode()),
        extra_query=escape(extra_query)
    )'''
    if query.get("add-to-toolbar") == "true":
        extension_settings["add_to_main_toolbar"] = buttons
        current_version_pref = "current.version." + chrome_name
        extension_settings["current_version_pref"] = current_version_pref
    output = io.BytesIO()
    try:
        buttons_obj = build.build_extension(
            extension_settings, output=output, button_locales=LOCALE)
    except build.ExtensionConfigError as e:
        messages.add_message(request, messages.ERROR, e)
        url = "".join((reverse("tbutton-custom", kwargs={}),
                       "?", query.urlencode()))
        return redirect(url)
    content_type = 'application/x-xpinstall'
    disposition = 'filename={}'
    if (query.get('offer-download') == 'true'
            or ('browser' not in applications and 'suite' not in applications)):
        content_type = 'application/octet-stream'
        disposition = 'attachment; filename={}'
    response = HttpResponse(output.getvalue(), content_type=content_type)
    output.close()
    file_name = extension_settings.get('output_file') % extension_settings
    response['Content-Disposition'] = disposition.format(file_name)
    
    if log_creation:
        session = DownloadSession()
        session.query_string = query.urlencode()
        session.ip_address = get_client_ip(request)
        session.user_agent = request.META.get("HTTP_USER_AGENT", "")[0:250]
        session.save()
        for button_record in buttons_obj.buttons():
            Button.objects.create(name=button_record, session=session)
        for button_record in buttons_obj.applications():
            Application.objects.create(name=button_record, session=session)
    return response

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[-1].strip()
    return request.META.get('REMOTE_ADDR')

@csrf_exempt
def create(request):
    #if request.method != "POST":
    #    raise Http404()
    buttons = request.GET.getlist("button")
    if not buttons or "update-submit" in request.GET:
        applications = "-".join(request.GET.getlist("button-application"))
        locale = request.GET.get("button-locale")
        kwargs = {}
        if locale:
            kwargs["locale_name"] = locale
        if applications:
            kwargs["applications"] = applications
        return redirect(reverse("tbutton-custom", kwargs=kwargs))
    return create_buttons(request, request.GET)

def safe_divide(numerator, denominator):
    if denominator != 0:
        return float(numerator) / denominator
    return 0

def statistics(request, days=30, template_name='tbutton_maker/statistics.html'):
    locale_str = locale_str_getter(None)
    time = datetime.datetime.now() - datetime.timedelta(days)
    buttons = Button.objects.filter(session__time__gt=time)
    sessions = DownloadSession.objects.filter(time__gt=time).count()
    stats = list(buttons.values('name').annotate(
        downloads=Count('name')).order_by("-downloads"))
    button_count = buttons.count()
    applications = dict(BUTTONS.button_applications().items())
    total = 0
    found = set()
    updates = UpdateSession.objects.filter(time__gt=time)
    update_counts = Counter()
    for row in updates:
        query = QueryDict(row.query_string)
        update_counts.update(query.getlist('button'))
    for item in stats:
        try:
            found.add(item["name"])
            count = item["downloads"]
            total += count
            apps = list(applications.get(item["name"], ()))
            apps.sort()
            item.update({
                "applications": apps,
                "icon": BUTTONS.get_icons(item["name"]),
                "label": locale_str('label', item["name"]),
                "average": safe_divide(count, days),
                "update": update_counts.get(item["name"], 0) / days,
                "percent": safe_divide(count, button_count * 100),
                "total": safe_divide(total, button_count * 100),
                "folder": BUTTONS.get_source_folder(item["name"]),
            })
        except KeyError:
            pass # if we change an id, this will happen, but we don't care
    for name in set(BUTTONS.buttons()).difference(found):
        apps = list(applications.get(name, ()))
        apps.sort()
        stats.append({
               "name": name,
               "downloads": 0,  
               "applications": apps,
               "icon": BUTTONS.get_icons(name),
               "label": locale_str('label', name),
               "update": 0,
               "average": 0,
               "percent": 0,
               "total": safe_divide(total, button_count * 100),
               "folder": BUTTONS.get_source_folder(name),   
        })
    data = {
        "stats": stats,
        "count": button_count,
        "updates": len(updates) // days,
        "sessions": sessions,
        "average": safe_divide(button_count, len(stats) * days)
    }
    return render(request, template_name, data)

def suggestions(request):
    days = 30
    time = datetime.datetime.now() - datetime.timedelta(days)
    button = request.GET.getlist('button')
    inner_qs = Button.objects.filter(
        name__in=button, session__time__gt=time).values('session')
    results = Button.objects.filter(
        session__in=inner_qs).exclude(name__in=button)
    stats = list(results.values('name').annotate(downloads=Count('name'))
                 .order_by("-downloads"))[0:int(request.GET.get('count', 10))]
    return HttpResponse(
        json.dumps(stats),
        content_type = 'application/javascript; charset=utf8'
    )

def old_update(request):
    query = QueryDict('').copy()
    query.setlist('button', request.GET.get('buttons').split('_'))
    return redirect("%s?%s" % (reverse('tbutton-update'), query.urlencode()))

def migrate_buttons(buttons):
    new_buttons = []
    for button_id in buttons:
        if button_id in BUTTONS.hidden_buttons:
            new_buttons.append(BUTTONS.hidden_buttons.get(button_id))
        else:
            new_buttons.append(button_id)
    return new_buttons

def update(request):
    version = SETTINGS.get("version")
    buttons = request.GET.getlist("button")
    applications = get_applications(request)
    args = request.GET.copy()
    args.setlist("button-application", applications)
    args.setlist('button', migrate_buttons(buttons))
    channel = request.GET.get("channel", "stable")
    if re.search(r'[a-z]+', version) and channel == "stable":
        app_data = None
    else:
        app_setting = SETTINGS.get("applications_data")
        if "all" in applications:
            app_data = itertools.chain.from_iterable(app_setting.values())
        else:
            app_info = (app_setting.get(app) for app in applications)
            app_data = itertools.chain.from_iterable(app_info)
    if channel == "nightly":
        version = "{}.r{}".format(version, util.get_git_revision(SETTINGS))
    update_url = "https://{domain}{path}?{query}".format(
        domain=Site.objects.get_current().domain,
        path=reverse("tbutton-make-button"),
        query=args.urlencode())

    extension_hash = hashlib.md5("_".join(sorted(buttons)).encode('utf-8')).hexdigest()
    extension_id_string = extension_hash + "@button.codefisher.org"

    extension_id = request.GET.get("item_id", extension_id_string)
    # quick patch around an important messed up update
    if request.GET.get("item_id") == "%ITEM_ID%":
        extension_id = extension_id_string
    data = {
        "applications": list(app_data) if app_data else None,
        "version": version,
        "update_url": update_url,
        "extension_id": extension_id,
        # this is our update fix
        "extension_hash": hashlib.md5("_".join(sorted(buttons)).encode('utf-8')).hexdigest(),
        "year_month": "1503",
        "days": ['%02d' % (x+1) for x in range(31)],
    }
    def config_order(conf):
        return len(conf.get('buttons', []))
    ext_configs = sorted(single_configs().values(), key=config_order)
    if (('icon-size' not in request.GET
                or request.GET.get('icon-size') == 'standard')
            and request.GET.get('create-toolbars') != 'true'):
        for ext_config in ext_configs:
            buttons = request.GET.getlist('button')
            ext_buttons = ext_config.get('buttons')
            if set(ext_buttons).issuperset(buttons):
                data['update_url'] = ext_config.get('download_link')
                data['version'] += '.1'
                break
    update_session = UpdateSession()
    update_session.ip_address = get_client_ip(request)
    update_session.query_string = args.urlencode()
    if request.META:
        update_session.user_agent = request.META.get("HTTP_USER_AGENT", "")[0:250]
    else:
        update_session.user_agent = ""
    update_session.save()
    return render(request, "tbutton_maker/update.rdf",
                  data, content_type="application/xml+rdf")

def update_static(request):
    app_data = itertools.chain.from_iterable(
        SETTINGS.get("applications_data").values())
    group = DownloadGroup.objects.get(identifier=SETTINGS.get("extension_id"))
    extension = ExtensionDownload.objects.get(pk=group.latest.pk)
    site = Site.objects.get_current()
    scheme = "https" if request.is_secure() else "http"
    data = {
        "applications": app_data,
        "version": SETTINGS.get("version"),
        "update_url": "{scheme}://{domain}{path}".format(
            scheme=scheme,
            domain=site.domain,
            path=extension.get_absolute_url()),
        "extension_id": SETTINGS.get("extension_id"),
    }
    return render(request, "tbutton_maker/update.rdf",
                  data, content_type="application/xml+rdf")

def make(request):
    return create_buttons(request, request.GET, log_creation=False)

def page_it(request, entries_list):
    paginator = Paginator(entries_list, 10)
    # todo: this does not work now
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        return paginator.page(page)
    except (EmptyPage, InvalidPage):
        # todo: better raise a redirect
        if page != 1:
            return paginator.page(paginator.num_pages)
    return []

def list_app_buttons(request, app_name, days=30,
                     template_name='tbutton_maker/app_list.html'):
    app_data = SETTINGS.get("applications_data")
    if app_name not in app_data:
        for key, items in app_data.items():
            if app_name.lower() in [item[0].lower() for item in items]:
                app_name = key
                break
        else:
            raise Http404
    time = datetime.datetime.now() - datetime.timedelta(days)
    buttons = Button.objects.filter(session__time__gt=time)
    stats = {item["name"]: item["downloads"]
             for item in buttons.values('name').annotate(
        downloads=Count('name')).order_by("-downloads")}
    def button_key(item):
        return 0 - stats.get(item[0], 0)
    data = index(request, applications=app_name, template_name=None)
    button_data = data["button_data"]()
    data["entries"] = page_it(request, sorted(button_data, key=button_key))
    data["application"] = app_name
    return render(request, template_name, data)
