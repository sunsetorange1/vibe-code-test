import os
import uuid # Not strictly needed in test, but good for understanding service logic
from app.services.storage_service import LocalStorageService
from werkzeug.datastructures import FileStorage # For type hints or direct creation if needed
from io import BytesIO
from flask import current_app # To access app.config within tests if needed

# Tests for LocalStorageService directly, using the temp_upload_folder fixture

def test_local_storage_save_and_load(temp_upload_folder, app, mock_file_storage): # app for context
    with app.app_context(): # Ensure current_app is available for LocalStorageService
        # UPLOAD_FOLDER is overridden by temp_upload_folder fixture via app.config
        service = LocalStorageService()
        assert service.upload_folder == temp_upload_folder # Verify fixture override

        # Use the mock_file_storage fixture
        # Default mock_file_storage: filename="test_file.txt", content=b"Hello, world!"

        subfolder = "my_tests/unit_tests"
        prefix = "save_test"
        relative_path = service.save(mock_file_storage, subfolder=subfolder, desired_filename_prefix=prefix)

        assert relative_path is not None
        # Path structure: <subfolder>/<prefix>_<uuid>.<original_ext_or.dat>
        # e.g. my_tests/unit_tests/save_test_uuid.txt
        # The subfolder in relative_path will be sanitized by get_safe_filename
        assert os.path.dirname(relative_path) == service.get_safe_filename(subfolder)
        assert os.path.basename(relative_path).startswith(prefix + "_")
        assert relative_path.endswith(".txt") # From default mock_file_storage

        # Verify file exists and content
        full_path = service.get_full_path(relative_path)
        assert full_path is not None
        assert os.path.exists(full_path)
        with open(full_path, 'rb') as f:
            assert f.read() == b"Hello, world!" # Default content from mock_file_storage

        # Test load_stream
        stream = service.load_stream(relative_path)
        assert stream is not None
        assert stream.read() == b"Hello, world!"
        stream.close()

def test_local_storage_delete(temp_upload_folder, app): # app for context
    with app.app_context():
        service = LocalStorageService()
        assert service.upload_folder == temp_upload_folder

        file_content = b"File to be deleted."
        mock_fs = FileStorage(stream=BytesIO(file_content), filename="delete_me.txt")

        relative_path = service.save(mock_fs, subfolder="delete_tests", desired_filename_prefix="del")
        assert relative_path is not None
        full_path = service.get_full_path(relative_path)
        assert full_path is not None
        assert os.path.exists(full_path)

        # Test delete
        assert service.delete(relative_path) is True
        assert not os.path.exists(full_path)
        assert service.delete(relative_path) is False # Deleting non-existent

def test_local_storage_save_unsafe_prefix_and_no_ext(temp_upload_folder, app):
    with app.app_context():
        service = LocalStorageService()
        assert service.upload_folder == temp_upload_folder

        mock_fs = FileStorage(stream=BytesIO(b"data"), filename="no_ext_file")
        # Test with potentially unsafe prefix and subfolder
        relative_path = service.save(mock_fs, subfolder="../unsafe_sub", desired_filename_prefix="../../try_escape")

        assert relative_path is not None
        # secure_filename on subfolder should turn "../unsafe_sub" into "unsafe_sub" or similar
        # secure_filename on prefix should turn "../../try_escape" into "try_escape" or similar

        path_parts = relative_path.split(os.sep)
        assert ".." not in path_parts # Ensure no '..' components in the final path parts

        # Check that the subfolder part is sanitized
        # e.g. "unsafe_sub" or "default" if sanitization of "../unsafe_sub" leads to empty
        # The service's get_safe_filename on subfolder should handle this.
        # If get_safe_filename("../unsafe_sub") -> "unsafe_sub"
        assert path_parts[0] == "unsafe_sub"

        # Check prefix part in filename
        filename_part = path_parts[1]
        assert filename_part.startswith("try_escape_") or filename_part.startswith("file_")


        assert relative_path.endswith(".dat") # Default extension for no_ext_file

def test_local_storage_get_full_path_traversal_protection(temp_upload_folder, app):
    with app.app_context():
        service = LocalStorageService()
        assert service.upload_folder == temp_upload_folder

        malicious_relative_path = "../../../etc/passwd"
        full_path = service.get_full_path(malicious_relative_path)
        assert full_path is None

        safe_relative_path = os.path.join("some_subfolder", "file.txt") # os.path.join for platform independence

        # Create a dummy file for this test at the expected safe location
        # This needs to be inside the temp_upload_folder structure
        expected_full_path_in_temp = os.path.join(temp_upload_folder, "some_subfolder", "file.txt")
        os.makedirs(os.path.dirname(expected_full_path_in_temp), exist_ok=True)
        with open(expected_full_path_in_temp, "w") as f: f.write("test")

        full_path_safe = service.get_full_path(safe_relative_path)
        assert full_path_safe is not None
        # Compare normalized paths
        assert os.path.normpath(full_path_safe) == os.path.normpath(expected_full_path_in_temp)
