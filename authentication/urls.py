from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import UserViewSet, SessionViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'sessions', SessionViewSet, basename='session')

urlpatterns = [
    path('', include(router.urls)),
]