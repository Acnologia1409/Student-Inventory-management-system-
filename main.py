import sys
import time
import threading
from datetime import datetime, timedelta

from models import InventoryItem, ElectronicItem, Student, inspect_object
from storage import DataStorage, WarehouseLayout
from utils import log_operation, calculate_compound_fine, parse_and_convert_asset_tag, analyze_fines_and_risks

# ==========================================
# 1. Multithreading Monitor Thread (Daemon)
# ==========================================
class StockAndFineMonitor(threading.Thread):
    """Background thread that runs periodically to inspect low stock and overdue items."""
    def __init__(self, storage: DataStorage, interval_seconds: int = 15):
        # Call thread initializer
        super().__init__()
        self.storage = storage
        self.interval = interval_seconds
        self.running = True
        self.daemon = True  # Allows program to exit even if thread is running

    def run(self):
        """Standard thread execution loop."""
        while self.running:
            # Sleep in 1-second chunks so we can terminate quickly on stop
            for _ in range(self.interval):
                if not self.running:
                    break
                time.sleep(1)
                
            if not self.running:
                break
                
            # Perform background checks
            self.check_system_status()

    def check_system_status(self):
        low_stock = []
        for item in self.storage.inventory.values():
            if item.available_qty <= 1:
                low_stock.append(f"{item.name} ({item.available_qty} left)")
                
        # Calculate active overdues
        overdue_count = 0
        today = datetime.now().date()
        for loan in self.storage.loans:
            if loan["status"] != "Returned":
                due_date = datetime.strptime(loan["due_date"], "%Y-%m-%d").date()
                if today > due_date:
                    overdue_count += 1
                    
        # Alert if anything found
        if low_stock or overdue_count > 0:
            print("\n" + "="*50)
            print("\033[93m⚠️  [BACKGROUND MONITOR ALERT] System Status Healthcheck:\033[0m")
            if low_stock:
                print(f"  - Low Stock Warning: {', '.join(low_stock)}")
            if overdue_count > 0:
                print(f"  - Overdue Loans Alert: {overdue_count} item(s) are currently past due date!")
            print("="*50)
            print("Select an option: ", end="", flush=True)

    def stop(self):
        self.running = False


# ==========================================
# 2. Control Flow: Nested Loop Pattern Printing
# ==========================================
def print_welcome_banner():
    """Prints a structured ASCII banner using nested loops (Pattern Printing)."""
    rows = 7
    cols = 60
    for r in range(rows):
        for c in range(cols):
            # Print border characters
            if r == 0 or r == rows - 1:
                print("=", end="")
            elif c == 0 or c == cols - 1:
                print("|", end="")
            # Print title text in the middle row
            elif r == 3 and c == (cols - 34) // 2:
                title = " EDUTRACK INVENTORY SYSTEM v2.0 "
                print(title, end="")
                # Advance column pointer by the length of the string minus 1
                # (since the outer loop will increment c by 1)
                for _ in range(len(title) - 1):
                    pass
            # Spacing
            elif r == 3 and (cols - 34) // 2 < c < (cols - 34) // 2 + 32:
                pass # Already handled by title print
            else:
                print(" ", end="")
        print() # Newline
    print()


# ==========================================
# 3. Interactive Main App
# ==========================================
class EduTrackCLI:
    def __init__(self):
        self.storage = DataStorage()
        self.layout = WarehouseLayout(rows=3, cols=3)
        self.monitor = None
        
        # Sync warehouse grid layout coordinate matrix from inventory location tuples
        self.sync_warehouse_layout()

    def sync_warehouse_layout(self):
        for item in self.storage.inventory.values():
            r, c = item.location
            # Fit inside 3x3 shelf bounds
            if 0 <= r < 3 and 0 <= c < 3:
                self.layout.assign_shelf(r, c, item.asset_id, "Stocked")

    def run(self):
        print_welcome_banner()
        
        # Check command line arguments (sys.argv)
        # Demonstrates sys.argv usage
        if len(sys.argv) > 1:
            cmd = sys.argv[1].lower()
            print(f"Executing CLI startup argument: {cmd}")
            if cmd == "seed":
                self.seed_defaults()
            elif cmd == "stats":
                self.show_quick_stats()
                sys.exit(0)
            else:
                print(f"Unknown argument '{cmd}'. Running standard session.")

        # Start background monitoring thread
        self.monitor = StockAndFineMonitor(self.storage, interval_seconds=20)
        self.monitor.start()

        # Command loop
        try:
            while True:
                self.display_menu()
                choice = input("Select an option (1-6): ").strip()
                
                # Branching conditionals
                if choice == "1":
                    self.inventory_menu()
                elif choice == "2":
                    self.student_menu()
                elif choice == "3":
                    self.checkout_menu()
                elif choice == "4":
                    self.warehouse_menu()
                elif choice == "5":
                    self.financial_summary()
                elif choice == "6":
                    print("Exiting EduTrack... Saving states.")
                    break
                else:
                    print("Invalid option. Please input a number from 1 to 6.")
        except KeyboardInterrupt:
            print("\nKeyboard Interrupt detected. Exiting cleanly...")
        finally:
            # Clean up: stop thread and join it
            if self.monitor:
                self.monitor.stop()
                print("Waiting for background thread to shutdown...")
                self.monitor.join(timeout=3)
            # Save files
            self.storage.save_students()
            self.storage.save_inventory()
            self.storage.save_loans()
            print("System state saved successfully. Goodbye!")

    def display_menu(self):
        print("\n" + "="*30)
        print("        MAIN SYSTEM MENU")
        print("="*30)
        print("1. Inventory Management Catalog")
        print("2. Student Records Directory")
        print("3. Checkouts & Loans Center")
        print("4. Warehouse Layout & Shelf Mapping")
        print("5. Financial Audit & Risk Report")
        print("6. Save & Exit Program")
        print("="*30)

    # ==========================================
    # Menu Actions
    # ==========================================
    @log_operation
    def inventory_menu(self):
        while True:
            print("\n--- Inventory Catalog Menu ---")
            print("1. List All Inventory Items")
            print("2. Search Catalog")
            print("3. Register New Inventory Asset")
            print("4. Restock Existing Asset (Operator Overloading +)")
            print("5. Compare Stock Levels (Operator Overloading <)")
            print("6. Back to Main Menu")
            
            ch = input("Enter choice: ").strip()
            if ch == "1":
                if not self.storage.inventory:
                    print("No items in catalog.")
                    continue
                for item in self.storage.inventory.values():
                    # Duck typing helper call
                    inspect_object(item)
                    # Base conversions tag print helper
                    bases = parse_and_convert_asset_tag(item.asset_id)
                    print(f"      [Asset Tag bases: Binary: {bases['binary']} | Octal: {bases['octal']} | Hex: {bases['hex']}]")
            elif ch == "2":
                q = input("Enter search term (name/category): ").strip().lower()
                # Functional Filter simulation
                results = list(filter(lambda x: q in x.name.lower() or q in x.category.lower(), self.storage.inventory.values()))
                if not results:
                    print("No matching items found.")
                for item in results:
                    item.display()
            elif ch == "3":
                self.add_inventory_item_wizard()
            elif ch == "4":
                # Operator overloading + demo
                item_id = input("Enter Item Asset ID: ").strip()
                if item_id in self.storage.inventory:
                    qty_str = input("Enter stock quantity to add: ").strip()
                    try:
                        qty = int(qty_str)
                        # Invoke overloaded + operator
                        self.storage.inventory[item_id] = self.storage.inventory[item_id] + qty
                        self.storage.save_inventory()
                        print(f"Stock updated! New total: {self.storage.inventory[item_id].total_qty}")
                    except ValueError:
                        print("Invalid quantity value.")
                else:
                    print("Asset ID not found.")
            elif ch == "5":
                # Operator overloading < demo
                id1 = input("Enter first Item ID: ").strip()
                id2 = input("Enter second Item ID: ").strip()
                if id1 in self.storage.inventory and id2 in self.storage.inventory:
                    item1 = self.storage.inventory[id1]
                    item2 = self.storage.inventory[id2]
                    if item1 < item2:
                        print(f"Item {item1.name} has LESS available stock ({item1.available_qty}) than {item2.name} ({item2.available_qty})")
                    else:
                        print(f"Item {item1.name} has EQUAL or MORE available stock ({item1.available_qty}) than {item2.name} ({item2.available_qty})")
                else:
                    print("One or both Asset IDs not found.")
            elif ch == "6" or not ch:
                break

    def add_inventory_item_wizard(self):
        try:
            item_id = input("Enter New Asset ID (e.g. INV105): ").strip().upper()
            if item_id in self.storage.inventory:
                print("Asset ID already exists.")
                return
            
            name = input("Enter Item Name: ").strip()
            cat = input("Enter Category: ").strip()
            price = float(input("Enter Unit Rental Price: $").strip())
            qty = int(input("Enter Initial Quantity: ").strip())
            
            r = int(input("Shelf Coordinate Row (0-2): ").strip())
            c = int(input("Shelf Coordinate Col (0-2): ").strip())
            loc = (r, c)
            
            brand = input("Enter Brand: ").strip()
            model = input("Enter Model: ").strip()
            weight = float(input("Enter Weight (kg): ").strip())
            
            is_elec = input("Is it an Electronic Item? (y/n): ").strip().lower() == 'y'
            if is_elec:
                serial = input("Enter Serial Number: ").strip()
                warranty = int(input("Enter Warranty (months): ").strip())
                new_item = ElectronicItem(item_id, name, cat, price, qty, qty, loc, brand, model, weight, serial, warranty)
            else:
                new_item = InventoryItem(item_id, name, cat, price, qty, qty, loc, brand, model, weight)
                
            self.storage.inventory[item_id] = new_item
            self.storage.save_inventory()
            self.sync_warehouse_layout()
            print("Asset registered successfully!")
        except Exception as e:
            print(f"Error registering asset: {e}")

    @log_operation
    def student_menu(self):
        while True:
            print("\n--- Student Directory Menu ---")
            print("1. List All Students")
            print("2. Register New Student")
            print("3. Modify Student Status")
            print("4. Back to Main Menu")
            
            ch = input("Enter choice: ").strip()
            if ch == "1":
                if not self.storage.students:
                    print("No students registered.")
                    continue
                # Method overloading demo: optionally display score vector
                show_score = input("Display academic vectors? (y/n): ").strip().lower() == 'y'
                for std in self.storage.students.values():
                    std.display(show_academic_score=show_score)
            elif ch == "2":
                sid = input("Enter Student ID (e.g. STU001): ").strip().upper()
                if sid in self.storage.students:
                    print("Student ID already registered.")
                    continue
                name = input("Enter Name: ").strip()
                email = input("Enter Email: ").strip()
                dept = input("Enter Department: ").strip()
                
                self.storage.students[sid] = Student(name, email, sid, dept)
                self.storage.save_students()
                print("Student registered successfully!")
            elif ch == "3":
                sid = input("Enter Student ID: ").strip().upper()
                if sid in self.storage.students:
                    new_status = input("Enter Status (Active/Suspended): ").strip()
                    if new_status in ("Active", "Suspended"):
                        self.storage.students[sid].status = new_status
                        self.storage.save_students()
                        print("Status updated.")
                    else:
                        print("Invalid status option.")
                else:
                    print("Student not found.")
            elif ch == "4" or not ch:
                break

    @log_operation
    def checkout_menu(self):
        while True:
            print("\n--- Checkout & Loans Center ---")
            print("1. Checkout an Asset (Loan creation)")
            print("2. Return checked-out Asset (Calculate fine)")
            print("3. List All Transactions")
            print("4. Show Overdue Loans (Generator usage)")
            print("5. Back to Main Menu")
            
            ch = input("Enter choice: ").strip()
            if ch == "1":
                sid = input("Enter Student ID: ").strip().upper()
                if sid not in self.storage.students:
                    print("Student record not found.")
                    continue
                student = self.storage.students[sid]
                if student.status == "Suspended":
                    print("Cannot loan items. Student status is Suspended!")
                    continue
                    
                iid = input("Enter Item Asset ID: ").strip()
                if iid not in self.storage.inventory:
                    print("Asset record not found.")
                    continue
                item = self.storage.inventory[iid]
                if item.available_qty <= 0:
                    print(f"Item '{item.name}' is out of stock.")
                    continue
                
                # Setup dates
                checkout_d = datetime.now().strftime("%Y-%m-%d")
                due_d = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
                
                # Create loan record
                loan_id = len(self.storage.loans) + 1
                new_loan = {
                    "loan_id": loan_id,
                    "student_id": sid,
                    "item_id": iid,
                    "checkout_date": checkout_d,
                    "due_date": due_d,
                    "return_date": None,
                    "status": "Active",
                    "fines_accrued": 0.0
                }
                
                self.storage.loans.append(new_loan)
                # Decrease inventory count
                item.available_qty -= 1
                self.storage.save_inventory()
                self.storage.save_loans()
                print(f"Loan checkout complete! ID: {loan_id}. Return deadline: {due_d}")
                
            elif ch == "2":
                try:
                    loan_id = int(input("Enter Transaction/Loan ID: ").strip())
                except ValueError:
                    print("Invalid Loan ID format.")
                    continue
                    
                matching_loan = None
                for loan in self.storage.loans:
                    if loan["loan_id"] == loan_id and loan["status"] != "Returned":
                        matching_loan = loan
                        break
                        
                if not matching_loan:
                    print("Active loan record not found.")
                    continue
                
                # Check overdue and calculate compound fine recursively
                due_date = datetime.strptime(matching_loan["due_date"], "%Y-%m-%d").date()
                today = datetime.now().date()
                fine_charge = 0.0
                
                if today > due_date:
                    days_overdue = (today - due_date).days
                    # RECURSIVE compounding fine calculation!
                    fine_charge = calculate_compound_fine(days_overdue, daily_rate=1.0)
                    print(f"⚠️ Loan is {days_overdue} days OVERDUE.")
                    print(f"Compounded fine calculated: ${fine_charge:.2f}")
                
                # Return item
                matching_loan["return_date"] = datetime.now().strftime("%Y-%m-%d")
                matching_loan["status"] = "Returned"
                matching_loan["fines_accrued"] = fine_charge
                
                # Restore stock count
                item = self.storage.inventory[matching_loan["item_id"]]
                item.available_qty += 1
                
                self.storage.save_inventory()
                self.storage.save_loans()
                print(f"Item returned successfully. Fines processed: ${fine_charge:.2f}")
                
            elif ch == "3":
                if not self.storage.loans:
                    print("No transactions recorded.")
                    continue
                for l in self.storage.loans:
                    ret_str = l["return_date"] if l["return_date"] else "Active"
                    print(f"Loan ID: {l['loan_id']} | Student: {l['student_id']} | Asset: {l['item_id']} | Out: {l['checkout_date']} | Due: {l['due_date']} | In: {ret_str} | Status: {l['status']} | Fine: ${l['fines_accrued']:.2f}")
            elif ch == "4":
                # Stream loans using Generator
                print("\n--- Current Active/Overdue Loans (Generator Stream) ---")
                gen = self.storage.loan_generator()
                found = False
                while True:
                    try:
                        loan = next(gen)
                        if loan["status"] in ("Active", "Overdue"):
                            found = True
                            print(f"  Loan #{loan['loan_id']}: Student {loan['student_id']} has item {loan['item_id']} (Due: {loan['due_date']}, Status: {loan['status']})")
                    except StopIteration:
                        break
                if not found:
                    print("No active/overdue loans found.")
            elif ch == "5" or not ch:
                break

    @log_operation
    def warehouse_menu(self):
        while True:
            print("\n--- Warehouse Shelf Mapping Menu ---")
            print("1. Display Warehouse Layout Grid (Matrix)")
            print("2. Reassign Asset Coordinates (Tuple Coordinate)")
            print("3. Demonstrate Deep Copy vs Shallow Copy in grid")
            print("4. Back to Main Menu")
            
            ch = input("Enter choice: ").strip()
            if ch == "1":
                self.layout.display_grid()
            elif ch == "2":
                item_id = input("Enter Asset ID: ").strip()
                if item_id not in self.storage.inventory:
                    print("Asset record not found.")
                    continue
                try:
                    r = int(input("Enter Shelf Row (0-2): ").strip())
                    c = int(input("Enter Shelf Col (0-2): ").strip())
                    
                    if 0 <= r < 3 and 0 <= c < 3:
                        # Clear old coordinates
                        old_r, old_c = self.storage.inventory[item_id].location
                        if self.layout.grid[old_r][old_c][0] == item_id:
                            self.layout.grid[old_r][old_c] = ["Empty", "Unused"]
                            
                        self.storage.inventory[item_id].location = (r, c)
                        self.storage.save_inventory()
                        self.sync_warehouse_layout()
                        print(f"Asset shelf remapped to coordinates: {(r, c)}")
                    else:
                        print("Coordinates must be between 0 and 2.")
                except ValueError:
                    print("Invalid row/col integers.")
            elif ch == "3":
                self.layout.demonstrate_copies()
            elif ch == "4" or not ch:
                break

    @log_operation
    def financial_summary(self):
        print("\n=== SYSTEM FINANCIAL AUDIT & RISK REPORT ===")
        # Map & Reduce asset calculations
        total_val = self.storage.get_total_asset_value()
        print(f"Total Portfolio Inventory Asset Value: ${total_val:.2f}")
        
        # Overdue list
        overdues = self.storage.filter_overdue_loans()
        print(f"Total Active Overdue Records: {len(overdues)}")
        
        # Calculate sum of accrued fines using standard library math functions
        sum_fines = sum([loan["fines_accrued"] for loan in self.storage.loans])
        print(f"Total Accrued System Fines: ${sum_fines:.2f}")
        
        if sum_fines > 0:
            ceiled, risk, metric = analyze_fines_and_risks(sum_fines)
            print(f"System Fine Risks Ceiled Valuation: ${ceiled:.2f}")
            print(f"System Fine logarithmic Metric: {metric}")
            print(f"System Operational Assessment: \033[91m{risk}\033[0m")
        else:
            print("System Operational Assessment: \033[92mHEALTHY - ZERO OUTSTANDING FINES\033[0m")
        print("============================================\n")

    def seed_defaults(self):
        """Seeds default objects if database files are empty."""
        print("Seeding default data records...")
        
        # Seed Students
        if not self.storage.students:
            self.storage.students["STU001"] = Student("Alice Smith", "alice@school.edu", "STU001", "Computer Science")
            self.storage.students["STU002"] = Student("Bob Jones", "bob@school.edu", "STU002", "Physics")
            self.storage.students["STU003"] = Student("Charlie Brown", "charlie@school.edu", "STU003", "Music")
            self.storage.students["STU004"] = Student("Evan Wright", "evan@school.edu", "STU004", "Chemistry", "Suspended")
            self.storage.save_students()
            
        # Seed Items
        if not self.storage.inventory:
            self.storage.inventory["INV101"] = ElectronicItem("INV101", "Dell Latitude Laptop", "Laptops", 850.00, 5, 4, (0, 0), "Dell", "Latitude", 1.8, "SN-DELL-8821", 12)
            self.storage.inventory["INV102"] = ElectronicItem("INV102", "Lenovo ThinkPad", "Laptops", 1200.00, 2, 1, (0, 1), "Lenovo", "ThinkPad", 1.5, "SN-LENO-4921", 24)
            self.storage.inventory["INV103"] = InventoryItem("INV103", "Physics Lab Kit", "Equipment", 45.00, 10, 10, (1, 0), "ScienceCo", "PhyKit", 3.0)
            self.storage.inventory["INV104"] = InventoryItem("INV104", "Calculus Textbook", "Textbooks", 110.00, 15, 14, (1, 1), "Pearson", "Calculus 9th", 1.2)
            self.storage.inventory["INV105"] = InventoryItem("INV105", "Violin", "Music", 400.00, 3, 0, (2, 0), "Stradivarius", "V100", 2.2)
            self.storage.save_inventory()
            
        # Seed Loans
        if not self.storage.loans:
            today = datetime.now()
            checkout_1 = (today - timedelta(days=10)).strftime('%Y-%m-%d')
            due_1 = (today + timedelta(days=4)).strftime('%Y-%m-%d')
            
            checkout_2 = (today - timedelta(days=20)).strftime('%Y-%m-%d')
            due_2 = (today - timedelta(days=6)).strftime('%Y-%m-%d') # Overdue by 6 days
            
            self.storage.loans.append({
                "loan_id": 1, "student_id": "STU001", "item_id": "INV101",
                "checkout_date": checkout_1, "due_date": due_1, "return_date": None,
                "status": "Active", "fines_accrued": 0.0
            })
            self.storage.loans.append({
                "loan_id": 2, "student_id": "STU003", "item_id": "INV105",
                "checkout_date": checkout_2, "due_date": due_2, "return_date": None,
                "status": "Overdue", "fines_accrued": 6.00
            })
            self.storage.save_loans()
            
        self.sync_warehouse_layout()
        self.storage.load_all()
        print("Database files seeded and synchronized.")

    def show_quick_stats(self):
        """Displays quick statistics without starting interactive menu."""
        print("EduTrack Dashboard Quick Stats:")
        print(f"  Total Students: {len(self.storage.students)}")
        print(f"  Total Assets registered: {len(self.storage.inventory)}")
        print(f"  Total Transactions recorded: {len(self.storage.loans)}")
        print(f"  Portfolio Value: ${self.storage.get_total_asset_value():.2f}")


# ==========================================
# 4. Standard entry check block
# ==========================================
if __name__ == "__main__":
    # Create the controller CLI class and start it
    cli = EduTrackCLI()
    cli.run()
