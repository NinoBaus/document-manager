import hashlib
from copy import deepcopy

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from propylon_document_manager.file_versions.models import FileVersion, FilePermissions
from .factories import UserFactory


class TestFileVersionModelSave(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.file_content = b"Hello world"
        self.file = SimpleUploadedFile("test.txt", self.file_content, content_type="text/plain")

    def test_file_model_creation(self):
        file_version = FileVersion.objects.create(
            file_name="test.txt",
            revision=1,
            user=self.user,
            path="documents/test",
            file=self.file
        )

        expected_hash = hashlib.sha256(self.file_content).hexdigest()
        self.assertEqual(file_version.revision, 1)
        self.assertIn("test.txt", file_version.file.name)
        self.assertEqual(file_version.content_hash, expected_hash)
        self.assertTrue(file_version.created_at)


class TestFileVersionAPI(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.file_name = "test.txt"
        self.file = SimpleUploadedFile(self.file_name, b"Hello world", content_type="text/plain")
        self.path = "documents/test"

        self.url = reverse("api:file_versions-list")

    def test_file_upload_creates_fileversion(self):
        data = {
            "path": self.path,
            "file": self.file
        }
        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        file_version = FileVersion.objects.get(pk=response.data["id"])
        self.assertEqual(file_version.user, self.user)
        self.assertEqual(file_version.path, self.path)
        self.assertIn(self.file_name, file_version.file.name)
        self.assertEqual(file_version.revision, 1)
        self.assertIsNotNone(file_version.content_hash)

    def test_multiple_file_upload_creates_fileversion(self):
        request_file = deepcopy(self.file)
        file_version_1 = FileVersion.objects.create(
            file_name=self.file_name,
            revision=1,
            user=self.user,
            path=self.path,
            file=self.file
        )
        data = {
            "path": self.path,
            "file": request_file
        }

        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        file_version_2 = FileVersion.objects.get(pk=response.data["id"])
        self.assertIn(file_version_1.file_name, file_version_2.file_name)
        self.assertIn(file_version_1.content_hash, file_version_2.content_hash)
        self.assertEqual(file_version_1.revision, 1)
        self.assertEqual(file_version_2.revision, 2)


class TestFileVersionAPIGet(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.second_user = UserFactory(email="some_random@user.com")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.file_name = "test.txt"
        self.file = SimpleUploadedFile(self.file_name, b"Hello world", content_type="text/plain")
        self.file_version = FileVersion.objects.create(
            file_name=self.file_name,
            path="documents/test",
            user=self.user,
            file=self.file,
        )

    def test_list_file_versions(self):
        url = reverse("api:file_versions-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["file_name"], self.file_name)

    def test_retrieve_single_file_version(self):
        url = reverse("api:file_versions-detail", args=[self.file_version.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["file_name"], self.file_name)
        self.assertEqual(response.data["path"], "documents/test")

    def test_get_by_cas_hash(self):
        url = reverse("file_cas", args=[self.file_version.content_hash])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["file_name"], "test.txt")

    def test_get_list_file_versions_by_another_user(self):
        url = reverse("api:file_versions-list")
        self.client.force_authenticate(user=self.second_user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_get_by_directory_and_file_name(self):
        url = reverse("file_cas", args=[self.file_version.content_hash])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["file_name"], "test.txt")


class TestFileDownloadAPI(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.user.save()

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.file_name = "download.txt"
        self.file_path = "documents/test"
        self.file = SimpleUploadedFile(self.file_name, b"Hello World!", content_type="text/plain")
        self.file_version = FileVersion.objects.create(
            file_name=self.file_name,
            path=self.file_path,
            user=self.user,
            file=self.file,
        )

    def test_download_file(self):
        file_path = f"{self.file_path}/{self.file_name}"
        url = reverse("serve_file", args=[file_path])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertIn(b"Hello World!", response.streaming_content)

    def test_download_nonexistent_file(self):
        url = reverse("serve_file", args=[f"{self.user.id}/does/not/exist.txt"])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestFilePermissions(APITestCase):
    def setUp(self):
        self.owner = UserFactory()
        self.owner.save()

        self.user = UserFactory()
        self.user.save()

        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

        self.file_name = "download.txt"
        self.file_path = "documents/test"
        self.file = SimpleUploadedFile(self.file_name, b"Hello World!", content_type="text/plain")
        self.file_version = FileVersion(
            file_name=self.file_name,
            path=self.file_path,
            user=self.owner,
            file=self.file,
        )
        self.file_version.save()
        self.data = {
            "user": self.user.email,
            "file": self.file_version.pk,
            "permissions": FilePermissions.READ
        }

    def test_file_permissions_creation(self):
        url = reverse("api:file_permissions-list")
        qs = FilePermissions.objects.filter(owner=self.owner)
        self.assertFalse(qs.exists())

        response = self.client.post(url, self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['file'], self.file_version.pk)
        self.assertEqual(response.data["user"], self.user.email)
        self.assertEqual(response.data["permissions"], FilePermissions.READ)
        qs = FilePermissions.objects.filter(owner=self.owner)
        self.assertTrue(qs.exists())

    def test_file_permissions_read(self):
        add_permissions_url = reverse("api:file_permissions-list")
        self.client.post(add_permissions_url, self.data)

        self.client.force_authenticate(self.user)
        get_files_url = reverse("api:file_versions-list")
        response = self.client.get(get_files_url)
        self.assertEqual(response.data[0]["id"], self.file_version.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        get_file_detail_url = reverse("api:file_versions-detail", kwargs={"id": self.file_version.pk})
        response = self.client.get(get_file_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.file_version.pk)

        response = self.client.delete(get_file_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_file_permissions_read_write(self):
        add_permissions_url = reverse("api:file_permissions-list")
        self.data["permissions"] = "read_write"
        self.client.post(add_permissions_url, self.data)

        self.client.force_authenticate(self.user)
        get_files_url = reverse("api:file_versions-list")
        response = self.client.get(get_files_url)
        self.assertEqual(response.data[0]["id"], self.file_version.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        get_file_detail_url = reverse("api:file_versions-detail", kwargs={"id": self.file_version.pk})
        response = self.client.get(get_file_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.file_version.pk)

        response = self.client.delete(get_file_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
