"""Test for making mmdc_path configuration optional."""

from unittest.mock import patch

from mkdocs_mermaid_to_svg.config import ConfigManager
from mkdocs_mermaid_to_svg.image_generator import MermaidImageGenerator


class TestMmdcPathOptional:
    """Test mmdc_path as optional configuration."""

    def test_config_scheme_has_optional_mmdc_path(self):
        """Test that config scheme includes mmdc_path as optional."""
        scheme = ConfigManager.get_config_scheme()
        scheme_dict = dict(scheme)

        # mmdc_pathがスキームに含まれている
        assert "mmdc_path" in scheme_dict

        # mmdc_pathがOptionalであること
        mmdc_path_option = scheme_dict["mmdc_path"]
        assert hasattr(mmdc_path_option, "default")

    def test_image_generator_works_without_mmdc_path_in_config(self):
        """Test that MermaidImageGenerator works when mmdc_path is not in config."""
        # mmdc_pathを含まない設定
        config = {
            "theme": "default",
            "error_on_fail": False,
            "log_level": "INFO",
        }

        with patch(
            "mkdocs_mermaid_to_svg.image_generator.is_command_available"
        ) as mock_available:
            mock_available.return_value = True

            # mmdc_pathが設定されていなくてもエラーにならない
            generator = MermaidImageGenerator(config)
            assert generator is not None

    def test_image_generator_uses_default_mmdc_when_not_configured(self):
        """Test that default mmdc command is used when mmdc_path is not configured."""
        config = {
            "theme": "default",
            "error_on_fail": False,
            "log_level": "INFO",
        }

        # Clear cache to ensure fresh test
        MermaidImageGenerator.clear_command_cache()

        with patch(
            "mkdocs_mermaid_to_svg.image_generator.is_command_available"
        ) as mock_available:
            mock_available.return_value = True

            generator = MermaidImageGenerator(config)

            # デフォルトの"mmdc"コマンドが使用されることを確認
            assert generator._resolved_mmdc_command == "mmdc"
