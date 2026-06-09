from django.contrib import admin
from .models import *
class YoutoModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        # Автоматически сохраняем при любых изменениях
        obj.save()
        
    def response_change(self, request, obj):
        # Сохраняем при изменении объекта
        obj.save()
        return super().response_change(request, obj)
    
    def response_add(self, request, obj, post_url_continue=None):
        # Сохраняем при добавлении нового объекта
        obj.save()
        return super().response_add(request, obj, post_url_continue)

admin.site.register(Student, YoutoModelAdmin)
admin.site.register(Message, YoutoModelAdmin)
admin.site.register(WorkSession, YoutoModelAdmin)
admin.site.register(Rule, YoutoModelAdmin)
admin.site.register(AdminProfile,YoutoModelAdmin)
admin.site.register(RuleAcceptance, YoutoModelAdmin)
admin.site.register(ComputerStation, YoutoModelAdmin)
