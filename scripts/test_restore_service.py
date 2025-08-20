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


def test_create_restore_returns_201_when_file_content_is_changed(tmp_path, setup_directory):
    data = json.dumps({'directoryPath': str(tmp_path)})

    commit_response = CommitService.commit(data)
    assert commit_response.status_code == HTTPStatus.CREATED.value

    version_control_directory_path = Path(f"{tmp_path}/.vc/1")
    assert version_control_directory_path.exists() and version_control_directory_path.is_dir()

    test_file3_path = Path(f"{tmp_path}/temp/nested_temp/test_file3.txt")
    test_file3_path.write_text("This is a changed file")

    with open(test_file3_path, mode='r') as test_file3:
        file_contents = test_file3.readlines()
    assert file_contents == ["This is a changed file"]

    data = json.dumps({'vcPath': str(version_control_directory_path), 'destinationPath': str(tmp_path)})
    restore_response = RestoreService.restore(data)

    response_dict = restore_response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert restore_response.status_code == HTTPStatus.CREATED.value
    assert received_response.status == HTTPStatus.CREATED.value
    assert received_response.results.sort() == ["test_file1.txt is already up to date\n",
                                                "test_file2.txt is already up to date\n",
                                                "test_file3.txt has been restored\n"].sort()
    assert received_response.message == "All changed files have been restored"

    with open(f'{tmp_path}/temp/nested_temp/test_file3.txt', mode='r') as test_file3:
        file_contents = test_file3.readlines()
    assert file_contents == ["This is a third test file"]


def test_create_restore_returns_201_when_file_name_is_changed(tmp_path, setup_directory):
    data = json.dumps({'directoryPath': str(tmp_path)})

    commit_response = CommitService.commit(data)
    assert commit_response.status_code == HTTPStatus.CREATED.value

    version_control_directory_path = Path(f"{tmp_path}/.vc/1")
    assert version_control_directory_path.exists() and version_control_directory_path.is_dir()

    test_file3_path = Path(f"{tmp_path}/temp/nested_temp/test_file3.txt")
    renamed_test_file_path = Path(f"{tmp_path}/temp/nested_temp/renamed_test_file.txt")

    os.rename(test_file3_path, renamed_test_file_path)
    assert test_file3_path.exists() is False and renamed_test_file_path.exists() is True

    data = json.dumps({'vcPath': str(version_control_directory_path), 'destinationPath': str(tmp_path)})
    restore_response = RestoreService.restore(data)

    response_dict = restore_response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert restore_response.status_code == HTTPStatus.CREATED.value
    assert received_response.status == HTTPStatus.CREATED.value
    assert received_response.results.sort() == ["test_file1.txt is already up to date\n",
                                                "test_file2.txt is already up to date\n",
                                                "test_file3.txt has been restored\n"].sort()
    assert received_response.message == "All changed files have been restored"


def test_create_restore_returns_201_when_the_destination_directory_is_the_vc_directory_parent(tmp_path,
                                                                                              setup_directory):
    data = json.dumps({'directoryPath': str(tmp_path)})

    commit_response = CommitService.commit(data)
    assert commit_response.status_code == HTTPStatus.CREATED.value

    version_control_directory_path = Path(f"{tmp_path}/.vc/1")
    assert version_control_directory_path.exists() and version_control_directory_path.is_dir()

    test_file3_path = Path(f"{tmp_path}/temp/nested_temp/test_file3.txt")
    test_file3_path.write_text("This is a changed file")

    with open(test_file3_path, mode='r') as test_file3:
        file_contents = test_file3.readlines()
    assert file_contents == ["This is a changed file"]

    second_commit_response = CommitService.commit(data)
    assert second_commit_response.status_code == HTTPStatus.CREATED.value

    data = json.dumps({'vcPath': str(version_control_directory_path), 'destinationPath': str(tmp_path)})
    restore_response = RestoreService.restore(data)

    response_dict = restore_response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert restore_response.status_code == HTTPStatus.CREATED.value
    assert received_response.status == HTTPStatus.CREATED.value
    assert received_response.results.sort() == ["test_file1.txt is already up to date\n",
                                                "test_file2.txt is already up to date\n",
                                                "test_file3.txt has been restored\n"].sort()
    assert received_response.message == "All changed files have been restored"

    with open(f'{tmp_path}/temp/nested_temp/test_file3.txt', mode='r') as test_file3:
        file_contents = test_file3.readlines()
    assert file_contents == ["This is a third test file"]


def test_create_restore_returns_201_when_the_destination_directory_is_different_from_the_vc_directory_parent(tmp_path,
                                                                                                             setup_directory):
    data = json.dumps({'directoryPath': str(tmp_path)})

    commit_response = CommitService.commit(data)
    assert commit_response.status_code == HTTPStatus.CREATED.value

    version_control_directory_path = Path(f"{tmp_path}/.vc/1")
    assert version_control_directory_path.exists() and version_control_directory_path.is_dir()

    destination_directory_path = Path(f"{tmp_path}/temp/destination")
    destination_directory_path.mkdir()
    assert destination_directory_path.exists() and destination_directory_path.is_dir()

    data = json.dumps(
        {'vcPath': str(version_control_directory_path), 'destinationPath': str(destination_directory_path)})
    restore_response = RestoreService.restore(data)

    response_dict = restore_response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert restore_response.status_code == HTTPStatus.CREATED.value
    assert received_response.status == HTTPStatus.CREATED.value
    assert received_response.results.sort() == ["test_file1.txt has been restored\n",
                                                "test_file2.txt has been restored\n",
                                                "test_file3.txt has been restored\n"].sort()
    assert received_response.message == "All changed files have been restored"

    restored_file_locations = [Path(f"{destination_directory_path}/test_file1.txt"),
                               Path(f"{destination_directory_path}/temp/test_file2.txt"),
                               Path(f"{destination_directory_path}/temp/nested_temp/test_file3.txt")]

    for restored_file_location in restored_file_locations:
        assert restored_file_location.exists() is True

    with open(restored_file_locations[0], mode='r') as test_file1:
        file_contents = test_file1.readlines()
    assert file_contents == ["This is a test file"]

    with open(restored_file_locations[1], mode='r') as test_file2:
        file_contents = test_file2.readlines()
    assert file_contents == ["This is a second test file"]

    with open(restored_file_locations[2], mode='r') as test_file3:
        file_contents = test_file3.readlines()
    assert file_contents == ["This is a third test file"]


def test_create_restore_with_invalid_vc_directory_returns_400(tmp_path):
    invalid_directory_path = tmp_path / "invalid_vc_directory"
    invalid_directory_path.mkdir()

    data = json.dumps({'vcPath': str(invalid_directory_path), 'destinationPath': str(tmp_path)})

    response = RestoreService.restore(data)
    response_dict = response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST.value
    assert received_response.status == HTTPStatus.BAD_REQUEST.value
    assert received_response.results == [f"{invalid_directory_path} is not a valid version control directory"]
    assert received_response.message == "The version control directory is not valid"


def test_create_restore_with_invalid_directory_returns_400(tmp_path):
    data = json.dumps({'directoryPath': str(tmp_path)})

    commit_response = CommitService.commit(data)
    assert commit_response.status_code == HTTPStatus.CREATED.value

    version_control_directory_path = Path(f"{tmp_path}/.vc/1")
    assert version_control_directory_path.exists() and version_control_directory_path.is_dir()

    invalid_directory_path = tmp_path / "invalid_vc_directory"

    data = json.dumps({'vcPath': str(version_control_directory_path), 'destinationPath': str(invalid_directory_path)})

    response = RestoreService.restore(data)
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


def test_create_restore_with_invalid_vc_directory_and_invalid_directory_returns_400(tmp_path):
    version_control_directory_path = Path(f"{tmp_path}/.vc/1")
    invalid_directory_path = tmp_path / "invalid_vc_directory"

    data = json.dumps({'vcPath': str(version_control_directory_path), 'destinationPath': str(invalid_directory_path)})

    response = RestoreService.restore(data)
    response_dict = response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST.value
    assert received_response.status == HTTPStatus.BAD_REQUEST.value
    assert received_response.results == [
        f"{version_control_directory_path} is not a valid version control directory and {invalid_directory_path} is not a directory"]
    assert received_response.message == "The version control directory and the destination directory are not valid"


def test_create_restore_returns_409_when_destination_directory_is_up_to_date_with_vc_directory(tmp_path,
                                                                                               setup_directory):
    data = json.dumps({'directoryPath': str(tmp_path)})

    response = CommitService.commit(data)
    assert response.status_code == HTTPStatus.CREATED.value

    version_control_directory_path = Path(f"{tmp_path}/.vc/1")
    assert version_control_directory_path.exists() and version_control_directory_path.is_dir()

    data = json.dumps({'vcPath': str(version_control_directory_path), 'destinationPath': str(tmp_path)})

    response = RestoreService.restore(data)
    response_dict = response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert response.status_code == HTTPStatus.CONFLICT.value
    assert received_response.status == HTTPStatus.CONFLICT.value
    assert received_response.results.sort() == ["test_file1.txt is already up to date",
                                                "test_file2.txt is already up to date",
                                                "test_file3.txt is already up to date"].sort()
    assert received_response.message == ("The requested destination directory is up to date with the version control "
                                         "directory")


@pytest.mark.skip(reason="Locking a file does not prevent restore from working")
def test_create_restore_returns_500_when_a_file_cannot_be_restored(tmp_path, setup_directory):
    is_accessible = True

    restricted_file_path = Path(f"{tmp_path}/temp/nested_temp/test_file3.txt")

    destination_directory_path = Path(f"{tmp_path}/test_directory")
    destination_directory_path.mkdir()

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

    data = json.dumps({'directoryPath': str(tmp_path)})
    commit_response = CommitService.commit(data)
    assert commit_response.status_code == HTTPStatus.CREATED.value

    version_control_directory_path = Path(f"{tmp_path}/.vc/1")
    assert version_control_directory_path.exists() and version_control_directory_path.is_dir()

    data = json.dumps(
        {'vcPath': str(version_control_directory_path), 'destinationPath': str(destination_directory_path)})
    restore_response = RestoreService.restore(data)
    response_dict = restore_response.json()

    received_response = Response(
        status=response_dict["status"],
        results=response_dict["results"],
        message=response_dict["message"]
    )

    assert restore_response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR.value
    assert received_response.status == HTTPStatus.INTERNAL_SERVER_ERROR.value
    assert received_response.results.sort() == ["test_file3.txt has not been restored\n",
                                                "test_file2.txt has been restored\n",
                                                "test_file1.txt has been restored\n"].sort()
    assert received_response.message == "Not all files have been restored"
