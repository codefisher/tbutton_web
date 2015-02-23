from django.conf.urls import patterns, url
from tbutton_web.lbutton import views

urlpatterns = patterns('',
    url(r'^link-button-maker/', views.index, name='lbutton-custom'),
    url(r'^link-button-create/', views.create, name='lbutton-create'),
    url(r'^link-button-make/', views.make, name='lbutton-make'),
    url(r'^link-button-update.rdf', views.update, name='lbutton-update'),
    url(r'^update-clb', views.update_legacy, name='lbutton-update-legacy'),
    url(r'^get_icons/', views.favicons, name='lbutton-custom-favicons'),
)