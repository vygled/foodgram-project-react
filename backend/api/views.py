from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from djoser.views import UserViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import RecipeFilter, IngredientFilter
from api.permissions import IsAuthorOrReadOnly
from api.pagination import PageLimitNumberPagination
from api.render import TXTShoppingCartRenderer
from api.serializers import (CustomUserCreateSerializer, CustomUserSerializer,
                             DownloadSCSerializer, IngredientSerializer,
                             RecipeCreateSerializer,
                             RecipeRepresentationSerializer,
                             RecipeShortSerializer, SubscriptionSerializer,
                             TagSerializer, UserSubscriptionSerializer)
from recipes.models import (Ingredient, Favorite, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
from users.models import Subscription


User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    """Функция представлния тегов (Список всех. Один тег.)"""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """Функция представления рецептов."""

    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        recipes = Recipe.objects.prefetch_related(
            'ingredients_in_recipe__ingredient',
            'tags'
        )
        return recipes

    def get_serializer_class(self):
        print(self.action)
        if self.action == 'create' or 'partial_update':
            print(12)
            print(self.action)

            return RecipeCreateSerializer
        print(23)
        return RecipeRepresentationSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(methods=['post', 'delete'], detail=True)
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            _, created = Favorite.objects.get_or_create(
                recipe=recipe,
                user=request.user
            )
            if not created:
                return Response({"errors": "Рецепт уже в избранных."},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = RecipeShortSerializer(recipe,
                                               context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            get_object_or_404(Favorite, recipe=recipe,
                              user=request.user).delete()
            return Response({'detail': 'Удален из избранных.'},
                            status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            _, created = ShoppingCart.objects.get_or_create(
                recipe=recipe,
                user=request.user
            )
            if not created:
                return Response({"errors": "Рецепт уже в списке."},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = RecipeShortSerializer(recipe,
                                               context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            get_object_or_404(ShoppingCart, user=request.user,
                              recipe=recipe).delete()
            return Response({'detail': 'Рецепт удален из списка.'},
                            status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"],
            renderer_classes=[TXTShoppingCartRenderer])
    def download_shopping_cart(self, request):
        queryset = RecipeIngredient.objects.filter(
            recipe__shopping_cart_recipe__user=request.user).values(
                'ingredient__name',
                'ingredient__measurement_unit').annotate(
                    amount=Sum('amount')).order_by('ingredient__name')

        now = timezone.now()
        file_name = (f"shopping_cart_{now:%Y-%m-%d_%H-%M-%S}"
                     f".{request.accepted_renderer.format}")
        serializer = DownloadSCSerializer(queryset, many=True)
        return Response(
            serializer.data,
            headers={
                "Content-Disposition": f'attachment; filename="{file_name}"'
            }
        )


class CustomUserViewSet(UserViewSet):
    '''Кастомный вьюсет, наследованный от Djoser,
    расширен queryset.'''

    def get_queryset(self):
        queryset = User.objects.all()
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    @action(methods=['post', 'delete'], detail=True,)
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data={'subscriber': request.user.id,
                      'author': author.id}
            )
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(
                author=author,
                subscriber=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            get_object_or_404(Subscription, author=author,
                              subscriber=request.user).delete()
            return Response({'detail': 'Отписка.'},
                            status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=False)
    def subscriptions(self, request):

        authors = User.objects.filter(subscription__subscriber=request.user.id)
        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = UserSubscriptionSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = UserSubscriptionSerializer(
            authors, many=True, context={'request': request})
        return Response(serializer.data)


class IngredietViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filterset_class = IngredientFilter
