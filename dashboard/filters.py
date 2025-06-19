from datetime import datetime

def register_filters(app):
    """Register custom filters with the Flask app."""
    
    @app.template_filter('datetime')
    def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
        """Format a datetime object or ISO timestamp string to a readable format."""
        if value is None:
            return ""
        
        # If value is already a datetime object
        if isinstance(value, datetime):
            return value.strftime(format)
        
        # If value is a string, try to parse it
        try:
            # Handle ISO format with timezone
            if isinstance(value, str):
                # Remove any timezone part for simpler parsing
                if 'T' in value:
                    # ISO format with 'T' separator
                    parts = value.split('.')
                    if len(parts) > 1:
                        # Has milliseconds
                        dt_str = parts[0]
                    else:
                        # No milliseconds
                        if '+' in value:
                            dt_str = value.split('+')[0]
                        elif 'Z' in value:
                            dt_str = value.replace('Z', '')
                        else:
                            dt_str = value
                    
                    # Parse the datetime
                    dt = datetime.fromisoformat(dt_str.replace('Z', ''))
                else:
                    # Simple format without 'T'
                    dt = datetime.fromisoformat(value)
                
                return dt.strftime(format)
        except (ValueError, TypeError):
            # If parsing fails, return the original value
            return value
        
        # If all else fails, return the original value
        return value