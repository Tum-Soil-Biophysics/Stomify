"""
FilenameParser — Extract plant ID, leaf position, and replicate
from microscopy image filenames.
"""

import os
import re


class FilenameParser:
    """Parse plant ID, position, and replicate from filename."""

    TOP_KEYWORDS = ["top", "adaxial", "upper", "ad", "up"]
    BOTTOM_KEYWORDS = ["bottom", "bot", "abaxial", "lower", "ab", "low"]

    @staticmethod
    def parse(filename: str) -> dict:
        name = os.path.splitext(filename)[0]
        name_lower = name.lower()

        plant_id = name
        position = "unknown"
        replicate = 1

        # Detect position
        for kw in FilenameParser.TOP_KEYWORDS:
            if kw in name_lower:
                position = "top"
                break

        if position == "unknown":
            for kw in FilenameParser.BOTTOM_KEYWORDS:
                if kw in name_lower:
                    position = "bottom"
                    break

        # Extract plant ID
        patterns = [
            r"^([^-_]+?)[\s]*[-_][\s]*(top|bottom|bot|adaxial|abaxial|upper|lower|ad|ab)",
            r"^(.+?)[-_\s]+(top|bottom|bot|adaxial|abaxial|upper|lower|ad|ab)",
            r"^([A-Za-z]+\d*)",
        ]

        for pattern in patterns:
            match = re.match(pattern, name, re.IGNORECASE)
            if match:
                plant_id = match.group(1).strip()
                break

        plant_id = re.sub(r"[-_\s]+$", "", plant_id)

        # Extract replicate number
        rep_patterns = [
            r"[-_\s](\d+)\s*$",
            r"[-_\s](\d+)\.",
            r"rep\s*(\d+)",
            r"r(\d+)",
        ]

        for pattern in rep_patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                replicate = int(match.group(1))
                break

        return {
            "plant_id": plant_id,
            "position": position,
            "replicate": replicate,
        }
