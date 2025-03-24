"""
URL configuration for periwinkleposts project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view as swagger_get_schema_view
from django.conf import settings
import django.views.static

schema_view = swagger_get_schema_view(
    openapi.Info(
        title="Periwinkle API",
        default_version="1.0.0",
        description="API documentation of Periwinkle node"
    ),
    public=True
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('pages/', include('pages.urls', namespace ='pages')),
    path('accounts/', include('accounts.urls')),
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)), 
    path('api/', include('api.urls')),
    path('api/', include('inbox.urls')),
    path('api/docs', schema_view.with_ui('swagger', cache_timeout=0), name="docs")
]

# thank god stackexchange had a fix for this -- DO NOT USE THIS IN PRODUCTION!! Caddy and Docker will serve in production. We should be testing production weeks before the due date.
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', django.views.static.serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]