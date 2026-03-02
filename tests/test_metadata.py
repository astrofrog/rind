"""Tests for rind._metadata module."""

import os
import sys
import tarfile
import tempfile
from pathlib import Path


class TestBuildMetadata:
    """Tests for build_metadata function."""

    def test_inherits_metadata(self, temp_project):
        """Test that metadata is inherited from core pyproject.toml."""
        from rind._metadata import build_metadata

        meta_dir = temp_project / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            meta = build_metadata()

            assert meta["name"] == "mypackage"
            assert meta["version"] == "1.2.3"
            assert meta["core_package"] == "mypackage-core"
            assert meta["metadata_fields"]["requires-python"] == ">=3.9"
            assert meta["metadata_fields"]["license"] == {"text": "MIT"}
            # Description is overridden
            assert meta["metadata_fields"]["description"] == "My package with batteries"
        finally:
            os.chdir(original_cwd)

    def test_static_version(self, temp_project_static):
        """Test that static version is read correctly."""
        from rind._metadata import build_metadata

        meta_dir = temp_project_static / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            meta = build_metadata()

            assert meta["version"] == "2.0.0"
            assert meta["core_package"] == "mypackage-core"
            assert "mypackage-core[extra1]==2.0.0" in meta["dependencies"][0]
        finally:
            os.chdir(original_cwd)

    def test_no_inherit_metadata(self, temp_project_no_inherit):
        """Test that inherit-metadata = false prevents inheritance."""
        from rind._metadata import build_metadata

        meta_dir = temp_project_no_inherit / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            meta = build_metadata()

            assert meta["name"] == "mypackage"
            # Should use local [project] values, not inherited
            assert meta["metadata_fields"]["description"] == "Custom description"
            assert meta["metadata_fields"]["requires-python"] == ">=3.10"
            # License should be None since not inherited and not in local
            assert meta["metadata_fields"]["license"] is None
        finally:
            os.chdir(original_cwd)

    def test_core_extras(self, temp_project):
        """Test that include-extras are included in dependencies."""
        from rind._metadata import build_metadata

        meta_dir = temp_project / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            meta = build_metadata()

            deps = meta["dependencies"]
            assert len(deps) == 1
            assert "mypackage-core[extra1,extra2]==1.2.3" in deps[0]
        finally:
            os.chdir(original_cwd)

    def test_passthrough_extras(self, temp_project):
        """Test that passthrough-extras are exposed."""
        from rind._metadata import build_metadata

        meta_dir = temp_project / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            meta = build_metadata()

            optional = meta["optional_deps"]
            assert "test" in optional
            assert "docs" in optional
            assert "mypackage-core[test]==1.2.3" in optional["test"][0]
            assert "mypackage-core[docs]==1.2.3" in optional["docs"][0]
        finally:
            os.chdir(original_cwd)

    def test_passthrough_extras_wildcard(self, temp_project_wildcard):
        """Test that passthrough-extras = ['*'] passes through all extras."""
        from rind._metadata import build_metadata

        meta_dir = temp_project_wildcard / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            meta = build_metadata()

            optional = meta["optional_deps"]
            # Should have all 4 extras from core package
            assert "extra1" in optional
            assert "extra2" in optional
            assert "test" in optional
            assert "docs" in optional
            assert "mypackage-core[extra1]==1.2.3" in optional["extra1"][0]
            assert "mypackage-core[test]==1.2.3" in optional["test"][0]
        finally:
            os.chdir(original_cwd)

    def test_dynamic_version_via_backend(self, temp_project_dynamic_setuptools):
        """Test version detection via PEP 517 backend fallback."""
        from rind._metadata import build_metadata

        meta_dir = temp_project_dynamic_setuptools / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            meta = build_metadata()

            # Version should be read via the backend fallback
            assert meta["version"] == "4.5.6"
            assert meta["core_package"] == "mypackage-core"
            assert "mypackage-core==4.5.6" in meta["dependencies"][0]
        finally:
            os.chdir(original_cwd)

    def test_build_metadata_from_sdist(self, temp_project_static):
        """Test build_metadata uses cached info when building from extracted sdist."""
        import rind
        from rind._metadata import build_metadata

        meta_dir = temp_project_static / "meta"
        original_cwd = os.getcwd()
        try:
            # Build sdist from the meta package
            os.chdir(meta_dir)
            with tempfile.TemporaryDirectory() as sdist_dir:
                sdist_name = rind.build_sdist(sdist_dir)
                sdist_path = Path(sdist_dir) / sdist_name

                # Extract sdist to a new location (simulating pip download)
                extract_dir = temp_project_static / "extracted"
                with tarfile.open(sdist_path, "r:gz") as tar:
                    if sys.version_info >= (3, 12):
                        tar.extractall(extract_dir, filter="data")
                    else:
                        tar.extractall(extract_dir)

                # Find the extracted directory
                extracted = list(extract_dir.iterdir())[0]

                # Now build metadata from within extracted sdist
                # (no access to core pyproject.toml - must use cache)
                os.chdir(extracted)
                meta = build_metadata()

                # Should use cached values from sdist
                assert meta["version"] == "2.0.0"
                assert meta["core_package"] == "mypackage-core"
                assert meta["metadata_fields"]["requires-python"] == ">=3.9"
        finally:
            os.chdir(original_cwd)
