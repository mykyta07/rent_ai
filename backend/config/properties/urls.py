from django.urls import path
from .views import (
    PropertyListView,
    MyPropertyListView,
    PropertyDetailView,
    PropertyCreateView,
    PropertyUpdateView,
    PropertyDeleteView,
    PropertyPhotosView,
    PropertyLocationView
)

urlpatterns = [
    # Список та створення
    path('', PropertyListView.as_view(), name='property-list'),
    path('my/', MyPropertyListView.as_view(), name='property-my-list'),
    path('create/', PropertyCreateView.as_view(), name='property-create'),
    
    # Деталі, оновлення, видалення
    path('<int:property_id>/', PropertyDetailView.as_view(), name='property-detail'),
    path('<int:property_id>/update/', PropertyUpdateView.as_view(), name='property-update'),
    path('<int:property_id>/delete/', PropertyDeleteView.as_view(), name='property-delete'),
    
    # Додаткова інформація
    path('<int:property_id>/photos/', PropertyPhotosView.as_view(), name='property-photos'),
    path('<int:property_id>/location/', PropertyLocationView.as_view(), name='property-location'),
]
