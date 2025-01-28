Generate a list of {unique_categories} unique, creative, and diverse top-level categories for an online marketplace focused on the theme of {store_theme}.
Here is some additional context about the online marketplace with the theme of {store_theme}: {store_description}
Give each category a UUID, name, and description. These categories should be specific to the marketplace theme, but general enough to allow subcategories.
For each category, create three subcategories. Each with their own UUID, name, and description. Also include the UUID of the parent category.
Let your response only be properly formatted JSON. Do not format your response as markdown, or include any other text other than properly formatted JSON.
Do not truncate or shorten your response in any way. It is vital that your response only be valid JSON
Return the answer in JSON format and strictly adhere to the following JSON schema. The response must be a valid JSON array starting with '[' and ending with ']'
Please do not nest subcategories within the top level category. Each category should be its own JSON object.
```
"metadata" : "string",
"name" : "string", # this should be the category name
"text" : "string", # this should be the category description and should also include the name of the category
"popularity_score" : "integer"
"is_subcategory" : "boolean"
"parent_id" : "string",
"error" : "string" # optional, only if the request cannot be fulfilled
```
If you don't know how to answer or have issues, please return an error message in JSON.