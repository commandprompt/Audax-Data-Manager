import os
import io
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import mock_open, patch

from app.file_manager.file_manager import FileManager
from app.views.file_manager import (
    create,
    delete,
    download,
    get_directory,
    rename,
    upload,
)
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, SimpleTestCase, TestCase
from django.urls import resolve, reverse
from django.test import override_settings

class FileManagerViewsTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client = Client()
        self.client.login(username="testuser", password="testpass")
        self.storage_path = os.path.join("user_data", self.user.username)

    @patch("app.file_manager.file_manager.FileManager.create")
    def test_create(self, mock_create):
        data = {"path": "test_dir", "name": "test_file.txt", "type": "file"}
        response = self.client.post(
            reverse("create_file_or_directory"), data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"data": "created"})
        mock_create.assert_called_once_with(data["path"], data["name"], data["type"])

    def test_create_invalid_data(self):
        data = {"name": "test_file.txt", "type": "file"}  # Missing "path"
        response = self.client.post(
            reverse("create_file_or_directory"), data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_create_url_resolves_create_view(self):
        view = resolve("/file_manager/create/")

        self.assertEqual(view.func.__name__, create.__name__)

    @patch("app.file_manager.file_manager.FileManager.get_directory_content")
    def test_get_directory(self, mock_get_directory_content):
        mock_get_directory_content.return_value = {"files": []}
        data = {"current_path": "test_dir"}
        response = self.client.post(
            reverse("get_directory"), data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"files": []})
        mock_get_directory_content.assert_called_once_with(data["current_path"])

    @patch("app.file_manager.file_manager.FileManager.get_parent_directory_content")
    def test_get_parent_directory(self, mock_get_parent_directory_content):
        mock_get_parent_directory_content.return_value = {"files": []}
        data = {"current_path": "test_dir", "parent_dir": True}
        response = self.client.post(
            reverse("get_directory"), data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"files": []})
        mock_get_parent_directory_content.assert_called_once_with(data["current_path"])

    @patch("app.file_manager.file_manager.FileManager.get_directory_content")
    def test_get_directory_no_path(self, mock_get_directory_content):
        mock_get_directory_content.return_value = {"files": []}
        data = {}
        response = self.client.post(
            reverse("get_directory"), data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"files": []})
        mock_get_directory_content.assert_called_once_with(None)

    @patch("app.file_manager.file_manager.FileManager.get_directory_content")
    def test_get_directory_raises_error(self, mock_get_directory_content):
        mock_get_directory_content.side_effect = Exception("Test error")
        data = {"current_path": "test_dir"}
        response = self.client.post(
            reverse("get_directory"), data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "Test error"})

    def test_get_directory_url_resolves_get_directory_view(self):
        view = resolve("/file_manager/get_directory/")

        self.assertEqual(view.func.__name__, get_directory.__name__)

    @patch("app.file_manager.file_manager.FileManager.rename")
    def test_rename(self, mock_rename):
        data = {"path": "test_dir/test_file.txt", "name": "new_name.txt"}
        response = self.client.post(
            reverse("rename_file_or_directory"), data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"data": "success"})
        mock_rename.assert_called_once_with(data["path"], data["name"])

    @patch("app.file_manager.file_manager.FileManager.rename")
    def test_rename_raises_error(self, mock_rename):
        mock_rename.side_effect = Exception("Test error")
        data = {"path": "test_dir/test_file.txt", "name": "new_name.txt"}
        response = self.client.post(
            reverse("rename_file_or_directory"), data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "Test error"})
        mock_rename.assert_called_once_with(data["path"], data["name"])

    def test_rename_url_resolves_rename_view(self):
        view = resolve("/file_manager/rename/")

        self.assertEqual(view.func.__name__, rename.__name__)

    @patch("app.file_manager.file_manager.FileManager.delete")
    def test_delete(self, mock_delete):
        data = {"path": "test_dir/test_file.txt"}
        response = self.client.post(
            reverse("delete_file_or_directory"), data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 204)
        mock_delete.assert_called_once_with(data["path"])

    @patch("app.file_manager.file_manager.FileManager.delete")
    def test_delete_file_not_found(self, mock_delete):
        mock_delete.side_effect = FileNotFoundError("File not found")
        data = {"path": "nonexistent_file.txt"}
        response = self.client.post(
            reverse("delete_file_or_directory"), data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "File not found"})
        mock_delete.assert_called_once_with(data["path"])

    def test_delete_url_resolves_delete_view(self):
        view = resolve("/file_manager/delete/")

        self.assertEqual(view.func.__name__, delete.__name__)

    @patch("app.file_manager.file_manager.FileManager.assert_exists")
    @patch("app.file_manager.file_manager.FileManager.resolve_path")
    @patch("builtins.open", new_callable=mock_open, read_data="file content")
    @patch("app.file_manager.file_manager.FileManager.check_access_permission")
    def test_download(
        self,
        mock_check_permission,
        mock_open_file,
        mock_resolve_path,
        mock_assert_exists,
    ):
        mock_assert_exists.return_value = True
        rel_path = "test_dir/test_file.txt"
        abs_path = os.path.join(self.storage_path, rel_path)

        mock_resolve_path.return_value = abs_path

        data = {"path": rel_path}
        response = self.client.get(
            reverse("download_file"), data, content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header("Content-Disposition"))
        self.assertIn(
            f'filename="{os.path.basename(abs_path)}"', response["Content-Disposition"]
        )
        mock_resolve_path.assert_called_once_with(rel_path)
        mock_check_permission.assert_called_once_with(abs_path)
        mock_open_file.assert_called_once_with(abs_path, "rb")

    def test_download_invalid_data(
        self,
    ):
        data = {"invalid_arg": "test_dir/test_file.txt"}
        response = self.client.get(
            reverse("download_file"), data, content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "File path is required."})

    @patch("app.file_manager.file_manager.FileManager.resolve_path")
    def test_download_raises_error(self, mock_resolve_path):
        mock_resolve_path.side_effect = Exception("Test error")
        data = {"path": "test_dir/test_file.txt"}
        response = self.client.get(
            reverse("download_file"), data, content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "Test error"})

    def test_download_url_resolves_download_view(self):
        view = resolve("/file_manager/download/")

        self.assertEqual(view.func.__name__, download.__name__)

    def _setup_mock_file(self, mock_open, initial_data=b""):
        """returns custom mock file that supports file pointer operations like seek and tell"""
        real_buffer = io.BytesIO(initial_data)

        mock_f = mock_open.return_value.__enter__.return_value
        mock_f.tell.side_effect = real_buffer.tell
        mock_f.seek.side_effect = real_buffer.seek
        mock_f.write.side_effect = real_buffer.write

        return real_buffer

    @patch("os.rename")
    @patch("app.file_manager.file_manager.FileManager.check_access_permission")
    @patch("os.path.abspath")
    @patch("builtins.open")
    def test_upload_first_chunk(self, mock_open, mock_abspath, mock_check_permission, mock_rename):
        mock_abspath.return_value = self.storage_path
        self._setup_mock_file(mock_open) # Start empty

        test_file = SimpleUploadedFile("test.txt", b"part1")

        response = self.client.post(reverse("upload_file"), {"file": test_file, "path": ".", "offset": 0, "total_size": 10})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "in_progress")
        self.assertEqual(response.json()["progress"], 50)

        expected_path = os.path.join(self.storage_path, "test.txt.incomplete")
        mock_check_permission.assert_called_once_with(expected_path)
        mock_open.assert_called_once_with(expected_path, "wb+")

    @patch("os.rename")
    @patch("app.file_manager.file_manager.FileManager.check_access_permission")
    @patch("os.path.abspath")
    @patch("builtins.open")
    def test_upload_final_chunk(self, mock_open, mock_abspath, mock_check_permission, mock_rename):
        mock_abspath.return_value = self.storage_path
        # fill the content of the first chunk, so it looks like we continue our upload
        self._setup_mock_file(mock_open, initial_data=b"part1")

        test_file = SimpleUploadedFile("test.txt", b"part2")
        response = self.client.post(reverse("upload_file"), {"file": test_file, "path": ".", "offset": 5, "total_size": 10})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "complete")
        self.assertEqual(response.json()["progress"], 100)

        expected_path = os.path.join(self.storage_path, "test.txt.incomplete")
        final_path = os.path.join(self.storage_path, "test.txt")

        mock_check_permission.assert_called_once_with(expected_path)
        mock_open.assert_called_with(expected_path, "rb+")
        mock_rename.assert_called_once_with(expected_path, final_path)

    def test_upload_no_file(self):
        response = self.client.post(reverse("upload_file"), {"path": ".", "total_size": 1})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["data"], "No file provided.")

    @patch("app.file_manager.file_manager.FileManager.resolve_path")
    @patch("builtins.open", new_callable=mock_open, read_data="file content")
    @patch("os.path.abspath")
    def test_upload_to_root(self, mock_abspath, mock_open_file, mock_resolve_path):
        file_content = b"Root test file"
        test_file = SimpleUploadedFile(
            "root_test.txt", file_content, content_type="text/plain"
        )
        mock_abspath.return_value = "/"
        response = self.client.post(
            reverse("upload_file"), {"file": test_file, "path": "/"}
        )

        self.assertEqual(response.status_code, 400)

    def test_upload_url_resolves_upload_view(self):
        view = resolve("/file_manager/upload/")

        self.assertEqual(view.func.__name__, upload.__name__)

    @override_settings(MAX_UPLOAD_SIZE=10)
    def test_upload_exceeds_size_limit(self):
        large_file_content = b"A" * (settings.MAX_UPLOAD_SIZE + 1)
        large_file = SimpleUploadedFile(
            "large_file.txt", large_file_content, content_type="text/plain"
        )

        response = self.client.post(
            reverse("upload_file"), {"file": large_file, "path": ".", "offset": 0, "total_size": len(large_file_content)}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("File size exceeds", response.json().get("data"))



class FileManagerTests(SimpleTestCase):
    """Tests for the FileManager class against a temporary storage directory."""

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.home_dir = temp_dir.name

        for target, value in (
            ("app.file_manager.file_manager.HOME_DIR", self.home_dir),
            ("app.file_manager.file_manager.DESKTOP_MODE", False),
        ):
            patcher = patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

        self.user = SimpleNamespace(id=1)
        self.file_manager = FileManager(self.user)

    def storage_path(self, *parts):
        return os.path.join(self.file_manager.storage, *parts)

    def make_file(self, name, content=b""):
        path = self.storage_path(name)
        with open(path, "wb") as file:
            file.write(content)
        return path

    def make_dir(self, name):
        path = self.storage_path(name)
        os.makedirs(path)
        return path

    def test_storage_directory_is_created_for_the_user(self):
        expected = os.path.join(self.home_dir, "storage", "1")
        self.assertEqual(self.file_manager.storage, expected)
        self.assertTrue(os.path.isdir(expected))

    def test_storage_directory_is_reused_when_it_exists(self):
        self.make_file("keep.txt")

        second = FileManager(self.user)

        self.assertEqual(second.storage, self.file_manager.storage)
        self.assertTrue(os.path.isfile(self.storage_path("keep.txt")))

    def test_each_user_gets_a_separate_storage_directory(self):
        other = FileManager(SimpleNamespace(id=2))

        self.assertNotEqual(other.storage, self.file_manager.storage)
        self.assertTrue(os.path.isdir(other.storage))

    def test_format_size_uses_bytes_below_one_kilobyte(self):
        self.assertEqual(self.file_manager._format_size(0), "0.0B")
        self.assertEqual(self.file_manager._format_size(512), "512.0B")

    def test_format_size_scales_to_larger_units(self):
        cases = [
            (1024, "1.0KB"),
            (1536, "1.5KB"),
            (1024**2, "1.0MB"),
            (1024**3, "1.0GB"),
            (1024**4, "1.0TB"),
        ]
        for size, expected in cases:
            with self.subTest(size=size):
                self.assertEqual(self.file_manager._format_size(size), expected)

    def test_format_size_keeps_the_sign_of_a_negative_value(self):
        self.assertEqual(self.file_manager._format_size(-2048), "-2.0KB")

    def test_format_size_gives_no_unit_above_the_unit_table(self):
        # The unit table stops at Z.
        self.assertEqual(self.file_manager._format_size(1024**8), "1.0 B")

    def test_format_size_accepts_a_different_suffix(self):
        self.assertEqual(self.file_manager._format_size(1024, suffix="b"), "1.0Kb")

    def test_get_file_extension(self):
        cases = [
            ("report.TXT", "txt"),
            ("dump.Sql", "sql"),
            ("archive.tar.gz", "gz"),
            ("noextension", ""),
            (".hidden", ""),
            ("trailingdot.", ""),
        ]
        for file_name, expected in cases:
            with self.subTest(file_name=file_name):
                self.assertEqual(
                    self.file_manager._get_file_extension(file_name), expected
                )

    def test_resolve_path_joins_a_relative_path_with_the_storage_directory(self):
        self.assertEqual(
            self.file_manager.resolve_path("sub/dump.sql"),
            self.storage_path("sub/dump.sql"),
        )

    def test_resolve_path_normalizes_the_path(self):
        self.assertEqual(
            self.file_manager.resolve_path("sub/./dump.sql"),
            self.storage_path("sub/dump.sql"),
        )

    def test_resolve_path_returns_an_absolute_path_unchanged(self):
        # An absolute path replaces the storage directory. check_access_permission refuses it.
        self.assertEqual(self.file_manager.resolve_path("/etc/passwd"), "/etc/passwd")

        with self.assertRaises(PermissionError):
            self.file_manager.check_access_permission("/etc/passwd")

    def test_check_access_permission_permits_a_path_in_the_storage_directory(self):
        self.assertIsNone(self.file_manager.check_access_permission(self.storage_path()))
        self.assertIsNone(
            self.file_manager.check_access_permission(self.storage_path("sub/dump.sql"))
        )

    def test_check_access_permission_refuses_a_path_outside_the_storage_directory(self):
        with self.assertRaisesMessage(PermissionError, "Access denied"):
            self.file_manager.check_access_permission("/etc/passwd")

    def test_check_access_permission_refuses_a_path_that_goes_up(self):
        with self.assertRaisesMessage(PermissionError, "Access denied"):
            self.file_manager.check_access_permission(self.storage_path("../escape"))

    def test_create_makes_a_file_in_the_root_directory(self):
        self.file_manager.create("/", "dump.sql", "file")

        path = self.storage_path("dump.sql")
        self.assertTrue(os.path.isfile(path))
        self.assertEqual(os.path.getsize(path), 0)

    def test_create_makes_a_directory_in_the_root_directory(self):
        self.file_manager.create("/", "backups", "dir")

        self.assertTrue(os.path.isdir(self.storage_path("backups")))

    def test_create_makes_a_file_in_a_sub_directory(self):
        self.make_dir("backups")

        self.file_manager.create("/backups", "dump.sql", "file")

        self.assertTrue(os.path.isfile(self.storage_path("backups/dump.sql")))

    def test_create_ignores_an_unknown_file_type(self):
        self.file_manager.create("/", "ghost", "symlink")

        self.assertFalse(os.path.exists(self.storage_path("ghost")))

    def test_create_refuses_a_name_that_exists(self):
        self.make_file("dump.sql")

        with self.assertRaisesMessage(
            FileExistsError, "File or directory with given name already exists."
        ):
            self.file_manager.create("/", "dump.sql", "file")

    def test_create_refuses_a_name_that_goes_outside_the_storage_directory(self):
        with self.assertRaisesMessage(PermissionError, "Access denied"):
            self.file_manager.create("/", "../escape.sql", "file")

        self.assertFalse(os.path.exists(os.path.join(self.home_dir, "storage", "escape.sql")))

    def test_create_refuses_a_path_that_goes_outside_the_storage_directory(self):
        with self.assertRaisesMessage(PermissionError, "Access denied"):
            self.file_manager.create("/../..", "escape", "dir")

    def test_get_directory_content_lists_the_root_directory(self):
        self.make_file("dump.sql")
        self.make_dir("backups")

        data = self.file_manager.get_directory_content()

        self.assertFalse(data["parent"])
        self.assertEqual(data["current_path"], "/")
        self.assertEqual(
            sorted(file["file_name"] for file in data["files"]), ["backups", "dump.sql"]
        )

    def test_get_directory_content_accepts_the_root_path_sign(self):
        data = self.file_manager.get_directory_content("/")

        self.assertEqual(data["current_path"], "/")
        # The parent flag is True here, but False when the caller gives no path.
        self.assertTrue(data["parent"])

    def test_get_directory_content_gives_the_metadata_of_a_file(self):
        path = self.make_file("dump.SQL", content=b"12345")

        data = self.file_manager.get_directory_content()

        entry = data["files"][0]
        self.assertEqual(entry["file_name"], "dump.SQL")
        self.assertEqual(entry["path"], "./dump.SQL")
        self.assertEqual(entry["file_size"], "5.0B")
        self.assertFalse(entry["is_directory"])
        self.assertEqual(entry["type"], "sql")
        self.assertIsNone(entry["dir_size"])
        self.assertEqual(entry["created"], time.ctime(os.path.getctime(path)))
        self.assertEqual(entry["modified"], time.ctime(os.path.getmtime(path)))

    def test_get_directory_content_counts_the_items_of_a_directory(self):
        self.make_dir("backups")
        self.make_file("backups/first.sql")
        self.make_file("backups/second.sql")

        data = self.file_manager.get_directory_content()

        entry = data["files"][0]
        self.assertTrue(entry["is_directory"])
        self.assertEqual(entry["dir_size"], 2)
        self.assertEqual(entry["type"], "")

    def test_get_directory_content_lists_a_sub_directory(self):
        self.make_dir("backups")
        self.make_file("backups/dump.sql")

        data = self.file_manager.get_directory_content("/backups")

        self.assertTrue(data["parent"])
        self.assertEqual(data["current_path"], "/backups")
        self.assertEqual(data["files"][0]["path"], "backups/dump.sql")

    def test_get_directory_content_gives_an_empty_list_for_an_empty_directory(self):
        self.make_dir("empty")

        data = self.file_manager.get_directory_content("/empty")

        self.assertEqual(data["files"], [])
        self.assertEqual(data["current_path"], "/empty")

    def test_get_directory_content_refuses_a_path_outside_the_storage_directory(self):
        with self.assertRaisesMessage(PermissionError, "Access denied"):
            self.file_manager.get_directory_content("/../..")

    def test_get_parent_directory_content_lists_the_parent_of_a_file(self):
        self.make_dir("backups")
        self.make_file("backups/dump.sql")

        data = self.file_manager.get_parent_directory_content("backups/dump.sql")

        self.assertEqual(data["current_path"], "/backups")
        self.assertEqual([file["file_name"] for file in data["files"]], ["dump.sql"])

    def test_rename_changes_the_name_of_a_file(self):
        self.make_file("old.sql", content=b"data")

        self.file_manager.rename("old.sql", "new.sql")

        self.assertFalse(os.path.exists(self.storage_path("old.sql")))
        self.assertTrue(os.path.isfile(self.storage_path("new.sql")))

    def test_rename_changes_the_name_of_a_directory(self):
        self.make_dir("old")

        self.file_manager.rename("old", "new")

        self.assertTrue(os.path.isdir(self.storage_path("new")))

    def test_rename_refuses_a_source_that_does_not_exist(self):
        with self.assertRaisesMessage(FileNotFoundError, "Invalid file or directory path."):
            self.file_manager.rename("missing.sql", "new.sql")

    def test_rename_refuses_a_name_that_exists(self):
        self.make_file("first.sql")
        self.make_file("second.sql")

        with self.assertRaisesMessage(
            FileExistsError, "File or directory with given name already exists."
        ):
            self.file_manager.rename("first.sql", "second.sql")

        self.assertTrue(os.path.isfile(self.storage_path("first.sql")))

    def test_rename_refuses_a_new_name_that_goes_outside_the_storage_directory(self):
        self.make_file("dump.sql")

        with self.assertRaisesMessage(PermissionError, "Access denied"):
            self.file_manager.rename("dump.sql", "../escape.sql")

        self.assertTrue(os.path.isfile(self.storage_path("dump.sql")))

    def test_rename_refuses_a_source_outside_the_storage_directory(self):
        with self.assertRaisesMessage(PermissionError, "Access denied"):
            self.file_manager.rename("../../etc/passwd", "dump.sql")

    def test_delete_removes_a_file(self):
        self.make_file("dump.sql")

        self.file_manager.delete("dump.sql")

        self.assertFalse(os.path.exists(self.storage_path("dump.sql")))

    def test_delete_removes_an_empty_directory(self):
        self.make_dir("empty")

        self.file_manager.delete("empty")

        self.assertFalse(os.path.exists(self.storage_path("empty")))

    def test_delete_refuses_a_path_that_does_not_exist(self):
        with self.assertRaisesMessage(FileNotFoundError, "Invalid file or directory path."):
            self.file_manager.delete("missing.sql")

    def test_delete_refuses_a_directory_that_is_not_empty(self):
        self.make_dir("backups")
        self.make_file("backups/dump.sql")

        with self.assertRaises(OSError):
            self.file_manager.delete("backups")

        self.assertTrue(os.path.isdir(self.storage_path("backups")))

    def test_delete_refuses_a_path_outside_the_storage_directory(self):
        with self.assertRaisesMessage(PermissionError, "Access denied"):
            self.file_manager.delete("../../etc")

    def test_desktop_mode_makes_no_storage_directory(self):
        with patch("app.file_manager.file_manager.DESKTOP_MODE", True):
            file_manager = FileManager(SimpleNamespace(id=99))

        self.assertIsNone(file_manager.storage)
        self.assertFalse(os.path.exists(os.path.join(self.home_dir, "storage", "99")))

    def test_desktop_mode_resolve_path_returns_the_given_path(self):
        with patch("app.file_manager.file_manager.DESKTOP_MODE", True):
            file_manager = FileManager(self.user)

            self.assertEqual(file_manager.resolve_path("/home/user/dump.sql"), "/home/user/dump.sql")
            self.assertEqual(file_manager.resolve_path("relative/dump.sql"), "relative/dump.sql")

    def test_desktop_mode_check_access_permission_permits_any_path(self):
        with patch("app.file_manager.file_manager.DESKTOP_MODE", True):
            file_manager = FileManager(self.user)

            self.assertIsNone(file_manager.check_access_permission("/etc/passwd"))
