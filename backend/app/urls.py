from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    RecipeViewSet,
    TagViewSet,
    IngredientViewSet,
    ObtainAuthToken,
    Logout,
    UserViewSet
)


router = DefaultRouter()

router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
router.register('users', UserViewSet)


urlpatterns = [
    path('token/login/', ObtainAuthToken.as_view()),
    path('token/logout/', Logout.as_view()),
    path('', include(router.urls)),
]
