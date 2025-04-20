from .processor import OMRProcessor

def parse_sheet(img_bytes, template_path="template.json"):
    """Convenience function to parse a sheet using the OMRProcessor."""
    processor = OMRProcessor(template_path)
    return processor.process_sheet(img_bytes)
