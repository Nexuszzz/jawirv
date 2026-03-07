import json

# Debug scraper output structure
with open('polinema_complete_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== DEBUG POLINEMA DATA STRUCTURE ===\n")

biodata = data.get('biodata', {})
print(f"Biodata type: {type(biodata)}")
print(f"Biodata keys: {list(biodata.keys()) if isinstance(biodata, dict) else 'NOT A DICT'}\n")

tables = biodata.get('tables', [])
print(f"Tables type: {type(tables)}")
print(f"Tables length: {len(tables)}\n")

if tables:
    first = tables[0]
    print(f"First table type: {type(first)}")
    
    if isinstance(first, dict):
        print(f"First table keys: {list(first.keys())}")
        rows = first.get('rows', [])
        print(f"Rows count: {len(rows)}")
        if rows:
            print(f"First row type: {type(rows[0])}")
            if isinstance(rows[0], dict):
                print(f"First row keys: {list(rows[0].keys())}")
                cells = rows[0].get('cells', [])
                print(f"Cells: {cells[:2]}")
    elif isinstance(first, list):
        print(f"ERROR: First table is a LIST, not DICT!")
        print(f"List length: {len(first)}")
        if first:
            print(f"First element: {first[0]}")
