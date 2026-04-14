from django.urls import path
from .views import (
    ChatAssistantView,
    ChatHistoryView,
    SemanticSearchView,
    ExplainPropertyView,
    ComparePropertiesView,
    GenerateListingDescriptionView,
)

urlpatterns = [
    path('chat/', ChatAssistantView.as_view(), name='ai-chat'),
    path('chat/history/', ChatHistoryView.as_view(), name='ai-chat-history'),
    path('search/', SemanticSearchView.as_view(), name='ai-semantic-search'),
    path('explain/', ExplainPropertyView.as_view(), name='ai-explain'),
    path('compare/', ComparePropertiesView.as_view(), name='ai-compare'),
    path(
        'generate-listing-description/',
        GenerateListingDescriptionView.as_view(),
        name='ai-generate-listing-description',
    ),
]
