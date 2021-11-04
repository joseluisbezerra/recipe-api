from django.contrib import admin
from django.urls import (
    path,
    include
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/', include('recipe.apps.user.urls')),
    path('api/recipe/', include('recipe.apps.recipe.urls')),
]
