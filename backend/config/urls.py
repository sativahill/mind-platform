from django.contrib import admin
from django.urls import include, path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    path(
        "api/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),

    path(
        "api/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),

    path('api/brain/', include("brain.urls")),

    path('api/daily-logs/', include("daily_logs.urls")),

    path('api/wins/', include("wins.urls")),

    path('api/chats/', include("ai_chat.urls")),

    path('api/home/', include("home.urls")),

    path('api/goals/', include("goals.urls")),

    path('api/board/', include("board.urls")),

    path('api/habits/', include("habits.urls")),

    path('api/register/', include("users.urls")),
    
    

    
]
