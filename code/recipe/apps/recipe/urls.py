from rest_framework.routers import DefaultRouter
from django.urls import (
    path,
    include
)

from recipe.apps.recipe import views


router = DefaultRouter()
router.register('tags', views.TagViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls))
]
