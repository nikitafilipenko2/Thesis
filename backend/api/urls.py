from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SummaryRequestViewSet

router = DefaultRouter()
router.register(r'requests', SummaryRequestViewSet)

urlpatterns = [
    path('', include(router.urls)),
]