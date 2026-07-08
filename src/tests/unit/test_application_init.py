"""Tests for application __init__ module."""

from unittest.mock import MagicMock, patch

from application import create_vocab_service, get_db_path


class TestGetDbPath:
    """Tests for get_db_path function."""

    @patch("application.read_config")
    def test_get_db_path_default_when_no_config(self, mock_read_config):
        """Test that get_db_path returns DEFAULT_DB_PATH when no custom data_dir."""
        mock_read_config.return_value = {}
        with patch("application.DEFAULT_DB_PATH", "/default/vocab.db"):
            result = get_db_path("/tmp/config.json")
            assert result == "/default/vocab.db"

    @patch("application.read_config")
    def test_get_db_path_custom_data_dir(self, mock_read_config):
        """Test that get_db_path uses custom data_dir from config."""
        mock_read_config.return_value = {"data_dir": "~/my_data"}
        with patch("application.os.path.expanduser", return_value="/home/user/my_data"):
            with patch("application.os.makedirs"):
                result = get_db_path("/tmp/config.json")
                assert result == "/home/user/my_data/vocab.db"

    @patch("application.read_config")
    def test_get_db_path_creates_directory(self, mock_read_config):
        """Test that get_db_path creates directory if needed."""
        mock_read_config.return_value = {"data_dir": "/tmp/custom_data"}
        with patch("application.os.makedirs") as mock_makedirs:
            with patch("application.os.path.dirname", return_value="/tmp/custom_data"):
                get_db_path("/tmp/config.json")
                mock_makedirs.assert_called_once_with("/tmp/custom_data", exist_ok=True)

    @patch("application.read_config")
    def test_get_db_path_invalid_custom_dir(self, mock_read_config):
        """Test that get_db_path handles non-string data_dir."""
        mock_read_config.return_value = {"data_dir": 123}  # Not a string
        with patch("application.DEFAULT_DB_PATH", "/default/vocab.db"):
            result = get_db_path("/tmp/config.json")
            assert result == "/default/vocab.db"


class TestCreateVocabService:
    """Tests for create_vocab_service function."""

    @patch("application.SQLiteDatabase")
    @patch("application.get_db_path")
    @patch("application.ServiceFactory")
    @patch("application.VocabService")
    @patch("application.TranslationServiceImpl")
    @patch("application.WordRepository")
    @patch("application.StatsRepository")
    @patch("application.SettingsRepository")
    @patch("application.LanguageRepository")
    @patch("application.WOTDRepository")
    def test_create_vocab_service_success(
        self,
        mock_wotd_repo,
        mock_lang_repo,
        mock_settings_repo,
        mock_stats_repo,
        mock_word_repo,
        mock_trans_service,
        mock_vocab_service,
        mock_factory,
        mock_get_db_path,
        mock_sqlite,
    ):
        """Test successful creation of VocabService."""
        mock_get_db_path.return_value = "/tmp/test.db"
        mock_db_instance = MagicMock()
        mock_sqlite.return_value = mock_db_instance

        result = create_vocab_service()

        mock_get_db_path.assert_called_once()
        mock_sqlite.assert_called_once_with("/tmp/test.db")
        mock_db_instance.connect.assert_called_once()
        assert result is not None

    @patch("application.os.path.exists", return_value=False)
    @patch("application.get_db_path", return_value="/tmp/nonexistent.db")
    @patch("application.SQLiteDatabase")
    def test_create_vocab_service_db_not_exists_must_exist(
        self, mock_sqlite, mock_get_db_path, mock_exists
    ):
        """Test that create_vocab_service returns None when must_exist=True and db doesn't exist."""
        result = create_vocab_service(must_exist=True)
        assert result is None

    @patch("application.os.path.exists", return_value=False)
    @patch("application.get_db_path", return_value="/tmp/new.db")
    @patch("application.SQLiteDatabase")
    @patch("application.os.makedirs")
    def test_create_vocab_service_creates_db_directory(
        self, mock_makedirs, mock_sqlite, mock_get_db_path, mock_exists
    ):
        """Test that create_vocab_service creates directory for new db."""
        mock_db_instance = MagicMock()
        mock_sqlite.return_value = mock_db_instance

        with patch("application.os.path.dirname", return_value="/tmp"):
            create_vocab_service(must_exist=False)
            mock_makedirs.assert_called_once_with("/tmp", exist_ok=True)

    @patch("application.get_db_path", return_value="/tmp/test.db")
    @patch("application.SQLiteDatabase")
    @patch("application.os.makedirs")
    def test_create_vocab_service_custom_db_path(self, mock_makedirs, mock_sqlite, mock_get_db_path):
        """Test that create_vocab_service uses custom db_path when provided."""
        mock_db_instance = MagicMock()
        mock_sqlite.return_value = mock_db_instance

        create_vocab_service(db_path="/custom/path.db")

        mock_sqlite.assert_called_once_with("/custom/path.db")
        mock_get_db_path.assert_not_called()
