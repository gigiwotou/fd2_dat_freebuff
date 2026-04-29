import json
from collections import Counter

data = json.load(open('output/maps/map_0_layout.json'))
print(f'Width: {data["width"]}')
print(f'Height: {data["height"]}')
terrain_ids = [tid for row in data['terrain_ids'] for tid in row]
print(f'Unique terrain IDs: {len(set(terrain_ids))}')
print(f'Range: {min(terrain_ids)}-{max(terrain_ids)}')
counter = Counter(terrain_ids)
print('Top 10 terrain IDs:')
for tid, count in counter.most_common(10):
    print(f'  {tid}: {count} times')
