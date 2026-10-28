"""
ReportGenerator — Multi-sheet Excel report output using openpyxl.
"""

from datetime import datetime

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils import get_column_letter

from .config import (
    APP_VERSION,
    LOW_CONFIDENCE_THRESHOLD,
    DEVELOPER_NAME,
    INSTITUTION,
    EMAIL,
)


class ReportGenerator:
    """Generate comprehensive Excel reports with FIXED plant summaries."""

    @staticmethod
    def generate(results_df, output_path, pixels_per_mm=None, model_info=None, include_low_conf_sheet=True):
        """Generate Excel report with multiple sheets."""
        if results_df.empty:
            return None

        wb = Workbook()

        # Styles
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill("solid", fgColor="1565C0")
        subheader_fill = PatternFill("solid", fgColor="42A5F5")
        green_fill = PatternFill("solid", fgColor="C8E6C9")
        yellow_fill = PatternFill("solid", fgColor="FFF9C4")
        border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )
        center = Alignment(horizontal="center", vertical="center")

        # ── Sheet 1: Plant Summary ───────────────────────────────────────
        ws = wb.active
        ws.title = "Plant Summary"

        ws["A1"] = "🔬 Stomatal Count Summary by Plant"
        ws["A1"].font = Font(bold=True, size=16, color="1565C0")
        ws.merge_cells("A1:H1")

        ws["A3"] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ws["A4"] = f"Total Images: {len(results_df)}"
        ws["A5"] = f"Total Stomata: {int(results_df['stomata_count'].sum())}"
        if model_info:
            ws["A6"] = f"Model: {model_info}"
        ws["A7"] = f"Developer: {DEVELOPER_NAME}"

        row = 10
        ws[f"A{row}"] = "Summary by Plant and Leaf Surface"
        ws[f"A{row}"].font = Font(bold=True, size=12, color="1565C0")
        row += 2

        pivot_data = {}
        for _, r in results_df.iterrows():
            plant = str(r["plant_id"]).strip()
            pos = str(r["position"]).lower().strip()
            count = int(r["stomata_count"])

            if plant not in pivot_data:
                pivot_data[plant] = {
                    "top_total": 0, "top_images": 0,
                    "bottom_total": 0, "bottom_images": 0,
                    "unknown_total": 0, "unknown_images": 0,
                }

            if pos in ["top", "adaxial", "upper", "ad"]:
                pivot_data[plant]["top_total"] += count
                pivot_data[plant]["top_images"] += 1
            elif pos in ["bottom", "bot", "abaxial", "lower", "ab"]:
                pivot_data[plant]["bottom_total"] += count
                pivot_data[plant]["bottom_images"] += 1
            else:
                pivot_data[plant]["unknown_total"] += count
                pivot_data[plant]["unknown_images"] += 1

        headers = [
            "Plant ID", "TOP Total", "TOP Mean", "TOP N",
            "BOTTOM Total", "BOTTOM Mean", "BOTTOM N", "GRAND TOTAL",
        ]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = center
        row += 1

        for plant in sorted(pivot_data.keys()):
            data = pivot_data[plant]
            top_mean = data["top_total"] / data["top_images"] if data["top_images"] > 0 else 0
            bot_mean = data["bottom_total"] / data["bottom_images"] if data["bottom_images"] > 0 else 0
            grand_total = data["top_total"] + data["bottom_total"] + data["unknown_total"]

            values = [
                plant,
                data["top_total"] if data["top_images"] > 0 else "-",
                round(top_mean, 1) if data["top_images"] > 0 else "-",
                data["top_images"] if data["top_images"] > 0 else "-",
                data["bottom_total"] if data["bottom_images"] > 0 else "-",
                round(bot_mean, 1) if data["bottom_images"] > 0 else "-",
                data["bottom_images"] if data["bottom_images"] > 0 else "-",
                grand_total,
            ]

            for col, val in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=val)
                cell.border = border
                cell.alignment = center
                if col == 8:
                    cell.font = Font(bold=True)
                    cell.fill = green_fill
            row += 1

        row += 1
        ws.cell(row=row, column=1, value="TOTAL").font = Font(bold=True)
        ws.cell(row=row, column=2, value=sum(d["top_total"] for d in pivot_data.values()))
        ws.cell(row=row, column=5, value=sum(d["bottom_total"] for d in pivot_data.values()))
        ws.cell(row=row, column=8, value=int(results_df["stomata_count"].sum())).font = Font(bold=True)

        for col in range(1, 9):
            ws.cell(row=row, column=col).border = border
            ws.cell(row=row, column=col).fill = subheader_fill

        for i, width in enumerate([15, 12, 12, 10, 14, 14, 10, 14], 1):
            ws.column_dimensions[get_column_letter(i)].width = width

        # ── Sheet 2: Raw Data ────────────────────────────────────────────
        ws_raw = wb.create_sheet("Raw Data")
        
        # Build headers dynamically based on available columns
        raw_headers = ["Filename", "Plant ID", "Position", "Replicate",
                       "Stomata Count", "Avg Confidence"]
        raw_fields = ["filename", "plant_id", "position", "replicate",
                      "stomata_count", "avg_confidence"]
        
        # Add density-related columns if present
        has_density = "density_per_mm2" in results_df.columns
        if has_density:
            raw_headers.extend(["Image W (px)", "Image H (px)", "Area (mm²)", "Density (/mm²)"])
            raw_fields.extend(["image_width_px", "image_height_px", "area_mm2", "density_per_mm2"])

        for col, header in enumerate(raw_headers, 1):
            cell = ws_raw.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = center

        for row_idx, (_, row_data) in enumerate(results_df.iterrows(), 2):
            for col_idx, field in enumerate(raw_fields, 1):
                val = row_data.get(field, "")
                if field == "stomata_count" and val != "":
                    val = int(val)
                elif field == "avg_confidence" and val != "":
                    val = round(float(val), 3)
                elif field in ("area_mm2", "density_per_mm2") and val != "" and pd.notna(val):
                    val = round(float(val), 4)
                elif field in ("image_width_px", "image_height_px") and val != "":
                    val = int(val)
                cell = ws_raw.cell(row=row_idx, column=col_idx, value=val if pd.notna(val) else "")
                cell.border = border

            if row_data.get("avg_confidence", 1.0) < LOW_CONFIDENCE_THRESHOLD and row_data.get("avg_confidence", 1.0) > 0:
                for col in range(1, len(raw_fields) + 1):
                    ws_raw.cell(row=row_idx, column=col).fill = yellow_fill

        for col in range(1, len(raw_headers) + 1):
            ws_raw.column_dimensions[get_column_letter(col)].width = 18

        # ── Sheet 3: Statistics ──────────────────────────────────────────
        ws_stats = wb.create_sheet("Statistics")
        ws_stats["A1"] = "Overall Statistics"
        ws_stats["A1"].font = Font(bold=True, size=14, color="1565C0")

        stats = [
            ("Total Images:", len(results_df)),
            ("Total Stomata:", int(results_df["stomata_count"].sum())),
            ("Mean Stomata/Image:", round(results_df["stomata_count"].mean(), 2)),
            ("Std Dev:", round(results_df["stomata_count"].std(), 2)),
            ("Min:", int(results_df["stomata_count"].min())),
            ("Max:", int(results_df["stomata_count"].max())),
        ]

        # Add density statistics if available
        if "density_per_mm2" in results_df.columns:
            density_col = results_df["density_per_mm2"].dropna()
            if len(density_col) > 0:
                stats.extend([
                    ("", ""),
                    ("── Density Statistics ──", ""),
                    ("Pixels/mm:", round(pixels_per_mm, 2) if pixels_per_mm else "Not set"),
                    ("Mean Density (/mm²):", round(density_col.mean(), 4)),
                    ("Std Dev Density:", round(density_col.std(), 4)),
                    ("Min Density:", round(density_col.min(), 4)),
                    ("Max Density:", round(density_col.max(), 4)),
                ])
        stats.append(("Avg Confidence:", round(results_df["avg_confidence"].mean(), 3)))

        for i, (label, value) in enumerate(stats, 3):
            ws_stats[f"A{i}"] = label
            ws_stats[f"B{i}"] = value
            ws_stats[f"A{i}"].font = Font(bold=True)
            ws_stats[f"B{i}"].alignment = center

        # Dynamic row after stats entries (3 + len(stats) + 1 blank row)
        cmp_start = 3 + len(stats) + 2

        ws_stats[f"A{cmp_start}"] = "TOP vs BOTTOM Comparison"
        ws_stats[f"A{cmp_start}"].font = Font(bold=True, size=12, color="1565C0")

        cmp_headers = ["Position", "Total", "Mean", "Std", "N"]
        header_row = cmp_start + 2
        for col, header in enumerate(cmp_headers, 1):
            cell = ws_stats.cell(row=header_row, column=col, value=header)
            cell.font = header_font
            cell.fill = subheader_fill
            cell.border = border

        top_data = results_df[
            results_df["position"].str.lower().isin(["top", "adaxial", "upper", "ad"])
        ]
        bot_data = results_df[
            results_df["position"].str.lower().isin(["bottom", "bot", "abaxial", "lower", "ab"])
        ]

        for pos_idx, (pos_name, pos_data) in enumerate(
            [("TOP", top_data), ("BOTTOM", bot_data)], header_row + 1
        ):
            if len(pos_data) > 0:
                ws_stats.cell(row=pos_idx, column=1, value=pos_name).border = border
                ws_stats.cell(row=pos_idx, column=2, value=int(pos_data["stomata_count"].sum())).border = border
                ws_stats.cell(row=pos_idx, column=3, value=round(pos_data["stomata_count"].mean(), 2)).border = border
                ws_stats.cell(row=pos_idx, column=4, value=round(pos_data["stomata_count"].std(), 2)).border = border
                ws_stats.cell(row=pos_idx, column=5, value=len(pos_data)).border = border



        # ── Sheet 4: Low Confidence Review ───────────────────────────────
        if include_low_conf_sheet:
            ws_low = wb.create_sheet("Low Confidence Review")
            ws_low["A1"] = f"⚠️ Images with Confidence < {LOW_CONFIDENCE_THRESHOLD:.0%} (Need Manual Review)"
            ws_low["A1"].font = Font(bold=True, size=12, color="E53935")
            ws_low.merge_cells("A1:G1")

            ws_low["A3"] = "Instructions: Check these images and enter manual counts if automatic count is wrong"
            ws_low["A3"].font = Font(italic=True, color="757575")

            low_headers = ["Filename", "Plant ID", "Position", "Auto Count",
                           "Confidence", "Manual Count", "Notes"]
            for col, header in enumerate(low_headers, 1):
                cell = ws_low.cell(row=5, column=col, value=header)
                cell.font = header_font
                cell.fill = PatternFill("solid", fgColor="E53935")
                cell.border = border

            low_conf_df = results_df[
                (results_df["avg_confidence"] < LOW_CONFIDENCE_THRESHOLD)
                & (results_df["avg_confidence"] > 0)
            ]

            for row_idx, (_, row_data) in enumerate(low_conf_df.iterrows(), 6):
                ws_low.cell(row=row_idx, column=1, value=row_data["filename"]).border = border
                ws_low.cell(row=row_idx, column=2, value=row_data["plant_id"]).border = border
                ws_low.cell(row=row_idx, column=3, value=row_data["position"]).border = border
                ws_low.cell(row=row_idx, column=4, value=int(row_data["stomata_count"])).border = border
                ws_low.cell(row=row_idx, column=5, value=round(row_data["avg_confidence"], 3)).border = border
                ws_low.cell(row=row_idx, column=6, value="").border = border
                ws_low.cell(row=row_idx, column=7, value="").border = border

                for col in range(1, 8):
                    ws_low.cell(row=row_idx, column=col).fill = yellow_fill

            for col, width in enumerate([30, 15, 12, 12, 12, 14, 25], 1):
                ws_low.column_dimensions[get_column_letter(col)].width = width

        # ── Sheet 5: About ───────────────────────────────────────────────
        ws_about = wb.create_sheet("About")
        ws_about["A1"] = "Stomatal Density Analyzer"
        ws_about["A1"].font = Font(bold=True, size=18, color="1565C0")

        about_info = [
            ("Version:", f"ML Version {APP_VERSION}"),
            ("Developer:", DEVELOPER_NAME),
            ("Institution:", INSTITUTION),
            ("Contact:", EMAIL),
            ("Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ("", ""),
            ("Method:", "YOLOv8 Object Detection"),
            ("Model:", model_info if model_info else "Custom trained"),
        ]

        for i, (label, value) in enumerate(about_info, 3):
            ws_about[f"A{i}"] = label
            ws_about[f"A{i}"].font = Font(bold=True)
            ws_about[f"B{i}"] = value

        wb.save(output_path)
        return output_path
