from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Subject)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Chapter)
admin.site.register(Test)
admin.site.register(User)
admin.site.register(TestChapter)
admin.site.register(StudentAnswers)