from django.urls import path
from .views import (
    ChatAssistantView,
    ChatHistoryView,
    PropertyExplainChatView,
    PropertyExplainChatHistoryView,
    SemanticSearchView,
    ExplainPropertyView,
    ExplainPropertyBriefView,
    ComparePropertiesView,
    GenerateListingDescriptionView,
)

urlpatterns = [
    path('chat/', ChatAssistantView.as_view(), name='ai-chat'),
    path('chat/history/', ChatHistoryView.as_view(), name='ai-chat-history'),
    path(
        'properties/<int:property_id>/explain/chat/',
        PropertyExplainChatView.as_view(),
        name='ai-property-explain-chat',
    ),
    path(
        'properties/<int:property_id>/explain/chat/history/',
        PropertyExplainChatHistoryView.as_view(),
        name='ai-property-explain-chat-history',
    ),
    path('search/', SemanticSearchView.as_view(), name='ai-semantic-search'),
    path('explain/', ExplainPropertyView.as_view(), name='ai-explain'),
    path('explain/brief/', ExplainPropertyBriefView.as_view(), name='ai-explain-brief'),
    path('compare/', ComparePropertiesView.as_view(), name='ai-compare'),
    path(
        'generate-listing-description/',
        GenerateListingDescriptionView.as_view(),
        name='ai-generate-listing-description',
    ),
]
