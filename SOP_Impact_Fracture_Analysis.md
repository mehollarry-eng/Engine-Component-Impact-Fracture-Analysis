# Technical Standard Operating Procedure (SOP)
## Engine Component Impact Fracture Analysis - FOD Investigation

**Document Number:** SOP-FME-FA-002  
**Version:** 1.0  
**Effective Date:** December 2025  
**Author:** Nicholas Rodriguez, Forensic Mechanical Engineer  
**Classification:** Technical Investigation Protocol

---

## 1. Purpose and Scope

This SOP establishes procedures for forensic analysis of **high-velocity impact damage** on engine components using ParaView. The workflow enables investigation of:

- **Impact crater formation** and material ejection
- **Stress wave propagation** through the component
- **Fragment trajectory tracking** for containment analysis
- **Yield exceedance identification** at microsecond resolution

### 1.1 Applicable Standards

- FAR 33.94: Blade Containment and Rotor Unbalance Tests
- ASTM E23: Charpy Impact Test
- SAE ARP1587: Foreign Object Damage

---

## 2. Input Data Requirements

### 2.1 Time Series Dataset

| File | Description |
|------|-------------|
| `blade_impact_simulation.pvd` | Blade structure (15 timesteps) |
| `fragment_trajectories.pvd` | Ejected fragments |
| `blade_impact_XXXX.vtk` | Individual timestep files |
| `fragments_XXXX.vtk` | Fragment particle files |

### 2.2 Material Properties (Inconel 718)

| Property | Value | Notes |
|----------|-------|-------|
| Yield Strength | 1100 MPa | Room temperature |
| Ultimate Strength | 1375 MPa | - |
| Young's Modulus | 205 GPa | - |
| Density | 8190 kg/m³ | - |
| Fracture Toughness | 100 MPa√m | High toughness alloy |

### 2.3 Impact Parameters

| Parameter | Value |
|-----------|-------|
| Impact Velocity | 200 m/s (720 km/h) |
| Impactor Mass | 0.15 kg |
| Impact Energy | 3000 J |
| Simulation Duration | 500 μs |
| Timesteps | 15 |

---

## 3. Procedure 1: Loading Time Series Data

### 3.1 Open Structure PVD

```
File > Open > blade_impact_simulation.pvd
```

### 3.2 Verify Time Range

- Check Animation toolbar
- Confirm **15 timesteps**
- Time range: **0 - 500 μs**

### 3.3 Load Fragment Data

```
File > Open > fragment_trajectories.pvd
```

Fragments appear after ~70 μs when material begins ejecting.

---

## 4. Procedure 2: Warp By Vector (Impact Deformation)

### 4.1 Objective
Visualize impact crater formation and stress wave effects through deformation amplification.

### 4.2 Steps

1. **Select blade structure** in Pipeline Browser

2. **Apply Warp By Vector:**
   ```
   Filters > Alphabetical > Warp By Vector
   ```

3. **Configure:**
   - Vectors: `Displacement`
   - Scale Factor: **50** (initial view)

4. **Click Apply**

### 4.3 Scale Factor Guidelines for Impact

| Scale | Application |
|-------|-------------|
| 10× | Overall blade deflection |
| 50× | **Recommended** - Impact crater detail |
| 100× | Stress wave ripples |
| 200× | Micro-damage visualization |

### 4.4 Impact-Specific Observations

| Feature | Interpretation |
|---------|----------------|
| Central depression | Impact crater |
| Radial ripples | Stress wave fronts |
| Back-surface bulge | Spallation initiation |
| Edge lifting | Blade bending response |

---

## 5. Procedure 3: Temporal Particles To Pathlines

### 5.1 Objective
Track fragment trajectories to understand ejection patterns and containment requirements.

### 5.2 Steps

1. **Select fragment source**

2. **Apply Temporal Particles To Pathlines:**
   ```
   Filters > Temporal > Temporal Particles To Pathlines
   ```

3. **Configure:**
   - Mask Points: **1**
   - Max Track Length: **200** mm
   - ID Channel Array: `FragmentID`

4. **Click Apply**

### 5.3 Visualization Settings

1. **Color by Velocity:**
   - Shows ejection energy
   - Range: 0 - 200 m/s

2. **Color by Temperature:**
   - Shows adiabatic heating
   - Range: 300 - 800 K

3. **Apply Tube filter:**
   ```
   Filters > Tube
   Radius: 0.3 mm
   ```

### 5.4 Fragment Analysis

| Observation | Significance |
|-------------|--------------|
| Forward trajectories | Front surface debris |
| Backward trajectories | Spall fragments |
| High velocity (>100 m/s) | High-energy primary fragments |
| High temperature (>500 K) | Adiabatic shear bands |

---

## 6. Procedure 4: Yield Exceedance Detection

### 6.1 Objective
Identify the exact microsecond and location where yield strength was exceeded.

### 6.2 Using Threshold Filter

1. **Select blade source**

2. **Apply Threshold:**
   ```
   Filters > Threshold
   ```

3. **Configure:**
   - Scalars: `yield_exceeded`
   - Lower: **0.5**
   - Upper: **1.5**
   - Method: Between

4. **Step through timesteps:**
   - Start at t = 0
   - Advance until threshold shows results
   - Record first occurrence

### 6.3 Selection Display Inspector

1. **Open Inspector:**
   ```
   View > Selection Display Inspector
   ```

2. **Configure labels:**
   - Point Labels: ON
   - Array: `von_mises_stress`
   - Format: `%.0f MPa`

3. **Select peak stress points:**
   - Use "Select Points On" tool
   - Click on impact region

### 6.4 Annotation

Create text annotation with:
```
YIELD EXCEEDANCE DETECTED
Time: [value] μs
Peak Stress: [value] MPa
Location: Impact zone
```

---

## 7. Procedure 5: Damage Parameter Analysis

### 7.1 Objective
Quantify material damage for structural integrity assessment.

### 7.2 Damage Zone Extraction

1. **Apply Threshold:**
   - Scalars: `damage_parameter`
   - Lower: **0.3** (30% damage)
   - Upper: **1.0**

2. **Visualize damage extent:**
   - Color by damage level
   - Use contour lines

### 7.3 Damage Interpretation

| Damage Level | Condition |
|--------------|-----------|
| 0.0 - 0.2 | Elastic deformation only |
| 0.2 - 0.5 | Plastic deformation |
| 0.5 - 0.8 | Significant damage |
| 0.8 - 1.0 | Material failure |

---

## 8. Procedure 6: Strain Rate Analysis

### 8.1 Importance
Strain rate effects are critical in impact - material response differs at high loading rates.

### 8.2 Threshold High-Rate Regions

```
Filters > Threshold
Scalars: strain_rate
Lower: 1000 (1/s)
Upper: 1e8
```

### 8.3 Rate-Dependent Effects

| Strain Rate | Regime | Effect |
|-------------|--------|--------|
| < 1 /s | Quasi-static | Standard properties |
| 1 - 100 /s | Intermediate | Slight strengthening |
| 100 - 10000 /s | **Impact** | Significant strengthening |
| > 10000 /s | Shock | Adiabatic conditions |

---

## 9. Procedure 7: Thermal Analysis

### 9.1 Adiabatic Heating
At high strain rates, plastic work converts to heat faster than it can dissipate.

### 9.2 Temperature Rise Mapping

1. **Color by `temperature_rise`**
2. **Threshold for significant heating:**
   - Lower: 100 K
   - Upper: 2000 K

### 9.3 Thermal Softening Risk

| Temperature Rise | Risk |
|------------------|------|
| < 100 K | Negligible |
| 100 - 300 K | Minor softening |
| 300 - 600 K | Significant softening |
| > 600 K | Adiabatic shear risk |

---

## 10. Procedure 8: Cross-Section Through Impact

### 10.1 Slice Configuration

1. **Apply Slice:**
   ```
   Filters > Slice
   ```

2. **Position through impact center:**
   - Origin: (0, 60, 0) mm
   - Normal: (1, 0, 0) for YZ plane

### 10.2 Examine:
- Stress distribution through thickness
- Damage penetration depth
- Spall plane location

---

## 11. Quality Assurance

### 11.1 Checklist

- [ ] All 15 timesteps load correctly
- [ ] Fragments appear after expected time (~70 μs)
- [ ] Warp direction is correct (inward at impact)
- [ ] Pathlines originate from blade surface
- [ ] Yield threshold identifies correct region
- [ ] Temperature units are Kelvin

### 11.2 Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| No fragments early | Physical - ejection delayed | Advance time > 70 μs |
| Warp inverted | Wrong displacement sign | Check vector direction |
| Pathlines scattered | Wrong ID array | Use FragmentID |

---

## 12. Report Contents

1. **Executive Summary**
2. **Impact Conditions**
3. **Damage Assessment**
   - Yield exceedance timeline
   - Damage zone extent
   - Fragment count and distribution
4. **Structural Integrity Evaluation**
5. **Containment Analysis**
6. **Recommendations**

---

## 13. References

1. Johnson, G.R. & Cook, W.H. (1983). Eng. Fract. Mech., 21:31-48
2. FAR 33.94: Foreign Object Ingestion
3. SAE ARP1587: FOD Characterization

---

*© 2025 Nicholas Rodriguez. Licensed under MIT License.*
