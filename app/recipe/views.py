from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import (
    RecipeDetailSerializer,
    RecipeImageSerializer,
    RecipeSerializer,
    TagSerializer,
    IngredientSerializer
)


class BaseRecipeAttr(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        """only returns objects for current authenticated user"""
        return self.queryset.filter(user=self.request.user).order_by('-name')

    def perform_create(self, serializer):
        """add current authenticated user to tag"""
        serializer.save(user=self.request.user)


class TagViewSet(BaseRecipeAttr):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(BaseRecipeAttr):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )

    def _params_to_int(self, qs):
        """converts a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """only returns objects for current authenticated user"""
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_int(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredient_ids = self._params_to_int(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)

        return queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """returns appropritae serializer class for detail and others"""
        if self.action == 'retrieve':
            return RecipeDetailSerializer
        elif self.action == 'upload_image':
            return RecipeImageSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        """add current authenticated user to recipe"""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """upload an image to a recipe"""
        recipe = self.get_object()
        serializer = self.get_serializer(
            recipe,
            data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
