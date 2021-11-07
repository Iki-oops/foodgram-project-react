from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .filters import RecipeFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework import permissions
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions, filters

from .permissions import AnonUserPermission, CurrentUserPermission

from .pagination import LimitPagination
from .mixins import UserModelMixin
from .models import Subscribe, Tag, Ingredient, Recipe, Favorite, User, Shopping
from .serializers import (
    AddRecipeInShoppingSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipePostSerializer,
    FavoriteSerializer,
    EmailTokenLogin,
    UserSerializer,
    SetPasswordSerializer,
    SubscriptionsRecipesSerializer,
    UserWithRecipeSerializer,
    ShoppingSerializer,
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [CurrentUserPermission]
    pagination_class = LimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update'):
            return RecipePostSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=['get', 'delete'],
        detail=True,
        permission_classes=[permissions.IsAuthenticated,])
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        favorite, is_created = Favorite.objects.get_or_create(
                user=request.user,
                recipe=recipe
            )
        if request.method == 'GET':
            if is_created:
                serializer = FavoriteSerializer(favorite)
                return Response(
                    data=serializer.data, status=status.HTTP_201_CREATED)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        favorite.delete()
        if is_created:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[permissions.IsAuthenticated,])
    def download_shopping_cart(self, request):
        queryset = request.user.shoppings.all()
        serializer = ShoppingSerializer(queryset, many=True)
        return HttpResponse(serializer.data, headers={
            'Content-Type': 'plain/text',
            'Content-Disposition': 'attachment; filename="file.txt"',
            })

    @action(
        methods=['GET', 'DELETE'],
        detail=True,
        permission_classes=[permissions.IsAuthenticated,])
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        shopping, created = Shopping.objects.get_or_create(
            user=request.user,
            recipe=recipe
        )
        if request.method == 'GET':
            if created:
                serializer = AddRecipeInShoppingSerializer(shopping)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        shopping.delete()
        if created:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


# Пользователи и токены
class UserViewSet(UserModelMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = LimitPagination

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[permissions.IsAuthenticated,])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        methods=['POST'],
        detail=False,
        permission_classes=[permissions.IsAuthenticated,])
    def set_password(self, request):
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        check_password = user.check_password(
            serializer.data['current_password']
        )
        if not check_password:
            return Response(
                data={'message': 'Пароль не совпадает'},
                status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[permissions.IsAuthenticated,])
    def subscriptions(self, request):
        users = request.user.subscribes.all()
        recipes_limit = request.GET.get('recipes_limit', '')
        serializer = SubscriptionsRecipesSerializer(
            users,
            context={'request': request},
            many=True
        )
        if not recipes_limit.isdigit():
            return Response(serializer.data)

        for i in range(len(serializer.data)):
            recipes = serializer.data[i]['recipes'][:int(recipes_limit)]
            serializer.data[i]['recipes'] = recipes
        return Response(serializer.data)

    @action(
        methods=['GET', 'DELETE'],
        detail=True,
        permission_classes=[permissions.IsAuthenticated,])
    def subscribe(self, request, pk):
        author = get_object_or_404(User, id=pk)
        recipes_limit = request.query_params.get('recipes_limit', '')
        serializer = UserWithRecipeSerializer(
            author,
            context={'request': request}
        )
        subscribe, is_created = Subscribe.objects.get_or_create(
            user=request.user,
            author=author
        )
        if request.method == 'GET':
            if is_created:
                if not recipes_limit.isdigit():
                    return Response(
                        serializer.data, status=status.HTTP_201_CREATED)
                recipes = serializer.data['recipes'][:int(recipes_limit)]
                serializer.data['recipes'] = recipes
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        subscribe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ObtainAuthToken(APIView):
    permission_classes = [AnonUserPermission]

    def post(self, request):
        serializer = EmailTokenLogin(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, email=serializer.data.get('email'))
        check_password = user.check_password(serializer.data.get('password'))
        if not check_password:
            return Response(
                data={'message': 'Пароль не совпадает'},
                status=status.HTTP_400_BAD_REQUEST)

        token, created = Token.objects.get_or_create(user=user)
        content = {
            'token': token.key,
        }
        return Response(content)


class Logout(APIView):
    def post(self, request):
        request.user.auth_token.delete()
        return Response({'null': 'null'}, status=status.HTTP_201_CREATED)
