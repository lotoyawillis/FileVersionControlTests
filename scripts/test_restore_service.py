import json
import msvcrt
import os
import stat
from http import HTTPStatus
from pathlib import Path

import pytest

from src.models.response import Response
from src.services.commit_service import CommitService
from src.services.restore_service import RestoreService


@pytest.fixture(scope='function')
def commit_service():
    return CommitService


@pytest.fixture(scope='function')
def restore_service():
    return RestoreService


@pytest.fixture(scope='function')
def directory_data(tmp_path):
    # -------------------- Creates three files and two directories within "tmp_path" directory --------------------
    (tmp_path / "test_file1.txt").write_text("This is a test file")

    nested_directory = tmp_path / "temp"
    nested_directory.mkdir()
    assert nested_directory.exists() and nested_directory.is_dir()

    (nested_directory / "test_file2.txt").write_text("This is a second test file")

    second_nested_directory = nested_directory / "nested_temp"
    second_nested_directory.mkdir()
    assert second_nested_directory.exists() and second_nested_directory.is_dir()

    (second_nested_directory / "test_file3.txt").write_text("This is a third test file")


@pytest.fixture(scope='function')
def vc_directory(tmp_path, directory_data, commit_service):
    # Packages the directory being committed into a dictionary and converts the dictionary to a JSON formatted string
    data = json.dumps({'directoryPath': str(tmp_path)})

    # Commits to create version control history
    commit_response = commit_service.commit(data)
    assert commit_response.status_code == HTTPStatus.CREATED.value

    # Ensures the version control directory was created
    version_control_directory_path = Path(f"{tmp_path}/.vc/1")
    assert version_control_directory_path.exists() and version_control_directory_path.is_dir()

    return version_control_directory_path


@pytest.fixture(scope='function')
def locked_destination_directory_data(tmp_path):
    is_accessible = True

    # Creates the directories needed for the restricted file
    destination_directory_path = Path(f"{tmp_path}/test_directory")
    destination_directory_path.mkdir()
    Path(f"{tmp_path}/test_directory/temp").mkdir()
    Path(f"{tmp_path}/test_directory/temp/nested_temp").mkdir()

    restricted_file_path = Path(f"{destination_directory_path}/temp/nested_temp/test_file3.txt")
    restricted_file_path.write_text("This is a locked file")

    # Removes all read permissions for a file to create a case where java's Files.copy
    # would fail. Only works on Mac
    current_file_permissions = restricted_file_path.stat().st_mode
    remove_all_read_permissions = current_file_permissions & ~stat.S_IRUSR & ~stat.S_IRGRP & ~stat.S_IROTH

    restricted_file_path.chmod(remove_all_read_permissions)

    # If changing the read permissions does not work, opens the file and locks it
    if os.access(restricted_file_path, os.R_OK):
        file_size = restricted_file_path.stat().st_size
        open_restricted_file = open(restricted_file_path, 'r+')
        msvcrt.locking(open_restricted_file.fileno(), msvcrt.LK_NBLCK, file_size)

        try:
            msvcrt.locking(open_restricted_file.fileno(), msvcrt.LK_NBLCK, file_size)
        except OSError:
            is_accessible = False

    # Asserts the file is in a state where attempting to restore it will fail
    assert os.access(restricted_file_path, os.R_OK) or is_accessible is False


def test_post_restore_returns_201_when_file_content_is_changed(tmp_path, vc_directory, restore_service):
    # Modifies the "test_file3.txt" file created in directory_data fixture
    test_file3_path = Path(f"{tmp_path}/temp/nested_temp/test_file3.txt")
    test_file3_path.write_text("This is a changed file")

    # Ensures "test_file3.txt" was modified
    with open(test_file3_path, mode='r') as test_file3:
        file_contents = test_file3.readlines()
    assert file_contents == ["This is a changed file"]

    # Packages the version control directory being restored and its destination directory into a dictionary
    # and converts the dictionary to a JSON formatted string
    data = json.dumps({'vcPath': str(vc_directory), 'destinationPath': str(tmp_path)})

    restore_response = restore_service.restore(data)
    response_dict = restore_response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert restore_response.status_code == HTTPStatus.CREATED.value
    assert received_response.status == HTTPStatus.CREATED.value
    assert sorted(received_response.results) == sorted(["test_file1.txt is already up to date\n",
                                                        "test_file2.txt is already up to date\n",
                                                        "test_file3.txt has been restored\n"])
    assert received_response.message == "All changed files have been restored"

    # Ensures "test_file3.txt" has been restored
    with open(f'{tmp_path}/temp/nested_temp/test_file3.txt', mode='r') as test_file3:
        file_contents = test_file3.readlines()
    assert file_contents == ["This is a third test file"]


def test_post_restore_returns_201_when_file_name_is_changed(tmp_path, vc_directory, restore_service):
    # Creates paths for the "test_file3.txt" file created in directory_data and the path it would have when renamed
    test_file3_path = Path(f"{tmp_path}/temp/nested_temp/test_file3.txt")
    renamed_test_file_path = Path(f"{tmp_path}/temp/nested_temp/renamed_test_file.txt")

    # Ensures the "test_file3.txt" file was renamed to "renamed_test_file.txt"
    os.rename(test_file3_path, renamed_test_file_path)
    assert test_file3_path.exists() is False and renamed_test_file_path.exists() is True

    # Packages the version control directory being restored and its destination directory into a dictionary
    # and converts the dictionary to a JSON formatted string
    data = json.dumps({'vcPath': str(vc_directory), 'destinationPath': str(tmp_path)})

    restore_response = restore_service.restore(data)
    response_dict = restore_response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert restore_response.status_code == HTTPStatus.CREATED.value
    assert received_response.status == HTTPStatus.CREATED.value
    assert sorted(received_response.results) == sorted(["test_file1.txt is already up to date\n",
                                                        "test_file2.txt is already up to date\n",
                                                        "test_file3.txt has been restored\n"])
    assert received_response.message == "All changed files have been restored"


def test_post_restore_returns_201_when_the_destination_directory_is_the_vc_directory_parent(tmp_path,
                                                                                            vc_directory,
                                                                                            restore_service):
    # Modifies the "test_file3.txt" file created in directory_data fixture
    test_file3_path = Path(f"{tmp_path}/temp/nested_temp/test_file3.txt")
    test_file3_path.write_text("This is a changed file")

    # Ensures "test_file3.txt" was modified
    with open(test_file3_path, mode='r') as test_file3:
        file_contents = test_file3.readlines()
    assert file_contents == ["This is a changed file"]

    # Packages the version control directory being restored and its destination directory into a dictionary
    # and converts the dictionary to a JSON formatted string
    data = json.dumps({'vcPath': str(vc_directory), 'destinationPath': str(tmp_path)})

    restore_response = restore_service.restore(data)
    response_dict = restore_response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert restore_response.status_code == HTTPStatus.CREATED.value
    assert received_response.status == HTTPStatus.CREATED.value
    assert sorted(received_response.results) == sorted(["test_file1.txt is already up to date\n",
                                                        "test_file2.txt is already up to date\n",
                                                        "test_file3.txt has been restored\n"])
    assert received_response.message == "All changed files have been restored"

    # Ensures "test_file3.txt" has been restored
    with open(f'{tmp_path}/temp/nested_temp/test_file3.txt', mode='r') as test_file3:
        file_contents = test_file3.readlines()
    assert file_contents == ["This is a third test file"]


def test_post_restore_returns_201_when_the_destination_directory_is_different_from_the_vc_directory_parent(tmp_path,
                                                                                                           vc_directory,
                                                                                                           restore_service):
    # Creates a Path variable for the destination directory, creates a directory with that Path,
    # and ensures it was created successfully
    destination_directory_path = Path(f"{tmp_path}/temp/destination")
    destination_directory_path.mkdir()
    assert destination_directory_path.exists() and destination_directory_path.is_dir()

    # Packages the version control directory being restored and its destination directory into a dictionary
    # and converts the dictionary to a JSON formatted string
    data = json.dumps(
        {'vcPath': str(vc_directory), 'destinationPath': str(destination_directory_path)})

    restore_response = restore_service.restore(data)
    response_dict = restore_response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert restore_response.status_code == HTTPStatus.CREATED.value
    assert received_response.status == HTTPStatus.CREATED.value
    assert sorted(received_response.results) == sorted(["test_file1.txt has been restored\n",
                                                        "test_file2.txt has been restored\n",
                                                        "test_file3.txt has been restored\n"])
    assert received_response.message == "All changed files have been restored"

    restored_file_locations = [Path(f"{destination_directory_path}/test_file1.txt"),
                               Path(f"{destination_directory_path}/temp/test_file2.txt"),
                               Path(f"{destination_directory_path}/temp/nested_temp/test_file3.txt")]

    for restored_file_location in restored_file_locations:
        assert restored_file_location.exists() is True

    # Ensures all three files have been restored
    with open(restored_file_locations[0], mode='r') as test_file1:
        file_contents = test_file1.readlines()
    assert file_contents == ["This is a test file"]

    with open(restored_file_locations[1], mode='r') as test_file2:
        file_contents = test_file2.readlines()
    assert file_contents == ["This is a second test file"]

    with open(restored_file_locations[2], mode='r') as test_file3:
        file_contents = test_file3.readlines()
    assert file_contents == ["This is a third test file"]


def test_post_restore_with_invalid_vc_directory_returns_400(tmp_path, restore_service):
    # Creates a Path variable for the invalid version control directory, creates a directory with that Path,
    # and ensures it was created successfully
    invalid_vc_directory_path = tmp_path / "invalid_vc_directory"
    invalid_vc_directory_path.mkdir()
    assert invalid_vc_directory_path.exists() and invalid_vc_directory_path.is_dir()

    # Packages the version control directory being restored and its destination directory into a dictionary
    # and converts the dictionary to a JSON formatted string
    data = json.dumps({'vcPath': str(invalid_vc_directory_path), 'destinationPath': str(tmp_path)})

    response = restore_service.restore(data)
    response_dict = response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST.value
    assert received_response.status == HTTPStatus.BAD_REQUEST.value
    assert received_response.results == [f"{invalid_vc_directory_path} is not a valid version control directory"]
    assert received_response.message == "The version control directory is not valid"


def test_post_restore_with_invalid_directory_returns_400(tmp_path, vc_directory, restore_service):
    # Creates a Path variable for the invalid directory
    invalid_directory_path = tmp_path / "invalid_directory"

    # Packages the version control directory being restored and its destination directory into a dictionary
    # and converts the dictionary to a JSON formatted string
    data = json.dumps({'vcPath': str(vc_directory), 'destinationPath': str(invalid_directory_path)})

    response = restore_service.restore(data)
    response_dict = response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST.value
    assert received_response.status == HTTPStatus.BAD_REQUEST.value
    assert received_response.results == [f"{invalid_directory_path} is not a directory"]
    assert received_response.message == "The destination directory is not valid"


def test_post_restore_with_invalid_vc_directory_and_invalid_directory_returns_400(tmp_path, restore_service):
    # Creates Path variables for the version control directory and the invalid directory path
    invalid_version_control_directory_path = Path(f"{tmp_path}/.vc/1")
    invalid_directory_path = tmp_path / "invalid_vc_directory"

    # Packages the version control directory being restored and its destination directory into a dictionary
    # and converts the dictionary to a JSON formatted string
    data = json.dumps(
        {'vcPath': str(invalid_version_control_directory_path), 'destinationPath': str(invalid_directory_path)})

    response = restore_service.restore(data)
    response_dict = response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST.value
    assert received_response.status == HTTPStatus.BAD_REQUEST.value
    assert received_response.results == [
        f"{invalid_version_control_directory_path} is not a valid version control directory and {invalid_directory_path} is not a directory"]
    assert received_response.message == "The version control directory and the destination directory are not valid"


def test_post_restore_returns_409_when_destination_directory_is_up_to_date_with_vc_directory(tmp_path,
                                                                                             vc_directory,
                                                                                             restore_service):
    # Packages the version control directory being restored and its destination directory into a dictionary
    # and converts the dictionary to a JSON formatted string
    data = json.dumps({'vcPath': str(vc_directory), 'destinationPath': str(tmp_path)})

    response = restore_service.restore(data)
    response_dict = response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert response.status_code == HTTPStatus.CONFLICT.value
    assert received_response.status == HTTPStatus.CONFLICT.value
    assert sorted(received_response.results) == sorted(["test_file1.txt is already up to date\n",
                                                        "test_file2.txt is already up to date\n",
                                                        "test_file3.txt is already up to date\n"])
    assert received_response.message == ("The requested destination directory is up to date with the version control "
                                         "directory")


@pytest.mark.skip(reason="Locking a file in the destination directory does not prevent restore from working")
def test_post_restore_returns_500_when_a_file_cannot_be_restored(tmp_path, vc_directory,
                                                                 locked_destination_directory_data, restore_service):
    destination_directory_path = Path(f"{tmp_path}/test_directory")
    restricted_file_path = Path(f"{destination_directory_path}/temp/nested_temp/test_file3.txt")

    # Packages the version control directory being restored and its destination directory into a dictionary
    # and converts the dictionary to a JSON formatted string
    data = json.dumps(
        {'vcPath': str(vc_directory), 'destinationPath': str(destination_directory_path)})

    restore_response = restore_service.restore(data)
    response_dict = restore_response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    # Ensures "test_file3.txt" has the same contents as before it was locked
    with open(restricted_file_path, mode='r') as test_file3:
        file_contents = test_file3.readlines()
    assert file_contents == ["This is a locked file"]

    assert restore_response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR.value
    assert received_response.status == HTTPStatus.INTERNAL_SERVER_ERROR.value
    assert sorted(received_response.results) == sorted(["test_file3.txt has not been restored\n",
                                                        "test_file2.txt has been restored\n",
                                                        "test_file1.txt has been restored\n"])
    assert received_response.message == "Not all files have been restored"
