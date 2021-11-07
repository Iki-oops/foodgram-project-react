from rest_framework import serializers

from .models import (
    RecipeIngredient,
    Subscribe,
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    User,
    Shopping
)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        from django.core.files.base import ContentFile
        import base64
        import six
        import uuid

        if isinstance(data, six.string_types):
            if 'data:' in data and ';base64,' in data:
                header, data = data.split(';base64,')

            try:
                decoded_file = base64.b64decode(data)
            except TypeError:
                self.fail('invalid_image')

            file_name = str(uuid.uuid4())[:12]
            file_extension = self.get_file_extension(file_name, decoded_file)

            complete_file_name = "%s.%s" % (file_name, file_extension, )

            data = ContentFile(decoded_file, name=complete_file_name)

        return super(Base64ImageField, self).to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        import imghdr

        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension

        return extension


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
        user = self.context['request'].user
        if not user.is_anonymous:
            subscribed = user.subscribes.filter(user=obj.id).first()
            if subscribed:
                return True
        return False


# Теги и ингредиенты
class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('pk', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('pk', 'name', 'measurement_unit')


# Для всех методов, кроме POST. Рецепты
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

    class Meta:
        model = Recipe
        fields = (
            'pk',
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
            'ingredients', 'name',
            'image', 'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if not user.is_anonymous:
            if obj.favorites.filter(user=user).first():
                return True
            return False
        return False
    
    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if not user.is_anonymous:
            print(obj.shoppings.filter(user=user))
            if obj.shoppings.filter(user=user).first():
                return True
            return False
        return False


# Для метода POST. Рецепты
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
    image = Base64ImageField(
        max_length=None,
        use_url=True
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time'
        )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients_in')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        for ingredient in ingredients:
            current_ingredient = (
                Ingredient.objects.get(pk=ingredient['ingredient']['id'].id)
            )
            RecipeIngredient.objects.create(
                ingredient=current_ingredient,
                recipe=recipe,
                amount=ingredient['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients_in')
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        instance.ingredients.clear()
        if not ingredients:
            return instance
        for ingredient in ingredients:
            current_ingredient = Ingredient.objects.get(
                pk=ingredient['ingredient']['id'].id
            )
            RecipeIngredient.objects.create(
                ingredient=current_ingredient,
                recipe=instance,
                amount=ingredient['amount']
            )
        return instance


# Избранное
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
        fields = ('pk', 'name', 'image', 'cooking_time')


# Для подписок
class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('pk', 'name', 'image', 'cooking_time')


# Для списка покупок
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
        fields = ('pk', 'name', 'ingredients', 'cooking_time')


class AddRecipeInShoppingSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='recipe.name')
    image = serializers.CharField(source='recipe.image')
    cooking_time = serializers.CharField(source='recipe.cooking_time')
    
    class Meta:
        model = Shopping
        fields = ('id', 'name', 'image', 'cooking_time')


# Пользователи с рецептами для ../subscriptions/
class SubscriptionsRecipesSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    email = serializers.CharField(source='user.email')
    username = serializers.CharField(source='user.username')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    recipes = ShortRecipeSerializer(many=True, source='user.recipes')
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscribe
        fields = (
            'email',
            'pk',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        return True

    def get_recipes_count(self, obj):
        return obj.user.recipes.count()


class UserWithRecipeSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    recipes = ShortRecipeSerializer(many=True)

    class Meta:
        model = User
        fields = (
            'email',
            'pk',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        subscribed = user.subscribes.filter(user=obj.id).first()
        if subscribed:
            return True
        return False

    def get_recipes_count(self, obj):
        return obj.recipes.count()


# Токены
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
