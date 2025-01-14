from langflow.custom import Component
from langflow.io import Output
from langflow.schema import Data
from typing import List, Dict
from langflow.inputs import IntInput, StrInput, HandleInput
from langflow.io import Output
from langflow.field_typing import LanguageModel
from langchain.schema import HumanMessage
import json

class CustomComponent(Component):
    display_name = "Custom Component"
    description = "Use as a template to create your own component."
    documentation: str = "http://docs.langflow.org/components/custom"
    icon = "code"
    name = "CustomComponent"
    inputs = [
        StrInput(name="store_theme", display_name="Theme", value="Consumer Electronics"),
        IntInput(name="num_categories", display_name="Categories", value=10),
        IntInput(name="num_products", display_name="Products", value=100),
        IntInput(name="num_users", display_name="Users", value=10),
        HandleInput(name="llm", display_name="Language Model", input_types=["LanguageModel"], info="Connect to a Language Model component"),
    ]
    outputs = [
        Output(name="categories_dataset", display_name="Categories", method="create_categories"),
        Output(name="products_dataset", display_name="Products", method="create_products"),
        Output(name="users_dataset", display_name="Users", method="create_users"),
    ]
    all_categories: List[Data] = []
    all_products: List[Data] = []
    all_users: List[Data] = []  
    def create_categories(self) -> List[Data]:
        top_level_prompt: str = (
            f"Generate a list of '{self.num_categories}' unique, creative, and diverse top-level categories for an online marketplace focused on the theme of '{self.store_theme}'."
            "Give each category a UUID, name, and description. These categories should be specific to the marketplace theme, but general enough to allow subcategories."
            "For each category, create three subcategories. Each with their own UUID, name, and description. Also include the UUID of the parent category."
            "Return the answer in JSON format and strictly adhere to the following JSON schema"
            """
            {
                "id" : "string",
                "name" : "string",
                "description" : "string",
                "subcategories" : [
                    {
                        "id" : "string",
                        "name" : "string",
                        "description" : "string",
                        "parent_id" : "string"
                    }
                ],
                "error" : "string (optional, only if the request cannot be fulfilled)"
            }
            """
            "If you don't know how to answer or have issues, please return an error message in JSON"
        )
        response = self.llm.invoke([HumanMessage(content=top_level_prompt)])
        response_content = response.content
        categories = json.loads(response_content)
        for category in categories:
            name = category.get("name", "")
            description = category.get("description", "")
            self.all_categories.append(Data(
                data={
                    "text": f"{name} {description}",
                    "id": category.get("id"),
                    "name": name,
                    "description": description,
                }
            ))
            subcategories = category.get("subcategories", [])
            for subcategory in subcategories:
                sub_name = subcategory.get("name", "")
                sub_description = subcategory.get("description", "")
                self.all_categories.append(Data(
                    data={
                        "text": f"{sub_name} {sub_description}",
                        "id": subcategory.get("id"),
                        "name": sub_name,
                        "description": sub_description,
                        "parent_id": subcategory.get("parent_id"),
                    }
                ))
        return self.all_categories
    def create_products(self) -> List[Data]:
        if not self.all_categories:
            print("Warning: No categories available. Run create_categories first.")
            return [Data(data={"text": "Error: No categories available", "error": "Categories must be generated first"})]
        category_info = []
        for cat in self.all_categories:
            cat_data = cat.data
            if "parent_id" not in cat_data:
                # This is a main category
                category_info.append(f"Category ID: {cat_data['id']}, Name: {cat_data['name']}")
            else:
                # This is a subcategory
                category_info.append(f"Subcategory ID: {cat_data['id']}, Name: {cat_data['name']}, Parent ID: {cat_data['parent_id']}")

        product_prompt: str = (
            f"Generate a list of {self.num_products} products for an online marketplace focused on {self.store_theme}. "
            "Return a JSON array where each element represents a product. "
            f"Use only the following categories:\n{json.dumps(category_info, indent=2)}\n"
            "The response must be a valid JSON array starting with '[' and ending with ']'. "
            "Each product object in the array must follow this exact schema:"
            """
            [
                {
                    "id": "string",
                    "name": "string",
                    "description": "string",
                    "category_id": "string",
                    "subcategory_id": "string",
                    "price": "number",
                    "specifications": {
                        "weight": "string",
                        "dimensions": "string",
                        "color": "string",
                        "material": "string",
                        "warranty": "string"
                    },
                    "inventory": {
                        "stock_count": "number",
                        "sku": "string",
                        "warehouse_location": "string"
                    },
                    "ratings": {
                        "average_score": "number (1-5)",
                        "review_count": "number"
                    },
                    "shipping_info": {
                        "free_shipping": "boolean",
                        "shipping_weight": "string",
                        "handling_time": "string"
                    }
                }
            ]
            """
            "Do not include any explanatory text, only return the JSON array. "
            "Make sure to use valid JSON syntax with double quotes for all strings. "
            "Use realistic prices and specifications appropriate for each product category."
        )

        try:
            response = self.llm.invoke([HumanMessage(content=product_prompt)])
            response_content = response.content.strip()
            if not response_content.startswith('['):
                start_idx = response_content.find('[')
                if start_idx != -1:
                    response_content = response_content[start_idx:]
            products = json.loads(response_content)
            if not isinstance(products, list):
                raise ValueError("Response is not a list of products")
            for product in products:
                name = product.get("name", "")
                description = product.get("description", "")
                # Verify category exists
                category_id = product.get("category_id", "")
                subcategory_id = product.get("subcategory_id", "")
                self.all_products.append(Data(
                    data={
                        "text": f"Product: {name} - {description}",
                        "id": product.get("id"),
                        "name": name,
                        "description": description,
                        "category_id": category_id,
                        "subcategory_id": subcategory_id,
                        "price": product.get("price"),
                        "specifications": product.get("specifications", {}),
                        "inventory": product.get("inventory", {}),
                        "ratings": product.get("ratings", {}),
                        "shipping_info": product.get("shipping_info", {})
                    }
                ))
            return self.all_products
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {str(e)}")
            return [Data(
                data={
                    "text": "Error generating products",
                    "error": f"Failed to parse JSON response: {str(e)}"
                }
            )]
        except Exception as e:
            print(f"Unexpected Error: {str(e)}")
            return [Data(
                data={
                    "text": "Error generating products",
                    "error": f"Unexpected error: {str(e)}"
                }
            )]
    def create_users(self) -> List[Data]:
        if not self.all_products or not self.all_categories:
            self.log("Warning: No products or categories available. Run create_categories and create_products first.")
            return [Data(data={"text": "Error: Products and categories must be generated first", 
                              "error": "Products and categories must be generated first"})]
        category_info = []
        for cat in self.all_categories:
            cat_data = cat.data
            if "parent_id" not in cat_data:
                category_info.append({
                    "id": cat_data["id"],
                    "name": cat_data["name"]
                })
        product_info = []
        for prod in self.all_products:
            prod_data = prod.data
            product_info.append({
                "id": prod_data["id"],
                "name": prod_data["name"],
                "price": prod_data["price"],
                "category_id": prod_data["category_id"]
            })
        user_prompt: str = (
            f"Generate a list of {self.num_users} realistic user profiles for an online marketplace focused on {self.store_theme}. "
            "Return a JSON array where each element represents a user profile. "
            f"Use only the following products and categories:\n"
            f"Categories:\n{json.dumps(category_info, indent=2)}\n"
            f"Products:\n{json.dumps(product_info[:10], indent=2)}...(more products available)\n"
            "For each user, create a purchase history of 3-5 items from the available products list, "
            "and a list of 2-3 favorite categories from the available categories. "
            "The response must be a valid JSON array starting with '[' and ending with ']'. "
            "Each user object in the array must follow this exact schema:"
            """
            [
                {
                    "id": "string",
                    "name": "string",
                    "email": "string",
                    "join_date": "string (YYYY-MM-DD)",
                    "purchase_history": [
                        {
                            "product_id": "string (must match a product from the provided list)",
                            "purchase_date": "string (YYYY-MM-DD)",
                            "price": "number (use actual price from product list)"
                        }
                    ],
                    "favorite_categories": [
                        {
                            "category_id": "string (must match a category from the provided list)",
                            "name": "string (use actual category name)"
                        }
                    ],
                    "total_spent": "number",
                    "account_status": "string (one of: active, inactive)",
                    "last_login": "string (YYYY-MM-DD)"
                }
            ]
            """
            "Do not include any explanatory text, only return the JSON array. "
            "Make sure to use valid JSON syntax with double quotes for all strings. "
            "Ensure all product_ids and category_ids match the provided lists exactly."
        )
        try:
            response = self.llm.invoke([HumanMessage(content=user_prompt)])
            response_content = response.content.strip()
            if not response_content.startswith('['):
                start_idx = response_content.find('[')
                if start_idx != -1:
                    response_content = response_content[start_idx:]
            users = json.loads(response_content)
            if not isinstance(users, list):
                raise ValueError("Response is not a list of users")
            for user in users:
                name = user.get("name", "")
                email = user.get("email", "")
                purchase_history = user.get("purchase_history", [])
                verified_purchases = []
                for purchase in purchase_history:
                    product_id = purchase.get("product_id")
                    if any(p.data["id"] == product_id for p in self.all_products):
                        verified_purchases.append(purchase)
                favorite_cats = user.get("favorite_categories", [])
                verified_categories = []
                for cat in favorite_cats:
                    category_id = cat.get("category_id")
                    if any(c.data["id"] == category_id for c in self.all_categories):
                        verified_categories.append(cat)
                self.all_users.append(Data(
                    data={
                        "text": f"User Profile: {name} ({email})",
                        "id": user.get("id"),
                        "name": name,
                        "email": email,
                        "join_date": user.get("join_date"),
                        "purchase_history": verified_purchases,
                        "favorite_categories": verified_categories,
                        "total_spent": user.get("total_spent", 0),
                        "account_status": user.get("account_status", "active"),
                        "last_login": user.get("last_login")
                    }
                ))
            return self.all_users
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {str(e)}")
            return [Data(
                data={
                    "text": "Error generating users",
                    "error": f"Failed to parse JSON response: {str(e)}"
                }
            )]
        except Exception as e:
            print(f"Unexpected Error: {str(e)}")
            return [Data(
                data={
                    "text": "Error generating users",
                    "error": f"Unexpected error: {str(e)}"
                }
            )]
