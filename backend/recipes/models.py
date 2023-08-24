from django.core.validators import MinValueValidator
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Tag(models.Model):
    '''Модель для тегов.'''

    class TagChoeces(models.TextChoices):
        '''Клас для выбора поля name.'''

        BREAKFAST = 'Завтрак'
        LUNCH = 'Обед'
        DINNER = 'Ужин'

    name = models.CharField(
        max_length=200,
        choices=TagChoeces.choices,
    )
    color = models.CharField(max_length=7)
    slug = models.SlugField(
        max_length=200,
        unique=True,
    )


class Recipe(models.Model):
    '''Модель рецептов.'''

    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient')
    )
    name = models.CharField(
        max_length=256,
    )
    image = models.ImageField(
        upload_to='media/',
    )
    text = models.TextField(unique=True)
    cooking_time = models.PositiveSmallIntegerField(
        validators=(MinValueValidator(1),)
    )
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-pub_date', )

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
    )
    measurement_unit = models.CharField(
        max_length=200
    )

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='recipes_in_ingredient',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='ingredients_in_recipe',
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(default=0)


class Favorite(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_user'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('user', 'recipe',),
                                    name='unique_favorite')
        ]


class ShoppingCart(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart_recipe'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart_user'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('user', 'recipe',),
                                    name='unique_user_recipe_shop')
        ]
