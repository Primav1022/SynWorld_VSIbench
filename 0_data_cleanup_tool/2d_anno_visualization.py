import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import os # Add os import

# Determine the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct relative paths
input_csv_path = os.path.join(script_dir, 'output', 'ranked_unique_actor_anno.csv')
output_visualization_path = os.path.join(script_dir, 'output', '2d_anno_visualization.png')

# Read the CSV file
df = pd.read_csv(input_csv_path)


# Create the figure and axis
plt.figure(figsize=(12, 8))

# Plot points and boxes
for idx, row in df.iterrows():
    # Plot center point
    plt.scatter(row['WorldX'], row['WorldY'], color='blue', zorder=2)
    
    # Calculate box coordinates (center to corner)
    half_width = row['WorldSizeX'] / 2
    half_height = row['WorldSizeY'] / 2
    box_x = row['WorldX'] - half_width
    box_y = row['WorldY'] - half_height
    
    # Draw box
    box = Rectangle((box_x, box_y), 
                   row['WorldSizeX'], row['WorldSizeY'],
                   fill=False, color='red', linestyle='--', alpha=0.5,
                   zorder=1)
    plt.gca().add_patch(box)
    
    # Add labels (ActorName and FirstFrame)
    label = f"{row['ActorName']}\n(Frame: {int(row['FirstFrame'])})"
    plt.annotate(label, 
                (row['WorldX'], row['WorldY']),
                xytext=(0, 10),  # 0 horizontal offset, 10 points vertical offset
                textcoords='offset points',
                fontsize=7,
                ha='center',  # Horizontal alignment center
                va='bottom',  # Vertical alignment bottom
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.7))

# Customize the plot
plt.title('Actor Positions with Bounding Boxes (Top View)')
plt.xlabel('World X (cm)')
plt.ylabel('World Y (cm)')
plt.grid(True, linestyle='--', alpha=0.7)
plt.axis('equal')  # Set equal aspect ratio

# Add a tight layout to prevent label clipping
plt.tight_layout()

# Save the plot
plt.savefig(output_visualization_path, dpi=300, bbox_inches='tight')
plt.show()