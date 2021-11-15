from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet, Logout, ObtainAuthToken, RecipeViewSet,
                    TagViewSet, UserViewSet)

router = DefaultRouter()

router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
router.register('users', UserViewSet)


urlpatterns = [
    path('auth/token/login/', ObtainAuthToken.as_view(), name='get_token'),
    path('auth/token/logout/', Logout.as_view(), name='delete_token'),
    path('', include(router.urls)),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
