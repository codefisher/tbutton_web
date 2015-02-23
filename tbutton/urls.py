from django.conf.urls import patterns, url
from tbutton_web.tbutton import views

urlpatterns = patterns('',
    url(r'^$', views.homepage, name='tbutton-homepage'),
    url(r'^(?P<mode>updated|installed|version)/(?P<version>[\w\.]+)/?', views.installed, name='tbutton-installed'),
)