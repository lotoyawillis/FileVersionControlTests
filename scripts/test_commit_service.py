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
def setup_directory(tmp_path):
    (tmp_path / "test_file1.txt").write_text("This is a test file")

    nested_directory = tmp_path / "temp"
    nested_directory.mkdir()
    assert nested_directory.exists() and nested_directory.is_dir()

    (nested_directory / "test_file2.txt").write_text("This is a second test file")

    second_nested_directory = nested_directory / "nested_temp"
    second_nested_directory.mkdir()
    assert second_nested_directory.exists() and second_nested_directory.is_dir()

    (second_nested_directory / "test_file3.txt").write_text("This is a third test file")


def test_create_commit_returns_201(tmp_path, setup_directory):
    data = json.dumps({'path': str(tmp_path)})

    response = CommitService.commit(data)
    response_dict = response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )
    assert response.status_code == HTTPStatus.CREATED.value
    assert received_response.status == HTTPStatus.CREATED.value
    assert received_response.results == ["test_file3.txt has been committed\n",
                                         "test_file2.txt has been committed\n",
                                         "test_file1.txt has been committed\n"]
    assert received_response.message == "All files have been committed"


def test_create_commit_with_invalid_data_returns_400(tmp_path):
    invalid_path = tmp_path / "invalid_directory"

    data = json.dumps({'path': str(invalid_path)})

    response = CommitService.commit(data)
    response_dict = response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST.value
    assert received_response.status == HTTPStatus.BAD_REQUEST.value
    assert received_response.results == [f"{invalid_path} is not a directory"]
    assert received_response.message == "The request is invalid"


def test_create_commit_returns_409_when_directory_is_up_to_date(tmp_path, setup_directory):
    data = json.dumps({'path': str(tmp_path)})

    response = CommitService.commit(data)
    assert response.status_code == HTTPStatus.CREATED.value

    response = CommitService.commit(data)
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


def test_create_commit_returns_500_when_a_file_cannot_be_committed(tmp_path):
    is_accessible = True

    restricted_file_path = Path(f"{tmp_path}/test_file1.txt")
    restricted_file_path.write_text("This is a test file")

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
        except:
            is_accessible = False

    # Asserts the file is in a state where attempting to commit it will fail
    assert os.access(restricted_file_path, os.R_OK) or is_accessible is False

    data = json.dumps({'path': str(tmp_path)})

    response = CommitService.commit(data)
    response_dict = response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR.value
    assert received_response.status == HTTPStatus.INTERNAL_SERVER_ERROR.value
    assert received_response.results == ["test_file1.txt has not been committed\n"]
    assert received_response.message == "Not all files have been committed"
