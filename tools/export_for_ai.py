#!/usr/bin/env python3
"""
FD2 AI-Friendly Export Tool

Exports FD2 game resources to AI-friendly formats:
- JSON: Structured data for AI parsing
- C Code: Direct usage in development
- Markdown: Human-readable documentation
- YAML: Configuration-friendly format

Usage:
    python tools/export_for_ai.py --game game --output output/ai-export --format json
    python tools/export_for_ai.py --game game --output output/ai-export --format c
    python tools/export_for_ai.py --game game --output output/ai-export --format markdown
    python tools/export_for_ai.py --game game --output output/ai-export --format yaml
    python tools/export_for_ai.py --game game --output output/ai-export --format all
"""

from __future__ import annotations

import argparse
import struct
import json
import math
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

# Constants
DAT_MAGIC = b"LLLLLL"
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 200


def read_dat_header(data: bytes) -> Optional[dict]:
    """Parse DAT file header, return None if not a valid DAT."""
    if len(data) < 10 or data[:6] != DAT_MAGIC:
        return None
    
    resource_count = struct.unpack_from("<I", data, 6)[0]
    offsets = []
    for i in range(resource_count):
        offset = 10 + i * 4
        if offset + 4 > len(data):
            break
        offsets.append(struct.unpack_from("<I", data, offset)[0])
    
    return {"resource_count": resource_count, "offsets": offsets}


def get_resource_data(data: bytes, offsets: list[int], idx: int) -> bytes:
    """Extract raw resource data by index."""
    start = offsets[idx]
    end = offsets[idx + 1] if idx + 1 < len(offsets) else len(data)
    return data[start:end]


def try_read_rle_header(res_data: bytes) -> Optional[tuple[int, int]]:
    """Try to read 16-bit little-endian width/height header."""
    if len(res_data) < 4:
        return None
    w, h = struct.unpack_from("<HH", res_data, 0)
    if 0 < w <= 640 and 0 < h <= 480:
        return (w, h)
    return None


def try_read_32bit_header(res_data: bytes) -> Optional[tuple[int, int]]:
    """Try to read 32-bit little-endian width/height header."""
    if len(res_data) < 8:
        return None
    w, h = struct.unpack_from("<II", res_data, 0)
    if 0 < w <= 640 and 0 < h <= 480:
        return (w, h)
    return None


def classify_resource(res_data: bytes) -> dict:
    """Classify a resource and return metadata."""
    info: dict[str, Any] = {"size": len(res_data)}
    
    if len(res_data) < 6:
        info["type"] = "tiny_raw"
        return info
    
    # Check for nested DAT
    if res_data[:6] == DAT_MAGIC:
        inner = read_dat_header(res_data)
        if inner:
            min_size = 10 + inner["resource_count"] * 4
            if len(res_data) >= min_size:
                all_valid = True
                for i in range(inner["resource_count"]):
                    off = 10 + i * 4
                    if off + 4 > len(res_data):
                        all_valid = False
                        break
                    ptr = struct.unpack_from("<I", res_data, off)[0]
                    if ptr >= len(res_data):
                        all_valid = False
                        break
                if all_valid:
                    info["type"] = "nested_dat"
                    info["inner_resource_count"] = inner["resource_count"]
                else:
                    info["type"] = "raw_data"
            else:
                info["type"] = "raw_data"
        else:
            info["type"] = "unknown"
        return info
    
    # Try 16-bit header
    dims16 = try_read_rle_header(res_data)
    if dims16:
        w, h = dims16
        expected = w * h
        compressed_size = len(res_data) - 4
        
        if compressed_size > 0 and expected > 0:
            compression_ratio = compressed_size / expected if expected > 0 else 0
            info["type"] = "rle_image"
            info["width"] = w
            info["height"] = h
            info["expected_pixels"] = expected
            info["compressed_size"] = compressed_size
            info["compression_ratio"] = round(compression_ratio, 3)
            return info
    
    # Try 32-bit header
    dims32 = try_read_32bit_header(res_data)
    if dims32:
        w, h = dims32
        info["type"] = "rle_image_32bit"
        info["width"] = w
        info["height"] = h
        return info
    
    # Check palette
    if len(res_data) == 768:
        info["type"] = "palette"
        return info
    
    # Check text
    printable = sum(1 for b in res_data[:min(100, len(res_data))] if 32 <= b <= 126 or b in (10, 13, 9))
    if printable > min(100, len(res_data)) * 0.7:
        info["type"] = "text"
        return info
    
    info["type"] = "raw_data"
    return info


def analyze_dat_file(dat_path: Path) -> dict:
    """Analyze a single DAT file and return structured data."""
    data = dat_path.read_bytes()
    header = read_dat_header(data)
    
    if not header:
        return {"error": "Invalid DAT file", "filename": dat_path.name}
    
    result = {
        "filename": dat_path.name,
        "file_size": len(data),
        "magic": DAT_MAGIC.decode('ascii'),
        "resource_count": header["resource_count"],
        "resources": []
    }
    
    offsets = header["offsets"]
    
    for idx in range(header["resource_count"]):
        res_data = get_resource_data(data, offsets, idx)
        info = classify_resource(res_data)
        info["index"] = idx
        info["offset"] = offsets[idx]
        info["size"] = len(res_data)
        
        # Add hex preview for raw data
        if info["type"] in ("raw_data", "tiny_raw"):
            info["hex_preview"] = res_data[:32].hex()
        
        # Add nested DAT info
        if info["type"] == "nested_dat":
            nested_header = read_dat_header(res_data)
            if nested_header:
                info["nested_resources"] = nested_header["resource_count"]
                info["nested_offsets"] = nested_header["offsets"]
        
        result["resources"].append(info)
    
    return result


def export_to_json(analyses: list[dict], output_path: Path):
    """Export analysis results to JSON format."""
    output = {
        "export_timestamp": datetime.now().isoformat(),
        "tool": "FD2 AI-Friendly Export Tool",
        "version": "1.0",
        "description": "FD2 game resource analysis for AI assistants",
        "dat_files": analyses
    }
    
    json_path = output_path / "fd2_resources.json"
    json_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"  JSON: {json_path}")


def export_to_yaml(analyses: list[dict], output_path: Path):
    """Export analysis results to YAML format."""
    try:
        import yaml
    except ImportError:
        print("  WARNING: PyYAML not installed. Install with: pip install pyyaml")
        return
    
    yaml_path = output_path / "fd2_resources.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(analyses, f, default_flow_style=False, allow_unicode=True)
    print(f"  YAML: {yaml_path}")


def export_to_c_code(analyses: list[dict], output_path: Path):
    """Export analysis results to C header file."""
    c_path = output_path / "fd2_resources.h"
    
    with open(c_path, "w", encoding="utf-8") as f:
        f.write("/*\n")
        f.write(" * FD2 Game Resource Definitions\n")
        f.write(f" * Generated: {datetime.now().isoformat()}\n")
        f.write(" * \n")
        f.write(" * Auto-generated from DAT file analysis.\n")
        f.write(" * DO NOT EDIT MANUALLY\n")
        f.write(" */\n\n")
        f.write("#ifndef FD2_RESOURCES_H\n")
        f.write("#define FD2_RESOURCES_H\n\n")
        f.write("/* Resource type definitions */\n")
        f.write("#define RES_TYPE_RLE_IMAGE      0\n")
        f.write("#define RES_TYPE_RLE_IMAGE_32   1\n")
        f.write("#define RES_TYPE_PALETTE        2\n")
        f.write("#define RES_TYPE_NESTED_DAT     3\n")
        f.write("#define RES_TYPE_RAW_DATA       4\n")
        f.write("#define RES_TYPE_TEXT           5\n\n")
        
        f.write("/* Resource structure */\n")
        f.write("typedef struct {\n")
        f.write("    int index;\n")
        f.write("    int offset;\n")
        f.write("    int size;\n")
        f.write("    int type;\n")
        f.write("    int width;\n")
        f.write("    int height;\n")
        f.write("    const char* description;\n")
        f.write("} fd2_resource_t;\n\n")
        
        for analysis in analyses:
            if "error" in analysis:
                continue
            
            dat_name = analysis["filename"].replace(".DAT", "").upper()
            f.write(f"/* {analysis['filename']} - {analysis['resource_count']} resources */\n")
            f.write(f"#define {dat_name}_COUNT {analysis['resource_count']}\n")
            f.write(f"#define {dat_name}_SIZE {analysis['file_size']}\n\n")
            
            # Generate resource array
            f.write(f"static const fd2_resource_t {dat_name.lower()}_resources[] = {{\n")
            
            for res in analysis.get("resources", []):
                res_type_map = {
                    "rle_image": "RES_TYPE_RLE_IMAGE",
                    "rle_image_32bit": "RES_TYPE_RLE_IMAGE_32",
                    "palette": "RES_TYPE_PALETTE",
                    "nested_dat": "RES_TYPE_NESTED_DAT",
                    "raw_data": "RES_TYPE_RAW_DATA",
                    "text": "RES_TYPE_TEXT",
                    "tiny_raw": "RES_TYPE_RAW_DATA"
                }
                
                res_type = res_type_map.get(res["type"], "RES_TYPE_RAW_DATA")
                width = res.get("width", 0)
                height = res.get("height", 0)
                
                f.write(
                    f"    {{{res['index']}, 0x{res['offset']:X}, {res['size']}, "
                    f"{res_type}, {width}, {height}, "
                    f"\"Resource {res['index']}\"}},\n"
                )
            
            f.write("};\n\n")
        
        f.write("#endif /* FD2_RESOURCES_H */\n")
    
    print(f"  C Header: {c_path}")


def export_to_markdown(analyses: list[dict], output_path: Path):
    """Export analysis results to Markdown documentation."""
    md_path = output_path / "fd2_resources.md"
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# FD2 Game Resource Analysis\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Tool**: FD2 AI-Friendly Export Tool v1.0\n\n")
        
        f.write("## Overview\n\n")
        f.write("| DAT File | Size | Resources |\n")
        f.write("|----------|------|-----------|\n")
        
        for analysis in analyses:
            if "error" in analysis:
                f.write(f"| {analysis['filename']} | - | ERROR |\n")
            else:
                f.write(
                    f"| {analysis['filename']} "
                    f"| {analysis['file_size']:,} bytes "
                    f"| {analysis['resource_count']} |\n"
                )
        
        f.write("\n")
        
        # Detailed analysis for each DAT file
        for analysis in analyses:
            if "error" in analysis:
                continue
            
            f.write(f"## {analysis['filename']}\n\n")
            f.write(f"- **文件大小**: {analysis['file_size']:,} bytes\n")
            f.write(f"- **资源数量**: {analysis['resource_count']}\n\n")
            
            # Summary table
            f.write("### 资源列表\n\n")
            f.write("| 索引 | 偏移 | 大小 | 类型 | 尺寸 |\n")
            f.write("|------|------|------|------|------|\n")
            
            for res in analysis.get("resources", []):
                dimensions = ""
                if "width" in res and "height" in res:
                    dimensions = f"{res['width']}x{res['height']}"
                
                type_desc = res["type"]
                if res["type"] == "nested_dat":
                    type_desc += f" ({res.get('inner_resource_count', 0)}子资源)"
                
                f.write(
                    f"| {res['index']} "
                    f"| 0x{res['offset']:X} "
                    f"| {res['size']:,} "
                    f"| {type_desc} "
                    f"| {dimensions} |\n"
                )
            
            f.write("\n")
            
            # Resource type summary
            type_counts = {}
            for res in analysis.get("resources", []):
                t = res["type"]
                type_counts[t] = type_counts.get(t, 0) + 1
            
            f.write("### 资源类型统计\n\n")
            f.write("| 类型 | 数量 |\n")
            f.write("|------|------|\n")
            for t, count in sorted(type_counts.items()):
                f.write(f"| {t} | {count} |\n")
            f.write("\n")
    
    print(f"  Markdown: {md_path}")


def export_resource_summary(analyses: list[dict], output_path: Path):
    """Export a summary of all resources."""
    summary = {
        "total_dat_files": len(analyses),
        "total_resources": 0,
        "resource_type_counts": {},
        "largest_files": [],
        "files_with_nested_dat": [],
        "image_resources": []
    }
    
    for analysis in analyses:
        if "error" in analysis:
            continue
        
        summary["total_resources"] += analysis.get("resource_count", 0)
        
        for res in analysis.get("resources", []):
            res_type = res["type"]
            summary["resource_type_counts"][res_type] = \
                summary["resource_type_counts"].get(res_type, 0) + 1
            
            if res_type == "nested_dat":
                summary["files_with_nested_dat"].append({
                    "file": analysis["filename"],
                    "index": res["index"],
                    "inner_resources": res.get("inner_resource_count", 0)
                })
            
            if "rle_image" in res_type:
                summary["image_resources"].append({
                    "file": analysis["filename"],
                    "index": res["index"],
                    "width": res.get("width", 0),
                    "height": res.get("height", 0)
                })
        
        summary["largest_files"].append({
            "filename": analysis["filename"],
            "size": analysis.get("file_size", 0),
            "resources": analysis.get("resource_count", 0)
        })
    
    summary["largest_files"].sort(key=lambda x: x["size"], reverse=True)
    
    summary_path = output_path / "resource_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"  Summary: {summary_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export FD2 resources to AI-friendly formats")
    parser.add_argument("--game", type=Path, default=Path("game"), help="Game directory")
    parser.add_argument("--output", type=Path, default=Path("output/ai-export"), help="Output directory")
    parser.add_argument("--format", type=str, default="all",
                       choices=["json", "yaml", "c", "markdown", "all"],
                       help="Export format")
    parser.add_argument("--dat", type=str, default=None, help="Process only this DAT file")
    args = parser.parse_args()
    
    game_dir = args.game.resolve()
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not game_dir.exists():
        print(f"Error: game directory not found: {game_dir}")
        return 1
    
    # Find DAT files
    dat_files = sorted(game_dir.glob("*.DAT"))
    if args.dat:
        dat_files = [game_dir / args.dat.upper()]
        if not dat_files[0].exists():
            print(f"Error: DAT file not found: {dat_files[0]}")
            return 1
    
    print(f"FD2 AI-Friendly Export Tool")
    print(f"Game: {game_dir}")
    print(f"Output: {output_dir}")
    print(f"Found {len(dat_files)} DAT files")
    print()
    
    # Analyze all DAT files
    analyses = []
    for dat_path in dat_files:
        print(f"Analyzing {dat_path.name}...")
        analysis = analyze_dat_file(dat_path)
        analyses.append(analysis)
    
    print()
    print(f"Exporting...")
    
    # Export in requested format(s)
    if args.format in ("json", "all"):
        export_to_json(analyses, output_dir)
        export_resource_summary(analyses, output_dir)
    
    if args.format in ("yaml", "all"):
        export_to_yaml(analyses, output_dir)
    
    if args.format in ("c", "all"):
        export_to_c_code(analyses, output_dir)
    
    if args.format in ("markdown", "all"):
        export_to_markdown(analyses, output_dir)
    
    print()
    print(f"Export complete!")
    print(f"  DAT files analyzed: {len(dat_files)}")
    print(f"  Total resources: {sum(a.get('resource_count', 0) for a in analyses)}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
