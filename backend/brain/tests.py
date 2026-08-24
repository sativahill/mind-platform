from contextlib import contextmanager
from copy import deepcopy
from unittest.mock import patch

from django.db import transaction
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User

from .models import Brain
from .services import (
    deep_merge_dict,
    update_brain_data,
)


class BrainAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="brain-owner",
            email="brain-owner@example.com",
            password="test-password",
        )
        self.other_user = User.objects.create_user(
            username="other-brain-owner",
            email="other-brain-owner@example.com",
            password="test-password",
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("brain")

    def test_public_user_data_merge_preserves_siblings(self):
        Brain.objects.filter(user=self.user).update(
            data={
                "user": {
                    "name": "Pavel",
                    "age": 20,
                },
                "progress": {
                    "wins_count": 3,
                },
            }
        )

        response = self.client.post(
            self.url,
            {
                "data": {
                    "user": {
                        "name": "Paul",
                    },
                },
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.user.brain.refresh_from_db()
        self.assertEqual(
            self.user.brain.data,
            {
                "user": {
                    "name": "Paul",
                    "age": 20,
                },
                "progress": {
                    "wins_count": 3,
                },
            },
        )

    def test_public_list_payload_is_rejected(self):
        response = self.client.post(
            self.url,
            [],
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_public_string_payload_is_rejected(self):
        response = self.client.post(
            self.url,
            "invalid",
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_public_number_payload_is_rejected(self):
        response = self.client.post(
            self.url,
            42,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_public_null_payload_is_rejected(self):
        response = self.client.post(
            self.url,
            None,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_public_system_section_overwrite_is_rejected(self):
        original_data = {
            "user": {},
            "progress": {
                "wins_count": 3,
            },
        }
        Brain.objects.filter(user=self.user).update(
            data=original_data
        )

        response = self.client.post(
            self.url,
            {
                "data": {
                    "progress": {
                        "wins_count": 0,
                    },
                },
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.user.brain.refresh_from_db()
        self.assertEqual(
            self.user.brain.data,
            original_data,
        )

    def test_public_update_preserves_other_users_brain(self):
        other_data = {
            "user": {
                "name": "Other user",
            },
        }
        Brain.objects.filter(
            user=self.other_user
        ).update(data=other_data)

        response = self.client.post(
            self.url,
            {
                "id": self.other_user.brain.id,
                "data": {
                    "user": {
                        "name": "Owner",
                    },
                },
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.other_user.brain.refresh_from_db()
        self.assertEqual(
            self.other_user.brain.data,
            other_data,
        )

    def test_public_read_returns_only_current_users_brain(self):
        response = self.client.get(
            f"{self.url}?id={self.other_user.brain.id}"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["id"],
            self.user.brain.id,
        )
        self.assertNotEqual(
            response.data["id"],
            self.other_user.brain.id,
        )


class BrainServiceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="brain-service-owner",
            email="brain-service-owner@example.com",
            password="test-password",
        )

    def test_internal_update_preserves_nested_siblings(self):
        Brain.objects.filter(user=self.user).update(
            data={
                "context": {
                    "goals": {
                        "active": 2,
                    },
                    "board": {
                        "todo": 4,
                    },
                },
            }
        )

        update_brain_data(
            user=self.user,
            patch={
                "context": {
                    "goals": {
                        "active": 3,
                    },
                },
            },
        )

        self.user.brain.refresh_from_db()
        self.assertEqual(
            self.user.brain.data["context"],
            {
                "goals": {
                    "active": 3,
                },
                "board": {
                    "todo": 4,
                },
            },
        )

    def test_deep_merge_does_not_mutate_inputs(self):
        original = {
            "context": {
                "board": {
                    "todo": 4,
                },
            },
        }
        patch_data = {
            "context": {
                "goals": {
                    "active": 3,
                },
            },
        }
        original_before = deepcopy(original)
        patch_before = deepcopy(patch_data)

        merged = deep_merge_dict(
            original,
            patch_data,
        )
        merged["context"]["goals"]["active"] = 9

        self.assertEqual(original, original_before)
        self.assertEqual(patch_data, patch_before)

    def test_helper_locks_and_rereads_inside_atomic(self):
        cached_brain = self.user.brain
        cached_brain.data = {
            "context": {
                "cached": True,
            },
        }
        Brain.objects.filter(user=self.user).update(
            data={
                "context": {
                    "fresh": True,
                },
            }
        )

        real_atomic = transaction.atomic
        inside_helper_atomic = {
            "value": False,
        }

        @contextmanager
        def tracked_atomic():
            with real_atomic():
                inside_helper_atomic["value"] = True
                try:
                    yield
                finally:
                    inside_helper_atomic["value"] = False

        def get_locked_brain(**kwargs):
            self.assertTrue(
                inside_helper_atomic["value"]
            )
            return Brain.objects.get(**kwargs)

        with (
            patch(
                "brain.services.transaction.atomic",
                side_effect=tracked_atomic,
            ) as mocked_atomic,
            patch(
                "brain.services.Brain.objects."
                "select_for_update"
            ) as mocked_select_for_update,
        ):
            (
                mocked_select_for_update
                .return_value.get
                .side_effect
            ) = get_locked_brain

            update_brain_data(
                user=self.user,
                patch={
                    "progress": {
                        "wins_count": 1,
                    },
                },
            )

        mocked_atomic.assert_called_once_with()
        mocked_select_for_update.assert_called_once_with()
        self.user.brain.refresh_from_db()
        self.assertEqual(
            self.user.brain.data,
            {
                "context": {
                    "fresh": True,
                },
                "progress": {
                    "wins_count": 1,
                },
            },
        )
