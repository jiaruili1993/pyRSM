# pyRSM: Synchrotron XRD Reciprocal Space Mapping Tool

A Python tool for processing synchrotron X-ray diffraction data from 2D detectors, converting scan data into 3D reciprocal space maps (h,k,l coordinates) with interactive visualization capabilities. This package has been tested at multiple beamlines at APS, CLS, SSRL, and ESRF, in multiple soft X-ray and hard X-ray diffraction and scattering experiments.

<img src="images\lscan.gif" width="300"/>

## Features

- Load and process synchrotron XRD spec files with 2D detector images
- Convert detector coordinates to reciprocal space (h,k,l) using sample orientation matrix
- Generate 3D intensity grids from single or multiple scans
- Interactive 3D visualization of detector images in reciprocal space
- Animated slice viewing through h, k, or l directions
- Data rebinning for performance optimization
- Support for custom h,k,l ranges and grid resolutions

## Quick Start

```python
from pyRSM import load_convert, rsm_convert, visualize_det, h_slice

# Load and convert a single scan
imgs, qx, qy, qz = load_convert('your_file', scan_number=14)

# Visualize detector images in 3D reciprocal space
fig = visualize_det(imgs, qx, qy, qz, cscale=[10, 95], downscale=10)
fig.show()

# Generate 3D reciprocal space map from multiple scans
grid_data, coords = rsm_convert('your_file', [14, 15, 16], 
                               h_n=100, k_n=100, l_n=100)

# Visualize h-slices through the data
h_slice(grid_data, coords, logscale=True, title="H-slices")
```
<table>
  <tr>
      <td align="center" style="vertical-align: bottom;">
        <em>Output of h_slice</em>
      </td>
      <td align="center" style="vertical-align: bottom;">
        <em>Output of visualize_det</em>
      </td>
    </tr>
  <br>
  <tr>
    <td align="center" style="vertical-align: bottom;">
      <div style="height: 200px; display: flex; align-items: center; justify-content: center;">
        <img src="images\lscan.gif" width="300" ; object-fit: contain;"/>
      </div>
    </td>
    <td align="center" style="vertical-align: bottom;">
      <div style="height: 200px; display: flex; align-items: center; justify-content: center;">
        <img src="images\detector.gif" width="300" ; object-fit: contain;"/>
      </div>
    </td>
  </tr>
</table>

## File Structure

Your data should be organized as:
```
your_project/
├── your_file.spec          # Spec file with scan metadata
└── images/
    └── S001/               # Scan directories (simplified structure)
        ├── your_file_S001_00000.tif
        ├── your_file_S001_00001.tif
        └── ...
```

## Technical Details

### Detector Configuration (different from experiment to experiment)
- **Detector**: 516×516 pixel area detector
- **Pixel size**: 55 μm
- **Distance**: 770mm from sample
- **Center Pixel**: (188, 146)

### Coordinate System (check beamline configuration)
- **Sample axes**: x+, z-, y+, z- rotation sequence
- **Detector axes**: x+, z- 
- **Reference vector**: [0,1,0] (surface normal)
- **Primary beam**: [0,0,1] direction

<img src="images\Diffractometer.png" width="300"/>

### Data Processing
- Automatic I0 normalization using ion chamber readings
- 3D gridding with configurable resolution
- Support for both measured and fixed motor positions

### Visualization Features
- **Colormaps**: viridis (standard), RdBu (dichroic signals)
- **Scaling**: Linear or logarithmic intensity scaling
- **Animation**: Smooth frame transitions with play/pause controls
- **Performance**: Automatic rebinning for large datasets

## Requirements

- Python >= 3.7
- numpy >= 1.18.0
- xrayutilities >= 1.7.0
- silx >= 1.0.0
- plotly >= 5.0.0
- pillow >= 8.0.0
- vtk >= 9.0.0

## Installation Notes

The package expects:
1. Standard Spec files from diffraction beamline
2. TIF image files organized by scan number
3. UB matrix stored in spec file sample section
4. X-ray energy in scan header (in unit of KeV)

## Citation

If you think this software helps your research, please cite:

```bibtex
@software{pyrsm,
  title={pyRSM: Synchrotron XRD Reciprocal Space Mapping Tool},
  author={Jiarui Li},
  year={2025},
  url={https://github.com/jiaruili1993/pyRSM}
}
```

## Support

For questions or issues, please contact: jiaruili@stanford.edu
