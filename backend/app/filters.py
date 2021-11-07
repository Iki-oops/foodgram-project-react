from django_filters import rest_framework as django_filters

from .models import Recipe


class RecipeFilter(django_filters.FilterSet):
    author = django_filters.CharFilter(
        field_name='author__username',
        lookup_expr='icontains'
    )
    is_favorited = django_filters.NumberFilter(
        method='filter_favorited'
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'is_favorited', 'is_in_shopping_cart')

    @property
    def qs(self):
        queryset = super().qs
        tags = dict(self.request.query_params).get('tags', None)
        if tags:
            for tag in tags:
                queryset = queryset.filter(tags__slug=tag)
        return queryset
    
    def filter_favorited(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            favorites = self.request.user.favorites.all()
            ids = [i.recipe.id for i in favorites]
            return queryset.filter(id__in=ids)
        return queryset

    def filter_in_shopping_cart(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            in_shopping_cart = self.request.user.shoppings.all()
            ids = [i.recipe.id for i in in_shopping_cart]
            return queryset.filter(id__in=ids)
        return queryset
