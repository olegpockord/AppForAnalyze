from django.urls import path
from citation_api import views

app_name = 'api'

urlpatterns = [
    path('article/<int:pk>/citation/<str:format_name>/', views.CitiationExportAPIView.as_view(), name ='citation_export'),
]