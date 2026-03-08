from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('history/', views.history_view, name='history'),
    path('files/', views.files_view, name='files'),
    path('request/<int:pk>/', views.request_detail_view, name='request_detail'),
]