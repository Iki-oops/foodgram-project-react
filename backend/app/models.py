from django.db import models
from django.core import validators
from django.contrib.auth import get_user_model


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

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Теги'
        verbose_name = 'Тег'


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=15,
        verbose_name='Единицы измерения'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Ингредиенты'
        verbose_name = 'Ингредиент'


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
        through='RecipeTag',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveIntegerField(
        help_text='Время приготовления в минутах',
        verbose_name='Длительность'
    )

    def short_text(self):
        if len(self.text) > 40:
            return f"{self.text[:40]}..."
        return self.text

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Рецепты'
        verbose_name = 'Рецепт'
        ordering = ('-id',)


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
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            )
        ]


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

    def __str__(self):
        return f"{self.recipe} - {self.ingredient}"
    

class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег'
    )

    def __str__(self):
        return f"{self.recipe} - {self.tag}"
