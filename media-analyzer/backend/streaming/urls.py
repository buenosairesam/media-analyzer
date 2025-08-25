from django.urls import path
from . import views

urlpatterns = [
    path('streams/', views.list_streams, name='list_streams'),
    path('streams/create/', views.create_stream, name='create_stream'),
    path('streams/webcam/start/', views.start_webcam_stream, name='start_webcam_stream'),
    path('streams/<str:stream_key>/start/', views.start_stream, name='start_stream'),
    path('streams/<str:stream_key>/stop/', views.stop_stream, name='stop_stream'),
    path('streams/<int:stream_id>/', views.delete_stream, name='delete_stream'),
    path('streams/<str:stream_key>/analyze/', views.trigger_analysis, name='trigger_analysis'),
    path('<str:filename>', views.serve_hls_file, name='serve_hls_file'),
]