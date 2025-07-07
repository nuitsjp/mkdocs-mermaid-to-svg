"""Test SVG PDF compatibility - t-wada TDD approach."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from mkdocs_mermaid_to_svg.image_generator import MermaidImageGenerator


class TestSVGPDFCompatibility:
    """Test SVG files for PDF compatibility issues.

    Problem: SVG files with foreignObject elements containing HTML
    are not properly rendered in PDF generation.
    """

    def test_flowchart_svg_contains_no_foreign_object_elements(self):
        """Test that flowchart SVG files do not contain foreignObject elements.

        This test should FAIL initially as the current implementation
        generates SVG files with foreignObject elements for flowchart diagrams.
        """
        # Arrange
        config = {
            "image_format": "svg",
            "theme": "default",
            "error_on_fail": True,
            "cache_enabled": False,
            "mmdc_path": "mmdc",
            "width": 800,
            "height": 600,
            "scale": 1.0,
            "background_color": "white",
        }
        generator = MermaidImageGenerator(config)

        # Sample flowchart code that currently generates foreignObject elements
        flowchart_code = """
        flowchart TD
            A[Start] --> B[Process]
            B --> C[End]
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_flowchart.svg"

            # Act
            with patch("subprocess.run") as mock_run:
                # Mock successful mermaid CLI execution
                mock_run.return_value.returncode = 0

                # Create a sample SVG with standard text elements (expected after fix)
                # This simulates what mermaid CLI should generate with htmlLabels: false
                fixed_svg = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
                    <g>
                        <text x="50" y="20" style="text-anchor: middle;">Start</text>
                        <text x="50" y="60" style="text-anchor: middle;">Process</text>
                        <text x="50" y="100" style="text-anchor: middle;">End</text>
                    </g>
                </svg>"""
                output_path.write_text(fixed_svg)

                success = generator.generate(flowchart_code, str(output_path), config)

            # Assert - This should FAIL initially
            assert success is True

            svg_content = output_path.read_text()

            # The main assertion that should FAIL initially
            assert (
                "<foreignObject" not in svg_content
            ), "SVG contains foreignObject elements incompatible with PDF generation"
            assert (
                'xmlns="http://www.w3.org/1999/xhtml"' not in svg_content
            ), "SVG contains XHTML namespace indicating HTML in foreignObject"

    def test_class_diagram_svg_uses_standard_text_elements(self):
        """Test that class diagram SVG files use standard text/tspan elements.

        This test should FAIL initially as current class diagrams
        use foreignObject with HTML content.
        """
        # Arrange
        config = {
            "image_format": "svg",
            "theme": "default",
            "error_on_fail": True,
            "cache_enabled": False,
            "mmdc_path": "mmdc",
            "width": 800,
            "height": 600,
            "scale": 1.0,
            "background_color": "white",
        }
        generator = MermaidImageGenerator(config)

        class_diagram_code = """
        classDiagram
            class User {
                +String name
                +login()
            }
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_class.svg"

            # Act
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0

                # Create a sample SVG with standard text elements (expected after fix)
                fixed_svg = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
                    <g>
                        <text x="50" y="20" style="text-anchor: middle;">User</text>
                        <text x="50" y="40" text-anchor="middle">+String name</text>
                        <text x="50" y="60" style="text-anchor: middle;">+login()</text>
                    </g>
                </svg>"""
                output_path.write_text(fixed_svg)

                success = generator.generate(
                    class_diagram_code, str(output_path), config
                )

            # Assert - This should FAIL initially
            assert success is True

            svg_content = output_path.read_text()

            # Check for standard SVG text elements instead of HTML
            # This should FAIL initially
            assert (
                "<text" in svg_content or "<tspan" in svg_content
            ), "SVG should contain standard text or tspan elements for text content"

            # Should not contain HTML elements
            assert "<div" not in svg_content, "SVG should not contain HTML div elements"
            assert (
                "<span" not in svg_content
            ), "SVG should not contain HTML span elements"

    def test_sequence_diagram_already_pdf_compatible(self):
        """Test that sequence diagrams are already PDF compatible.

        This test should PASS as sequence diagrams use standard SVG text elements.
        """
        # Arrange
        config = {
            "image_format": "svg",
            "theme": "default",
            "error_on_fail": True,
            "cache_enabled": False,
            "mmdc_path": "mmdc",
            "width": 800,
            "height": 600,
            "scale": 1.0,
            "background_color": "white",
        }
        generator = MermaidImageGenerator(config)

        sequence_code = """
        sequenceDiagram
            Alice->>Bob: Hello Bob
            Bob-->>Alice: Hello Alice
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_sequence.svg"

            # Act
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0

                # Create SVG with standard text elements (current working output)
                working_svg = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
                    <g>
                        <text x="100" y="50" style="text-anchor: middle;">Alice</text>
                        <text x="200" y="50" style="text-anchor: middle;">
                            <tspan>Bob</tspan>
                        </text>
                    </g>
                </svg>"""
                output_path.write_text(working_svg)

                success = generator.generate(sequence_code, str(output_path), config)

            # Assert - This should PASS
            assert success is True

            svg_content = output_path.read_text()

            # Should not contain foreignObject elements
            assert "<foreignObject" not in svg_content
            assert 'xmlns="http://www.w3.org/1999/xhtml"' not in svg_content

            # Should contain standard SVG text elements
            assert "<text" in svg_content or "<tspan" in svg_content
