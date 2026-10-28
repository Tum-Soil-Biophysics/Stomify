"""
HelpTab -- Comprehensive in-app user documentation and how-to-use guide.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser

from core.config import APP_VERSION, DEVELOPER_NAME, INSTITUTION, EMAIL
from i18n import tr


class HelpTab(QWidget):
    """User documentation tab using rich text."""

    def __init__(self, settings_model, parent=None):
        super().__init__(parent)
        self.settings = settings_model
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet("padding: 15px;")
        self.browser.setHtml(self._build_html(self.settings.language))
        layout.addWidget(self.browser)

    def retranslate(self, lang: str):
        self.browser.setHtml(self._build_html(lang))

    def _build_html(self, lang: str) -> str:
        t = lambda key: tr(key, lang)
        return f"""
<html>
<head>
<style>
  body {{ font-family: 'Segoe UI', sans-serif; font-size: 10pt; color: #212121; line-height: 1.5; }}
  h1 {{ color: #1565C0; border-bottom: 2px solid #42A5F5; padding-bottom: 6px; font-size: 16pt; }}
  h2 {{ color: #1565C0; margin-top: 24px; font-size: 13pt; }}
  h3 {{ color: #0D47A1; margin-top: 16px; font-size: 11pt; }}
  .section {{ margin-bottom: 20px; }}
  code {{ background: #E3F2FD; padding: 2px 6px; border-radius: 3px; font-family: Consolas; }}
  .tip {{ background: #E8F5E9; padding: 10px 14px; border-left: 4px solid #43A047; margin: 10px 0; border-radius: 3px; }}
  .warn {{ background: #FFF3E0; padding: 10px 14px; border-left: 4px solid #FB8C00; margin: 10px 0; border-radius: 3px; }}
  .info {{ background: #E3F2FD; padding: 10px 14px; border-left: 4px solid #1565C0; margin: 10px 0; border-radius: 3px; }}
  pre {{ background: #F5F5F5; padding: 10px; border-radius: 4px; font-family: Consolas; font-size: 9pt; }}
  table {{ border-collapse: collapse; margin: 8px 0; width: 100%; }}
  th {{ background: #E3F2FD; color: #1565C0; padding: 6px 10px; text-align: left; border: 1px solid #BBDEFB; }}
  td {{ padding: 6px 10px; border: 1px solid #E0E0E0; }}
  tr:nth-child(even) {{ background: #FAFAFA; }}
  ol, ul {{ margin: 6px 0; }}
  li {{ margin-bottom: 4px; }}
</style>
</head>
<body>

<h1>{t('help.title')} v{APP_VERSION}</h1>
<p>Complete guide to using the Stomatal Density Analyzer.</p>

<!-- ============================================================ -->
<h2>1. Getting Started</h2>
<!-- ============================================================ -->

<h3>Step 1: Load Your Model</h3>
<ol>
<li>Click <b>Load Model</b> in the header bar (or <code>File &gt; Load Model</code>, shortcut <code>Ctrl+M</code>).</li>
<li>Browse to your trained YOLOv8 model file (<code>.pt</code> format).</li>
<li>The header will update to show the model name and type.</li>
<li>The model path is saved automatically and restored next time you open the app.</li>
</ol>

<div class="tip">
<b>Tip:</b> You only need to load the model once. It is remembered between sessions.
</div>

<h3>Step 2: Prepare Your Images</h3>
<p>Name your image files using this pattern for automatic grouping in reports:</p>
<pre>
PlantID_Position_Replicate.jpg

Examples:
  SaApD1_bot_1.jpg     (Plant SaApD1, bottom surface, replicate 1)
  WT3_top_2.png        (Plant WT3, top surface, replicate 2)
  Control_adaxial_1.tif (Plant Control, adaxial, replicate 1)
</pre>

<table>
<tr><th>Position Keywords</th><th>Interpreted As</th></tr>
<tr><td>top, adaxial, upper, ad</td><td>Adaxial (upper)</td></tr>
<tr><td>bottom, bot, abaxial, lower, ab</td><td>Abaxial (lower)</td></tr>
</table>

<div class="info">
<b>Note:</b> If your filenames don't match this pattern, the analyzer will still work. 
Plant ID, position, and replicate will just show as "Unknown".
</div>

<!-- ============================================================ -->
<h2>2. Tab-by-Tab Guide</h2>
<!-- ============================================================ -->

<h3>Tab 1: Smart Counter</h3>
<p>For manual or semi-automatic counting of individual images.</p>
<ol>
<li>Click <b>Add Image</b> to load one or more microscope images.</li>
<li>Use <b>Prev / Next</b> buttons to navigate between images.</li>
<li><b>Left-click</b> on the image to place a stoma marker (green circle).</li>
<li><b>Right-click</b> on a marker to remove it.</li>
<li>Click <b>AI Count</b> to run automatic detection on the current image. 
    The AI will place boxes that you can then manually adjust.</li>
<li>Click <b>Auto Count All</b> to run AI detection on all loaded images at once.</li>
<li>Use the <b>Confidence slider</b> at the top to adjust detection sensitivity before running AI.</li>
<li>Click <b>Undo / Redo</b> to reverse or redo your manual edits.</li>
<li>When finished, click <b>Export</b> to save a report with all counts.</li>
</ol>

<div class="tip">
<b>Tip:</b> Smart Counter is ideal when you have a small number of images 
and want precise control over every count.
</div>

<h3>Tab 2: Batch Analysis</h3>
<p>For automated analysis of many images at once.</p>
<ol>
<li>Click <b>Folder</b> to select a folder of images, or <b>Images</b> to pick individual files.</li>
<li>The image list populates automatically with parsed filenames.</li>
<li>Set an <b>Output</b> folder (auto-generated if left empty).</li>
<li>Click <b>Analyze All</b> to start batch detection.</li>
<li>A progress bar shows real-time progress. Click <b>Stop</b> to cancel.</li>
<li>Results appear in the table: count and average confidence per image.</li>
<li>If low-confidence images are found, a <b>Review Flagged Images</b> button appears.</li>
<li>An Excel report is automatically saved to the output folder.</li>
</ol>

<div class="warn">
<b>Important:</b> Always check the "Settings" bar at the top of this tab. 
It shows your current Confidence, IoU, and Edge Filtering settings.
Change them in the <b>Settings</b> tab before running analysis.
</div>

<h3>Tab 3: Calibrate &amp; Test</h3>
<p>For testing detection on a single image and calibrating the scale bar.</p>
<ol>
<li>Click <b>Load Image</b> to open a test image.</li>
<li>Click <b>Detect</b> to run the AI and see detection boxes.</li>
<li>Check the stomata count displayed at the top right.</li>
<li>To calibrate the scale:
    <ol type="a">
    <li>Click <b>Calibrate Scale</b> (button turns red).</li>
    <li>Click and drag a line along your scale bar in the image.</li>
    <li>Hold <b>Shift</b> while dragging for a perfectly horizontal or vertical line.</li>
    <li>Enter the <b>real-world distance</b> (in micrometers) in the popup dialog.</li>
    <li>The pixels-per-mm calibration is saved and used for density calculations.</li>
    </ol>
</li>
</ol>

<div class="info">
<b>Calibration</b> enables density calculations (stomata/mm&sup2;) in your reports.
Without calibration, only raw counts are reported.
</div>

<h3>Tab 4: Settings</h3>
<p>All configurable parameters in one place:</p>

<table>
<tr><th>Section</th><th>What It Controls</th></tr>
<tr><td><b>Detection Parameters</b></td><td>
    <b>Confidence</b> (0.05 - 0.95): How sure the AI must be. Lower = more detections but more false positives.<br>
    <b>IoU</b> (0.10 - 0.90): Overlap threshold for merging duplicate boxes. Lower = fewer duplicates.<br>
    <b>Low Confidence Threshold</b>: Images below this average confidence get flagged for review.
</td></tr>
<tr><td><b>Counting Rules</b></td><td>
    Edge Stomata Filtering: removes partial stomata at image borders. See "Edge Filtering" section below.
</td></tr>
<tr><td><b>Calibration</b></td><td>
    Shows current pixels/mm value (set via Calibrate &amp; Test tab).
</td></tr>
<tr><td><b>Appearance</b></td><td>
    <b>Theme</b>: Switch between Light and Dark mode.<br>
    <b>Bounding Box Color</b>: Color of detection rectangles on annotated images (Batch output + Calibrate preview).<br>
    <b>Marker Size</b>: Size of circle markers in Smart Counter and center dots on detections.<br>
    <b>Font Size</b>: Size of numbered labels (e.g. "1 (95%)") on annotated output images.
</td></tr>
<tr><td><b>Export Preferences</b></td><td>
    Choose Excel (.xlsx) or CSV (.csv) format. Set default output folder. Auto-open report after export.
</td></tr>
<tr><td><b>Language</b></td><td>Switch between English and Deutsch.</td></tr>
<tr><td><b>Current Model</b></td><td>Shows loaded model info. Has a "Load Model" button.</td></tr>
<tr><td><b>Data &amp; Reset</b></td><td>Reset all settings to defaults. Shows settings file location.</td></tr>
</table>

<!-- ============================================================ -->
<h2>3. Review Flagged Images</h2>
<!-- ============================================================ -->

<p>After batch analysis, images with low average confidence are flagged for manual review.</p>
<ol>
<li>Click the <b>Review Flagged Images</b> button (orange, shows count) in Batch Analysis.</li>
<li>Or use <b>View &gt; Review Window</b> (shortcut <code>Ctrl+R</code>) anytime.</li>
<li>The Review dialog opens with a list of flagged images on the left.</li>
<li>Select an image to view it on the right canvas.</li>
<li><b>Left-click</b> on the image to add a stoma marker (green circle).</li>
<li><b>Right-click</b> near a marker to remove it.</li>
<li>Click <b>Save &amp; Close</b> to apply your corrections back to the results.</li>
</ol>

<div class="tip">
<b>Tip:</b> After reviewing, you can re-export a corrected report from the File menu.
</div>

<!-- ============================================================ -->
<h2>4. Edge Stomata Filtering</h2>
<!-- ============================================================ -->

<p>Edge filtering removes partial stomata at image borders 
that may distort your density calculations.</p>

<h3>Method A: Standard Top/Left Rule</h3>
<ul>
<li>Keeps boxes touching the <b>Top</b> or <b>Left</b> image edge.</li>
<li>Deletes boxes touching the <b>Bottom</b> or <b>Right</b> edge.</li>
<li><b>Rationale:</b> When images are tiled in a grid, this avoids double-counting 
    the same stomata at the boundary between two adjacent images.</li>
</ul>

<h3>Method B: Area Percentage Rule</h3>
<ul>
<li>Calculates the <b>median area</b> of all centre (non-edge) boxes.</li>
<li>An edge box is kept only if its area &gt;= X% of that median.</li>
<li>Use a lower percentage (30-40%) to keep more partial stomata.</li>
<li>Use a higher percentage (60-80%) for stricter filtering.</li>
</ul>

<h3>Parameters</h3>
<table>
<tr><th>Parameter</th><th>Description</th><th>Default</th></tr>
<tr><td>Edge Margin (px)</td><td>How close a box must be to the border to be "edge"</td><td>5 px</td></tr>
<tr><td>Area Threshold (%)</td><td>Minimum % of median area for edge boxes (Method B only)</td><td>50%</td></tr>
</table>

<div class="info">
Enable edge filtering in <b>Settings &gt; Counting Rules</b>.
</div>

<!-- ============================================================ -->
<h2>5. Save &amp; Load Projects</h2>
<!-- ============================================================ -->

<p>Save your entire session (images, results, corrections, model path) as a <code>.stproj</code> file.</p>
<ul>
<li><b>Save:</b> <code>File &gt; Save Project</code> (shortcut <code>Ctrl+S</code>)</li>
<li><b>Load:</b> <code>File &gt; Open Project</code> (shortcut <code>Ctrl+O</code>)</li>
</ul>

<!-- ============================================================ -->
<h2>6. Output Files</h2>
<!-- ============================================================ -->

<table>
<tr><th>File</th><th>Description</th></tr>
<tr><td><code>Stomata_Report_*.xlsx</code></td><td>Multi-sheet Excel report with Summary, Raw Data, Statistics by Plant/Position, and Low Confidence images</td></tr>
<tr><td><code>Annotated_Images/</code></td><td>Folder with the original images overlaid with detection boxes</td></tr>
<tr><td><code>*.stproj</code></td><td>Saved project file (JSON) for restoring sessions</td></tr>
</table>

<!-- ============================================================ -->
<h2>7. Keyboard Shortcuts</h2>
<!-- ============================================================ -->

<table>
<tr><th>Shortcut</th><th>Action</th></tr>
<tr><td><code>Ctrl+M</code></td><td>Load Model</td></tr>
<tr><td><code>Ctrl+S</code></td><td>Save Project</td></tr>
<tr><td><code>Ctrl+O</code></td><td>Open Project</td></tr>
<tr><td><code>Ctrl+R</code></td><td>Review Window</td></tr>
<tr><td><code>Ctrl+Q</code></td><td>Exit</td></tr>
<tr><td><code>Shift+Drag</code></td><td>Constrain calibration line to horizontal/vertical</td></tr>
<tr><td><code>Mouse Scroll</code></td><td>Zoom in/out on image canvas</td></tr>
</table>

<!-- ============================================================ -->
<h2>8. Troubleshooting</h2>
<!-- ============================================================ -->

<table>
<tr><th>Problem</th><th>Solution</th></tr>
<tr><td>Missing stomata (too few detected)</td><td>Lower the Confidence threshold in Settings (try 0.15)</td></tr>
<tr><td>False detections (artifacts detected as stomata)</td><td>Raise the Confidence threshold (try 0.40)</td></tr>
<tr><td>Duplicate boxes on the same stomata</td><td>Lower the IoU threshold (try 0.30)</td></tr>
<tr><td>Missing close-together stomata</td><td>Raise the IoU threshold (try 0.55)</td></tr>
<tr><td>Wrong counts at image borders</td><td>Enable Edge Filtering in Settings &gt; Counting Rules</td></tr>
<tr><td>No density values in report</td><td>Calibrate your scale in Calibrate &amp; Test tab</td></tr>
<tr><td>Model won't load</td><td>Ensure it's a YOLOv8 <code>.pt</code> file and <code>ultralytics</code> is installed</td></tr>
</table>

<!-- ============================================================ -->
<hr>
<div class="section" style="margin-top: 16px; padding-top: 10px;">
<p><b>Developer:</b> {DEVELOPER_NAME}<br>
<b>Institution:</b> {INSTITUTION}<br>
<b>Contact:</b> {EMAIL}<br>
<b>Version:</b> {APP_VERSION}</p>
<p style="color: #9E9E9E; font-size: 9pt;">Powered by YOLOv8, Python, PySide6, OpenCV</p>
</div>

</body>
</html>
"""
