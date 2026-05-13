# Engine Component Impact Fracture Analysis

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![ParaView](https://img.shields.io/badge/ParaView-5.10+-green.svg)](https://www.paraview.org/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org/)

**Author:** Nicholas Rodriguez, Forensic Mechanical Engineer  
**Application:** High-Velocity Impact & Foreign Object Damage (FOD) Analysis  
**Last Updated:** December 2025

---

## Overview

This portfolio provides a complete forensic workflow for analyzing **high-velocity impact damage** on turbine engine components using ParaView. The time-series simulation models foreign object damage (FOD) on a nickel superalloy turbine blade, capturing crater formation, stress wave propagation, and fragment ejection at microsecond resolution.

### Key Features

- ⏱️ **15-Timestep Time Series** (500 μs impact duration)
- 🔍 **Warp By Vector** for crater and stress wave visualization
- 📍 **Temporal Particles to Pathlines** for fragment tracking
- 📋 **Yield Exceedance Detection** with microsecond precision
- 🌡️ **Thermal Analysis** for adiabatic heating effects
- 🐍 **Automated Python scripts** for impact forensics

---

## Repository Structure

```
portfolio-peter-vocelka-engine-impact/
│
├── impact-simulation/
│   ├── generate_impact_fracture.py    # Time series generator
│   ├── blade_impact_simulation.pvd    # Structure PVD
│   ├── fragment_trajectories.pvd      # Fragment PVD
│   ├── blade_impact_XXXX.vtk          # 15 structure timesteps
│   └── fragments_XXXX.vtk             # 15 particle timesteps
│
├── scripts/
│   └── impact_fracture_analysis.py    # Automated analysis
│
├── documentation/
│   └── SOP_Impact_Fracture_Analysis.md
│
├── README.md
└── LICENSE
```

---

## Quick Start

### 1. Load Impact Simulation

```bash
paraview impact-simulation/blade_impact_simulation.pvd
```

### 2. Apply Warp By Vector (50×)

```
Filters > Warp By Vector
- Vectors: Displacement
- Scale Factor: 50
```

### 3. Track Fragment Trajectories

```
File > Open > fragment_trajectories.pvd
Filters > Temporal > Temporal Particles To Pathlines
- ID Channel: FragmentID
```

### 4. Find Yield Exceedance

```
Filters > Threshold
- Scalars: yield_exceeded
- Lower: 0.5
```

### 5. Run Automated Analysis

```bash
pvpython scripts/impact_fracture_analysis.py
```

---

## Dataset Specifications

### Geometry: Turbine Blade (Simplified)

| Parameter | Value |
|-----------|-------|
| Chord Length | 80 mm |
| Span Height | 120 mm |
| Maximum Thickness | 8 mm |
| Airfoil Profile | NACA 0012 |
| Grid Resolution | 40 × 60 × 35 |
| Total Nodes | 84,000 |

### Material: Inconel 718 (Nickel Superalloy)

| Property | Value |
|----------|-------|
| Yield Strength | 1100 MPa |
| Ultimate Strength | 1375 MPa |
| Young's Modulus | 205 GPa |
| Density | 8190 kg/m³ |
| Fracture Toughness | 100 MPa√m |

### Impact Parameters

| Parameter | Value |
|-----------|-------|
| Impact Velocity | **200 m/s** (720 km/h) |
| Impactor Mass | 0.15 kg (small bird) |
| Impact Energy | **3000 J** |
| Impact Location | Leading edge, mid-span |
| Simulation Duration | 500 μs |

---

## Scalar Fields

| Array Name | Description | Units |
|------------|-------------|-------|
| `blade_region` | 1=Core, 2=LE, 3=TE, 4=Tip | - |
| `von_mises_stress` | von Mises stress | MPa |
| `yield_exceeded` | Yield flag (0 or 1) | - |
| `plastic_strain` | Accumulated plastic strain | % |
| `damage_parameter` | Johnson-Cook damage (0-1) | - |
| `strain_rate` | Strain rate | 1/s |
| `temperature_rise` | Adiabatic heating | K |
| `Displacement` | Deformation vector | mm |

---

## Impact Timeline

```
t = 0 μs     ─── Impact initiation
    │
    │        Elastic wave propagation (~5000 m/s)
    │
t = 35 μs    ─── Stress wave reaches back surface
    │
t = 70 μs    ─── Fragment ejection begins
    │            First material separation
    │
t = 140 μs   ─── Crater fully formed
    │            Peak damage accumulation
    │
t = 250 μs   ─── Spallation on back surface
    │
t = 350 μs   ─── Fragment dispersion
    │
t = 500 μs   ─── SIMULATION END
                 ~150 fragments ejected
```

---

## ParaView Workflow Summary

### Workflow 1: Warp By Vector

**Purpose:** Visualize impact crater and stress waves

| Scale | Use Case |
|-------|----------|
| 10× | Blade bending |
| **50×** | Impact crater detail |
| 100× | Stress wave ripples |

### Workflow 2: Temporal Particles to Pathlines

**Purpose:** Track fragment ejection trajectories

- Color by `Velocity` for ejection energy
- Color by `Temperature` for thermal damage
- Use Tube filter for visibility

### Workflow 3: Annotate Selection

**Purpose:** Document yield exceedance

1. Threshold `yield_exceeded > 0.5`
2. Selection Display Inspector for labels
3. Record timestep, stress, location

---

## Impact Damage Mechanisms

### 1. Direct Impact Damage
- Crater formation at impact site
- Plastic deformation zone
- Material compression

### 2. Stress Wave Effects
- Elastic wave propagation
- Reflection from boundaries
- Constructive interference

### 3. Spallation
- Tensile wave at back surface
- Material ejection opposite to impact
- Secondary fragmentation

### 4. Adiabatic Shear
- High strain rate localization
- Thermal softening
- Shear band formation

---

## Applications

This workflow applies to:

- **Aerospace:** Bird strike, FOD analysis
- **Automotive:** Crash simulation, ballistic protection
- **Defense:** Armor penetration, blast effects
- **Manufacturing:** High-speed machining
- **Forensics:** Impact event reconstruction

---

## Fragment Statistics (Final Timestep)

| Category | Count |
|----------|-------|
| Total Fragments | ~150 |
| Front Surface (crater) | ~105 |
| Back Surface (spall) | ~45 |
| High Velocity (>100 m/s) | ~60 |
| High Temperature (>500 K) | ~40 |

---

## Requirements

- ParaView 5.10+
- Python 3.8+

---

## References

1. Johnson, G.R. & Cook, W.H. (1983). A Constitutive Model for Metals
2. FAR 33.94: Bird Ingestion Requirements
3. SAE ARP1587: FOD Characterization

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## Contact

**Nicholas Rodriguez**  
Forensic Mechanical Engineer  
Impact Dynamics & Fracture Mechanics

---

*Part of the Forensic Mechanical Failure Analysis Portfolio*
