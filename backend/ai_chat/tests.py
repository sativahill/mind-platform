from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APIClient

from .models import Chat, Message


User = get_user_model()


class AIChatTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="chat-user",
            email="chat-user@example.com",
            password="testpass123",
        )

        self.other_user = User.objects.create_user(
            username="chat-other",
            email="chat-other@example.com",
            password="testpass123",
        )

        self.client.force_authenticate(
            user=self.user
        )

        self.chat = Chat.objects.create(
            user=self.user,
            title="English B2",
        )

        self.other_chat = Chat.objects.create(
            user=self.user,
            title="Sport",
        )

        self.foreign_chat = Chat.objects.create(
            user=self.other_user,
            title="Private Chat",
        )

        self.chat_url = "/api/chats/"
        self.messages_url = (
            f"/api/chats/{self.chat.id}/messages/"
        )

    def test_chat_list_requires_authentication(self):
        self.client.force_authenticate(
            user=None
        )

        response = self.client.get(
            self.chat_url
        )

        self.assertIn(
            response.status_code,
            (401, 403),
        )

    def test_message_list_requires_authentication(self):
        self.client.force_authenticate(
            user=None
        )

        response = self.client.get(
            self.messages_url
        )

        self.assertIn(
            response.status_code,
            (401, 403),
        )

    def test_user_only_sees_own_chats(self):
        response = self.client.get(
            self.chat_url
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        ids = {
            item["id"]
            for item in response.data
        }

        self.assertIn(
            self.chat.id,
            ids,
        )

        self.assertIn(
            self.other_chat.id,
            ids,
        )

        self.assertNotIn(
            self.foreign_chat.id,
            ids,
        )

    def test_create_chat(self):
        response = self.client.post(
            self.chat_url,
            {
                "title": "Programming",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["title"],
            "Programming",
        )

        chat = Chat.objects.get(
            id=response.data["id"]
        )

        self.assertEqual(
            chat.user,
            self.user,
        )

    def test_create_chat_strips_title(self):
        response = self.client.post(
            self.chat_url,
            {
                "title": "   Programming   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["title"],
            "Programming",
        )

    def test_create_chat_rejects_empty_title(self):
        response = self.client.post(
            self.chat_url,
            {
                "title": "     ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "title",
            response.data,
        )

    def test_cannot_access_foreign_chat_messages(self):
        url = (
            f"/api/chats/"
            f"{self.foreign_chat.id}/messages/"
        )

        response = self.client.get(
            url
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_get_messages_in_chronological_order(self):
        first = Message.objects.create(
            chat=self.chat,
            role=Message.USER,
            content="First",
        )

        second = Message.objects.create(
            chat=self.chat,
            role=Message.ASSISTANT,
            content="Second",
        )

        response = self.client.get(
            self.messages_url
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            2,
        )

        self.assertEqual(
            response.data[0]["id"],
            first.id,
        )

        self.assertEqual(
            response.data[1]["id"],
            second.id,
        )

    def test_message_list_does_not_include_other_chat_messages(self):
        Message.objects.create(
            chat=self.chat,
            role=Message.USER,
            content="Own message",
        )

        Message.objects.create(
            chat=self.other_chat,
            role=Message.USER,
            content="Other chat message",
        )

        response = self.client.get(
            self.messages_url
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        contents = [
            item["content"]
            for item in response.data
        ]

        self.assertEqual(
            contents,
            ["Own message"],
        )

    @patch(
        "ai_chat.views.generate_ai_response"
    )
    def test_post_message_creates_user_and_assistant_messages(
        self,
        mock_generate,
    ):
        mock_generate.return_value = (
            "AI response"
        )

        response = self.client.post(
            self.messages_url,
            {
                "content": "Hello",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["role"],
            Message.ASSISTANT,
        )

        self.assertEqual(
            response.data["content"],
            "AI response",
        )

        messages = list(
            Message.objects
            .filter(chat=self.chat)
            .order_by("created_at")
        )

        self.assertEqual(
            len(messages),
            2,
        )

        self.assertEqual(
            messages[0].role,
            Message.USER,
        )

        self.assertEqual(
            messages[0].content,
            "Hello",
        )

        self.assertEqual(
            messages[1].role,
            Message.ASSISTANT,
        )

        self.assertEqual(
            messages[1].content,
            "AI response",
        )

    @patch(
        "ai_chat.views.generate_ai_response"
    )
    def test_post_message_strips_content(
        self,
        mock_generate,
    ):
        mock_generate.return_value = "Response"

        self.client.post(
            self.messages_url,
            {
                "content": "   Hello there   ",
            },
            format="json",
        )

        message = (
            Message.objects
            .filter(
                chat=self.chat,
                role=Message.USER,
            )
            .latest("id")
        )

        self.assertEqual(
            message.content,
            "Hello there",
        )

    @patch(
        "ai_chat.views.generate_ai_response"
    )
    def test_post_message_rejects_empty_content(
        self,
        mock_generate,
    ):
        response = self.client.post(
            self.messages_url,
            {
                "content": "     ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertFalse(
            mock_generate.called
        )

        self.assertEqual(
            Message.objects
            .filter(chat=self.chat)
            .count(),
            0,
        )

    @patch(
        "ai_chat.views.generate_ai_response"
    )
    def test_user_cannot_choose_message_role(
        self,
        mock_generate,
    ):
        mock_generate.return_value = "Response"

        self.client.post(
            self.messages_url,
            {
                "content": "Hello",
                "role": "assistant",
            },
            format="json",
        )

        user_message = (
            Message.objects
            .filter(
                chat=self.chat,
                content="Hello",
            )
            .get()
        )

        self.assertEqual(
            user_message.role,
            Message.USER,
        )

    @patch(
        "ai_chat.views.generate_ai_response"
    )
    def test_current_chat_title_is_passed_to_ai(
        self,
        mock_generate,
    ):
        mock_generate.return_value = "Response"

        self.client.post(
            self.messages_url,
            {
                "content": "Hello",
            },
            format="json",
        )

        self.assertTrue(
            mock_generate.called
        )

        kwargs = (
            mock_generate
            .call_args
            .kwargs
        )

        self.assertEqual(
            kwargs[
                "current_chat_title"
            ],
            "English B2",
        )

    @patch(
        "ai_chat.views.generate_ai_response"
    )
    def test_other_user_chat_titles_are_passed_to_ai(
        self,
        mock_generate,
    ):
        mock_generate.return_value = "Response"

        Chat.objects.create(
            user=self.user,
            title="Wardrobe",
        )

        self.client.post(
            self.messages_url,
            {
                "content": "Hello",
            },
            format="json",
        )

        kwargs = (
            mock_generate
            .call_args
            .kwargs
        )

        titles = set(
            kwargs[
                "other_chat_titles"
            ]
        )

        self.assertIn(
            "Sport",
            titles,
        )

        self.assertIn(
            "Wardrobe",
            titles,
        )

        self.assertNotIn(
            "English B2",
            titles,
        )

        self.assertNotIn(
            "Private Chat",
            titles,
        )

    @patch(
        "ai_chat.views.generate_ai_response"
    )
    def test_foreign_user_chat_is_not_passed_to_ai(
        self,
        mock_generate,
    ):
        mock_generate.return_value = "Response"

        self.client.post(
            self.messages_url,
            {
                "content": "Hello",
            },
            format="json",
        )

        kwargs = (
            mock_generate
            .call_args
            .kwargs
        )

        self.assertNotIn(
            "Private Chat",
            kwargs[
                "other_chat_titles"
            ],
        )

    @patch(
        "ai_chat.views.generate_ai_response"
    )
    def test_current_user_message_is_passed_to_ai(
        self,
        mock_generate,
    ):
        mock_generate.return_value = "Response"

        self.client.post(
            self.messages_url,
            {
                "content": "Latest message",
            },
            format="json",
        )

        kwargs = (
            mock_generate
            .call_args
            .kwargs
        )

        messages = kwargs["messages"]

        self.assertEqual(
            messages[-1].role,
            Message.USER,
        )

        self.assertEqual(
            messages[-1].content,
            "Latest message",
        )

    @patch(
        "ai_chat.views.generate_ai_response"
    )
    def test_only_last_twenty_previous_messages_are_passed_to_ai(
        self,
        mock_generate,
    ):
        mock_generate.return_value = "Response"

        for index in range(25):
            Message.objects.create(
                chat=self.chat,
                role=(
                    Message.USER
                    if index % 2 == 0
                    else Message.ASSISTANT
                ),
                content=f"Message {index}",
            )

        self.client.post(
            self.messages_url,
            {
                "content": "Latest",
            },
            format="json",
        )

        kwargs = (
            mock_generate
            .call_args
            .kwargs
        )

        messages = kwargs["messages"]

        self.assertEqual(
            len(messages),
            21,
        )

        self.assertEqual(
            messages[0].content,
            "Message 5",
        )

        self.assertEqual(
            messages[-2].content,
            "Message 24",
        )

        self.assertEqual(
            messages[-1].content,
            "Latest",
        )

    @patch(
        "ai_chat.views.generate_ai_response"
    )
    def test_ai_history_is_chronological(
        self,
        mock_generate,
    ):
        mock_generate.return_value = "Response"

        for index in range(4):
            Message.objects.create(
                chat=self.chat,
                role=Message.USER,
                content=f"Message {index}",
            )

        self.client.post(
            self.messages_url,
            {
                "content": "Latest",
            },
            format="json",
        )

        messages = (
            mock_generate
            .call_args
            .kwargs[
                "messages"
            ]
        )

        contents = [
            message.content
            for message in messages
        ]

        self.assertEqual(
            contents,
            [
                "Message 0",
                "Message 1",
                "Message 2",
                "Message 3",
                "Latest",
            ],
        )

    @patch(
        "ai_chat.views.generate_ai_response"
    )
    def test_post_message_updates_chat_updated_at(
        self,
        mock_generate,
    ):
        mock_generate.return_value = "Response"

        old_time = timezone.now()

        Chat.objects.filter(
            id=self.chat.id
        ).update(
            updated_at=old_time
            - timezone.timedelta(
                hours=2
            )
        )

        self.chat.refresh_from_db()

        previous_updated_at = (
            self.chat.updated_at
        )

        self.client.post(
            self.messages_url,
            {
                "content": "Hello",
            },
            format="json",
        )

        self.chat.refresh_from_db()

        self.assertGreater(
            self.chat.updated_at,
            previous_updated_at,
        )

    @patch(
        "ai_chat.views.generate_ai_response"
    )
    def test_ai_response_is_saved_as_assistant(
        self,
        mock_generate,
    ):
        mock_generate.return_value = (
            "Generated answer"
        )

        self.client.post(
            self.messages_url,
            {
                "content": "Question",
            },
            format="json",
        )

        assistant_message = (
            Message.objects
            .filter(
                chat=self.chat,
                role=Message.ASSISTANT,
            )
            .get()
        )

        self.assertEqual(
            assistant_message.content,
            "Generated answer",
        )

    @patch(
        "ai_chat.views.generate_ai_response"
    )
    def test_brain_is_passed_to_ai(
        self,
        mock_generate,
    ):
        mock_generate.return_value = "Response"

        self.client.post(
            self.messages_url,
            {
                "content": "Hello",
            },
            format="json",
        )

        kwargs = (
            mock_generate
            .call_args
            .kwargs
        )

        self.assertIn(
            "brain",
            kwargs,
        )

        expected_brain = getattr(
            self.user,
            "brain",
            None,
        )

        self.assertEqual(
            kwargs["brain"],
            expected_brain,
        )

    def test_foreign_user_cannot_post_message_to_chat(self):
        url = (
            f"/api/chats/"
            f"{self.foreign_chat.id}/messages/"
        )

        response = self.client.post(
            url,
            {
                "content": "Hello",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertFalse(
            Message.objects
            .filter(
                chat=self.foreign_chat,
                content="Hello",
            )
            .exists()
        )
