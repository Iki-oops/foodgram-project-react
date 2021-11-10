from django.contrib.auth import get_user_model
from django.core import validators
from django.db import models
from django.db.models.constraints import UniqueConstraint

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Название'
    )
    color = models.CharField(
        max_length=7,
        unique=True,
        verbose_name='Цвет',
        help_text='Цвет в формате HEX-кода',
        validators=[
            validators.RegexValidator(
                regex='^#[A-Z0-9]{6}$',
                message='Неправильный формат'
            )
        ]
        )
    slug = models.SlugField(max_length=100, unique=True,
                            verbose_name='Ссылка')

    class Meta:
        verbose_name_plural = 'Теги'
        verbose_name = 'Тег'
    
    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=15,
        verbose_name='Единицы измерения'
    )

    class Meta:
        verbose_name_plural = 'Ингредиенты'
        verbose_name = 'Ингредиент'
    
    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Владелец'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
    )
    text = models.TextField(
        verbose_name='Текст'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    cooking_time = models.PositiveIntegerField(
        help_text='Время приготовления в минутах',
        verbose_name='Длительность'
    )

    class Meta:
        verbose_name_plural = 'Рецепты'
        verbose_name = 'Рецепт'
        ordering = ('-id',)

    def __str__(self):
        return self.name

    def short_text(self):
        if len(self.text) > 40:
            return f"{self.text[:40]}..."
        return self.text


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        related_name='favorites',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorites',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name_plural = 'Избранные'
        verbose_name = 'Избранное'
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite'
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.recipe}"


class Shopping(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shoppings'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shoppings'
    )

    class Meta:
        verbose_name_plural = 'Покупки'
        verbose_name = 'Покупка'
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping'
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.recipe}"


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        related_name='subscribers',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        related_name='subscribes',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name_plural = 'Подписки'
        verbose_name = 'Подписка'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            )
        ]
    
    def __str__(self):
        return f"{self.user} - {self.author}"


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='ingredients_in'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='ingredients_in'
    )
    amount = models.FloatField(
        validators=[
            validators.RegexValidator(
                regex='^[0-9.]+$',
                message='Число должно быть положительное'
            )
        ]
    )

    class Meta:
        verbose_name_plural = 'Рецепты с ингредиентами'
        verbose_name = 'Рецепт с ингредиентом'
        # constraints = [
        #     UniqueConstraint(
        #         fields=('recipe', 'ingredient'),
        #         name='unique_recipe_ingredient'
        #     )
        # ]

    def __str__(self):
        return f"{self.recipe} - {self.ingredient}"
