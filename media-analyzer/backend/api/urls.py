from django.urls import path
from . import views

urlpatterns = [
    path('streams/<str:stream_id>/analysis/', views.stream_analysis, name='stream_analysis'),
    path('providers/', views.providers, name='providers'),
    path('brands/', views.brands, name='brands'),
]