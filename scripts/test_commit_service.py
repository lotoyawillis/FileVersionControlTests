import json
import msvcrt
import os
import stat
from http import HTTPStatus
from pathlib import Path

import pytest

from src.models.response import Response
from src.services.commit_service import CommitService


@pytest.fixture(scope='function')
def commit_service():
    return CommitService


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


def test_post_commit_returns_201_when_vc_directory_does_not_exist(tmp_path, directory_data, commit_service):
    # Packages the directory being committed into a dictionary and converts the dictionary to a JSON formatted string
    data = json.dumps({'directoryPath': str(tmp_path)})

    response = commit_service.commit(data)
    response_dict = response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )
    assert response.status_code == HTTPStatus.CREATED.value
    assert received_response.status == HTTPStatus.CREATED.value
    assert sorted(received_response.results) == sorted(["test_file3.txt has been committed\n",
                                                        "test_file2.txt has been committed\n",
                                                        "test_file1.txt has been committed\n"])
    assert received_response.message == "All files have been committed"


def test_post_commit_returns_201_when_the_file_content_has_changed_since_the_last_commit(tmp_path, directory_data,
                                                                                         commit_service):
    # Packages the directory being committed into a dictionary and converts the dictionary to a JSON formatted string
    data = json.dumps({'directoryPath': str(tmp_path)})

    # Commits to create version control history
    first_commit_response = commit_service.commit(data)
    assert first_commit_response.status_code == HTTPStatus.CREATED.value

    # Ensures the version control directory was created
    version_control_directory_path = Path(f"{tmp_path}/.vc/1")
    assert version_control_directory_path.exists() and version_control_directory_path.is_dir()

    # Modifies the "test_file3.txt" file created in directory_data fixture
    test_file3_path = Path(f"{tmp_path}/temp/nested_temp/test_file3.txt")
    test_file3_path.write_text("This is a changed file")

    # Ensures "test_file3.txt" was modified
    with open(test_file3_path, mode='r') as test_file3:
        file_contents = test_file3.readlines()
    assert file_contents == ["This is a changed file"]

    second_commit_response = commit_service.commit(data)
    response_dict = second_commit_response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )
    assert second_commit_response.status_code == HTTPStatus.CREATED.value
    assert received_response.status == HTTPStatus.CREATED.value
    assert sorted(received_response.results) == sorted(["test_file3.txt has been committed\n",
                                                        "test_file2.txt has been committed\n",
                                                        "test_file1.txt has been committed\n"])
    assert received_response.message == "All files have been committed"


def test_post_commit_returns_201_when_the_file_name_has_changed_since_the_last_commit(tmp_path, directory_data,
                                                                                      commit_service):
    # Packages the directory being committed into a dictionary and converts the dictionary to a JSON formatted string
    data = json.dumps({'directoryPath': str(tmp_path)})

    # Commits to create version control history
    first_commit_response = commit_service.commit(data)
    assert first_commit_response.status_code == HTTPStatus.CREATED.value

    # Ensures the version control directory was created
    version_control_directory_path = Path(f"{tmp_path}/.vc/1")
    assert version_control_directory_path.exists() and version_control_directory_path.is_dir()

    # Creates paths for the "test_file3.txt" file created in directory_data and the path it would have when renamed
    test_file3_path = Path(f"{tmp_path}/temp/nested_temp/test_file3.txt")
    renamed_test_file_path = Path(f"{tmp_path}/temp/nested_temp/renamed_test_file.txt")

    # Ensures the "test_file3.txt" file was renamed to "renamed_test_file.txt"
    os.rename(test_file3_path, renamed_test_file_path)
    assert test_file3_path.exists() is False and renamed_test_file_path.exists() is True

    second_commit_response = commit_service.commit(data)
    response_dict = second_commit_response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )
    assert second_commit_response.status_code == HTTPStatus.CREATED.value
    assert received_response.status == HTTPStatus.CREATED.value
    assert sorted(received_response.results) == sorted(["renamed_test_file.txt has been committed\n",
                                                        "test_file2.txt has been committed\n",
                                                        "test_file1.txt has been committed\n"])
    assert received_response.message == "All files have been committed"


def test_post_commit_returns_201_when_the_file_name_and_file_content_has_changed_since_the_last_commit(tmp_path,
                                                                                                       directory_data,
                                                                                                       commit_service):
    # Packages the directory being committed into a dictionary and converts the dictionary to a JSON formatted string
    data = json.dumps({'directoryPath': str(tmp_path)})

    # Commits to create version control history
    first_commit_response = commit_service.commit(data)
    assert first_commit_response.status_code == HTTPStatus.CREATED.value

    # Ensures the version control directory was created
    version_control_directory_path = Path(f"{tmp_path}/.vc/1")
    assert version_control_directory_path.exists() and version_control_directory_path.is_dir()

    # Creates paths for the "test_file3.txt" file created in directory_data and the path it would have when renamed
    test_file3_path = Path(f"{tmp_path}/temp/nested_temp/test_file3.txt")
    renamed_test_file_path = Path(f"{tmp_path}/temp/nested_temp/renamed_test_file.txt")

    # Ensures the "test_file3.txt" file was renamed to "renamed_test_file.txt"
    os.rename(test_file3_path, renamed_test_file_path)
    assert test_file3_path.exists() is False and renamed_test_file_path.exists() is True

    # Modifies the "renamed_test_file.txt" file created in directory_data fixture
    renamed_test_file_path.write_text("This is a changed file")

    # Ensures "renamed_test_file.txt" was modified
    with open(renamed_test_file_path, mode='r') as renamed_file:
        file_contents = renamed_file.readlines()
    assert file_contents == ["This is a changed file"]

    second_commit_response = commit_service.commit(data)
    response_dict = second_commit_response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )
    assert second_commit_response.status_code == HTTPStatus.CREATED.value
    assert received_response.status == HTTPStatus.CREATED.value
    assert sorted(received_response.results) == sorted(["renamed_test_file.txt has been committed\n",
                                                        "test_file2.txt has been committed\n",
                                                        "test_file1.txt has been committed\n"])
    assert received_response.message == "All files have been committed"


def test_post_commit_with_invalid_data_returns_400(tmp_path, commit_service):
    # Creates a path to a directory that does not exist
    invalid_path = tmp_path / "invalid_directory"

    # Packages the directory being committed into a dictionary and converts the dictionary to a JSON formatted string
    data = json.dumps({'directoryPath': str(invalid_path)})

    response = commit_service.commit(data)
    response_dict = response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST.value
    assert received_response.status == HTTPStatus.BAD_REQUEST.value
    assert received_response.results == [f"{invalid_path} is not a directory"]
    assert received_response.message == "The requested directory is not valid"


def test_post_commit_returns_409_when_directory_is_up_to_date(tmp_path, directory_data, commit_service):
    # Packages the directory being committed into a dictionary and converts the dictionary to a JSON formatted string
    data = json.dumps({'directoryPath': str(tmp_path)})

    # Commits to create version control history
    response = commit_service.commit(data)
    assert response.status_code == HTTPStatus.CREATED.value

    response = commit_service.commit(data)
    response_dict = response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert response.status_code == HTTPStatus.CONFLICT.value
    assert received_response.status == HTTPStatus.CONFLICT.value
    assert received_response.results == [f"{tmp_path} is up to date"]
    assert received_response.message == "The requested directory is up to date"


def test_post_commit_returns_500_when_a_file_cannot_be_committed(tmp_path, directory_data, commit_service):
    is_accessible = True

    restricted_file_path = Path(f"{tmp_path}/temp/nested_temp/test_file3.txt")

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

    # Asserts the file is in a state where attempting to commit it will fail
    assert os.access(restricted_file_path, os.R_OK) or is_accessible is False

    # Packages the directory being committed into a dictionary and converts the dictionary to a JSON formatted string
    data = json.dumps({'directoryPath': str(tmp_path)})

    response = commit_service.commit(data)
    response_dict = response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR.value
    assert received_response.status == HTTPStatus.INTERNAL_SERVER_ERROR.value
    assert sorted(received_response.results) == sorted(["test_file3.txt has not been committed\n",
                                                        "test_file2.txt has been committed\n",
                                                        "test_file1.txt has been committed\n"])
    assert received_response.message == "Not all files have been committed"
