import pandas as pd
import numpy as np
import os
from itertools import combinations # Import combinations

def calculate_min_distance(df, actor1_name, actor2_name):
    # Get data for both actors
    actor1 = df[df['ActorName'] == actor1_name].iloc[0]
    actor2 = df[df['ActorName'] == actor2_name].iloc[0]
    
    # Calculate bounding box corners for actor1
    actor1_x_min = actor1['WorldX'] - actor1['WorldSizeX']/2
    actor1_x_max = actor1['WorldX'] + actor1['WorldSizeX']/2
    actor1_y_min = actor1['WorldY'] - actor1['WorldSizeY']/2
    actor1_y_max = actor1['WorldY'] + actor1['WorldSizeY']/2
    actor1_z_min = actor1['WorldZ'] - actor1['WorldSizeZ']/2
    actor1_z_max = actor1['WorldZ'] + actor1['WorldSizeZ']/2
    
    # Calculate bounding box corners for actor2
    actor2_x_min = actor2['WorldX'] - actor2['WorldSizeX']/2
    actor2_x_max = actor2['WorldX'] + actor2['WorldSizeX']/2
    actor2_y_min = actor2['WorldY'] - actor2['WorldSizeY']/2
    actor2_y_max = actor2['WorldY'] + actor2['WorldSizeY']/2
    actor2_z_min = actor2['WorldZ'] - actor2['WorldSizeZ']/2
    actor2_z_max = actor2['WorldZ'] + actor2['WorldSizeZ']/2
    
    # Calculate the x, y, and z overlap/distance
    # Check for overlap in each dimension
    overlap_x = (actor1_x_min <= actor2_x_max and actor1_x_max >= actor2_x_min)
    overlap_y = (actor1_y_min <= actor2_y_max and actor1_y_max >= actor2_y_min)
    overlap_z = (actor1_z_min <= actor2_z_max and actor1_z_max >= actor2_z_min)
    
    # If overlapping in all dimensions, distance is 0
    if overlap_x and overlap_y and overlap_z:
        return 0.0
    
    # Calculate signed distances
    dx = (actor1_x_min - actor2_x_max) if actor1_x_min > actor2_x_max else (actor2_x_min - actor1_x_max if actor1_x_max < actor2_x_min else 0)
    dy = (actor1_y_min - actor2_y_max) if actor1_y_min > actor2_y_max else (actor2_y_min - actor1_y_max if actor1_y_max < actor2_y_min else 0)
    dz = (actor1_z_min - actor2_z_max) if actor1_z_min > actor2_z_max else (actor2_z_min - actor1_z_max if actor1_z_max < actor2_z_min else 0)
    
    # If any dimension overlaps, set its distance to 0
    dx = 0 if overlap_x else dx
    dy = 0 if overlap_y else dy
    dz = 0 if overlap_z else dz
    
    # Calculate minimum distance
    min_distance = np.sqrt(dx**2 + dy**2 + dz**2)
    return min_distance

def ensure_output_directory():
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

def main():
    # Read the CSV file    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) # Assumes this script is one level down from project root
    input_csv_path = os.path.join(project_root, '0_data_cleanup_tool', 'output', 'ranked_unique_actor_anno.csv')
    df = pd.read_csv(input_csv_path)

    actor_names = df['ActorName'].unique()
    output_dir = ensure_output_directory()
    
    # Process all valid combinations of two different actors
    all_results = []
    possibility_counter = 1
    
    # Use combinations to ensure order-independent pairs
    for actor1, actor2 in combinations(actor_names, 2):
        try:
            # Calculate minimum distance
            distance = calculate_min_distance(df, actor1, actor2)
            
            # Round the distance first
            rounded_distance = round(distance, 2)
            
            # Skip if rounded distance is 0.0 (overlapping items)
            if rounded_distance == 0.0:
                continue
            
            # Get display names from the DataFrame
            actor1_row = df[df['ActorName'] == actor1].iloc[0]
            actor2_row = df[df['ActorName'] == actor2].iloc[0]

            actor1_desc = actor1_row.get('ActorDescription')
            display_actor1 = actor1_desc if pd.notna(actor1_desc) and str(actor1_desc).strip() else actor1_row['ShortActorName']

            actor2_desc = actor2_row.get('ActorDescription')
            display_actor2 = actor2_desc if pd.notna(actor2_desc) and str(actor2_desc).strip() else actor2_row['ShortActorName']
            
            question = f"Measuring from the closest point of each object, what is the distance between the {display_actor1} and the {display_actor2} (in meters)?"
            
            # Record results with the pre-rounded distance
            all_results.append({
                'Possibility': possibility_counter,
                'Actor1': actor1,
                'Actor2': actor2,
                'Question': question,
                'Answer': rounded_distance
            })
            
            possibility_counter += 1
            
        except Exception as e:
            print(f"Error processing combination {possibility_counter}: {actor1}, {actor2}")
            print(f"Error message: {str(e)}")
            continue
    
    # Save all results to CSV
    if all_results:
        output_df = pd.DataFrame(all_results)
        output_df.to_csv(os.path.join(output_dir, 'absolute_distances_all.csv'), index=False)
        print(f"Successfully processed {len(all_results)} possibility")

if __name__ == "__main__":
    main()