Generate a list of {product_count} products for an online marketplace focused on {store_theme}
Let your response only be properly formatted JSON. Do not format your response as markdown, or include any other text other than properly formatted JSON.
Do not truncate or shorten your response in any way. It is vital that your response only be valid JSON
Return the answer in JSON format and strictly adhere to the following JSON schema. The response must be a valid JSON array starting with '[' and ending with ']'
Each product object in the array must follow this exact schema:
[
"metadata": "string", # UUID for the product
"name": "string",
"text": "string", # Brief description of the product, and should also include the product name
"category_name": "string",
"category_id": "string",
"subcategory_name": "string",
"subcategory_id": "string",
"price": "float", # in US dollars
"weight": "string", 
"dimensions": "string", # length by width by height
"color": "string",
"material": "string", # Description of the materials used to create the product
"warranty": "string"
"stock_count": "int",
"sku": "string",
"warehouse_location": "string", # City and State in the United States of America
"average_rating": "float", # floating point number on a scale from 0 to 10
"review_count": "int"
"free_shipping": "boolean",
"shipping_weight": "string",
"handling_time": "string"
]
Use only the following categories and subcategories. Subcategories contain "is_subcategory : true" and will contain the "parent_id" of their parent category.