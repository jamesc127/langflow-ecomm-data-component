from langflow.custom import Component
from langflow.io import Output
from langflow.schema import Data
from langflow.logging import logger
from langflow.inputs import IntInput, StrInput, HandleInput
from langflow.io import Output
from langchain.schema import HumanMessage
from typing import List, Dict
import json
import re


class CustomComponent(Component):
    display_name = "eComm Data Generator"
    description = "Use as a template to create your own component."
    documentation: str = "http://docs.langflow.org/components/custom"
    icon = "code"
    name = "ecomm-data-generator"
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
    llog = logger
    all_categories: List[Data] = []
    all_products: List[Data] = []
    all_users: List[Data] = []
    def generate_category_prompt(self) -> str:
        return (
            f"Generate a list of '{self.num_categories}' unique, creative, and diverse top-level categories for an online marketplace focused on the theme of '{self.store_theme}'."
            "Give each category a UUID, name, and description. These categories should be specific to the marketplace theme, but general enough to allow subcategories."
            "For each category, create three subcategories. Each with their own UUID, name, and description. Also include the UUID of the parent category."
            "Do not format your response as markdown, or include any other text other than properly formatted JSON."
            "Do not truncate or shorten your response in any way. It is vital that your response only be valid JSON"
            "Return the answer in JSON format and strictly adhere to the following JSON schema. The response must be a valid JSON array starting with '[' and ending with ']'"
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
    def generate_products_prompt(self, category_info: List[Dict]) -> str:
        return (
            f"Generate a list of {self.num_products} products for an online marketplace focused on {self.store_theme}. "
            "Return a JSON array where each element represents a product. "
            f"Use only the following categories:\n{json.dumps(category_info, indent=2)}\n"
            "The response must be a valid JSON array starting with '[' and ending with ']'. Do not format your response as markdown, or include any other text other than properly formatted JSON."
            "Do not truncate or shorten your response in any way. It is vital that your response only be valid JSON"
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
        )
    def generate_users_prompt(self, category_info: List[Dict], product_info: List[Dict]) -> str:
        return (
            f"Generate a list of {self.num_users} realistic user profiles for an online marketplace "
            f"focused on {self.store_theme}. "
            "Return a JSON array where each element represents a user profile. "
            f"Use only the following products and categories:\n"
            f"Categories:\n{json.dumps(category_info, indent=2)}\n"
            f"Products:\n{json.dumps(product_info[:10], indent=2)}...(more products available)\n"
            "For each user, create a purchase history of 3-5 items from the available products list, "
            "and a list of 2-3 favorite categories from the available categories. "
            "The response must be a valid JSON array starting with '[' and ending with ']'. Do not format your response as markdown, or include any other text other than properly formatted JSON."
            "Do not truncate or shorten your response in any way. It is vital that your response only be valid JSON"
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
        )
    def validate_llm_response(self,response_content: str, context: str = "") -> tuple[bool, str]:
        """
        Validates LLM response content and ensures it's properly formatted JSON
        Returns: (is_valid: bool, cleaned_content: str)
        """
        try:
            # Log raw response for debugging
            self.llog.debug(f"Raw LLM response for {context}: {response_content[:500]}...")            
            # Clean and validate response
            cleaned_content = response_content.strip()
            if not cleaned_content.startswith('['):
                self.llog.warning(f"Response for {context} doesn't start with '[', attempting to extract JSON")
                start_idx = cleaned_content.find('[')
                if start_idx == -1:
                    self.llog.error(f"No JSON array found in response for {context}")
                    return False, cleaned_content
                cleaned_content = cleaned_content[start_idx:]
                self.llog.info(f"Extracted JSON content for {context}: {cleaned_content[:500]}...")
            # Validate JSON structure
            json.loads(cleaned_content)  # This will raise JSONDecodeError if invalid
            return True, cleaned_content
        except json.JSONDecodeError as e:
            self.llog.error(f"Invalid JSON in {context} at position {e.pos}: {e.msg}")
            self.llog.error(f"Problematic content: {response_content[max(0, e.pos-50):min(len(response_content), e.pos+50)]}")
            return False, response_content
        except Exception as e:
            self.llog.error(f"Unexpected error validating {context}: {str(e)}")
            return False, response_content
    def safe_llm_invoke(self, prompt: str, context: str) -> tuple[bool, str]:
        """
        Safely invokes LLM and handles response
        Returns: (success: bool, content: str)
        """
        try:
            self.log(f"Sending prompt for {context}")
            response = self.llm.invoke([HumanMessage(content=prompt)])

            if not response or not hasattr(response, 'content'):
                self.llog.error(f"Invalid response object for {context}")
                return False, "Invalid LLM response object"

            is_valid, content = self.validate_llm_response(response.content, context)
            return is_valid, content

        except Exception as e:
            self.log(f"Error invoking LLM for {context}: {str(e)}")
            self.llog.error(f"Error invoking LLM for {context}: {str(e)}")
            return False, str(e)
    def create_categories(self) -> List[Data]:
        success, response_content = self.safe_llm_invoke(
            prompt=self.generate_category_prompt(),
            context="category generation"
        )
        if not success:
            return [Data(data={"text": "Error generating categories", 
                              "error": f"Failed to get valid response: {response_content}"})]
        try:
            categories = json.loads(response_content)
            self.llog.info(f"Successfully generated {len(categories)} categories")
            # Process categories with detailed logging
            for category in categories:
                try:
                    name = category.get("name", "")
                    if not name:
                        self.llog.warning(f"Category missing name: {category}")
                        continue
                    description = category.get("description", "")
                    category_id = category.get("id")
                    if not category_id:
                        self.llog.warning(f"Category missing ID: {category}")
                        continue                   
                    self.all_categories.append(Data(
                        data={
                            "text": f"{name} {description}",
                            "id": category_id,
                            "name": name,
                            "description": description,
                        }
                    ))
                    # Process subcategories
                    subcategories = category.get("subcategories", [])
                    self.llog.debug(f"Processing {len(subcategories)} subcategories for {name}")
                    for subcategory in subcategories:
                        try:
                            sub_name = subcategory.get("name", "")
                            if not sub_name:
                                self.llog.warning(f"Subcategory missing name: {subcategory}")
                                continue
                            sub_id = subcategory.get("id")
                            if not sub_id:
                                self.llog.warning(f"Subcategory missing ID: {subcategory}")
                                continue
                            self.all_categories.append(Data(
                                data={
                                    "text": f"{sub_name} {subcategory.get('description', '')}",
                                    "id": sub_id,
                                    "name": sub_name,
                                    "description": subcategory.get("description", ""),
                                    "parent_id": subcategory.get("parent_id"),
                                }
                            ))
                        except Exception as e:
                            self.llog.error(f"Error processing subcategory: {str(e)}")
                            continue
                except Exception as e:
                    self.llog.error(f"Error processing category: {str(e)}")
                    continue
            self.llog.info(f"Successfully processed {len(self.all_categories)} total categories and subcategories")
            return self.all_categories
        except Exception as e:
            self.llog.error(f"Error processing categories response: {str(e)}")
            return [Data(data={"text": "Error processing categories", 
                              "error": f"Failed to process response: {str(e)}"})]
    def create_products(self) -> List[Data]:
        if not self.all_categories:
            self.llog.error("Attempting to create products without categories")
            return [Data(data={
                "text": "Error: No categories available",
                "error": "Categories must be generated first"
            })]
        try:
            # Prepare category information for prompt
            category_info = []
            for cat in self.all_categories:
                cat_data = cat.data
                try:
                    if "parent_id" not in cat_data:
                        category_info.append(f"Category ID: {cat_data['id']}, Name: {cat_data['name']}")
                    else:
                        category_info.append(
                            f"Subcategory ID: {cat_data['id']}, "
                            f"Name: {cat_data['name']}, "
                            f"Parent ID: {cat_data['parent_id']}"
                        )
                except KeyError as e:
                    self.llog.warning(f"Missing required field in category data: {e}")
                    continue
            self.llog.info(f"Prepared {len(category_info)} categories for product generation")
            # Generate products using LLM
            success, response_content = self.safe_llm_invoke(
                prompt=self.generate_products_prompt(category_info),
                context="product generation"
            )
            if not success:
                return [Data(data={
                    "text": "Error generating products",
                    "error": f"Failed to get valid response: {response_content}"
                })]
            # Process products
            products = json.loads(response_content)
            self.llog.info(f"Successfully generated {len(products)} products")
            for product in products:
                try:
                    # Validate required fields
                    required_fields = ["id", "name", "description", "category_id", "subcategory_id", "price"]
                    missing_fields = [field for field in required_fields if not product.get(field)]
                    if missing_fields:
                        self.llog.warning(f"Product missing required fields {missing_fields}: {product}")
                        continue
                    # Validate category references
                    category_id = product["category_id"]
                    subcategory_id = product["subcategory_id"]
                    if not any(c.data["id"] == category_id for c in self.all_categories):
                        self.llog.warning(f"Product references invalid category_id {category_id}")
                        continue
                    if not any(c.data["id"] == subcategory_id for c in self.all_categories):
                        self.llog.warning(f"Product references invalid subcategory_id {subcategory_id}")
                        continue
                    # Validate numeric fields
                    try:
                        price = float(product["price"])
                        if price <= 0:
                            self.llog.warning(f"Invalid price {price} for product {product['id']}")
                            continue
                    except (ValueError, TypeError):
                        self.llog.warning(f"Invalid price format for product {product['id']}")
                        continue
                    # Add validated product
                    self.all_products.append(Data(
                        data={
                            "text": f"Product: {product['name']} - {product['description']}",
                            "id": product["id"],
                            "name": product["name"],
                            "description": product["description"],
                            "category_id": category_id,
                            "subcategory_id": subcategory_id,
                            "price": price,
                            "specifications": product.get("specifications", {}),
                            "inventory": product.get("inventory", {}),
                            "ratings": product.get("ratings", {}),
                            "shipping_info": product.get("shipping_info", {})
                        }
                    ))
                except Exception as e:
                    self.llog.error(f"Error processing product: {str(e)}")
                    continue
            self.llog.info(f"Successfully processed {len(self.all_products)} products")
            return self.all_products
        except Exception as e:
            self.llog.error(f"Error in create_products: {str(e)}")
            return [Data(data={
                "text": "Error generating products",
                "error": f"Unexpected error: {str(e)}"
            })]
    def create_users(self) -> List[Data]:
        if not self.all_products or not self.all_categories:
            self.llog.error("Attempting to create users without products or categories")
            return [Data(data={
                "text": "Error: Products and categories must be generated first",
                "error": "Products and categories must be generated first"
            })]
        try:
            # Prepare category and product information for prompt
            category_info = []
            product_info = []
            # Process categories
            for cat in self.all_categories:
                try:
                    cat_data = cat.data
                    if "parent_id" not in cat_data:
                        try:
                            category_info.append({
                                "id": cat_data["id"],
                                "name": cat_data["name"]
                            })
                        except (KeyError, TypeError) as e:
                            self.llog.warning(f"Missing or invalid fields in category: {str(e)}")
                            continue
                except Exception as e:
                    self.llog.warning(f"Invalid category data structure: {str(e)}")
                    continue
            # Process products
            for prod in self.all_products:
                try:
                    prod_data = prod.data
                    try:
                        product_info.append({
                            "id": prod_data["id"],
                            "name": prod_data["name"],
                            "price": prod_data["price"],
                            "category_id": prod_data["category_id"]
                        })
                    except (KeyError, TypeError) as e:
                        self.llog.warning(f"Missing or invalid fields in product: {str(e)}")
                        continue
                except Exception as e:
                    self.llog.warning(f"Invalid product data structure: {str(e)}")
                    continue
            self.llog.info(f"Prepared {len(category_info)} categories and {len(product_info)} products for user generation")
            # Generate users using LLM
            success, response_content = self.safe_llm_invoke(
                prompt=self.generate_users_prompt(category_info, product_info),
                context="user generation"
            )
            if not success:
                return [Data(data={
                    "text": "Error generating users",
                    "error": f"Failed to get valid response: {response_content}"
                })]
            # Process users
            users = json.loads(response_content)
            self.llog.info(f"Successfully generated {len(users)} users")
            for user in users:
                try:
                    # Validate required fields
                    required_fields = ["id", "name", "email", "join_date"]
                    missing_fields = [field for field in required_fields if not user.get(field)]
                    if missing_fields:
                        self.llog.warning(f"User missing required fields {missing_fields}: {user}")
                        continue
                    try:
                        # Validate purchase history
                        purchase_history = user.get("purchase_history", [])
                        verified_purchases = []
                        for purchase in purchase_history:
                            try:
                                product_id = purchase.get("product_id")
                                if not product_id or not any(p.data["id"] == product_id for p in self.all_products):
                                    self.llog.warning(f"Invalid product_id in purchase history: {product_id}")
                                    continue
                                verified_purchases.append(purchase)
                            except Exception as e:
                                self.llog.warning(f"Error processing purchase: {str(e)}")
                                continue
                    except Exception as e:
                        self.llog.error(f"Error processing purchase history: {str(e)}")
                        verified_purchases = []
                    try:
                        # Validate favorite categories
                        favorite_cats = user.get("favorite_categories", [])
                        verified_categories = []
                        for cat in favorite_cats:
                            try:
                                category_id = cat.get("category_id")
                                if not category_id or not any(c.data["id"] == category_id for c in self.all_categories):
                                    self.llog.warning(f"Invalid category_id in favorites: {category_id}")
                                    continue
                                verified_categories.append(cat)
                            except Exception as e:
                                self.llog.warning(f"Error processing favorite category: {str(e)}")
                                continue
                    except Exception as e:
                        self.llog.error(f"Error processing favorite categories: {str(e)}")
                        verified_categories = []
                    # Validate date formats
                    for date_field in ["join_date", "last_login"]:
                        date_value = user.get(date_field)
                        if date_value and not re.match(r'^\d{4}-\d{2}-\d{2}', date_value):
                            self.llog.warning(f"Invalid date format for {date_field}: {date_value}")
                            user[date_field] = None
                    # Add validated user
                    self.all_users.append(Data(
                        data={
                            "text": f"User Profile: {user['name']} ({user['email']})",
                            "id": user["id"],
                            "name": user["name"],
                            "email": user["email"],
                            "join_date": user["join_date"],
                            "purchase_history": verified_purchases,
                            "favorite_categories": verified_categories,
                            "total_spent": user.get("total_spent", 0),
                            "account_status": user.get("account_status", "active"),
                            "last_login": user.get("last_login")
                        }
                    ))
                except Exception as e:
                    self.llog.error(f"Error processing user: {str(e)}")
                    continue
            self.llog.info(f"Successfully processed {len(self.all_users)} users")
            return self.all_users
        except Exception as e:
            self.llog.error(f"Error in create_users: {str(e)}")
            return [Data(data={
                "text": "Error generating users",
                "error": f"Unexpected error: {str(e)}"
            })]
