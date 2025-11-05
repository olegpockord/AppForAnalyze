from django.urls import path

from onearticle import views

app_name = 'onearticle'

urlpatterns = [
    path('', views.SearchView.as_view(), name ='search'),
]