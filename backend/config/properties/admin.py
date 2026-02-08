from django.contrib import admin
from .models import Property, Location, PropertyPhoto


class PropertyPhotoInline(admin.TabularInline):
    model = PropertyPhoto
    extra = 1


class LocationInline(admin.StackedInline):
    model = Location
    can_delete = False


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'currency', 'rooms_count', 'realty_type', 'sale_type', 'created_at']
    list_filter = ['realty_type', 'sale_type', 'is_commercial']
    search_fields = ['title', 'description', 'location__district', 'location__street']
    inlines = [LocationInline, PropertyPhotoInline]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['property', 'city', 'district', 'street', 'metro_station']
    search_fields = ['city', 'district', 'street', 'metro_station']


@admin.register(PropertyPhoto)
class PropertyPhotoAdmin(admin.ModelAdmin):
    list_display = ['property', 'url', 'is_main']
    list_filter = ['is_main']
