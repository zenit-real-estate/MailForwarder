import re
import json

def parse_price(price_str):
    """Convert a price string like '580’000 CHF' into an integer (e.g., 580000)."""
    cleaned_price = re.sub(r"[^\d]", "", price_str)
    return int(cleaned_price) if cleaned_price else 0

def format_price(price_int):
    """Convert an integer price into the Swiss format '580’000 CHF'."""
    return f"{price_int:,.0f}".replace(",", "’") + " CHF"

class MiogestObject:
    def __init__(self, code: str, locality: str, owner: str, price: str, for_rent: bool, 
                 requests_count: int = 0, sellers=None, acquirers=None):
        """
        Initialize a MiogestObject.

        :param code: Unique code of the object (e.g., A000685)
        :param locality: Address or locality of the object
        :param owner: Name of the owner
        :param price: Price (either as a string or integer)
        :param for_rent: Boolean indicating if the object is for rent (True) or for sale (False)
        :param requests_count: Number of requests received for this object
        :param sellers: List of sellers (strings)
        :param acquirers: List of acquirers (strings)
        """
        self.code = code
        self.locality = locality
        self.owner = owner
        self.price = parse_price(price) if isinstance(price, str) else price
        self.for_rent = for_rent
        self.requests_count = requests_count
        self.sellers = sellers if sellers else []
        self.acquirers = acquirers if acquirers else []

    def __str__(self):
        """String representation of the object."""
        rent_status = "For Rent" if self.for_rent else "For Sale"
        return (f"[{self.code}] {self.locality} - Owner: {self.owner}, "
                f"Price: {format_price(self.price)}, Status: {rent_status}, "
                f"Requests: {self.requests_count}, Sellers: {self.sellers}, Acquirers: {self.acquirers}")

    def to_dict(self):
        """Convert the object to a dictionary for JSON storage."""
        return {
            "code": self.code,
            "locality": self.locality,
            "owner": self.owner,
            "price": self.price,
            "for_rent": self.for_rent,
            "requests_count": self.requests_count,
            "sellers": self.sellers,
            "acquirers": self.acquirers
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create a MiogestObject from a dictionary."""
        return cls(
            code=data["code"],
            locality=data["locality"],
            owner=data["owner"],
            price=data["price"],
            for_rent=data["for_rent"],
            requests_count=data.get("requests_count", 0),
            sellers=data.get("sellers", []),
            acquirers=data.get("acquirers", [])
        )