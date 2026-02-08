from django.contrib import admin
from .models import ChatMessage, PropertyEmbedding


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'created_at', 'content_preview']
    list_filter = ['role', 'created_at']
    search_fields = ['content', 'user__username']
    readonly_fields = ['created_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Preview'


@admin.register(PropertyEmbedding)
class PropertyEmbeddingAdmin(admin.ModelAdmin):
    list_display = ['property', 'model_name', 'created_at']
    list_filter = ['model_name', 'created_at']
    readonly_fields = ['created_at']
