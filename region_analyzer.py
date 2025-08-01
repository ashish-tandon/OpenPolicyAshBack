#!/usr/bin/env python3
import os
import json
import sys
from pathlib import Path

def get_all_scrapers():
    scrapers_dir = Path('scrapers')
    regions = {
        'federal': [],
        'provincial': [],
        'municipal': [],
        'disabled': []
    }
    
    # Check if there are any disabled scrapers
    disabled_dir = scrapers_dir / 'disabled'
    if disabled_dir.exists():
        for item in disabled_dir.iterdir():
            if item.is_dir() and item.name.startswith('ca_'):
                regions['disabled'].append({
                    'name': f'{item.name} (Disabled)',
                    'directory': str(item),
                    'path': str(item),
                    'files': [f.name for f in item.iterdir() if f.suffix == '.py']
                })
    
    for item in scrapers_dir.iterdir():
        if item.is_dir() and item.name.startswith('ca'):
            # Check what files are in this directory
            files = [f.name for f in item.iterdir() if f.suffix == '.py']
            
            if item.name == 'ca':
                regions['federal'].append({
                    'name': 'Canada (Federal)',
                    'directory': item.name,
                    'path': str(item),
                    'files': files
                })
            elif '_' in item.name:
                parts = item.name.split('_')
                if len(parts) == 2:  # provincial (ca_XX)
                    province = parts[1]
                    regions['provincial'].append({
                        'name': f'{province.upper()} (Provincial)',
                        'directory': item.name, 
                        'path': str(item),
                        'files': files
                    })
                else:  # municipal (ca_XX_city)
                    province = parts[1]
                    city = '_'.join(parts[2:])
                    regions['municipal'].append({
                        'name': f'{city.replace("_", " ").title()}, {province.upper()}',
                        'directory': item.name,
                        'path': str(item),
                        'files': files
                    })
    
    return regions

def main():
    regions = get_all_scrapers()
    
    print("=== CANADIAN CIVIC DATA SCRAPERS ANALYSIS ===")
    print(f"Federal: {len(regions['federal'])} jurisdictions")
    print(f"Provincial: {len(regions['provincial'])} jurisdictions") 
    print(f"Municipal: {len(regions['municipal'])} jurisdictions")
    print(f"Disabled: {len(regions['disabled'])} jurisdictions")
    print(f"Total Active: {len(regions['federal']) + len(regions['provincial']) + len(regions['municipal'])}")
    print()
    
    # Save detailed report
    with open('regions_report.json', 'w') as f:
        json.dump(regions, f, indent=2)
    
    # Print summary by province
    provincial_summary = {}
    for region in regions['municipal']:
        province = region['name'].split(', ')[-1]
        if province not in provincial_summary:
            provincial_summary[province] = []
        provincial_summary[province].append(region['name'].split(', ')[0])
    
    print("=== MUNICIPAL SCRAPERS BY PROVINCE ===")
    for province, cities in sorted(provincial_summary.items()):
        print(f"{province}: {len(cities)} cities")
        for city in sorted(cities):
            print(f"  - {city}")
        print()
    
    return regions

if __name__ == "__main__":
    main()