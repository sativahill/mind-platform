from django.urls import path

from .views import (
    ChatView,
    MessageView,
)


urlpatterns = [
    path(
        "",
        ChatView.as_view(),
        name="chats",
    ),

    path(
        "<int:chat_id>/messages/",
        MessageView.as_view(),
        name="chat-messages",
    ),
]