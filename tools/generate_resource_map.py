#!/usr/bin/env python3
"""
FD2 Resource Map Generator

Generates a comprehensive JSON resource map for all DAT files.
This serves as the reference document for the 1:1 port.
"""

import struct
import json
from pathlib import Path
from typing import Any, Optional

DAT_MAGIC = b"LLLLLL"


def analyze_dat(dat_path: Path) -> dict:
    """Analyze a single DAT file and return resource information."""
    data = dat_path.read_bytes()
    
    if len(data) < 10 or data[:6] != DAT_MAGIC:
        return {"error": "Not a valid DAT file", "size": len(data)}
    
    resource_count = struct.unpack_from("<I", data, 6)[0]
    offsets = []
    for i in range(resource_count):
        offset = 10 + i * 4
        if offset + 4 > len(data):
            break
        offsets.append(struct.unpack_from("<I", data, offset)[0])
    
    resources = []
    categories = {"images": 0, "raw": 0, "tiny": 0, "text": 0, "palette": 0}
    
    for idx in range(len(offsets)):
        start = offsets[idx]
        end = offsets[idx + 1] if idx + 1 < len(offsets) else len(data)
        size = max(0, end - start)
        res_data = data[start:end]
        
        res_info: dict[str, Any] = {
            "index": idx,
            "offset": start,
            "size": size,
        }
        
        if size == 0:
            res_info["type"] = "empty"
            categories["tiny"] += 1
        elif size == 768:
            res_info["type"] = "palette"
            categories["palette"] += 1
        elif size < 10:
            res_info["type"] = "tiny"
            categories["tiny"] += 1
        else:
            # Try 16-bit header
            dims = None
            if size >= 4:
                try:
                    w, h = struct.unpack_from("<HH", res_data, 0)
                    if 0 < w <= 640 and 0 < h <= 480:
                        dims = (w, h)
                except:
                    pass
            
            if dims:
                w, h = dims
                res_info["type"] = "rle_image"
                res_info["width"] = w
                res_info["height"] = h
                res_info["expected_pixels"] = w * h
                res_info["compressed_size"] = size - 4
                res_info["compression_ratio"] = round((size - 4) / (w * h), 3) if w * h > 0 else 0
                categories["images"] += 1
            else:
                # Check for text
                printable = sum(1 for b in res_data[:min(100, len(res_data))] if 32 <= b <= 126 or b in (10, 13, 9))
                if printable > min(100, len(res_data)) * 0.7:
                    res_info["type"] = "text"
                    categories["text"] += 1
                else:
                    res_info["type"] = "raw"
                    categories["raw"] += 1
        
        resources.append(res_info)
    
    return {
        "resource_count": resource_count,
        "file_size": len(data),
        "categories": categories,
        "resources": resources,
    }


def main():
    game_dir = Path("game")
    dat_files = sorted(game_dir.glob("*.DAT"))
    
    resource_map = {
        "game": "FD2 (Flame Dragon 2)",
        "platform": "DOS (DOS4GW extender)",
        "resolution": "320x200",
        "dat_files": {},
        "summary": {
            "total_dat_files": len(dat_files),
            "total_resources": 0,
            "total_images": 0,
            "total_raw": 0,
            "total_text": 0,
            "total_palette": 0,
        }
    }
    
    for dat_path in dat_files:
        info = analyze_dat(dat_path)
        resource_map["dat_files"][dat_path.name] = info
        resource_map["summary"]["total_resources"] += info.get("resource_count", 0)
        cats = info.get("categories", {})
        resource_map["summary"]["total_images"] += cats.get("images", 0)
        resource_map["summary"]["total_raw"] += cats.get("raw", 0)
        resource_map["summary"]["total_text"] += cats.get("text", 0)
        resource_map["summary"]["total_palette"] += cats.get("palette", 0)
    
    output_path = Path("output/extracted/resource_map.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(resource_map, indent=2), encoding="utf-8")
    
    print(f"Resource map saved to: {output_path}")
    print(f"Summary:")
    for key, value in resource_map["summary"].items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
