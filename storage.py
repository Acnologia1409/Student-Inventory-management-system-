import csv
import os
import copy
from functools import reduce
from models import InventoryItem, ElectronicItem, Student

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

STUDENTS_FILE = os.path.join(DATA_DIR, "students.csv")
INVENTORY_FILE = os.path.join(DATA_DIR, "inventory.csv")
LOANS_FILE = os.path.join(DATA_DIR, "loans.csv")
AUDIT_LOG_FILE = os.path.join(DATA_DIR, "audit_log.txt")

class WarehouseLayout:
    def __init__(self, rows: int = 3, cols: int = 3):
        # 2D Matrix representing warehouse shelf slots
        # Each cell contains a list representing [Item ID, Status] (mutable object to demonstrate copies)
        self.grid = [[["Empty", "Unused"] for _ in range(cols)] for _ in range(rows)]
        self.rows = rows
        self.cols = cols

    def assign_shelf(self, row: int, col: int, item_id: str, status: str = "Active"):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.grid[row][col][0] = item_id
            self.grid[row][col][1] = status
        else:
            raise IndexError("Shelf coordinates out of range.")

    def demonstrate_copies(self):
        """Demonstrates shallow copy vs deep copy on the 2D layout matrix."""
        print("\n--- Shallow vs Deep Copy Demonstration ---")
        
        # 1. Create a shallow copy
        shallow_grid = copy.copy(self.grid)
        # 2. Create a deep copy
        deep_grid = copy.deepcopy(self.grid)

        # Modify an inner mutable element in the original grid
        original_cell = self.grid[0][0]
        original_cell[0] = "MODIFIED-ID"
        original_cell[1] = "Modified"

        print(f"Original[0][0] modified to: {self.grid[0][0]}")
        print(f"Shallow Copy[0][0] reflects change: {shallow_grid[0][0]} (Same reference!)")
        print(f"Deep Copy[0][0] unaffected: {deep_grid[0][0]} (New nested structure!)")
        
        # Restore cell
        self.grid[0][0] = ["Empty", "Unused"]
        print("-------------------------------------------\n")

    def display_grid(self):
        """Displays the warehouse layout grid using nested loops (pattern printing)."""
        print("Warehouse Layout Matrix (Rows x Cols):")
        for i in range(self.rows):
            row_str = " | ".join([f"[{cell[0] if cell[0] != 'Empty' else '.....'}]" for cell in self.grid[i]])
            print(f"Row {i}: {row_str}")
        print()


class DataStorage:
    def __init__(self):
        self.students = {}       # Dict: student_id -> Student object
        self.inventory = {}      # Dict: item_id -> InventoryItem object
        self.loans = []          # List of Dicts representing checkout records
        self.categories_set = set() # Set of unique item categories
        
        # Initialize files if not existing
        self._ensure_files()
        # Load existing data
        self.load_all()

    def _ensure_files(self):
        for path in (STUDENTS_FILE, INVENTORY_FILE, LOANS_FILE):
            if not os.path.exists(path):
                try:
                    with open(path, 'w', newline='', encoding='utf-8') as f:
                        pass # Touch file
                except Exception as e:
                    print(f"Error creating file {path}: {e}")

    def load_all(self):
        """Loads students, inventory, and loans from CSV. Employs try-except-finally."""
        # 1. Load Students
        try:
            with open(STUDENTS_FILE, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                self.students.clear()
                for row in reader:
                    if not row: continue
                    std_id, name, email, dept, status = row
                    self.students[std_id] = Student(name, email, std_id, dept, status)
        except Exception as e:
            print(f"Error loading students: {e}")

        # 2. Load Inventory
        try:
            with open(INVENTORY_FILE, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                self.inventory.clear()
                self.categories_set.clear()
                for row in reader:
                    if not row: continue
                    (item_id, name, cat, price, total_qty, avail_qty, 
                     sh_row, sh_col, brand, model, weight, is_elec, serial_no, warranty) = row
                    
                    location = (int(sh_row), int(sh_col))
                    
                    if is_elec == 'True':
                        item = ElectronicItem(
                            item_id, name, cat, float(price), int(total_qty), int(avail_qty), 
                            location, brand, model, float(weight), serial_no, int(warranty)
                        )
                    else:
                        item = InventoryItem(
                            item_id, name, cat, float(price), int(total_qty), int(avail_qty), 
                            location, brand, model, float(weight)
                        )
                    self.inventory[item_id] = item
                    self.categories_set.add(cat)
        except Exception as e:
            print(f"Error loading inventory: {e}")

        # 3. Load Loans
        try:
            with open(LOANS_FILE, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                self.loans.clear()
                for row in reader:
                    if not row: continue
                    loan_id, stud_id, item_id, checkout_d, due_d, return_d, status, fines = row
                    self.loans.append({
                        "loan_id": int(loan_id),
                        "student_id": stud_id,
                        "item_id": item_id,
                        "checkout_date": checkout_d,
                        "due_date": due_d,
                        "return_date": return_d if return_d != "None" else None,
                        "status": status,
                        "fines_accrued": float(fines)
                    })
        except Exception as e:
            print(f"Error loading loans: {e}")

    def save_students(self):
        try:
            with open(STUDENTS_FILE, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for s in self.students.values():
                    writer.writerow([s.student_id, s.name, s.email, s.department, s.status])
        except Exception as e:
            print(f"Error saving students: {e}")

    def save_inventory(self):
        try:
            with open(INVENTORY_FILE, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for i in self.inventory.values():
                    is_elec = isinstance(i, ElectronicItem)
                    serial = i.serial_number if is_elec else ""
                    warranty = i.warranty_months if is_elec else 0
                    
                    writer.writerow([
                        i.asset_id, i.name, i.category, i.price, i.total_qty, i.available_qty,
                        i.location[0], i.location[1], i.specs.brand, i.specs.model, i.specs.weight,
                        is_elec, serial, warranty
                    ])
        except Exception as e:
            print(f"Error saving inventory: {e}")

    def save_loans(self):
        try:
            with open(LOANS_FILE, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for l in self.loans:
                    writer.writerow([
                        l["loan_id"], l["student_id"], l["item_id"],
                        l["checkout_date"], l["due_date"], 
                        l["return_date"] if l["return_date"] is not None else "None",
                        l["status"], l["fines_accrued"]
                    ])
        except Exception as e:
            print(f"Error saving loans: {e}")

    def copy_file(self, src: str, dest: str) -> bool:
        """Copies any text/binary file (e.g. system state or image files) in chunks."""
        if not os.path.exists(src):
            return False
        try:
            with open(src, 'rb') as fsrc:
                with open(dest, 'wb') as fdest:
                    while True:
                        chunk = fsrc.read(1024)
                        if not chunk:
                            break
                        fdest.write(chunk)
            return True
        except Exception as e:
            print(f"Failed to copy file: {e}")
            return False
        finally:
            # Demonstration of finally block executing after copy
            pass

    def loan_generator(self):
        """Custom generator to stream loans one by one."""
        for loan in self.loans:
            yield loan

    def get_total_asset_value(self) -> float:
        """Calculates total financial value of all items using map and reduce."""
        if not self.inventory:
            return 0.0
        # Map: Get value of each item
        values = map(lambda item: item.get_value(), self.inventory.values())
        # Reduce: Sum all values
        total_value = reduce(lambda acc, val: acc + val, values)
        return total_value

    def filter_overdue_loans(self) -> list:
        """Returns all loans that are currently overdue using filter."""
        return list(filter(lambda loan: loan["status"] == "Overdue", self.loans))

    def get_all_categories(self) -> list:
        """Returns categories mapped and cast to unique list via set."""
        return list(self.categories_set)
