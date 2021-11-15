from django.db.utils import IntegrityError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import RecipeFilter
from .mixins import UserModelMixin
from .models import (Favorite, Ingredient, Recipe, Shopping, Subscribe, Tag,
                     User)
from .pagination import LimitPagination
from .permissions import AnonUserPermission, CurrentUserPermission
from .serializers import (AddRecipeInShoppingSerializer, EmailTokenLogin,
                          FavoriteSerializer, IngredientSerializer,
                          RecipePostSerializer, RecipeSerializer,
                          SetPasswordSerializer, ShoppingSerializer,
                          SubscriptionsRecipesSerializer, TagSerializer,
                          UserSerializer, UserWithRecipeSerializer)


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

        if request.method == 'GET':
            try:
                favorite = Favorite.objects.create(
                    user=request.user,
                    recipe=recipe
                )
            except IntegrityError:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = FavoriteSerializer(favorite)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            try:
                favorite = Favorite.objects.get(
                    user=request.user,
                    recipe=recipe
                )
            except Favorite.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            favorite.delete()
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

        if request.method == 'GET':
            try:
                shopping = Shopping.objects.create(
                    user = request.user,
                    recipe=recipe
                )
            except IntegrityError:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = AddRecipeInShoppingSerializer(shopping)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            try:
                shopping = Shopping.objects.get(
                    user=request.user,
                    recipe=recipe
                )
            except Shopping.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            shopping.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


# Пользователи и токены
class UserViewSet(UserModelMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny,]
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
            serializer.validated_data.get('new_password')
        )
        if not check_password:
            return Response(
                data={'message': 'Пароль не совпадает'},
                status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data.get('new_password'))
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[permissions.IsAuthenticated,])
    def subscriptions(self, request):
        users = request.user.subscribers.all()
        recipes_limit = request.GET.get('recipes_limit', '')
        serializer = SubscriptionsRecipesSerializer(
            users,
            context={'request': request},
            many=True
        )
        page = self.paginate_queryset(users)
        if page is not None:
            if not recipes_limit.isdigit():
                return self.get_paginated_response(serializer.data)
            else:
                for item in serializer.data:
                    recipes = item['recipes'][:int(recipes_limit)]
                    item['recipes'] = recipes
                return self.get_paginated_response(serializer.data)
        else:
            return Response(serializer.data)

    @action(
        methods=['GET', 'DELETE'],
        detail=True,
        permission_classes=[permissions.IsAuthenticated,])
    def subscribe(self, request, pk):
        author = get_object_or_404(User, id=pk)
        recipes_limit = request.query_params.get('recipes_limit', '')

        if request.method == 'GET':
            try:
                Subscribe.objects.create(user=request.user, author=author)
            except IntegrityError:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = UserWithRecipeSerializer(
                author,
                context={'request': request}
            )
            serialized_data = serializer.data
            if not recipes_limit.isdigit():
                return Response(
                    serialized_data, status=status.HTTP_201_CREATED)
            recipes = serializer.data['recipes'][:int(recipes_limit)]
            serialized_data['recipes'] = recipes
            return Response(serialized_data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            try:
                subscribe = Subscribe.objects.get(
                    user=request.user,
                    author=author
                )
            except Subscribe.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            subscribe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class ObtainAuthToken(APIView):
    permission_classes = [AnonUserPermission,]

    def post(self, request):
        serializer = EmailTokenLogin(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User, email=serializer.validated_data.get('email'))
        check_password = user.check_password(
            serializer.validated_data.get('password'))
        if not check_password:
            return Response(
                data={'message': 'Пароль не совпадает'},
                status=status.HTTP_400_BAD_REQUEST)

        token, created = Token.objects.get_or_create(user=user)
        content = {
            'auth_token': token.key,
        }
        return Response(content)


class Logout(APIView):
    def post(self, request):
        request.user.auth_token.delete()
        return Response({'null': 'null'}, status=status.HTTP_201_CREATED)
