import numpy as np
import pandas as pd
import json
import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as patches

# Use a default font that supports Japanese if possible, or fallback
plt.rcParams['font.family'] = 'Meiryo'



def generate_exact_static_image(df, x, y, star_colors, scores, names, output_path='static_network_glow.png', show_lines=True):
    print("Generating Exact Static Image (Glow)...")
    limit_min, limit_max = -500, 500
    fig, ax = plt.subplots(figsize=(10, 10), facecolor='#020617')
    ax.set_facecolor('#020617')
    ax.set_xlim(limit_min, limit_max)
    ax.set_ylim(limit_min, limit_max)
    ax.set_aspect('equal')
    ax.axis('off')

    # Background
    if os.path.exists("universe_bg.png"):
        img = mpimg.imread("universe_bg.png")
        ax.imshow(img, extent=[limit_min, limit_max, limit_min, limit_max], zorder=0)

    num_stars = len(df)
    
    # Lines (Canvas: alpha=0.4, linewidth=1.0)
    if show_lines:
        for i in range(num_stars):
            for j in range(i + 1, num_stars):
                dist = np.sqrt((x[i]-x[j])**2 + (y[i]-y[j])**2)
                if dist < 160:
                    ax.plot([x[i], x[j]], [y[i], y[j]], color="#fff7d6", alpha=0.4, linewidth=1.0, zorder=1)

    # Ripples & Nodes (Canvas Style)
    bg_circle_size_outer = (80/1000 * 10 * 72)**2 / 4 # Approximate sizing logic
    # Simplified visual sizing:
    # Outer Glow Radius 40px @ 1000px width.
    # Figure 10 inch. 1000px width -> 100 dpi.
    # 40px = 0.4 inch = 28.8 points. s = area? s in scatter is approx diameter^2 in points approx?
    # Actually s is area in points^2. Radius r points -> Area pi * r^2.
    # Marker size s is defined as the area of the marker in points**2.
    # r = 28.8 points. Area = 2600.
    s_outer = 2500
    s_inner = 1200 # 0.7 radius -> 0.49 area
    s_core = 30
    
    for i in range(num_stars):
        # Ripple: Solid ring, Canvas col, alpha 0.5, linewidth 2.5
        # Radius ratio 1/2 of previous (4.5 -> 2.25)
        r_size = scores[i] * 2.25
        circle = patches.Circle((x[i], y[i]), r_size, edgecolor=star_colors[i], facecolor='none', alpha=0.5, linewidth=2.5, zorder=2)
        ax.add_patch(circle)
    
    # Batch scatter for glow (efficiency and blending)
    # Canvas: Outer Alpha 0.075
    ax.scatter(x, y, s=s_outer, c="#fff7d6", alpha=0.075, edgecolors='none', zorder=3)
    # Canvas: Inner Alpha 0.2
    ax.scatter(x, y, s=s_inner, c="#fff7d6", alpha=0.2, edgecolors='none', zorder=4)
    # Canvas: Core Alpha 0.9
    ax.scatter(x, y, s=s_core, c="#ffffff", alpha=0.9, edgecolors='none', zorder=5)
    
    # Names
    for i in range(num_stars):
         ax.text(x[i]+5, y[i]-5, names[i], color="#fff7d6", fontsize=7, fontweight='bold', alpha=0.9, zorder=6)

    plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    print(f"Exact static image exported to {output_path}")

def generate_animation_from_df(df, output_path='animation_data.json', show_lines=True):
    # 設定
    num_stars = len(df)
    names = df['Name'].tolist()

    # 色設定
    color_map = {
        "安心": "#0ea5e9", "挑戦": "#f97316", "確信": "#eab308", 
        "充足": "#4ade80", "静観": "#ffffff"
    }
    
    star_colors = [color_map.get(s, "#ffffff") for s in df['Q4_Switch']]
    scores = df['Q2'].values

    np.random.seed(42)
    # Background -500 to 500. Content -400 to 400.
    content_min, content_max = -400, 400
    x = np.random.uniform(content_min, content_max, num_stars)
    y = np.random.uniform(content_min, content_max, num_stars)
    
    # スピード設定
    # Order: ["安心", "挑戦", "確信", "充足", "静観"]
    # Secondary: Q2 (Ascending)
    order_map = {"安心": 0, "挑戦": 1, "確信": 2, "充足": 3, "静観": 4}
    
    # Create temporary sort columns
    df['sort_primary'] = df['Q4_Switch'].map(lambda x: order_map.get(x, 5))
    df['sort_secondary'] = df['Q2']
    
    # Sort
    df_sorted = df.sort_values(by=['sort_primary', 'sort_secondary'], ascending=[True, True])
    
    # Assign delays based on rank
    # Spread over 0 to ~2800 frames (leaving 1200 frames for tail in 4000 frame duration)
    # len(df) is roughly 100. Step ~28.
    df_sorted['delay_val'] = np.arange(len(df)) * 28
    
    appearance_delay = np.zeros(num_stars)
    for idx, row in df_sorted.iterrows():
        appearance_delay[idx] = int(row['delay_val'])
    
    appearance_delay = appearance_delay.astype(int).tolist()
    
    # Network Lines
    lines_data = []
    if show_lines:
        for i in range(num_stars):
            for j in range(i + 1, num_stars):
                dist = np.sqrt((x[i]-x[j])**2 + (y[i]-y[j])**2)
                # Threshold 160
                if dist < 160:
                    lines_data.append({
                        "source": i,
                        "target": j,
                        "delay": max(appearance_delay[i], appearance_delay[j])
                    })

    # Prepare Data
    nodes_data = []
    for i in range(num_stars):
        nodes_data.append({
            "id": i,
            "x": float(x[i]),
            "y": float(y[i]),
            "name": names[i],
            "color": star_colors[i],
            "score": float(scores[i]),
            "delay": appearance_delay[i]
        })

    data = {
        "nodes": nodes_data,
        "lines": lines_data,
        "config": {
            "limit_min": -500,
            "limit_max": 500,
            "duration_frames": 4000,
            "fps": 20
        }
    }
    
    with open(output_path, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Data exported to {output_path}")

    # Generate Exact Static Image (Glow)
    generate_exact_static_image(df, x, y, star_colors, scores, names, output_path='static_network_glow.png', show_lines=show_lines)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-lines', action='store_true', help='Disable network lines')
    args = parser.parse_args()
    
    try:
        df = pd.read_csv("survey_data.csv")
        generate_animation_from_df(df, show_lines=not args.no_lines)
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
