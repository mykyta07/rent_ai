from django.urls import path
from .views import (
    ChatAssistantView,
    SemanticSearchView,
    ExplainPropertyView,
    ComparePropertiesView
)

urlpatterns = [
    path('chat/', ChatAssistantView.as_view(), name='ai-chat'),
    path('search/', SemanticSearchView.as_view(), name='ai-semantic-search'),
    path('explain/', ExplainPropertyView.as_view(), name='ai-explain'),
    path('compare/', ComparePropertiesView.as_view(), name='ai-compare'),
]
