from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Import models from their respective apps
from api.accounts.models import User
from api.brands.models import Brand
from api.color.models import Color
from api.items.models import Item
from api.relationships.models import ItemColor, SeasonColor
from api.season.models import Season


# Custom admin for the custom User model
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Include the custom season field in the admin form and list display
    fieldsets = BaseUserAdmin.fieldsets + ((None, {"fields": ("season",)}),)
    list_display = BaseUserAdmin.list_display + ("season",)
    search_fields = BaseUserAdmin.search_fields + ("season__name",)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "styles")
    search_fields = ("name",)
    # ArrayField styles may be easier to inspect in a readonly field
    readonly_fields = ("styles",)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("description", "price", "size", "brand")
    search_fields = ("description", "brand__name")
    list_filter = ("brand",)
    ordering = ("brand", "price")


@admin.register(ItemColor)
class ItemColorAdmin(admin.ModelAdmin):
    list_display = ("item", "color", "image_url")
    search_fields = ("item__description", "color__name")
    list_filter = ("color",)


@admin.register(SeasonColor)
class SeasonColorAdmin(admin.ModelAdmin):
    list_display = ("season", "color")
    search_fields = ("season__name", "color__name")
    list_filter = ("season", "color")


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
