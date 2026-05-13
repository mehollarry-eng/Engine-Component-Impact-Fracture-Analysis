"""
Impact Fracture Analysis Script
ParaView Python Automation for Engine Component FOD Investigation

Author: Nicholas Rodriguez, Forensic Mechanical Engineer
Purpose: High-velocity impact damage assessment and fragment tracking

Usage:
  pvpython impact_fracture_analysis.py
  OR in ParaView: Tools > Python Shell > Run Script
"""

try:
    from paraview.simple import *
except ImportError:
    print("ParaView not available - running standalone")

import math
import os

# ============================================================================
# MATERIAL AND IMPACT PARAMETERS
# ============================================================================

INCONEL_718 = {
    'name': 'Inconel 718',
    'yield_strength': 1100,      # MPa
    'ultimate_strength': 1375,   # MPa
    'E': 205000,                 # MPa
    'density': 8190,             # kg/m³
}

IMPACT_PARAMS = {
    'velocity': 200,             # m/s
    'impactor_mass': 0.15,       # kg
    'energy': 3000,              # J
    'duration': 500,             # μs
}


def run_impact_analysis_paraview():
    """
    Complete impact fracture analysis in ParaView.
    """
    
    print("="*65)
    print("ENGINE COMPONENT IMPACT FRACTURE ANALYSIS")
    print("Turbine Blade Foreign Object Damage (FOD) Investigation")
    print("="*65)
    
    # =========================================================================
    # LOAD TIME SERIES
    # =========================================================================
    print("\n--- Loading Impact Simulation Data ---")
    
    blade_pvd = "blade_impact_simulation.pvd"
    if not os.path.exists(blade_pvd):
        blade_pvd = "../impact-simulation/blade_impact_simulation.pvd"
    
    if not os.path.exists(blade_pvd):
        print(f"ERROR: Cannot find {blade_pvd}")
        return
    
    blade = PVDReader(FileName=blade_pvd)
    RenameSource("Blade_Structure", blade)
    
    time_steps = blade.TimestepValues
    print(f"  Loaded blade data: {len(time_steps)} timesteps")
    print(f"  Time range: {time_steps[0]:.1f} to {time_steps[-1]:.1f} μs")
    
    # Load fragments
    frag_pvd = "fragment_trajectories.pvd"
    if not os.path.exists(frag_pvd):
        frag_pvd = "../impact-simulation/fragment_trajectories.pvd"
    
    fragments = PVDReader(FileName=frag_pvd)
    RenameSource("Impact_Fragments", fragments)
    print(f"  Loaded fragment particle data")
    
    time_keeper = GetTimeKeeper()
    
    # =========================================================================
    # WORKFLOW 1: WARP BY VECTOR (Impact Deformation)
    # =========================================================================
    print("\n--- Workflow 1: Warp By Vector (Deformation Amplification) ---")
    
    # For high-speed impact, actual deformations are already significant
    # Use moderate amplification
    
    warp_50x = WarpByVector(Input=blade)
    warp_50x.Vectors = ['POINTS', 'Displacement']
    warp_50x.ScaleFactor = 50
    RenameSource("Warped_50x", warp_50x)
    UpdatePipeline(proxy=warp_50x)
    
    warp_100x = WarpByVector(Input=blade)
    warp_100x.Vectors = ['POINTS', 'Displacement']
    warp_100x.ScaleFactor = 100
    RenameSource("Warped_100x", warp_100x)
    UpdatePipeline(proxy=warp_100x)
    
    print("  Created warped views: 50x, 100x")
    print("  Use 50x for impact crater, 100x for stress wave effects")
    
    # =========================================================================
    # WORKFLOW 2: TEMPORAL PARTICLES TO PATHLINES (Fragment Tracking)
    # =========================================================================
    print("\n--- Workflow 2: Temporal Particles To Pathlines ---")
    
    pathlines = TemporalParticlesToPathlines(Input=fragments)
    pathlines.MaskPoints = 1
    pathlines.MaxTrackLength = 200
    pathlines.IdChannelArray = 'FragmentID'
    RenameSource("Fragment_Pathlines", pathlines)
    UpdatePipeline(proxy=pathlines)
    
    print("  Created fragment trajectory pathlines")
    print("  Color by 'Velocity' or 'Temperature' for energy analysis")
    
    pathline_data = servermanager.Fetch(pathlines)
    n_paths = pathline_data.GetNumberOfCells() if pathline_data else 0
    print(f"  Total trajectories: {n_paths}")
    
    # =========================================================================
    # WORKFLOW 3: YIELD EXCEEDANCE DETECTION
    # =========================================================================
    print("\n--- Workflow 3: Yield Exceedance Detection ---")
    
    yield_results = {
        'first_timestep': None,
        'first_time': None,
        'peak_stress': 0,
        'damage_progression': {}
    }
    
    for t_idx, t_val in enumerate(time_steps):
        time_keeper.Time = t_val
        UpdatePipeline(proxy=blade)
        
        # Threshold for yielded material
        yield_thresh = Threshold(Input=blade)
        yield_thresh.Scalars = ['POINTS', 'yield_exceeded']
        yield_thresh.LowerThreshold = 0.5
        yield_thresh.UpperThreshold = 1.5
        yield_thresh.ThresholdMethod = 'Between'
        
        UpdatePipeline(proxy=yield_thresh)
        
        yielded_data = servermanager.Fetch(yield_thresh)
        n_yielded = yielded_data.GetNumberOfPoints() if yielded_data else 0
        
        yield_results['damage_progression'][t_val] = n_yielded
        
        if n_yielded > 0 and yield_results['first_timestep'] is None:
            yield_results['first_timestep'] = t_idx
            yield_results['first_time'] = t_val
            
            # Get peak stress
            stress_array = yielded_data.GetPointData().GetArray('von_mises_stress')
            if stress_array:
                for i in range(stress_array.GetNumberOfTuples()):
                    s = stress_array.GetValue(i)
                    if s > yield_results['peak_stress']:
                        yield_results['peak_stress'] = s
        
        Delete(yield_thresh)
    
    print(f"\n  YIELD ANALYSIS REPORT:")
    print(f"  Material: {INCONEL_718['name']}")
    print(f"  Yield Strength: {INCONEL_718['yield_strength']} MPa")
    
    if yield_results['first_timestep'] is not None:
        print(f"\n  ⚠ FIRST YIELD:")
        print(f"     Time: {yield_results['first_time']:.1f} μs")
        print(f"     Peak Stress: {yield_results['peak_stress']:.0f} MPa")
        print(f"     Overstress: {yield_results['peak_stress']/INCONEL_718['yield_strength']:.2f}x yield")
    
    print(f"\n  Damage progression:")
    for t, n in sorted(yield_results['damage_progression'].items()):
        if n > 0:
            print(f"     t = {t:.1f} μs: {n:,} yielded points")
    
    # =========================================================================
    # DAMAGE ZONE VISUALIZATION
    # =========================================================================
    print("\n--- Damage Zone Analysis ---")
    
    # Go to final timestep
    time_keeper.Time = time_steps[-1]
    UpdatePipeline(proxy=blade)
    
    # Threshold high damage
    damage_zone = Threshold(Input=blade)
    damage_zone.Scalars = ['POINTS', 'damage_parameter']
    damage_zone.LowerThreshold = 0.3
    damage_zone.UpperThreshold = 1.0
    damage_zone.ThresholdMethod = 'Between'
    
    RenameSource("Damage_Zone", damage_zone)
    UpdatePipeline(proxy=damage_zone)
    
    damage_data = servermanager.Fetch(damage_zone)
    n_damaged = damage_data.GetNumberOfPoints() if damage_data else 0
    print(f"  Severely damaged points: {n_damaged:,}")
    
    # =========================================================================
    # STRAIN RATE ANALYSIS (Impact-specific)
    # =========================================================================
    print("\n--- Strain Rate Analysis ---")
    
    # High strain rate regions indicate dynamic loading
    high_rate = Threshold(Input=blade)
    high_rate.Scalars = ['POINTS', 'strain_rate']
    high_rate.LowerThreshold = 1000  # 1000 /s
    high_rate.UpperThreshold = 1e8
    high_rate.ThresholdMethod = 'Between'
    
    RenameSource("High_Strain_Rate", high_rate)
    UpdatePipeline(proxy=high_rate)
    
    rate_data = servermanager.Fetch(high_rate)
    n_high_rate = rate_data.GetNumberOfPoints() if rate_data else 0
    print(f"  High strain rate points (>1000/s): {n_high_rate:,}")
    
    # =========================================================================
    # THERMAL EFFECTS
    # =========================================================================
    print("\n--- Adiabatic Heating Analysis ---")
    
    temp_thresh = Threshold(Input=blade)
    temp_thresh.Scalars = ['POINTS', 'temperature_rise']
    temp_thresh.LowerThreshold = 100  # 100 K rise
    temp_thresh.UpperThreshold = 2000
    temp_thresh.ThresholdMethod = 'Between'
    
    RenameSource("Thermal_Zone", temp_thresh)
    UpdatePipeline(proxy=temp_thresh)
    
    temp_data = servermanager.Fetch(temp_thresh)
    n_heated = temp_data.GetNumberOfPoints() if temp_data else 0
    print(f"  Significantly heated points (ΔT>100K): {n_heated:,}")
    
    # =========================================================================
    # FRAGMENT TRAJECTORY ANALYSIS
    # =========================================================================
    print("\n--- Fragment Ejection Analysis ---")
    
    # Go through timesteps to count fragments
    frag_counts = []
    for t_idx, t_val in enumerate(time_steps):
        time_keeper.Time = t_val
        UpdatePipeline(proxy=fragments)
        
        frag_data = servermanager.Fetch(fragments)
        n_frags = frag_data.GetNumberOfPoints() if frag_data else 0
        frag_counts.append((t_val, n_frags))
    
    print("  Fragment count vs time:")
    for t, n in frag_counts:
        if n > 0:
            print(f"     t = {t:.1f} μs: {n} fragments")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "="*65)
    print("IMPACT ANALYSIS SUMMARY")
    print("="*65)
    
    print(f"\nIMPACT CONDITIONS:")
    print(f"  Velocity: {IMPACT_PARAMS['velocity']} m/s")
    print(f"  Energy: {IMPACT_PARAMS['energy']} J")
    print(f"  Duration: {IMPACT_PARAMS['duration']} μs")
    
    print(f"\nDAMAGE ASSESSMENT:")
    print(f"  First yield: {yield_results['first_time']:.1f} μs" if yield_results['first_time'] else "  No yield detected")
    print(f"  Peak stress: {yield_results['peak_stress']:.0f} MPa")
    print(f"  Damage zone: {n_damaged:,} points")
    print(f"  Fragments ejected: {frag_counts[-1][1] if frag_counts else 0}")
    
    print("\nFORENSIC FINDINGS:")
    print("  1. Impact crater formation visible in warped view")
    print("  2. Fragment trajectories indicate ejection energy")
    print("  3. Yield exceedance timeline established")
    print("  4. High strain rate zone identifies impact center")


def standalone_analysis():
    """Standalone analysis without ParaView."""
    print("="*65)
    print("STANDALONE IMPACT ANALYSIS")
    print("="*65)
    
    vtk_dir = "."
    if not os.path.exists("blade_impact_0000.vtk"):
        vtk_dir = "../impact-simulation"
    
    if not os.path.exists(os.path.join(vtk_dir, "blade_impact_0000.vtk")):
        print("VTK files not found.")
        return
    
    print(f"\nAnalyzing files in: {vtk_dir}")
    print(f"Material: {INCONEL_718['name']}")
    print(f"Yield Strength: {INCONEL_718['yield_strength']} MPa\n")
    
    for t_idx in range(15):
        filename = os.path.join(vtk_dir, f"blade_impact_{t_idx:04d}.vtk")
        if not os.path.exists(filename):
            continue
        
        # Quick parse for yield count
        yield_count = 0
        reading_yield = False
        
        with open(filename, 'r') as f:
            for line in f:
                if "SCALARS yield_exceeded" in line:
                    reading_yield = True
                    continue
                elif line.startswith("SCALARS"):
                    reading_yield = False
                    continue
                elif line.startswith("LOOKUP_TABLE"):
                    continue
                
                if reading_yield:
                    try:
                        if float(line.strip()) > 0.5:
                            yield_count += 1
                    except:
                        pass
        
        if yield_count > 0:
            print(f"  Timestep {t_idx}: {yield_count:,} yielded points")


if __name__ == "__main__":
    try:
        from paraview.simple import GetActiveSource
        run_impact_analysis_paraview()
    except ImportError:
        standalone_analysis()
