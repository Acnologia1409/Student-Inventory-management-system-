from abc import ABC, abstractmethod
from datetime import datetime

# ==========================================
# 1. Abstraction: Abstract Base Class
# ==========================================
class Asset(ABC):
    def __init__(self, asset_id: str, name: str):
        self.asset_id = asset_id
        self.name = name

    @abstractmethod
    def get_value(self) -> float:
        """Calculate the financial value of the asset."""
        pass

    @abstractmethod
    def display(self) -> None:
        """Display basic details of the asset."""
        pass


# ==========================================
# 2. Mixin: Multiple Inheritance Partner
# ==========================================
class AuditableMixin:
    def __init__(self):
        self.created_at = datetime.now()
        self.last_updated = datetime.now()

    def update_timestamp(self):
        self.last_updated = datetime.now()

    def get_audit_log(self) -> str:
        return f"Created: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')} | Updated: {self.last_updated.strftime('%Y-%m-%d %H:%M:%S')}"


# ==========================================
# 3. Multiple Inheritance & Inner Classes
# ==========================================
class InventoryItem(Asset, AuditableMixin):
    # Inner Class representing technical specifications
    class Specifications:
        def __init__(self, brand: str, model: str, weight: float):
            self.brand = brand
            self.model = model
            self.weight = weight  # Float

        def get_details(self) -> str:
            return f"Brand: {self.brand}, Model: {self.model}, Weight: {self.weight}kg"

    def __init__(self, item_id: str, name: str, category: str, price: float, total_qty: int, available_qty: int, location: tuple, brand: str, model: str, weight: float):
        # Call constructor of abstract base class
        Asset.__init__(self, item_id, name)
        # Call constructor of mixin
        AuditableMixin.__init__(self)
        
        self.category = category
        self.price = price  # Float
        self.total_qty = total_qty  # Integer
        self.available_qty = available_qty  # Integer
        self.location = location  # Tuple coordinate e.g. (row, col)
        
        # Inner Class instantiation
        self.specs = self.Specifications(brand, model, weight)

    # Overriding Abstract Method
    def get_value(self) -> float:
        return self.price * self.total_qty

    # Overriding Abstract Method (Polymorphism)
    def display(self) -> None:
        print(f"[{self.asset_id}] {self.name} | Category: {self.category}")
        print(f"    Stock: {self.available_qty}/{self.total_qty} | Price: ${self.price:.2f} | Location Shelf: Row {self.location[0]}, Col {self.location[1]}")
        print(f"    Specs: {self.specs.get_details()}")
        print(f"    Audit: {self.get_audit_log()}")

    # ==========================================
    # Operator Overloading (Polymorphism)
    # ==========================================
    def __add__(self, quantity: int):
        """Operator overloading (+) to add stock quantity to the item."""
        if not isinstance(quantity, int):
            raise TypeError("Quantity to add must be an integer.")
        self.total_qty += quantity
        self.available_qty += quantity
        self.update_timestamp()
        return self

    def __lt__(self, other) -> bool:
        """Operator overloading (<) to compare items by available quantity."""
        if not isinstance(other, InventoryItem):
            raise TypeError("Comparison must be between InventoryItems.")
        return self.available_qty < other.available_qty

    def __str__(self) -> str:
        return f"InventoryItem({self.asset_id}, {self.name}, Stock={self.available_qty}/{self.total_qty})"


# ==========================================
# 4. Multilevel Inheritance
# ==========================================
class ElectronicItem(InventoryItem):
    def __init__(self, item_id: str, name: str, category: str, price: float, total_qty: int, available_qty: int, location: tuple, brand: str, model: str, weight: float, serial_number: str, warranty_months: int):
        # Call parent constructor using super()
        super().__init__(item_id, name, category, price, total_qty, available_qty, location, brand, model, weight)
        self.serial_number = serial_number
        self.warranty_months = warranty_months  # Integer

    # Method Overriding: customizing display logic for Electronic Items
    def display(self) -> None:
        print(f"[{self.asset_id}] {self.name} (Electronic Asset)")
        print(f"    Serial: {self.serial_number} | Warranty: {self.warranty_months} months")
        print(f"    Stock: {self.available_qty}/{self.total_qty} | Price: ${self.price:.2f} | Shelf: {self.location}")
        print(f"    Specs: {self.specs.get_details()}")
        print(f"    Audit: {self.get_audit_log()}")


# ==========================================
# 5. Single Inheritance
# ==========================================
class Person:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    def display(self) -> None:
        print(f"Name: {self.name} | Email: {self.email}")


class Student(Person):
    def __init__(self, name: str, email: str, student_id: str, department: str, status: str = "Active"):
        # Call parent constructor using super()
        super().__init__(name, email)
        self.student_id = student_id
        self.department = department
        self.status = status  # Active or Suspended
        
        # Complex number demo (as required by basic types - maybe a performance metric)
        self.academic_score_vector = complex(85.0, 90.0) # Real part = exam, Imaginary = project

    # Method Overloading (Using default argument parameters)
    def display(self, show_academic_score: bool = False) -> None:
        status_symbol = "🟢" if self.status == "Active" else "🔴"
        print(f"{status_symbol} [{self.student_id}] {self.name} ({self.department})")
        print(f"    Contact: {self.email} | Status: {self.status}")
        if show_academic_score:
            print(f"    Academic Score Vector: {self.academic_score_vector} (Exams: {self.academic_score_vector.real}, Projects: {self.academic_score_vector.imag})")


# ==========================================
# 6. Duck Typing Demonstration
# ==========================================
def inspect_object(obj) -> None:
    """Demonstrates Duck Typing. As long as obj has a display() method, this runs."""
    if hasattr(obj, "display") and callable(getattr(obj, "display")):
        obj.display()
    else:
        print(f"Object {type(obj).__name__} does not support display interface!")
