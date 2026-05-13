"""
Engine Component Impact Fracture Analysis Generator
Time-Series Simulation of Turbine Blade Foreign Object Damage (FOD)

Author: Nicholas Rodriguez, Forensic Mechanical Engineer
Application: ParaView Impact Dynamics & Fracture Mechanics
"""
import math
import os
import random

# ============================================================================
# SIMULATION PARAMETERS
# ============================================================================

# Time stepping (microsecond scale for impact)
NUM_TIMESTEPS = 15
TIME_START = 0.0
TIME_END = 500.0  # microseconds
DT = (TIME_END - TIME_START) / (NUM_TIMESTEPS - 1)

# Turbine blade geometry (simplified airfoil)
BLADE_LENGTH = 80      # mm (chord)
BLADE_HEIGHT = 120     # mm (span)
BLADE_THICKNESS = 8    # mm (max thickness)
LEADING_EDGE_RADIUS = 1.5  # mm

# Grid resolution
nx, ny, nz = 40, 60, 35
spacing = 1.0  # mm
origin = (-20, -30, -17)

# Material: Inconel 718 (Nickel superalloy)
MATERIAL = {
    'name': 'Inconel 718',
    'E': 205000,           # Young's modulus (MPa)
    'nu': 0.30,            # Poisson's ratio
    'density': 8190,       # kg/m³
    'yield_strength': 1100,# MPa (at RT)
    'ultimate_strength': 1375,  # MPa
    'elongation': 0.21,    # 21% at break
    'fracture_toughness': 100,  # MPa√m (high toughness)
    'johnson_cook': {      # JC plasticity parameters
        'A': 1241,         # MPa
        'B': 622,          # MPa
        'n': 0.6522,
        'C': 0.0134,
        'm': 1.00
    }
}

# Impact parameters (bird strike simulation)
IMPACT_VELOCITY = 200    # m/s (720 km/h - approach speed)
IMPACTOR_MASS = 0.15     # kg (small bird)
IMPACT_ANGLE = 15        # degrees from blade surface
IMPACT_LOCATION = (0, 60, 0)  # Near leading edge, mid-span

# Impact energy
IMPACT_ENERGY = 0.5 * IMPACTOR_MASS * IMPACT_VELOCITY**2  # 3000 J

def airfoil_profile(x, z, chord=BLADE_LENGTH):
    """
    NACA 0012 airfoil approximation.
    Returns half-thickness at given x position.
    """
    # Normalized position
    xc = (x + chord/2) / chord  # 0 to 1
    if xc < 0 or xc > 1:
        return 0
    
    # NACA 0012 thickness distribution
    t = 0.12  # 12% thickness
    yt = 5 * t * (0.2969 * math.sqrt(xc) 
                  - 0.1260 * xc 
                  - 0.3516 * xc**2 
                  + 0.2843 * xc**3 
                  - 0.1015 * xc**4)
    
    return yt * chord / 2  # Half-thickness in mm

def blade_geometry(x, y, z):
    """
    Define turbine blade geometry.
    Returns: (region_type, in_blade)
    0=outside, 1=core, 2=leading_edge, 3=trailing_edge, 4=tip
    """
    # Check span (y-direction)
    if y < 0 or y > BLADE_HEIGHT:
        return 0, False
    
    # Get airfoil thickness at this x position
    half_thick = airfoil_profile(x, z)
    
    if half_thick == 0:
        return 0, False
    
    # Check if inside airfoil
    if abs(z) < half_thick:
        # Determine region
        if x < -BLADE_LENGTH/2 + 5:  # Leading edge (first 5mm)
            region = 2
        elif x > BLADE_LENGTH/2 - 10:  # Trailing edge (last 10mm)
            region = 3
        elif y > BLADE_HEIGHT - 10:  # Tip region
            region = 4
        else:
            region = 1  # Core
        
        return region, True
    
    return 0, False

def distance_3d(x, y, z, cx, cy, cz):
    return math.sqrt((x-cx)**2 + (y-cy)**2 + (z-cz)**2)

def impact_wave_propagation(x, y, z, time_us):
    """
    Model stress wave propagation from impact site.
    Based on elastic wave speed in Inconel 718.
    """
    # Wave speeds
    c_longitudinal = math.sqrt(MATERIAL['E'] * 1e6 / MATERIAL['density'])  # ~5000 m/s
    c_shear = c_longitudinal / math.sqrt(3)  # ~2900 m/s
    
    # Distance from impact
    dist = distance_3d(x, y, z, *IMPACT_LOCATION)
    
    # Time for wave to reach this point (convert m/s to mm/μs)
    wave_speed_mm_us = c_longitudinal / 1000  # mm/μs
    arrival_time = dist / wave_speed_mm_us
    
    if time_us < arrival_time:
        return 0, 0, False  # Wave hasn't arrived
    
    # Time since wave arrival
    dt = time_us - arrival_time
    
    # Wave amplitude decay (geometric spreading + damping)
    amplitude = 1.0 / (1 + dist/10) * math.exp(-dt/200)
    
    # Peak stress from impact (simplified Hertzian contact)
    # P_max ≈ (3F/2πa²) where F is impact force
    contact_duration = 50  # μs
    peak_force = IMPACTOR_MASS * IMPACT_VELOCITY * 1000 / contact_duration  # N
    contact_radius = 5  # mm (estimated)
    
    peak_stress = 1.5 * peak_force / (math.pi * contact_radius**2)  # MPa
    
    # Stress at this point
    stress = peak_stress * amplitude
    
    # Plastic strain development
    if stress > MATERIAL['yield_strength']:
        plastic = (stress - MATERIAL['yield_strength']) / MATERIAL['E'] * 100
    else:
        plastic = 0
    
    return stress, plastic, True

def calculate_damage(x, y, z, time_fraction, stress, in_blade):
    """
    Calculate damage accumulation using Johnson-Cook failure model.
    """
    if not in_blade:
        return 0, 0, (0, 0, 0)
    
    # Distance from impact center
    dist = distance_3d(x, y, z, *IMPACT_LOCATION)
    
    # Impact zone damage (within 20mm of impact)
    if dist < 20:
        # Time-dependent crater formation
        crater_progress = min(1.0, time_fraction * 2)
        crater_radius = 15 * crater_progress
        
        if dist < crater_radius:
            damage = 1.0 - dist / crater_radius
            damage *= crater_progress
        else:
            damage = 0.1 * (1 - (dist - crater_radius) / 10)
            damage = max(0, damage)
    else:
        # Spallation damage on back surface
        if z < -BLADE_THICKNESS/2 + 2 and dist < 40:
            damage = 0.3 * (1 - dist/40) * time_fraction
        else:
            damage = 0
    
    # Strain rate effect on damage
    strain_rate = stress / MATERIAL['E'] / (DT / 1e6)  # 1/s
    
    # Displacement (from impact)
    if dist < 30:
        impact_disp = 2.0 * (1 - dist/30) * time_fraction
        angle = math.atan2(z - IMPACT_LOCATION[2], x - IMPACT_LOCATION[0])
        ux = -impact_disp * math.cos(angle) * 0.3
        uy = -impact_disp * 0.8  # Primarily downward (blade bending)
        uz = impact_disp * math.sin(angle)
    else:
        ux, uy, uz = 0, 0, 0
    
    return damage, strain_rate, (ux, uy, uz)

def generate_fragment_particles(time_us, time_fraction):
    """
    Generate debris particles from impact crater and spallation.
    """
    particles = []
    
    if time_fraction < 0.1:
        return particles
    
    # Number of fragments increases with time
    n_particles = int(time_fraction * 150)
    
    random.seed(42 + int(time_us))  # Reproducible randomness
    
    for i in range(n_particles):
        # Origin: impact crater or spall zone
        if random.random() < 0.7:
            # Crater debris (front surface)
            px = IMPACT_LOCATION[0] + random.gauss(0, 8)
            py = IMPACT_LOCATION[1] + random.gauss(0, 5)
            pz = IMPACT_LOCATION[2] + random.uniform(-2, 2)
            
            # Velocity (ejected forward and up)
            speed = random.uniform(50, 150)  # m/s
            vx = speed * random.uniform(-0.5, 0.5)
            vy = speed * random.uniform(0.3, 1.0)  # Mostly upward
            vz = speed * random.uniform(0.5, 1.0)   # Forward
        else:
            # Spall debris (back surface)
            px = IMPACT_LOCATION[0] + random.gauss(0, 10)
            py = IMPACT_LOCATION[1] + random.gauss(0, 8)
            pz = -BLADE_THICKNESS/2 - 2  # Back surface
            
            speed = random.uniform(30, 80)
            vx = speed * random.uniform(-0.3, 0.3)
            vy = speed * random.uniform(-0.2, 0.5)
            vz = -speed * random.uniform(0.5, 1.0)  # Backward
        
        # Fragment mass (small particles)
        mass = random.uniform(0.0001, 0.002)  # 0.1 to 2 grams
        
        # Fragment temperature (from adiabatic heating)
        temp = 300 + random.uniform(0, 500)  # K
        
        particles.append({
            'pos': (px, py, pz),
            'vel': (vx, vy, vz),
            'mass': mass,
            'temp': temp,
            'id': i
        })
    
    return particles

def write_vtk_timestep(filename, data, time_value, title):
    """Write VTK structured grid file."""
    with open(filename, 'w') as f:
        f.write("# vtk DataFile Version 3.0\n")
        f.write(f"{title} | Time = {time_value:.1f} μs\n")
        f.write("ASCII\nDATASET STRUCTURED_POINTS\n")
        f.write(f"DIMENSIONS {nx} {ny} {nz}\n")
        f.write(f"ORIGIN {origin[0]} {origin[1]} {origin[2]}\n")
        f.write(f"SPACING {spacing} {spacing} {spacing}\n")
        f.write(f"POINT_DATA {nx*ny*nz}\n")
        
        for name, values in data.items():
            if name == "Displacement":
                f.write(f"VECTORS {name} float\n")
                for v in values:
                    f.write(f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            else:
                f.write(f"SCALARS {name} float\nLOOKUP_TABLE default\n")
                for v in values:
                    f.write(f"{v:.6f}\n")

def write_particles_vtk(filename, particles, time_value):
    """Write fragment particles as VTK polydata."""
    if not particles:
        with open(filename, 'w') as f:
            f.write("# vtk DataFile Version 3.0\n")
            f.write(f"Impact Fragments | Time = {time_value:.1f} μs\n")
            f.write("ASCII\nDATASET POLYDATA\n")
            f.write("POINTS 0 float\n")
        return
    
    with open(filename, 'w') as f:
        f.write("# vtk DataFile Version 3.0\n")
        f.write(f"Impact Fragments | Time = {time_value:.1f} μs\n")
        f.write("ASCII\nDATASET POLYDATA\n")
        f.write(f"POINTS {len(particles)} float\n")
        
        for p in particles:
            f.write(f"{p['pos'][0]:.4f} {p['pos'][1]:.4f} {p['pos'][2]:.4f}\n")
        
        f.write(f"\nVERTICES {len(particles)} {len(particles)*2}\n")
        for i in range(len(particles)):
            f.write(f"1 {i}\n")
        
        f.write(f"\nPOINT_DATA {len(particles)}\n")
        
        f.write("VECTORS Velocity float\n")
        for p in particles:
            f.write(f"{p['vel'][0]:.4f} {p['vel'][1]:.4f} {p['vel'][2]:.4f}\n")
        
        f.write("SCALARS Mass float\nLOOKUP_TABLE default\n")
        for p in particles:
            f.write(f"{p['mass']:.6f}\n")
        
        f.write("SCALARS Temperature float\nLOOKUP_TABLE default\n")
        for p in particles:
            f.write(f"{p['temp']:.1f}\n")
        
        f.write("SCALARS FragmentID int\nLOOKUP_TABLE default\n")
        for p in particles:
            f.write(f"{p['id']}\n")

# ============================================================================
# MAIN GENERATION
# ============================================================================

print("="*65)
print("ENGINE COMPONENT IMPACT FRACTURE ANALYSIS")
print("Turbine Blade Foreign Object Damage (FOD) Simulation")
print("="*65)
print(f"\nMaterial: {MATERIAL['name']}")
print(f"Yield Strength: {MATERIAL['yield_strength']} MPa")
print(f"Impact Velocity: {IMPACT_VELOCITY} m/s ({IMPACT_VELOCITY*3.6:.0f} km/h)")
print(f"Impact Energy: {IMPACT_ENERGY:.0f} J")
print(f"\nGenerating {NUM_TIMESTEPS} timesteps ({TIME_END:.0f} μs duration)...")

first_yield_timestep = None
first_yield_location = None
first_yield_stress = None

for t_idx in range(NUM_TIMESTEPS):
    time_us = TIME_START + t_idx * DT
    time_fraction = t_idx / (NUM_TIMESTEPS - 1)
    
    print(f"\n  Timestep {t_idx}: t = {time_us:.1f} μs ({time_fraction*100:.0f}%)")
    
    data = {
        "blade_region": [], "von_mises_stress": [], "yield_exceeded": [],
        "plastic_strain": [], "damage_parameter": [], "strain_rate": [],
        "temperature_rise": [], "Displacement": []
    }
    
    for k in range(nz):
        z = origin[2] + k * spacing
        for j in range(ny):
            y = origin[1] + j * spacing
            for i in range(nx):
                x = origin[0] + i * spacing
                
                region, in_blade = blade_geometry(x, y, z)
                
                if in_blade:
                    stress, plastic, wave_arrived = impact_wave_propagation(x, y, z, time_us)
                    damage, strain_rate, disp = calculate_damage(x, y, z, time_fraction, stress, in_blade)
                    
                    yield_exceeded = 1.0 if stress > MATERIAL['yield_strength'] else 0.0
                    
                    # Temperature rise from plastic work
                    temp_rise = plastic * 10  # Simplified
                    
                    # Track first yield
                    if yield_exceeded > 0 and first_yield_timestep is None:
                        first_yield_timestep = t_idx
                        first_yield_location = (x, y, z)
                        first_yield_stress = stress
                else:
                    stress, plastic, damage = 0, 0, 0
                    yield_exceeded, strain_rate, temp_rise = 0, 0, 0
                    disp = (0, 0, 0)
                
                data["blade_region"].append(region)
                data["von_mises_stress"].append(stress)
                data["yield_exceeded"].append(yield_exceeded)
                data["plastic_strain"].append(plastic)
                data["damage_parameter"].append(damage)
                data["strain_rate"].append(strain_rate)
                data["temperature_rise"].append(temp_rise)
                data["Displacement"].append(disp)
    
    # Write structure
    filename = f"blade_impact_{t_idx:04d}.vtk"
    write_vtk_timestep(filename, data, time_us, "Turbine Blade Impact Analysis")
    print(f"    Created: {filename}")
    
    # Generate fragments
    particles = generate_fragment_particles(time_us, time_fraction)
    particle_file = f"fragments_{t_idx:04d}.vtk"
    write_particles_vtk(particle_file, particles, time_us)
    if particles:
        print(f"    Created: {particle_file} ({len(particles)} fragments)")

# ============================================================================
# GENERATE PVD FILES
# ============================================================================

print("\nGenerating PVD time series files...")

# Structure PVD
pvd_content = '<?xml version="1.0"?>\n'
pvd_content += '<VTKFile type="Collection" version="0.1">\n'
pvd_content += '  <Collection>\n'
for t_idx in range(NUM_TIMESTEPS):
    time_us = TIME_START + t_idx * DT
    pvd_content += f'    <DataSet timestep="{time_us:.2f}" file="blade_impact_{t_idx:04d}.vtk"/>\n'
pvd_content += '  </Collection>\n'
pvd_content += '</VTKFile>\n'

with open("blade_impact_simulation.pvd", "w") as f:
    f.write(pvd_content)
print("  Created: blade_impact_simulation.pvd")

# Fragments PVD
pvd_frag = '<?xml version="1.0"?>\n'
pvd_frag += '<VTKFile type="Collection" version="0.1">\n'
pvd_frag += '  <Collection>\n'
for t_idx in range(NUM_TIMESTEPS):
    time_us = TIME_START + t_idx * DT
    pvd_frag += f'    <DataSet timestep="{time_us:.2f}" file="fragments_{t_idx:04d}.vtk"/>\n'
pvd_frag += '  </Collection>\n'
pvd_frag += '</VTKFile>\n'

with open("fragment_trajectories.pvd", "w") as f:
    f.write(pvd_frag)
print("  Created: fragment_trajectories.pvd")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*65)
print("GENERATION COMPLETE")
print("="*65)
print(f"Grid: {nx} x {ny} x {nz} = {nx*ny*nz:,} points")
print(f"Timesteps: {NUM_TIMESTEPS} (t = 0 to {TIME_END:.0f} μs)")
print(f"\nYield Strength First Exceeded:")
if first_yield_timestep is not None:
    t_yield = TIME_START + first_yield_timestep * DT
    print(f"  Timestep: {first_yield_timestep} (t = {t_yield:.1f} μs)")
    print(f"  Location: ({first_yield_location[0]:.1f}, {first_yield_location[1]:.1f}, {first_yield_location[2]:.1f}) mm")
    print(f"  Stress: {first_yield_stress:.0f} MPa")
print(f"\nFiles Generated:")
print(f"  - blade_impact_simulation.pvd")
print(f"  - fragment_trajectories.pvd")
print(f"  - {NUM_TIMESTEPS} structure VTK files")
print(f"  - {NUM_TIMESTEPS} fragment VTK files")
