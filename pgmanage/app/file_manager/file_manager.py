import os
import pathlib
import time
from typing import Optional, Dict, Any

from pgmanage.settings import DESKTOP_MODE, HOME_DIR


class FileManagerError(Exception):
    """Raised deliberately by FileManager with a message that is safe to show to the client."""


class FileManager:
    def __init__(self, current_user):
        self.user = current_user
        self.storage = self._get_storage_directory()

    def _get_storage_directory(self) -> Optional[str]:
        """
        Get the storage directory for the current user, creating it if it does not exist.

        Returns:
            Optional[str]: The absolute path to the user's storage directory if not in desktop mode,
            otherwise None.
        """
        if not DESKTOP_MODE:
            storage_dir = os.path.join(HOME_DIR, "storage", str(self.user.id))

            if not os.path.exists(storage_dir):
                os.makedirs(storage_dir)

            return storage_dir
        return None

    def _create_file(self, path: str) -> None:
        """Create an empty file at the specified path."""
        with open(path, mode="w") as fp:
            pass

    def _create_dir(self, path: str) -> None:
        """Create a directory at the specified path."""
        os.makedirs(path, exist_ok=True)

    def _assert_not_exists(self, path: str) -> None:
        """Raise an error if the path already exists."""
        if os.path.exists(path):
            raise FileManagerError("File or directory with given name already exists.")

    def validate_name(self, name: str) -> None:
        """Raise an error if the given file/directory name is not a single, well-formed path segment."""
        if not name or name in (".", "..") or any(
            char in name for char in ("/", "\\", "\x00")
        ):
            raise ValueError("Invalid file or directory name.")

    def assert_exists(self, path: str) -> None:
        """Raise an error if the path does not exist."""
        if not os.path.exists(path):
            raise FileManagerError("Invalid file or directory path.")

    def _format_size(self, num: float, suffix: str = "B") -> str:
        """
        Format file size into human-readable format.

        Args:
            num: The file size in bytes.
            suffix: The suffix to append (default is "B").

        Returns:
            str: The formatted file size.
        """
        for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
            if abs(num) < 1024.0:
                return f"{num:3.1f}{unit}{suffix}"
            num /= 1024.0

        return f"{num:.1f} {suffix}"

    def create(self, path: str, name: str, file_type: str) -> None:
        """
        Create a file or directory.

        Args:
            path: The relative path within the storage directory.
            name: The name of the file or directory to create.
            file_type: The type of entity to create ("file" or "dir").
        """
        self.validate_name(name)

        normalized_path = "." if path == "/" else os.path.normpath(path.lstrip('/'))
        abs_path = self.resolve_path(normalized_path)
        full_path = os.path.abspath(os.path.join(abs_path, name))

        self.check_access_permission(full_path)
        self._assert_not_exists(full_path)

        if file_type == "dir":
            self._create_dir(full_path)
        elif file_type == "file":
            self._create_file(full_path)

    def get_directory_content(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the contents of a directory.

        Args:
            path: The relative path of the directory (default is the root storage directory).

        Returns:
            dict: A dictionary containing the directory's content metadata.
        """
        abs_path = ""
        if path is None:
            abs_path = self.storage
        else:
            normalized_path = "." if path == "/" else os.path.normpath(path.lstrip('/'))
            abs_path = os.path.join(self.storage, normalized_path)

        rel_path = os.path.relpath(abs_path, self.storage)

        self.check_access_permission(abs_path)

        if rel_path == ".":
            current_path = "/"
        else:
            current_path = f"/{rel_path}"

        data = {
            "parent": abs_path != self.storage,
            "current_path": current_path,
            "files": [],
        }

        directory_content = os.listdir(abs_path)
        if not directory_content:
            return data

        for file in directory_content:

            file_path = os.path.join(abs_path, file)
            rel_file_path = os.path.join(rel_path, file)
            file_size = os.path.getsize(file_path)
            is_directory = os.path.isdir(file_path)
            file_type = self._get_file_extension(file)
            created = os.path.getctime(file_path)
            modified = os.path.getmtime(file_path)
            dir_size = None
            if os.path.isdir(file_path):
                dir_size = len(os.listdir(file_path))

            data["files"].append(
                {
                    "file_name": file,
                    "path": rel_file_path,
                    "file_size": self._format_size(file_size),
                    "is_directory": is_directory,
                    "type": file_type,
                    "created": time.ctime(created),
                    "modified": time.ctime(modified),
                    "dir_size": dir_size,
                }
            )

        return data

    def get_parent_directory_content(self, path: str) -> Dict[str, Any]:
        """
        Get the contents of the parent directory of the specified path.

        Args:
            path: The relative path of the current directory.

        Returns:
            dict: The parent directory's content metadata.
        """
        return self.get_directory_content(os.path.dirname(path))

    def rename(self, path: str, name: str) -> None:
        """
        Rename a file or directory.

        Args:
            path: The relative path of the file or directory.
            name: The new name.
        """
        self.validate_name(name)

        abs_path = self.resolve_path(path)

        self.check_access_permission(abs_path)
        self.assert_exists(abs_path)

        dirpath, _ = os.path.split(abs_path)

        new_path = os.path.join(dirpath, name)

        self.check_access_permission(new_path)
        self._assert_not_exists(new_path)

        os.rename(abs_path, new_path)

    def delete(self, path: str) -> None:
        """
        Delete a file or directory.

        Args:
            path: The relative path of the file or directory.
        """
        abs_path = self.resolve_path(path)

        self.check_access_permission(abs_path)

        self.assert_exists(abs_path)

        if os.path.isdir(abs_path):
            os.rmdir(abs_path)

        elif os.path.isfile(abs_path):
            os.remove(abs_path)

    def check_access_permission(self, path: str) -> None:
        """
        Check if the path is within the allowed storage directory.

        Args:
            path: The absolute or relative path to check.

        Raises:
            FileManagerError: If the path is outside the allowed storage directory.
        """
        if DESKTOP_MODE:
            return

        abs_path = os.path.abspath(path)

        if not pathlib.Path(abs_path).is_relative_to(self.storage):
            raise FileManagerError("Access denied")

    def _get_file_extension(self, file_name: str) -> str:
        """
        Get the file extension of a file.

        Args:
            file_name: The file name.

        Returns:
            str: The file extension (lowercase, without the leading dot).
        """
        _, extension = os.path.splitext(file_name)
        return extension.lstrip(".").lower() if extension else ""

    def resolve_path(self, path: str) -> str:
        """
        Normalize and resolve the absolute path.

        Args:
            path: The relative path to resolve.

        Returns:
            str: The resolved absolute path.

        """
        if DESKTOP_MODE:
            return path

        normalized_path = os.path.normpath(path)
        abs_path = os.path.join(self.storage, normalized_path)

        return abs_path
