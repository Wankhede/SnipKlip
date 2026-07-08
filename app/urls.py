from django.contrib import admin
from django.urls import path, re_path
import debug_toolbar
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import TemplateView
from django.conf.urls import include
from django.contrib.auth import views as auth_views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

urlpatterns = [
    path('api/v3/',include('api.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('account-management/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name="schema"),
    path('api/schema/docs', SpectacularSwaggerView.as_view(url_name="schema")),
    path('accounts/', include('allauth.urls')),
]
urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
