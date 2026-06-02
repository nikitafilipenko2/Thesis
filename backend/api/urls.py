from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import SummaryRequestViewSet
from .api_views import FileUploadViewSet

router = DefaultRouter()
router.register(r'requests', SummaryRequestViewSet)
router.register(r'files', FileUploadViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
