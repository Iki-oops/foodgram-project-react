from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from .fields import Base64ImageField
from .models import (Favorite, Ingredient, Recipe, RecipeIngredient, Shopping,
                     Subscribe, Tag, User)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'password'
        )
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        user = User(
            email=validated_data.pop('email'),
            username=validated_data.pop('username'),
            first_name=validated_data.pop('first_name'),
            last_name=validated_data.pop('last_name'),
        )
        user.set_password(validated_data.pop('password'))
        user.save()
        return user

    def get_is_subscribed(self, obj):
        try:
            user = self.context['request'].user
            if not user.is_anonymous:
                return user.subscribers.filter(author=obj.id).exists()
            else:
                return False
        except KeyError:
            return False


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient.id',
        queryset=Ingredient.objects.all()
    )
    name = serializers.CharField(
        source='ingredient.name'
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(
        many=True,
        read_only=True
    )
    ingredients = RecipeIngredientSerializer(
        many=True,
        read_only=True,
        source='ingredients_in'
    )
    author = UserSerializer(
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
            'ingredients', 'name',
            'image', 'text',
            'cooking_time',
        )
    
    def get_image(self, obj):
        return '/media/' + obj.image.name

    def get_is_favorited(self, obj):
        try:
            user = self.context['request'].user
            if not user.is_anonymous:
                return obj.favorites.filter(user=user).exists()
            else:
                return False
        except KeyError:
            return False
    
    def get_is_in_shopping_cart(self, obj):
        try:
            user = self.context['request'].user
            if not user.is_anonymous:
                return obj.shoppings.filter(user=user).exists()
            else:
                return False
        except KeyError:
            return False


class PostRecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient.id'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipePostSerializer(serializers.ModelSerializer):
    ingredients = PostRecipeIngredientSerializer(
        many=True,
        source='ingredients_in'
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time'
        )

    @staticmethod
    def save_ingredients(ingredients, recipe):
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                Ingredient, pk=ingredient['ingredient']['id'].id)
            RecipeIngredient.objects.create(
                ingredient=current_ingredient,
                recipe=recipe,
                amount=ingredient['amount']
            )
    
    def validate(self, data):
        tag_ids = [tag.id for tag in data['tags']]
        ingredient_ids = [
            ingredient['ingredient']['id'].id
            for ingredient in data['ingredients_in']
        ]
        if len(set(tag_ids)) != len(tag_ids):
            raise serializers.ValidationError('Теги должны быть уникальны.')
        elif len(set(ingredient_ids)) != len(ingredient_ids):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальны.')
        elif data['cooking_time'] < 0:
            raise serializers.ValidationError(
                'Время готовки должно быть больше или равно нулю')

        for ingredient in data['ingredients_in']:
            if ingredient['amount'] < 0:
                raise serializers.ValidationError(
                    'Количество ингредиентов не должно быть меньше нуля')
        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients_in')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.save_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients_in')
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.save_ingredients(ingredients, instance)
        super().update(instance, validated_data)
        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        read_only=True,
        source='recipe.name'
    )
    image = serializers.ImageField(
        read_only=True,
        source='recipe.image'
    )
    cooking_time = serializers.IntegerField(
        read_only=True,
        source='recipe.cooking_time'
    )

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')


class ShortRecipeSerializerForSubscriptions(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
    
    def get_image(self, obj):
        return '/media/' + obj.image.name


class ShortRecipeSerializerForUsers(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingIngredientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        source='ingredient.name'
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('name', 'measurement_unit', 'amount')


class ShoppingSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        source='recipe.name'
    )
    ingredients = ShoppingIngredientSerializer(
        source='recipe.ingredients_in', many=True
    )
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time'
    )

    class Meta:
        model = Shopping
        fields = ('id', 'name', 'ingredients', 'cooking_time')


class AddRecipeInShoppingSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image')
    cooking_time = serializers.CharField(source='recipe.cooking_time')
    
    class Meta:
        model = Shopping
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionsRecipesSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='author.id',
        queryset=User.objects.all()
    )
    is_subscribed = serializers.SerializerMethodField()
    email = serializers.CharField(
        source='author.email'
    )
    username = serializers.CharField(
        source='author.username'
    )
    first_name = serializers.CharField(
        source='author.first_name'
    )
    last_name = serializers.CharField(
        source='author.last_name'
    )
    recipes = ShortRecipeSerializerForSubscriptions(
        many=True,
        source='author.recipes'
    )
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscribe
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        try:
            user = self.context['request'].user
            if not user.is_anonymous:
                return user.subscribers.filter(author=obj.author.id).exists()
            else:
                return False
        except KeyError:
            return False

    def get_recipes_count(self, obj):
        return obj.user.recipes.count()


class UserWithRecipeSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    recipes = ShortRecipeSerializerForSubscriptions(many=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        try:
            user = self.context['request'].user
            if not user.is_anonymous:
                return user.subscribers.filter(author=obj.id).exists()
            else:
                return False
        except KeyError:
            return False

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField()
    current_password = serializers.CharField()


class EmailTokenLogin(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('email', 'password')
        extra_kwargs = {
            'email': {'required': True},
            'password': {'required': True},
        }
