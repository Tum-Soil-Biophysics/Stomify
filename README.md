# Stomify v1.0

Stomify is a desktop application for automated stomatal counting and stomatal density measurement from leaf epidermal impressions. It uses a YOLOv8m deep learning model (Ultralytics) trained on maize leaf impressions imaged with a light microscope at 10x magnification.

Authors: Vimukthi Arachchillage, Nupur Prakashbhai Chaudhary, Saniv Gupta, Mohsen Zarebanadkouki
Affiliation: Soil Biophysics and Environmental Systems, Technical University of Munich (TUM School of Life Sciences)
Contact: viduranga.sav@gmail.com

## Repository layout

| Folder | Content |
|---|---|
| code/ | Source code of the desktop application |
| notebooks/ | Training notebooks (YOLOv8 and Faster R-CNN baseline) |
| requirements.txt | Python packages needed to run from source |
| LICENSE | GNU Affero General Public License v3.0 |
| CITATION.cff | Citation information |

The trained model (StomifyModel.pt) and the Windows installer are not in this repository. They are part of the Zenodo record (DOI 10.5281/zenodo.23319544, https://zenodo.org/records/23319544).

The training notebooks use the Roboflow platform. Add your own Roboflow API key where the notebooks say YOUR_API_KEY.

## Model

- Architecture: YOLOv8m, trained with Ultralytics 8.4.24
- Input size: 640 x 640 pixels
- Classes: "stomata" and "artifact". The artifact class (bubbles, dust, trichome bases) is used only to reduce false positives. Stomify reports stomata counts only.

## Installation

Windows: run StomifySetup_v1.0_Windows.exe and follow the steps.

From source (Python 3.10 or newer):

    pip install -r requirements.txt
    cd code
    python main.py

Then download StomifyModel.pt from the Zenodo record and load it in the application settings.

## Main features

- Smart Counter: AI-assisted counting of single images, with manual correction of detections
- Batch Analysis: automatic counting of whole folders of images
- Calibrate and Test: scale calibration (pixels per mm) and quick checks of the model
- Settings: confidence threshold, marker size, language (English and German) and light or dark theme
- Export of counts and stomatal density (stomata per mm²) to Excel or CSV

## Basic use

1. Load the model file (StomifyModel.pt).
2. Calibrate the image scale (pixels per mm) with a stage micrometer image.
3. Select a folder of leaf impression images.
4. Run detection. Review and correct counts if needed.
5. Export counts and stomatal density (stomata per mm²) as Excel or CSV.

The default confidence threshold is 0.25 and can be changed in Settings.

## Acknowledgements

Stomify was developed by Vimukthi Arachchillage. Training images were provided by the Chair of Soil Biophysics and Environmental Systems, TUM, and by the co-authors.

## Licence

Stomify is released under the GNU Affero General Public License v3.0 (AGPL-3.0), in line with the Ultralytics YOLOv8 licence.

## How to cite

Please cite Stomify with its Zenodo DOI: https://doi.org/10.5281/zenodo.23319544
