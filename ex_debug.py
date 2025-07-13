## ex_debug.py
import pdb

def calculate_total(items):
    total = 0
    for item in items:
        pdb.set_trace()
        total += get_item_price(item)  # When stepping, you'll enter this function
    return total

def get_item_price(item):
    base_price = item['price']
    tax = base_price * 0.1
    return base_price + tax

# Main code
products = [{'name': 'Laptop', 'price': 1000}, {'name': 'Mouse', 'price': 25}]
final_total = calculate_total(products)
print(f"Total: ${final_total}")