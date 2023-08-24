from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer, UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    '''Сериализатор отображения эндпоинтов тегов.'''

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class DownloadSCSerializer(serializers.Serializer):

    ingredient__name = serializers.CharField()
    ingredient__measurement_unit = serializers.CharField()
    amount = serializers.IntegerField()

    class Meta:
        fields = ('name', 'measurement_unit', 'amount')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return Subscription.objects.filter(
            author=obj,
            subscriber=request.user).exists()


class CustomUserCreateSerializer(UserCreateSerializer):
    email = serializers.EmailField(
        max_length=254,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        max_length=150,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Имя пользователя содержит недопустимый символ'
            ),
            UniqueValidator(queryset=User.objects.all())
        ]
    )
    first_name = serializers.CharField(
        max_length=150,
    )
    last_name = serializers.CharField(
        max_length=150,
    )
    password = serializers.CharField(
        max_length=150,
    )

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')


class RecipeRepresentationSerializer(serializers.ModelSerializer):
    '''Для списка рецептов и возвращения одного рецепта.'''

    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='ingredients_in_recipe'
    )
    author = CustomUserSerializer()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Favorite.objects.filter(user=request.user,
                                       recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=request.user,
                                           recipe=obj).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    '''Для создания/изменения рецепта'''

    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def update_recipeingredient(self, recipe, ingredients):
        recipeingredient_list = [RecipeIngredient(
            recipe=recipe,
            ingredient=ingredient.get('ingredient'),
            amount=ingredient.get('amount')
            ) for ingredient in ingredients]
        if recipeingredient_list:
            RecipeIngredient.objects.bulk_create(recipeingredient_list)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        instance = super().create(validated_data)
        self.update_recipeingredient(instance, ingredients)

        return instance

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.update_recipeingredient(instance, ingredients)

        return instance

    def to_representation(self, instance):
        serializer = RecipeRepresentationSerializer(instance,
                                                    context=self.context)
        return serializer.data


class RecipeShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('__all__',)


class UserSubscriptionSerializer(UserSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('__all__')

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj)
        if limit:
            recipes = recipes[:int(limit)]
        return RecipeShortSerializer(recipes, many=True).data
