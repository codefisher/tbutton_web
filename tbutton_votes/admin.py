from django.contrib import admin

from django.contrib import admin
from tbutton_web.tbutton_votes.models import TbuttonRequest, TbuttonRequestComment
from upvotes.admin import RequestAdmin, RequestCommentAdmin

admin.site.register(TbuttonRequest, RequestAdmin) 
admin.site.register(TbuttonRequestComment, RequestCommentAdmin)

