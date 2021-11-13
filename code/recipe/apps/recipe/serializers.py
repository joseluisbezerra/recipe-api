from rest_framework import serializers

from recipe.apps.core.models import (
    Tag,
    Recipe,
    Ingredient
)


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag object"""

    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)

    def validate_name(self, value):
        if not (self.instance and value == self.instance.name):
            if Tag.objects.filter(
                name=value,
                user=self.context['request'].user
            ).exists():
                raise serializers.ValidationError(
                    "There is already a tag with this name registered."
                )

        return value


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for an ingredient object"""

    class Meta:
        model = Ingredient
        fields = ('id', 'name')
        read_only_fields = ('id',)

    def validate_name(self, value):
        if not (self.instance and value == self.instance.name):
            if Ingredient.objects.filter(
                name=value,
                user=self.context['request'].user
            ).exists():
                raise serializers.ValidationError(
                    "There is already a ingredient with this name registered."
                )

        return value


class RecipeSerializer(serializers.ModelSerializer):
    """Serialize a recipe"""
    ingredients = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Ingredient.objects.all(),
        required=False
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=False
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'image',
            'title',
            'ingredients',
            'tags',
            'time_minutes',
            'price',
            'link'
        )
        read_only_fields = ('id',)

    def validate_time_minutes(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "The time in minutes cannot be less than one"
            )

        return value

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Price cannot be negative"
            )

        return value

    def validate_title(self, value):
        if not (self.instance and value == self.instance.title):
            if Recipe.objects.filter(
                title=value,
                user=self.context['request'].user
            ).exists():
                raise serializers.ValidationError(
                    "There is already a recipe with this title registered."
                )

        return value


class RecipeDetailSerializer(RecipeSerializer):
    """Serialize a recipe detail"""
    ingredients = IngredientSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
