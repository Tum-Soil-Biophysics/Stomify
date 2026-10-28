"""
Translations -- simple dictionary-based EN / DE localisation.

Usage:
    from i18n import tr
    label.setText(tr("btn.analyze_all", lang="de"))
"""

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # -- Tabs --
        "tab.smart_counter":    "Smart Counter",
        "tab.batch_analysis":   "Batch Analysis",
        "tab.calibrate_test":   "Calibrate && Test",
        "tab.settings":         "Settings",

        # -- Menu --
        "menu.file":            "&File",
        "menu.view":            "&View",
        "menu.help":            "&Help",
        "menu.load_model":      "Load Model...",
        "menu.save_project":    "Save Project...",
        "menu.open_project":    "Open Project...",
        "menu.exit":            "Exit",
        "menu.review_window":   "Review Window",
        "menu.about":           "About",

        # -- Buttons --
        "btn.analyze_all":      "Analyze All",
        "btn.stop":             "Stop",
        "btn.clear":            "Clear",
        "btn.load_model":       "Load Model",
        "btn.load_image":       "Load Image",
        "btn.detect":           "Detect",
        "btn.calibrate_scale":  "Calibrate Scale",
        "btn.cancel_calibration": "Cancel Calibration",
        "btn.review_flagged":   "Review {count} Flagged Images",
        "btn.save_close":       "Save && Close",
        "btn.export_report":    "Export Report",
        "btn.add_images":       "Add Images",
        "btn.prev":             "Prev",
        "btn.next":             "Next",
        "btn.ai_count":         "AI Count",
        "btn.auto_count_all":   "Auto Count All",
        "btn.clear_boxes":      "Clear Boxes",
        "btn.undo":             "Undo",
        "btn.redo":             "Redo",
        "btn.remove":           "Remove",
        "btn.clear_all":        "Clear All",
        "btn.open_folder":      "Open Folder",
        "btn.add_image":        "Add Image",
        "btn.save":             "Save",
        "btn.browse":           "Browse",
        "btn.folder":           "Folder",
        "btn.images":           "Images",
        "btn.reset_defaults":   "Reset to Defaults",
        "btn.pick_color":       "Pick...",

        # -- Labels --
        "lbl.input":            "Input:",
        "lbl.output":           "Output:",
        "lbl.stomata":          "Stomata:",
        "lbl.count":            "Count:",
        "lbl.ready":            "Ready",
        "lbl.no_model":         "No model loaded",
        "lbl.confidence":       "Confidence:",
        "lbl.iou":              "IoU:",
        "lbl.pixels_per_mm":    "Pixels/mm:",
        "lbl.stomata_detected": "stomata detected",
        "lbl.images":           "Images",

        # -- Group Boxes --
        "grp.input_output":     "Input && Output",
        "grp.detection_params": "Detection Parameters",
        "grp.counting_rules":   "Counting Rules (Edge Filtering)",
        "grp.calibration":      "Calibration",
        "grp.appearance":       "Appearance",
        "grp.export_prefs":     "Export Preferences",
        "grp.language":         "Language",
        "grp.reset":            "Data && Reset",
        "grp.model_info":       "Current Model",
        "grp.conf_threshold":   "Confidence Threshold",

        # -- Settings --
        "settings.low_conf_thresh":   "Low Confidence Threshold:",
        "settings.edge_filter":       "Enable Edge Filtering",
        "settings.edge_method":       "Filtering Method:",
        "settings.edge_standard":     "Standard Top/Left Rule",
        "settings.edge_area":         "Area Percentage Rule",
        "settings.edge_margin":       "Edge Margin (px):",
        "settings.edge_area_thresh":  "Area Threshold (%):",
        "settings.theme":             "Theme:",
        "settings.theme_light":       "Light",
        "settings.theme_dark":        "Dark",
        "settings.bbox_color":        "Bounding Box Color:",
        "settings.box_text_color":    "Box Text Color:",
        "settings.marker_size":       "Marker Size (px):",
        "settings.font_size":         "Font Size (pt):",
        "settings.export_format":     "Default Export Format:",
        "settings.output_folder":     "Default Output Folder:",
        "settings.auto_open":         "Auto-open report after export",
        "settings.language":          "Interface Language:",
        "settings.settings_location": "Settings location:",
        "settings.show_conf_labels":  "Show confidence labels on boxes",
        "settings.calibration_note":  "(Set via Calibrate && Test tab)",
        "settings.not_set":           "Not set",

        # -- Review Dialog --
        "review.title":         "Review Flagged Images",
        "review.select_image":  "Select an image to review:",
        "review.instructions":  "Left click = Add   |   Right click = Remove",
        "review.no_images":     "No images analyzed yet",
        "review.all_good":      "All images have good confidence scores",
        "review.need_review":   "{count} images need manual review",
        "review.saved":         "Saved: {filename} to {count} stomata",
        "review.added_stoma":   "Added stoma at ({x}, {y})",
        "review.removed_stoma": "Removed stoma",
        "review.no_nearby":     "No stoma nearby to remove",

        # -- Status --
        "status.loading_model":     "Loading model... please wait",
        "status.model_loaded":      "Model loaded: {name}",
        "status.processing":        "Processing {current}/{total}: {filename}",
        "status.complete":          "Complete! Total: {total} stomata",
        "status.stopped":           "Analysis stopped or no results",
        "status.ai_detected":       "AI detected {count} stomata",
        "status.ai_failed":         "AI detection failed",
        "status.calibrated":        "Scale calibrated: {ppm:.1f} pixels/mm",
        "status.cleared":           "Cleared",
        "status.batch_complete":    "Batch AI Count complete for {total} images",
        "status.report_saved":      "Report saved",

        # -- Errors --
        "err.no_model":         "Please load a model first",
        "err.no_images":        "No images to analyze. Select a folder or images first.",
        "err.load_image_first": "Load an image first",
        "err.load_failed":      "Load failed",

        # -- Help --
        "help.title":           "STOMATAL DENSITY ANALYZER",
        "help.quick_start":     "QUICK START GUIDE",
        "help.file_naming":     "FILE NAMING CONVENTION",
        "help.output_files":    "OUTPUT FILES",
        "help.low_conf":        "LOW CONFIDENCE REVIEW",
        "help.troubleshooting": "TROUBLESHOOTING",
        "help.edge_filtering":  "EDGE STOMATA FILTERING",
        "help.edge_desc":       (
            "Edge filtering removes partial stomata at image borders that may "
            "distort your density calculations.\n\n"
            "Method A: Standard Top/Left Rule\n"
            "  Keeps boxes touching the Top or Left image edge.\n"
            "  Deletes boxes touching the Bottom or Right edge.\n"
            "  Rationale: avoids double-counting when images tile.\n\n"
            "Method B: Area Percentage Rule\n"
            "  Calculates the median area of all centre (non-edge) boxes.\n"
            "  An edge box is kept only if its area >= X% of that median.\n"
            "  Use a lower percentage (30-40%) to keep more partial stomata,\n"
            "  or a higher percentage (60-80%) for stricter filtering.\n\n"
            "Edge Margin (px): How close a box must be to the image border\n"
            "  to be considered an 'edge' box. Default: 5 px.\n\n"
            "Enable edge filtering in Settings > Counting Rules."
        ),

        # -- Empty states --
        "empty.analysis":       "Welcome! Load a model, then select images to begin.",
        "empty.preview":        "Click 'Load Image' to preview a single image with detection.",
        "empty.smart_counter":  "Add images to start counting stomata.",

        # -- About --
        "about.title":          "About",
        "about.app_name":       "Stomatal Density Analyzer",
        "about.developed_by":   "Developed by:",
        "about.powered_by":     "Powered by YOLOv8, Python, OpenCV",
    },
    "de": {
        # -- Tabs --
        "tab.smart_counter":    "Intelligenter Zahler",
        "tab.batch_analysis":   "Stapelanalyse",
        "tab.calibrate_test":   "Kalibrieren && Testen",
        "tab.settings":         "Einstellungen",

        # -- Menu --
        "menu.file":            "&Datei",
        "menu.view":            "&Ansicht",
        "menu.help":            "&Hilfe",
        "menu.load_model":      "Modell laden...",
        "menu.save_project":    "Projekt speichern...",
        "menu.open_project":    "Projekt offnen...",
        "menu.exit":            "Beenden",
        "menu.review_window":   "Uberprufungsfenster",
        "menu.about":           "Uber",

        # -- Buttons --
        "btn.analyze_all":      "Alle analysieren",
        "btn.stop":             "Stoppen",
        "btn.clear":            "Loschen",
        "btn.load_model":       "Modell laden",
        "btn.load_image":       "Bild laden",
        "btn.detect":           "Erkennen",
        "btn.calibrate_scale":  "Massstab kalibrieren",
        "btn.cancel_calibration": "Kalibrierung abbrechen",
        "btn.review_flagged":   "{count} markierte Bilder prufen",
        "btn.save_close":       "Speichern && Schliessen",
        "btn.export_report":    "Bericht exportieren",
        "btn.add_images":       "Bilder hinzufugen",
        "btn.prev":             "Zuruck",
        "btn.next":             "Weiter",
        "btn.ai_count":         "KI-Zahlung",
        "btn.auto_count_all":   "Alle automatisch zahlen",
        "btn.clear_boxes":      "Boxen loschen",
        "btn.undo":             "Ruckgangig",
        "btn.redo":             "Wiederholen",
        "btn.remove":           "Entfernen",
        "btn.clear_all":        "Alle loschen",
        "btn.open_folder":      "Ordner offnen",
        "btn.add_image":        "Bild hinzufugen",
        "btn.save":             "Speichern",
        "btn.browse":           "Durchsuchen",
        "btn.folder":           "Ordner",
        "btn.images":           "Bilder",
        "btn.reset_defaults":   "Auf Standard zurucksetzen",
        "btn.pick_color":       "Auswahlen...",

        # -- Labels --
        "lbl.input":            "Eingabe:",
        "lbl.output":           "Ausgabe:",
        "lbl.stomata":          "Stomata:",
        "lbl.count":            "Anzahl:",
        "lbl.ready":            "Bereit",
        "lbl.no_model":         "Kein Modell geladen",
        "lbl.confidence":       "Konfidenz:",
        "lbl.iou":              "IoU:",
        "lbl.pixels_per_mm":    "Pixel/mm:",
        "lbl.stomata_detected": "Stomata erkannt",
        "lbl.images":           "Bilder",

        # -- Group Boxes --
        "grp.input_output":     "Eingabe && Ausgabe",
        "grp.detection_params": "Erkennungsparameter",
        "grp.counting_rules":   "Zahlregeln (Kantenfilterung)",
        "grp.calibration":      "Kalibrierung",
        "grp.appearance":       "Erscheinungsbild",
        "grp.export_prefs":     "Exporteinstellungen",
        "grp.language":         "Sprache",
        "grp.reset":            "Daten && Zurucksetzen",
        "grp.model_info":       "Aktuelles Modell",
        "grp.conf_threshold":   "Konfidenzschwelle",

        # -- Settings --
        "settings.low_conf_thresh":   "Niedrige Konfidenzschwelle:",
        "settings.edge_filter":       "Kantenfilterung aktivieren",
        "settings.edge_method":       "Filtermethode:",
        "settings.edge_standard":     "Standard Oben/Links-Regel",
        "settings.edge_area":         "Flachenprozent-Regel",
        "settings.edge_margin":       "Kantenabstand (px):",
        "settings.edge_area_thresh":  "Flachenschwelle (%):",
        "settings.theme":             "Design:",
        "settings.theme_light":       "Hell",
        "settings.theme_dark":        "Dunkel",
        "settings.bbox_color":        "Begrenzungsrahmenfarbe:",
        "settings.box_text_color":    "Box-Textfarbe:",
        "settings.marker_size":       "Markierungsgrosse (px):",
        "settings.font_size":         "Schriftgrosse (Pkt):",
        "settings.export_format":     "Standard-Exportformat:",
        "settings.output_folder":     "Standard-Ausgabeordner:",
        "settings.auto_open":         "Bericht nach Export automatisch offnen",
        "settings.language":          "Oberflachensprache:",
        "settings.settings_location": "Speicherort der Einstellungen:",
        "settings.show_conf_labels":  "Konfidenzwerte auf Boxen anzeigen",
        "settings.calibration_note":  "(Eingestellt uber Kalibrieren && Testen)",
        "settings.not_set":           "Nicht gesetzt",

        # -- Review Dialog --
        "review.title":         "Markierte Bilder prufen",
        "review.select_image":  "Bild zum Prufen auswahlen:",
        "review.instructions":  "Linksklick = Hinzufugen   |   Rechtsklick = Entfernen",
        "review.no_images":     "Noch keine Bilder analysiert",
        "review.all_good":      "Alle Bilder haben gute Konfidenzwerte",
        "review.need_review":   "{count} Bilder benotigen manuelle Prufung",
        "review.saved":         "Gespeichert: {filename} mit {count} Stomata",
        "review.added_stoma":   "Stoma bei ({x}, {y}) hinzugefugt",
        "review.removed_stoma": "Stoma entfernt",
        "review.no_nearby":     "Kein Stoma in der Nahe zum Entfernen",

        # -- Status --
        "status.loading_model":     "Modell wird geladen... bitte warten",
        "status.model_loaded":      "Modell geladen: {name}",
        "status.processing":        "Verarbeitung {current}/{total}: {filename}",
        "status.complete":          "Fertig! Gesamt: {total} Stomata",
        "status.stopped":           "Analyse gestoppt oder keine Ergebnisse",
        "status.ai_detected":       "KI hat {count} Stomata erkannt",
        "status.ai_failed":         "KI-Erkennung fehlgeschlagen",
        "status.calibrated":        "Massstab kalibriert: {ppm:.1f} Pixel/mm",
        "status.cleared":           "Geloscht",
        "status.batch_complete":    "Stapel-KI-Zahlung fur {total} Bilder abgeschlossen",
        "status.report_saved":      "Bericht gespeichert",

        # -- Errors --
        "err.no_model":         "Bitte laden Sie zuerst ein Modell",
        "err.no_images":        "Keine Bilder zum Analysieren. Wahlen Sie zuerst einen Ordner oder Bilder.",
        "err.load_image_first": "Laden Sie zuerst ein Bild",
        "err.load_failed":      "Laden fehlgeschlagen",

        # -- Help --
        "help.title":           "STOMATADICHTE-ANALYSATOR",
        "help.quick_start":     "SCHNELLSTARTANLEITUNG",
        "help.file_naming":     "DATEIBENENNUNGSKONVENTION",
        "help.output_files":    "AUSGABEDATEIEN",
        "help.low_conf":        "NIEDRIGE KONFIDENZ-PRUFUNG",
        "help.troubleshooting": "FEHLERBEHEBUNG",
        "help.edge_filtering":  "KANTEN-STOMATA-FILTERUNG",
        "help.edge_desc":       (
            "Die Kantenfilterung entfernt unvollstandige Stomata an Bildrandern, "
            "die Ihre Dichteberechnungen verfalschen konnen.\n\n"
            "Methode A: Standard Oben/Links-Regel\n"
            "  Behalt Boxen, die den oberen oder linken Bildrand beruhren.\n"
            "  Loscht Boxen am unteren oder rechten Rand.\n"
            "  Begrundung: vermeidet Doppelzahlung bei Bildkacheln.\n\n"
            "Methode B: Flachenprozent-Regel\n"
            "  Berechnet die mittlere Flache aller Zentrumsboxen.\n"
            "  Eine Kantenbox wird nur behalten, wenn ihre Flache >= X% des Medians ist.\n"
            "  Verwenden Sie eine niedrigere Prozentangabe (30-40%) fur mehr partielle Stomata,\n"
            "  oder eine hohere Prozentangabe (60-80%) fur strengere Filterung.\n\n"
            "Kantenabstand (px): Wie nah eine Box am Bildrand sein muss,\n"
            "  um als 'Kantenbox' zu gelten. Standard: 5 px.\n\n"
            "Aktivieren Sie die Kantenfilterung unter Einstellungen > Zahlregeln."
        ),

        # -- Empty states --
        "empty.analysis":       "Willkommen! Laden Sie ein Modell und wahlen Sie Bilder aus.",
        "empty.preview":        "Klicken Sie auf 'Bild laden' fur eine Vorschau mit Erkennung.",
        "empty.smart_counter":  "Fugen Sie Bilder hinzu, um mit der Zahlung zu beginnen.",

        # -- About --
        "about.title":          "Uber",
        "about.app_name":       "Stomatadichte-Analysator",
        "about.developed_by":   "Entwickelt von:",
        "about.powered_by":     "Basierend auf YOLOv8, Python, OpenCV",
    },
}

# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------

def tr(key: str, lang: str = "en", **kwargs) -> str:
    """Look up a translation string.

    Supports ``str.format``-style placeholders:
        tr("btn.review_flagged", lang="en", count=5)
        -> "Review 5 Flagged Images"
    """
    table = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    raw = table.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        try:
            return raw.format(**kwargs)
        except (KeyError, IndexError):
            return raw
    return raw
