from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (CustomUserViewSet, IngredietViewSet,
                       RecipeViewSet, TagViewSet)

router = DefaultRouter()

router.register('users', CustomUserViewSet)
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet)
router.register('ingredients', IngredietViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path(r'auth/', include('djoser.urls.authtoken')),
]
