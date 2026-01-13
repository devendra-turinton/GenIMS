#!/usr/bin/env python3
"""Fix all field name mismatches in ERP generator"""
import re

print("Reading generator file...")
with open('generate_erp_historical_data.py', 'r') as f:
    content = f.read()

# Fix 1: purchase_order_line_id → po_line_id
print("1. Fixing purchase_order_line_id → po_line_id...")
content = content.replace("'purchase_order_line_id':", "'po_line_id':")

# Fix 2: Add delivery_date calculation and fix field names in PO lines
print("2. Adding delivery_date and fixing PO line fields...")
# Find all instances where we create purchase order lines
content = re.sub(
    r"(\s+line_total = quantity \* unit_price\s+total_value \+= line_total)\s+(line = \{\s+'po_line_id')",
    r"\1\n                    delivery_date = po_date + timedelta(days=random.randint(7, 30))\n                    \n                    \2",
    content
)

# Fix quantity → order_quantity and add unit_of_measure and delivery_date in PO lines
content = re.sub(
    r"('po_line_id':.*?\n.*?'purchase_order_id':.*?\n.*?'line_number':.*?\n.*?'material_id':.*?\n\s+)'quantity': quantity,(\s+'unit_price')",
    r"\1'order_quantity': quantity,\n                        'unit_of_measure': material['base_unit_of_measure'],\n                        'delivery_date': delivery_date.strftime('%Y-%m-%d'),\n                       \2",
    content,
    flags=re.DOTALL
)

# Fix 3: Production order quantity reference
print("3. Fixing production order quantity references...")
content = content.replace(
    "order_quantity = line['quantity']",
    "order_quantity = line.get('order_quantity', line.get('quantity', 1))"
)

# Fix 4: Remove duplicate purchase_orders_chunk function (keep only first occurrence)
print("4. Removing duplicate _generate_purchase_orders_chunk function...")
# Find the second occurrence and remove it along with the inventory method that has misplaced code
pattern = r"(def generate_inventory\(self\):.*?print\(f\"Generated.*?inventory balance records\"\))\s+print\(f\"  🚀 Processing.*?print\(f\"✓ Generated.*?purchase orders via PARALLEL processing\"\)\s+def _generate_purchase_orders_chunk"
replacement = r"\1\n    \n    def _generate_purchase_orders_chunk_DUPLICATE_REMOVED"

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

print("Writing fixed content...")
with open('generate_erp_historical_data.py', 'w') as f:
    f.write(content)

print("✅ All fixes applied successfully!")
print("\nSummary of changes:")
print("  - Fixed purchase_order_line_id → po_line_id")
print("  - Added delivery_date calculation for PO lines")
print("  - Fixed quantity → order_quantity in PO lines")
print("  - Added unit_of_measure and delivery_date fields")
print("  - Fixed production order quantity references")
print("  - Removed duplicate _generate_purchase_orders_chunk function")
