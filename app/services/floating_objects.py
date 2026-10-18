from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from xml.etree import ElementTree


DRAWING_PART_PREFIXES = (
    "xl/drawings/",
    "xl/media/",
    "xl/charts/",
    "xl/ctrlProps/",
    "xl/embeddings/",
    "xl/activeX/",
    "xl/vml",
    "xl/comments",
    "xl/threadedComments/",
    "xl/persons/",
)
RELATIONSHIP_PART_PREFIX = "xl/worksheets/_rels/"
CONTENT_TYPES_PART = "[Content_Types].xml"
RELATIONSHIPS_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/content-types"
WORKSHEET_OBJECT_ELEMENTS = {"drawing", "legacyDrawing", "legacyDrawingHF", "picture", "oleObjects", "controls"}


class FloatingObjectPreserver:
    """Restore OOXML drawing parts that openpyxl cannot reliably round-trip."""

    def preserve(self, template_path: Path, generated_path: Path) -> None:
        temporary_path = generated_path.with_suffix(".floating-objects.xlsx")
        with ZipFile(template_path) as template_zip, ZipFile(generated_path) as generated_zip:
            template_entries = {entry.filename: template_zip.read(entry) for entry in template_zip.infolist()}
            generated_entries = {entry.filename: generated_zip.read(entry) for entry in generated_zip.infolist()}

        for name, content in template_entries.items():
            if self._is_floating_object_part(name) or self._is_worksheet_relationship(name):
                generated_entries[name] = content
        for name, content in template_entries.items():
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml") and name in generated_entries:
                generated_entries[name] = self._restore_worksheet_object_references(generated_entries[name], content)
        generated_entries[CONTENT_TYPES_PART] = self._merge_content_types(
            generated_entries[CONTENT_TYPES_PART], template_entries[CONTENT_TYPES_PART]
        )

        with ZipFile(temporary_path, "w", compression=ZIP_DEFLATED) as output_zip:
            for name, content in generated_entries.items():
                output_zip.writestr(name, content)
        temporary_path.replace(generated_path)

    @staticmethod
    def _is_floating_object_part(name: str) -> bool:
        return any(name.startswith(prefix) for prefix in DRAWING_PART_PREFIXES)

    @staticmethod
    def _is_worksheet_relationship(name: str) -> bool:
        return name.startswith(RELATIONSHIP_PART_PREFIX) and name.endswith(".rels")

    @staticmethod
    def _merge_content_types(generated: bytes, template: bytes) -> bytes:
        namespace = f"{{{CONTENT_TYPES_NAMESPACE}}}"
        generated_root = ElementTree.fromstring(generated)
        template_root = ElementTree.fromstring(template)
        existing = {(element.tag, element.attrib.get("PartName"), element.attrib.get("Extension")) for element in generated_root}
        for element in template_root:
            key = (element.tag, element.attrib.get("PartName"), element.attrib.get("Extension"))
            if key not in existing and element.tag in {f"{namespace}Default", f"{namespace}Override"}:
                generated_root.append(element)
        return ElementTree.tostring(generated_root, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def _restore_worksheet_object_references(generated: bytes, template: bytes) -> bytes:
        generated_root = ElementTree.fromstring(generated)
        template_root = ElementTree.fromstring(template)
        template_objects = [
            element for element in template_root
            if element.tag.rsplit("}", 1)[-1] in WORKSHEET_OBJECT_ELEMENTS
        ]
        if not template_objects:
            return generated
        for element in list(generated_root):
            if element.tag.rsplit("}", 1)[-1] in WORKSHEET_OBJECT_ELEMENTS:
                generated_root.remove(element)
        generated_root.extend(template_objects)
        return ElementTree.tostring(generated_root, encoding="utf-8", xml_declaration=True)