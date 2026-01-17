from django.urls import path

from catalog import views

app_name = 'catalog'

urlpatterns = [
    path('', views.CatalogView.as_view(), name ='catalog_all'),
    path('<slug:filter_slug>/', views.CatalogView.as_view(), name='catalog'),
    path('work/<int:pk>', views.WorkDetailView.as_view(), name='work_detail'), # Временно изменим на pk
]