from django.conf.urls import url
from tbutton_web.tbutton_maker import views

urlpatterns = [
    url(r'^custom/create-addon/$', views.create, name='tbutton-create'),
    url(r'^statistics/', views.statistics, name='tbutton-statistics'),
    url(r'^statistics/(?P<days>\d+)/', views.statistics, name='tbutton-statistics'),
    url(r'^toolbar_button_maker/$', views.index, name='tbutton-custom'),
    url(r'^toolbar_button_maker/(?P<locale_name>[a-z]{2}(-[A-Z]{2})?)/$',
        views.index, name='tbutton-custom'),
    url(r'^toolbar_button_maker/(?P<locale_name>[a-z]{2}(-[A-Z]{2})?)/(?P<applications>[\w-]+)/$',
        views.index, name='tbutton-custom'),
     url(r'^suggestions/$',
        views.suggestions, name='tbutton-suggestions'),
    url(r'^button_list/$',
        views.list_buttons, name='tbutton-list'),
    url(r'^button_list/(?P<locale_name>[a-z]{2}(-[A-Z]{2})?)/$',
        views.list_buttons, name='tbutton-list'),
    url(r'^button_list/(?P<locale_name>[a-z]{2}(-[A-Z]{2})?)/(?P<applications>[\w,]+)/$',
        views.list_buttons, name='tbutton-list'),
    url(r'^button/(?P<button_id>.+?)/(?P<locale_name>[a-z]{2}(-[A-Z]{2})?)/$', views.buttons_page, name='tbutton-button'),
    url(r'^button/(?P<button_id>.+?)/$', views.buttons_page, name='tbutton-button'),
    url(r'^custom_update', views.old_update),
    url(r'^static_update.rdf', views.update_static),
    url(r'^update.rdf', views.update, name='tbutton-update'),
    url(r'^make_button/', views.make, name='tbutton-make-button'),    
    url(r'^(?P<app_name>[\w]+)/', views.list_app_buttons, name='tbutton-make-button'),
]
