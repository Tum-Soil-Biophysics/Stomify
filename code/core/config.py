"""
Application-wide configuration: version, colors, thresholds, developer info.
"""

# -- Developer Information ----------------------------------------------------
DEVELOPER_NAME = "Vimukthi Viduranga"
INSTITUTION = "Technical University of Munich"
EMAIL = "vimvidu@gmail.com"
LINKEDIN = "http://linkedin.com/in/sav-viduranga"

# -- Application Info ---------------------------------------------------------
APP_VERSION = "1.0"
APP_TITLE = f"Stomify - Stomatal Density Analyzer v{APP_VERSION}"

# -- Detection Defaults -------------------------------------------------------
LOW_CONFIDENCE_THRESHOLD = 0.75
DEFAULT_CONFIDENCE = 0.25
DEFAULT_IOU = 0.45


# -- Color Scheme (Material Design) -------------------------------------------
COLORS = {
    "primary":          "#1565C0",
    "primary_light":    "#42A5F5",
    "primary_dark":     "#0D47A1",
    "secondary":        "#43A047",
    "secondary_light":  "#66BB6A",
    "background":       "#FAFAFA",
    "surface":          "#FFFFFF",
    "card":             "#FFFFFF",
    "text":             "#212121",
    "text_secondary":   "#757575",
    "error":            "#E53935",
    "warning":          "#FB8C00",
    "success":          "#43A047",
    "divider":          "#E0E0E0",
    "hover":            "#E3F2FD",
}

# Dark-mode colour scheme
COLORS_DARK = {
    "primary":          "#42A5F5",
    "primary_light":    "#90CAF9",
    "primary_dark":     "#1565C0",
    "secondary":        "#66BB6A",
    "secondary_light":  "#81C784",
    "background":       "#1E1E1E",
    "surface":          "#2D2D30",
    "card":             "#3C3C3C",
    "text":             "#E0E0E0",
    "text_secondary":   "#9E9E9E",
    "error":            "#EF5350",
    "warning":          "#FFA726",
    "success":          "#66BB6A",
    "divider":          "#424242",
    "hover":            "#37474F",
}

# Supported image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}
