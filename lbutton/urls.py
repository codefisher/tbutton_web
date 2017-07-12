from django.conf.urls import url
from tbutton_web.lbutton import views

urlpatterns = [
    url(r'^link-button-maker/', views.index, name='lbutton-custom'),
    url(r'^link-button-create/', views.create, name='lbutton-create'),
    url(r'^link-button-make/', views.make, name='lbutton-make'),
    url(r'^link-button-update.rdf', views.update, name='lbutton-update'),
    
    url(r'^link-button/$', views.buttons, name='lbutton-buttons'),
    url(r'^link-button/(?P<page>[0-9]+)/$', views.buttons, name='lbutton-buttons'),
    url(r'^link-button/make/(?P<button>[\w-]+)/$', views.button_make, name='lbutton-button-make'),
    url(r'^link-button/(?P<button>[\w-]+)/$', views.button, name='lbutton-button'),
    url(r'^link-button/update.rdf', views.button_update, name='lbutton-button-update'),
    
    url(r'^update-clb', views.update_legacy, name='lbutton-update-legacy'),
    url(r'^get-icons/', views.favicons, name='lbutton-custom-favicons'),
]