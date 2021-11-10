from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet, Logout, ObtainAuthToken, RecipeViewSet,
                    TagViewSet, UserViewSet)

router = DefaultRouter()

router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
router.register('users', UserViewSet)


urlpatterns = [
    path('token/login/', ObtainAuthToken.as_view(), name='get_token'),
    path('token/logout/', Logout.as_view(), name='delete_token'),
    path('', include(router.urls)),
]
