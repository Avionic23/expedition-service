from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ExpeditionViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'expeditions', ExpeditionViewSet, basename='expedition')

urlpatterns = [
    path('', include(router.urls)),
]