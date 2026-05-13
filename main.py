from fastapi import FastAPI, Query, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

# -----------------------------------
# MENU DATA
# -----------------------------------
menu = [
    {
        "id": 1,
        "name": "Veg Pizza",
        "price": 299,
        "category": "Pizza",
        "is_available": True
    },
    {
        "id": 2,
        "name": "Chicken Burger",
        "price": 199,
        "category": "Burger",
        "is_available": True
    },
    {
        "id": 3,
        "name": "Cold Coffee",
        "price": 149,
        "category": "Drink",
        "is_available": True
    },
    {
        "id": 4,
        "name": "French Fries",
        "price": 99,
        "category": "Snack",
        "is_available": False
    },
    {
        "id": 5,
        "name": "Ice Cream",
        "price": 89,
        "category": "Dessert",
        "is_available": True
    },
    {
        "id": 6,
        "name": "Paneer Wrap",
        "price": 179,
        "category": "Wrap",
        "is_available": True
    }
]

orders = []
cart = []
order_counter = 1


# -----------------------------------
# MODELS
# -----------------------------------
class OrderRequest(BaseModel):
    customer_name: str = Field(min_length=2)
    item_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=20)
    delivery_address: str = Field(min_length=10)
    order_type: str = "delivery"


class NewMenuItem(BaseModel):
    name: str = Field(min_length=2)
    price: int = Field(gt=0)
    category: str = Field(min_length=2)
    is_available: bool = True


class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str


# -----------------------------------
# HELPER FUNCTIONS
# -----------------------------------
def find_menu_item(item_id):

    for item in menu:
        if item["id"] == item_id:
            return item

    return None


def calculate_bill(price, quantity, order_type="delivery"):

    total = price * quantity

    if order_type == "delivery":
        total += 30

    return total


def filter_menu_logic(category, max_price, is_available):

    result = []

    for item in menu:

        if category is not None and item["category"] != category:
            continue

        if max_price is not None and item["price"] > max_price:
            continue

        if is_available is not None and item["is_available"] != is_available:
            continue

        result.append(item)

    return result


# -----------------------------------
# HOME ROUTE
# -----------------------------------
@app.get("/")
def home():

    return {
        "message": "Welcome to QuickBite Food Service"
    }


# -----------------------------------
# GET MENU
# -----------------------------------
@app.get("/menu")
def get_menu():

    return {
        "total_items": len(menu),
        "menu": menu
    }


# -----------------------------------
# MENU SUMMARY
# -----------------------------------
@app.get("/menu/summary")
def menu_summary():

    available = sum(
        1 for item in menu
        if item["is_available"]
    )

    unavailable = len(menu) - available

    categories = list(
        set(item["category"] for item in menu)
    )

    return {
        "total_items": len(menu),
        "available_items": available,
        "unavailable_items": unavailable,
        "categories": categories
    }


# -----------------------------------
# GET ORDERS
# -----------------------------------
@app.get("/orders")
def get_orders():

    return {
        "total_orders": len(orders),
        "orders": orders
    }


# -----------------------------------
# FILTER MENU
# -----------------------------------
@app.get("/menu/filter")
def filter_menu(
    category: Optional[str] = None,
    max_price: Optional[int] = None,
    is_available: Optional[bool] = None
):

    result = filter_menu_logic(
        category,
        max_price,
        is_available
    )

    return {
        "count": len(result),
        "items": result
    }


# -----------------------------------
# SEARCH MENU
# -----------------------------------
@app.get("/menu/search")
def search_menu(keyword: str):

    result = [
        item for item in menu
        if keyword.lower() in item["name"].lower()
        or keyword.lower() in item["category"].lower()
    ]

    if not result:
        return {
            "message": "No food items found"
        }

    return {
        "total_found": len(result),
        "items": result
    }


# -----------------------------------
# SORT MENU
# -----------------------------------
@app.get("/menu/sort")
def sort_menu(
    sort_by: str = "price",
    order: str = "asc"
):

    if sort_by not in ["price", "name", "category"]:

        raise HTTPException(
            status_code=400,
            detail="Invalid sorting field"
        )

    reverse = order == "desc"

    sorted_menu = sorted(
        menu,
        key=lambda x: x[sort_by],
        reverse=reverse
    )

    return {
        "sorted_by": sort_by,
        "order": order,
        "items": sorted_menu
    }


# -----------------------------------
# PAGINATION
# -----------------------------------
@app.get("/menu/page")
def paginate_menu(
    page: int = 1,
    limit: int = 3
):

    start = (page - 1) * limit

    data = menu[start:start + limit]

    total_pages = (len(menu) + limit - 1) // limit

    return {
        "page": page,
        "limit": limit,
        "total_items": len(menu),
        "total_pages": total_pages,
        "items": data
    }


# -----------------------------------
# COMBINED BROWSE
# -----------------------------------
@app.get("/menu/browse")
def browse_menu(
    keyword: Optional[str] = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 4
):

    data = menu

    # Search
    if keyword:
        data = [
            item for item in data
            if keyword.lower() in item["name"].lower()
        ]

    # Sort
    reverse = order == "desc"

    data = sorted(
        data,
        key=lambda x: x[sort_by],
        reverse=reverse
    )

    # Pagination
    start = (page - 1) * limit

    paginated = data[start:start + limit]

    return {
        "total_items": len(data),
        "page": page,
        "items": paginated
    }


# -----------------------------------
# ADD MENU ITEM
# -----------------------------------
@app.post("/menu", status_code=201)
def add_item(item: NewMenuItem):

    for menu_item in menu:

        if menu_item["name"].lower() == item.name.lower():

            raise HTTPException(
                status_code=400,
                detail="Food item already exists"
            )

    new_item = item.dict()

    new_item["id"] = len(menu) + 1

    menu.append(new_item)

    return new_item


# -----------------------------------
# UPDATE MENU ITEM
# -----------------------------------
@app.put("/menu/{item_id}")
def update_item(
    item_id: int,
    price: Optional[int] = None,
    is_available: Optional[bool] = None
):

    item = find_menu_item(item_id)

    if not item:

        raise HTTPException(
            status_code=404,
            detail="Food item not found"
        )

    if price is not None:
        item["price"] = price

    if is_available is not None:
        item["is_available"] = is_available

    return item


# -----------------------------------
# DELETE MENU ITEM
# -----------------------------------
@app.delete("/menu/{item_id}")
def delete_item(item_id: int):

    item = find_menu_item(item_id)

    if not item:

        raise HTTPException(
            status_code=404,
            detail="Food item not found"
        )

    menu.remove(item)

    return {
        "message": "Food item deleted successfully",
        "deleted_item": item["name"]
    }


# -----------------------------------
# ADD TO CART
# -----------------------------------
@app.post("/cart/add")
def add_to_cart(
    item_id: int,
    quantity: int = 1
):

    item = find_menu_item(item_id)

    if not item or not item["is_available"]:

        raise HTTPException(
            status_code=400,
            detail="Food item not available"
        )

    for cart_item in cart:

        if cart_item["item_id"] == item_id:

            cart_item["quantity"] += quantity

            return {
                "message": "Cart updated successfully",
                "cart": cart
            }

    cart.append({
        "item_id": item_id,
        "quantity": quantity
    })

    return {
        "message": "Item added to cart",
        "cart": cart
    }


# -----------------------------------
# VIEW CART
# -----------------------------------
@app.get("/cart")
def view_cart():

    total = 0

    detailed_cart = []

    for cart_item in cart:

        item = find_menu_item(cart_item["item_id"])

        bill = item["price"] * cart_item["quantity"]

        total += bill

        detailed_cart.append({
            "name": item["name"],
            "quantity": cart_item["quantity"],
            "total_price": bill
        })

    return {
        "cart_items": detailed_cart,
        "grand_total": total
    }


# -----------------------------------
# REMOVE CART ITEM
# -----------------------------------
@app.delete("/cart/{item_id}")
def remove_cart(item_id: int):

    for cart_item in cart:

        if cart_item["item_id"] == item_id:

            cart.remove(cart_item)

            return {
                "message": "Item removed from cart"
            }

    raise HTTPException(
        status_code=404,
        detail="Item not found in cart"
    )


# -----------------------------------
# CHECKOUT
# -----------------------------------
@app.post("/cart/checkout", status_code=201)
def checkout(data: CheckoutRequest):

    global order_counter

    if not cart:

        raise HTTPException(
            status_code=400,
            detail="Cart is empty"
        )

    placed_orders = []

    total = 0

    for cart_item in cart:

        item = find_menu_item(cart_item["item_id"])

        bill = item["price"] * cart_item["quantity"]

        order = {
            "order_id": order_counter,
            "customer_name": data.customer_name,
            "food_item": item["name"],
            "quantity": cart_item["quantity"],
            "total_bill": bill,
            "delivery_address": data.delivery_address
        }

        orders.append(order)

        placed_orders.append(order)

        total += bill

        order_counter += 1

    cart.clear()

    return {
        "message": "Order placed successfully",
        "orders": placed_orders,
        "grand_total": total
    }


# -----------------------------------
# GET ITEM BY ID
# -----------------------------------
@app.get("/menu/{item_id}")
def get_item(item_id: int):

    item = find_menu_item(item_id)

    if not item:

        raise HTTPException(
            status_code=404,
            detail="Food item not found"
        )

    return item
