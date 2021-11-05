from django.contrib import admin
from django.urls import (
    path,
    include
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('recipe.apps.recipe.urls')),
    path('api/user/', include('recipe.apps.user.urls')),
]
