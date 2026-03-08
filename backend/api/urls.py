from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SummaryRequestViewSet
from .views import FileUploadViewSet

router = DefaultRouter()
router.register(r'requests', SummaryRequestViewSet)
router.register(r'files', FileUploadViewSet)

urlpatterns = [
    path('', include(router.urls)),
]