"""Tests for rind._utils module."""


class TestHelperFunctions:
    """Tests for utility functions."""

    def test_safe_name(self):
        """Test wheel-safe name generation."""
        from rind._utils import safe_name

        assert safe_name("My_Package") == "my_package"
        assert safe_name("my.package") == "my_package"
        assert safe_name("my--package") == "my_package"

    def test_wheel_name(self):
        """Test wheel filename generation."""
        from rind._utils import wheel_name

        name = wheel_name("my-package", "1.2.3")
        assert name == "my_package-1.2.3-py3-none-any.whl"

    def test_record_hash(self):
        """Test RECORD hash generation."""
        from rind._utils import record_hash

        data = b"test content"
        hash_str = record_hash(data)
        assert hash_str.startswith("sha256=")
        # Should be consistent
        assert record_hash(data) == hash_str
