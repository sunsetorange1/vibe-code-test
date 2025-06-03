import os
import uuid
from abc import ABC, abstractmethod
from flask import current_app
from werkzeug.utils import secure_filename

class StorageService(ABC):
    @abstractmethod
    def save(self, file_storage, subfolder="default", desired_filename_prefix="file"):
        '''
        Saves a FileStorage object.
        :param file_storage: The FileStorage object from Flask's request.files.
        :param subfolder: A subfolder within the main upload directory to store the file.
        :param desired_filename_prefix: A prefix for the generated unique filename.
        :return: The relative path to the saved file within the UPLOAD_FOLDER, or None on failure.
        '''
        pass

    @abstractmethod
    def load_stream(self, relative_file_path):
        '''
        Loads a file as a stream.
        :param relative_file_path: The relative path of the file within UPLOAD_FOLDER.
        :return: A file-like object (stream), or None if file not found.
        '''
        pass

    @abstractmethod
    def delete(self, relative_file_path):
        '''
        Deletes a file.
        :param relative_file_path: The relative path of the file within UPLOAD_FOLDER.
        :return: True on success, False on failure.
        '''
        pass

    @abstractmethod
    def get_full_path(self, relative_file_path):
        '''
        Gets the full absolute path of a file.
        :param relative_file_path: The relative path of the file within UPLOAD_FOLDER.
        :return: The absolute path, or None if base UPLOAD_FOLDER is not configured or path is unsafe.
        '''
        pass

    def get_safe_filename(self, original_filename):
        """
        Generates a secure version of the original filename.
        """
        if not original_filename:
            return ''
        return secure_filename(original_filename)


class LocalStorageService(StorageService):
    def __init__(self):
        self.upload_folder = current_app.config.get('UPLOAD_FOLDER')
        if not self.upload_folder:
            current_app.logger.error("UPLOAD_FOLDER is not configured for LocalStorageService.")
            # Methods will check self.upload_folder and fail gracefully if it's None.

    def save(self, file_storage, subfolder="default", desired_filename_prefix="file"):
        if not self.upload_folder:
            current_app.logger.error("LocalStorageService cannot save: UPLOAD_FOLDER not configured.")
            return None
        if not file_storage or not file_storage.filename: # Check file_storage.filename as well
            current_app.logger.error("Invalid FileStorage object or filename provided to LocalStorageService.save().")
            return None

        original_filename_part = self.get_safe_filename(file_storage.filename)
        if not original_filename_part:
            original_filename_part = "untitled"

        unique_id = uuid.uuid4().hex
        _, ext = os.path.splitext(original_filename_part)

        safe_prefix = self.get_safe_filename(desired_filename_prefix) if desired_filename_prefix else "file"
        if not safe_prefix: # Handles cases where desired_filename_prefix is e.g. '../'
            safe_prefix = "file"

        final_ext = ext if ext else '.dat' # Ensure there's an extension
        secure_name = f"{safe_prefix}_{unique_id}{final_ext}"

        safe_subfolder = self.get_safe_filename(subfolder) # Sanitize subfolder name as well
        if not safe_subfolder: # if subfolder name is unsafe or empty
            safe_subfolder = "default"


        target_folder = os.path.join(self.upload_folder, safe_subfolder)

        try:
            if not os.path.exists(target_folder):
                os.makedirs(target_folder, exist_ok=True)

            file_path_abs = os.path.join(target_folder, secure_name)
            file_storage.save(file_path_abs)

            relative_path = os.path.join(safe_subfolder, secure_name)
            current_app.logger.info(f"File saved by LocalStorageService to: {relative_path} (abs: {file_path_abs})")
            return relative_path
        except Exception as e:
            current_app.logger.error(f"LocalStorageService failed to save file {original_filename_part} to {target_folder}: {e}", exc_info=True)
            return None

    def load_stream(self, relative_file_path):
        if not self.upload_folder:
            current_app.logger.error("LocalStorageService cannot load_stream: UPLOAD_FOLDER not configured.")
            return None
        if not relative_file_path:
            current_app.logger.warning("LocalStorageService.load_stream: relative_file_path is empty.")
            return None

        full_path = self.get_full_path(relative_file_path)
        if not full_path:
            return None

        if os.path.exists(full_path) and os.path.isfile(full_path):
            try:
                return open(full_path, 'rb')
            except Exception as e:
                current_app.logger.error(f"LocalStorageService failed to open file stream for {full_path}: {e}", exc_info=True)
                return None
        current_app.logger.warning(f"LocalStorageService: File not found at {full_path} (relative: {relative_file_path})")
        return None

    def delete(self, relative_file_path):
        if not self.upload_folder:
            current_app.logger.error("LocalStorageService cannot delete: UPLOAD_FOLDER not configured.")
            return False
        if not relative_file_path:
            current_app.logger.warning("LocalStorageService.delete: relative_file_path is empty.")
            return False

        full_path = self.get_full_path(relative_file_path)
        if not full_path:
            return False

        if os.path.exists(full_path) and os.path.isfile(full_path):
            try:
                os.remove(full_path)
                current_app.logger.info(f"LocalStorageService deleted file: {full_path}")
                return True
            except Exception as e:
                current_app.logger.error(f"LocalStorageService failed to delete file {full_path}: {e}", exc_info=True)
                return False
        current_app.logger.warning(f"LocalStorageService: File not found for deletion at {full_path} (relative: {relative_file_path})")
        return False

    def get_full_path(self, relative_file_path):
        if not self.upload_folder:
            current_app.logger.warning("LocalStorageService.get_full_path: UPLOAD_FOLDER not configured.")
            return None
        if not relative_file_path:
            current_app.logger.warning("LocalStorageService.get_full_path: relative_file_path is empty.")
            return None

        # Normalize both paths to prevent trivial escapes like '..' at the start of relative_file_path
        # before joining.
        norm_upload_folder = os.path.normpath(os.path.abspath(self.upload_folder))

        # Sanitize relative_file_path to prevent it from being absolute or trying to go "up" too much
        # os.path.join will handle some of this if relative_file_path starts with '/',
        # but an explicit check or more robust sanitization might be needed for user-supplied relative_file_path.
        # For now, assume relative_file_path is somewhat trusted or pre-validated if from user input.
        # The commonprefix check below is the main guard.

        prospective_path = os.path.normpath(os.path.join(norm_upload_folder, relative_file_path))

        if os.path.commonprefix([prospective_path, norm_upload_folder]) == norm_upload_folder:
            return prospective_path
        else:
            current_app.logger.error(f"LocalStorageService: Path traversal attempt detected or invalid path. Relative: '{relative_file_path}', Base: '{self.upload_folder}', Resolved: '{prospective_path}'")
            return None
