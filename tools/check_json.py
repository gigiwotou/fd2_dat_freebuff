import json
from collections import Counter

data = json.load(open('output/maps/map_0_layout.json'))
terrain_ids = [tid for row in data['terrain_ids'] for tid in row]
counter = Counter(terrain_ids)
print(f'Terrain IDs in map_0_layout.json:')
print(f'Range: {min(terrain_ids)}-{max(terrain_ids)}')
print(f'Unique: {len(set(terrain_ids))}')
print('Top 15:')
for tid, count in counter.most_common(15):
    print(f'  {tid}: {count} times')