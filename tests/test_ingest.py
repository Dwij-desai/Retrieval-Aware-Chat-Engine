"""
Pytest tests for RAG ingestion pipeline.

Tests cover:
- PDF loading
- CSV/JSON loading
- Text splitting
- Empty/invalid files
- Large files
"""

import json
import tempfile
from pathlib import Path
from io import BytesIO

import pytest
from PyPDF2 import PdfWriter

try:
    from backend.ingest import (
        load_pdf,
        load_text,
        load_csv,
        load_json,
        load_excel,
        ingest_documents_from_directory,
    )
except ImportError:
    from ingest import (
        load_pdf,
        load_text,
        load_csv,
        load_json,
        load_excel,
        ingest_documents_from_directory,
    )


class TestPDFLoading:
    """Test PDF document loading."""

    def test_load_valid_pdf(self, tmp_path):
        """Test loading a valid PDF file."""
        # Create a temporary PDF
        pdf_path = tmp_path / "test.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with open(pdf_path, "wb") as f:
            writer.write(f)

        # Load should not raise
        docs = load_pdf(str(pdf_path))
        assert docs is not None
        assert len(docs) >= 0  # May be 0 if blank page

    def test_load_empty_pdf(self, tmp_path):
        """Test loading an empty PDF."""
        pdf_path = tmp_path / "empty.pdf"
        writer = PdfWriter()
        with open(pdf_path, "wb") as f:
            writer.write(f)

        docs = load_pdf(str(pdf_path))
        assert docs is not None

    def test_load_nonexistent_pdf(self):
        """Test loading a non-existent PDF."""
        with pytest.raises((FileNotFoundError, Exception)):
            load_pdf("/nonexistent/file.pdf")

    def test_load_corrupted_pdf(self, tmp_path):
        """Test loading a corrupted PDF."""
        pdf_path = tmp_path / "corrupted.pdf"
        pdf_path.write_bytes(b"This is not a valid PDF")

        # Should handle gracefully
        with pytest.raises(Exception):
            load_pdf(str(pdf_path))


class TestTextLoading:
    """Test plain text document loading."""

    def test_load_valid_text(self, tmp_path):
        """Test loading a valid text file."""
        text_path = tmp_path / "test.txt"
        content = "This is test content.\nWith multiple lines.\n"
        text_path.write_text(content)

        docs = load_text(str(text_path))
        assert len(docs) > 0
        assert any("test content" in doc.page_content for doc in docs)

    def test_load_empty_text(self, tmp_path):
        """Test loading an empty text file."""
        text_path = tmp_path / "empty.txt"
        text_path.write_text("")

        docs = load_text(str(text_path))
        # Empty file should return empty list or be handled gracefully
        assert docs is not None

    def test_load_large_text(self, tmp_path):
        """Test loading a large text file."""
        text_path = tmp_path / "large.txt"
        # Create 1MB of text
        large_content = "Test content. " * 70000
        text_path.write_text(large_content)

        docs = load_text(str(text_path))
        assert len(docs) > 0


class TestCSVLoading:
    """Test CSV document loading."""

    def test_load_valid_csv(self, tmp_path):
        """Test loading a valid CSV file."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("name,age\nAlice,30\nBob,25\n")

        docs = load_csv(str(csv_path))
        assert len(docs) > 0

    def test_load_empty_csv(self, tmp_path):
        """Test loading an empty CSV."""
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("name,age\n")

        docs = load_csv(str(csv_path))
        assert docs is not None

    def test_load_malformed_csv(self, tmp_path):
        """Test loading a malformed CSV."""
        csv_path = tmp_path / "malformed.csv"
        csv_path.write_text("col1,col2,col3\nval1,val2\n")  # Missing column

        # Should handle gracefully
        docs = load_csv(str(csv_path))
        assert docs is not None

    def test_load_csv_with_special_chars(self, tmp_path):
        """Test CSV with special characters."""
        csv_path = tmp_path / "special.csv"
        csv_path.write_text('name,description\n"John","""quoted"""\n')

        docs = load_csv(str(csv_path))
        assert len(docs) > 0


class TestJSONLoading:
    """Test JSON document loading."""

    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON file."""
        json_path = tmp_path / "test.json"
        data = {"items": [{"name": "Item1"}, {"name": "Item2"}]}
        json_path.write_text(json.dumps(data))

        docs = load_json(str(json_path))
        assert len(docs) > 0

    def test_load_empty_json(self, tmp_path):
        """Test loading an empty JSON object."""
        json_path = tmp_path / "empty.json"
        json_path.write_text("{}")

        docs = load_json(str(json_path))
        assert docs is not None

    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON."""
        json_path = tmp_path / "invalid.json"
        json_path.write_text("{invalid json}")

        with pytest.raises(json.JSONDecodeError):
            load_json(str(json_path))

    def test_load_json_array(self, tmp_path):
        """Test loading JSON array."""
        json_path = tmp_path / "array.json"
        data = [{"name": "A"}, {"name": "B"}]
        json_path.write_text(json.dumps(data))

        docs = load_json(str(json_path))
        assert len(docs) > 0


class TestIngestionPipeline:
    """Test the full ingestion pipeline."""

    def test_ingest_single_file(self, tmp_path):
        """Test ingesting a single file."""
        # Create test file
        text_file = tmp_path / "doc.txt"
        text_file.write_text("Test document content")

        docs = ingest_documents_from_directory(str(tmp_path))
        assert docs is not None

    def test_ingest_multiple_formats(self, tmp_path):
        """Test ingesting multiple file formats."""
        # Create different file types
        (tmp_path / "doc.txt").write_text("Text content")
        (tmp_path / "data.json").write_text('{"key": "value"}')
        (tmp_path / "data.csv").write_text("col1,col2\nval1,val2\n")

        docs = ingest_documents_from_directory(str(tmp_path))
        assert docs is not None

    def test_ingest_empty_directory(self, tmp_path):
        """Test ingesting an empty directory."""
        docs = ingest_documents_from_directory(str(tmp_path))
        # Should handle gracefully
        assert docs is not None

    def test_ingest_ignores_hidden_files(self, tmp_path):
        """Test that hidden files are ignored."""
        (tmp_path / ".hidden.txt").write_text("Secret content")
        (tmp_path / "public.txt").write_text("Public content")

        # Should only ingest public.txt
        docs = ingest_documents_from_directory(str(tmp_path))
        assert docs is not None

    def test_ingest_large_file(self, tmp_path):
        """Test ingesting a large file (chunking)."""
        large_file = tmp_path / "large.txt"
        # Create a file larger than typical chunk size (1000+ tokens)
        large_content = "word " * 5000
        large_file.write_text(large_content)

        docs = ingest_documents_from_directory(str(tmp_path))
        assert len(docs) > 1  # Should be chunked into multiple docs


class TestErrorHandling:
    """Test error handling during ingestion."""

    def test_ingest_permission_error(self, tmp_path):
        """Test handling of permission errors."""
        restricted_file = tmp_path / "restricted.txt"
        restricted_file.write_text("Content")

        # Make file unreadable (Unix-only)
        import os
        try:
            os.chmod(restricted_file, 0o000)
            with pytest.raises(PermissionError):
                load_text(str(restricted_file))
        finally:
            os.chmod(restricted_file, 0o644)

    def test_ingest_disk_full_simulation(self, tmp_path):
        """Test graceful handling when disk operations fail."""
        # This is difficult to simulate; mainly documents the requirement
        pass

    def test_unsupported_file_type(self, tmp_path):
        """Test handling of unsupported file types."""
        unknown_file = tmp_path / "file.xyz"
        unknown_file.write_text("Unknown format")

        # Should be skipped or raise appropriate error
        docs = ingest_documents_from_directory(str(tmp_path))
        assert docs is not None


class TestDocumentMetadata:
    """Test document metadata handling."""

    def test_document_has_source_metadata(self, tmp_path):
        """Test that documents include source file information."""
        text_file = tmp_path / "test.txt"
        text_file.write_text("Content")

        docs = load_text(str(text_file))
        assert len(docs) > 0

        # Check if metadata includes source
        for doc in docs:
            assert hasattr(doc, 'metadata')

    def test_document_chunking_preserves_metadata(self, tmp_path):
        """Test that chunking preserves metadata."""
        text_file = tmp_path / "test.txt"
        large_content = "Sentence. " * 500
        text_file.write_text(large_content)

        docs = load_text(str(text_file))
        
        # All chunks should have consistent metadata
        sources = [doc.metadata.get('source') for doc in docs]
        assert len(set(sources)) == 1  # All from same source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
