from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import SessionViewSet

router = DefaultRouter()
router.register(r'sessions', SessionViewSet, 'session')

urlpatterns = [
    path('', include(router.urls)),
]