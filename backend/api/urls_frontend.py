from django.urls import path
from .auth_views import login_view, logout_view, register_view
from .web_views import home_view, history_view, files_view, request_detail_view, file_summarize_view

urlpatterns = [
    path('', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('history/', history_view, name='history'),
    path('files/', files_view, name='files'),
    path('files/<int:pk>/summarize/', file_summarize_view, name='file_summarize'),
    path('request/<int:pk>/', request_detail_view, name='request_detail'),
]
