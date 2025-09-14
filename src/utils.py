import pandas as pd
import numpy as np
from typing import Generator, Dict, List


def load_data_in_chunks(file_path: str, chunk_size: int = 10000) -> Generator[pd.DataFrame, None, None]:
    """
    Load CSV data in chunks to prevent memory overload
    """
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        # Convert speed from m/s to km/h for better readability
        chunk['spd'] = chunk['spd'] * 3.6
        # Calculate azimuth changes for each chunk
        chunk['azm_change'] = calculate_azimuth_changes(chunk)
        yield chunk


def calculate_azimuth_changes(df: pd.DataFrame) -> pd.Series:
    """
    Calculate azimuth changes for a DataFrame, handling 360-degree wrapping
    """
    # Calculate azimuth changes within each trip
    azm_change = abs(df.groupby('randomized_id')['azm'].diff())
    # Handle 360-degree wrap-around
    azm_change = azm_change.apply(lambda x: min(x, 360-x) if pd.notnull(x) else 0)
    return azm_change


def calculate_trip_metrics(df: pd.DataFrame) -> Dict:
    """
    Calculate safety metrics for a chunk of data
    """
    metrics = {
        'avg_speed': df['spd'].mean(),
        'max_speed': df['spd'].max(),
        'high_speed_points': (df['spd'] > 80).mean() * 100,  # % of points above 80 km/h
        'sharp_turns': len(df[df['azm_change'] > 45]),
        'total_trips': len(df['randomized_id'].unique())
    }
    return metrics


def calculate_distance(lat_lng_array: np.ndarray) -> float:
    """
    Calculate approximate distance in kilometers using Euclidean distance
    Note: This is a simplified calculation, not accounting for Earth's curvature
    """
    if len(lat_lng_array) <= 1:
        return 0
    
    # Convert latitude/longitude differences to approximate kilometers
    # 1 degree of latitude = ~111 km
    # 1 degree of longitude = ~111 km * cos(latitude)
    lat_avg = np.mean(lat_lng_array[:, 0])
    km_per_deg_lon = 111 * np.cos(np.radians(lat_avg))
    
    distances = np.diff(lat_lng_array, axis=0)
    distances[:, 0] *= 111  # latitude to km
    distances[:, 1] *= km_per_deg_lon  # longitude to km
    
    return np.sum(np.sqrt(np.sum(distances**2, axis=1)))


def process_trip_details(df: pd.DataFrame) -> List[Dict]:
    """
    Process detailed metrics for each unique trip
    """
    trip_details = []
    
    for trip_id in df['randomized_id'].unique():
        trip_data = df[df['randomized_id'] == trip_id]
        
        # Calculate distance
        distance = calculate_distance(trip_data[['lat', 'lng']].values)
            
        trip_details.append({
            'trip_id': str(trip_id),
            'avg_speed': round(trip_data['spd'].mean(), 2),
            'max_speed': round(trip_data['spd'].max(), 2),
            'avg_azimuth_change': round(trip_data['azm_change'].mean(), 2),
            'sharp_turns': len(trip_data[trip_data['azm_change'] > 45]),
            'distance': round(distance, 2)
        })
    
    return trip_details


def detect_unusual_routes(df: pd.DataFrame) -> int:
    # Unusual route: large azimuth change (>120°) or sharp speed drop (>20 km/h)
    unusual = ((df['azm_change'] > 120) | (df['spd'].diff() < -20)).sum()
    return int(unusual)


def detect_sharp_declines(df: pd.DataFrame) -> int:
    # Sharp decline: speed drops by more than 20 km/h between points
    sharp_declines = (df['spd'].diff() < -20).sum()
    return int(sharp_declines)


def get_speed_distribution(df: pd.DataFrame) -> dict:
    # Histogram of speed values
    bins = [0, 20, 40, 60, 80, 100, 120]
    hist, edges = np.histogram(df['spd'], bins=bins)
    return {'bins': bins, 'counts': hist.tolist()}