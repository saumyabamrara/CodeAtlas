"""Tests for Java source-root scope classification."""

import pytest

from app.services.source_scope_service import SourceScopeService


@pytest.mark.parametrize(
    ("file_path", "expected_scope"),
    [
        ("project/src/main/java/com/example/App.java", "production"),
        ("project/src/test/java/com/example/AppTests.java", "test"),
        ("project/java/com/example/Legacy.java", "production"),
        (r"C:\project\src\main\java\com\example\App.java", "production"),
        (r"C:\project\src\test\java\com\example\AppTests.java", "test"),
        ("/workspace/project/src/test/java/com/example/deep/AppTests.java", "test"),
        ("/workspace/src/test/java/AppTests.java", "test"),
        ("/workspace/src/test/java-tools/AppTests.java", "production"),
        ("/workspace/my-src/test/java/AppTests.java", "production"),
        ("/workspace/src/testing/java/AppTests.java", "production"),
        ("/workspace/SRC/TEST/JAVA/AppTests.java", "test"),
    ],
)
def test_get_scope_uses_normalized_source_root_segments(
    file_path: str,
    expected_scope: str,
) -> None:
    assert SourceScopeService().get_scope(file_path) == expected_scope
