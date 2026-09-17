import pytest


def test_default_settings_are_local_and_debug_is_disabled(load_settings):
    settings = load_settings()

    assert settings["debug"] is False
    assert settings["hosts"] == ["localhost", "127.0.0.1", "[::1]"]
    assert settings["database"]["HOST"] == "127.0.0.1"
    assert settings["database"]["PORT"] == "5432"


@pytest.mark.parametrize("value", ["True", "true", "1", "yes", " ON "])
def test_debug_can_be_enabled(load_settings, value):
    assert load_settings(environment={"DEBUG": value})["debug"] is True


@pytest.mark.parametrize("value", ["False", "false", "0", "no", "off", ""])
def test_debug_can_be_disabled(load_settings, value):
    assert load_settings(environment={"DEBUG": value})["debug"] is False


def test_dotenv_is_loaded_independently_of_working_directory(load_settings):
    settings = load_settings(
        {
            "DJANGO_SECRET": "test-settings-secret",
            "DEBUG": "True",
            "ALLOWED_HOSTS": "localhost, example.test, ,127.0.0.1,",
            "DB_HOST": "127.0.0.1",
            "DB_PORT": "55432",
            "DB_NAME": "settings_test",
            "DB_USER": "settings_user",
            "DB_PASSWORD": "settings_password",
        }
    )

    assert settings["debug"] is True
    assert settings["hosts"] == ["localhost", "example.test", "127.0.0.1"]
    assert settings["database"]["PORT"] == "55432"
    assert settings["database"]["NAME"] == "settings_test"
    assert settings["database"]["USER"] == "settings_user"
    assert settings["database"]["PASSWORD"] == "settings_password"  # noqa: S105


def test_environment_overrides_dotenv_for_docker(load_settings):
    settings = load_settings(
        {
            "DJANGO_SECRET": "test-file-secret",
            "DB_HOST": "127.0.0.1",
            "DB_PORT": "55432",
            "DEBUG": "True",
            "ALLOWED_HOSTS": "localhost",
        },
        {
            "DJANGO_SECRET": "test-environment-secret",
            "DB_HOST": "postgres",
            "DB_PORT": "5432",
            "DEBUG": "False",
            "ALLOWED_HOSTS": "example.test",
        },
    )

    assert settings["secret"] == "test-environment-secret"  # noqa: S105
    assert settings["debug"] is False
    assert settings["hosts"] == ["example.test"]
    assert settings["database"]["HOST"] == "postgres"
    assert settings["database"]["PORT"] == "5432"


def test_missing_secret_reports_configuration_error(load_settings):
    result = load_settings(file_values={}, check=False)

    assert result.returncode != 0
    assert "Set DJANGO_SECRET in backend/.env or the environment." in result.stderr
