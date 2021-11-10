from django.contrib import admin

from .models import (
    Favorite,
    Recipe,
    Ingredient,
    Subscribe,
    Tag,
    RecipeIngredient,
    Shopping
)


admin.site.register(RecipeIngredient)
admin.site.register(Subscribe)
admin.site.register(Shopping)
admin.site.register(Favorite)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'short_text')
    search_fields = ('name', 'text')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug')
    search_fields = ('name', 'color')
    prepopulated_fields = {'slug': ('name',)}
