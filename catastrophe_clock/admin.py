from django.contrib import admin

from .models import Catastrophe


class CatastropheAdmin(admin.ModelAdmin):
    list_display = ('name', 'arrival_date', 'description', )

admin.site.register(Catastrophe, CatastropheAdmin)
