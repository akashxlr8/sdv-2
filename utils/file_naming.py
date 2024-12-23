from datetime import datetime
import os

def generate_filename(prefix, source_files=None, timestamp=None):
    """Generate consistent filenames across the application"""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if source_files:
        # Filter out None values and empty strings
        valid_sources = [f for f in source_files if f]
        if not valid_sources:
            return f"{prefix}_{timestamp}"
            
        # Extract base names without extensions
        source_names = [os.path.splitext(f)[0] for f in valid_sources]
        source_str = "_".join(source_names[:2])
        if len(valid_sources) > 2:
            source_str += "_etc"
        return f"{prefix}_{source_str}_{timestamp}"
    
    return f"{prefix}_{timestamp}"