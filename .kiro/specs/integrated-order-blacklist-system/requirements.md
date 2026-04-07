# Requirements Document

## Introduction

This document specifies the requirements for integrating a comprehensive blacklist detection and order management system into the bakingRecipe application. The system will enable shop owners to upload Excel order files, automatically detect malicious buyers against a blacklist database, manage product-recipe mappings, and calculate material requirements for production batches. The primary goal is to protect the business from fraudulent refund requests while automating the time-consuming and error-prone process of calculating ingredient quantities for production cycles.

## Glossary

- **System**: The integrated order blacklist management system within bakingRecipe
- **Order_Parser**: Component that reads and validates Excel order files
- **Blacklist_Matcher**: Component that performs fuzzy matching between orders and blacklist entries
- **Material_Calculator**: Component that calculates total ingredient requirements for production batches
- **Excel_File**: Order data file with columns: 跟团号, 下单人, 团员备注, 支付时间, 团长备注, 商品, 订单金额, 退款金额, 订单状态, 自提点, 收货人, 联系电话, 详细地址
- **Group_Tour_Number**: Unique identifier (跟团号) representing a single user's orders
- **Production_Batch**: A collection of Group_Tour_Numbers selected for a production cycle
- **Risk_Level**: Classification of blacklist match severity (HIGH, MEDIUM, LOW)
- **Blacklist_Entry**: Record of a malicious buyer with contact information and fraud history
- **Product_Recipe_Mapping**: Association between a product name and its recipe
- **Material_List**: Aggregated ingredient quantities required for production
- **Shop_Owner**: User who manages orders, blacklist, and production planning
- **Malicious_Buyer**: Individual who purchases products and then fraudulently requests refunds (职业打假人)

## Requirements

### Requirement 1: Excel Order File Upload and Parsing

**User Story:** As a Shop_Owner, I want to upload Excel order files, so that I can import order data into the system for processing and analysis.

#### Acceptance Criteria

1. WHEN a Shop_Owner uploads an Excel file, THE Order_Parser SHALL validate that the file contains all required columns: 跟团号, 下单人, 团员备注, 支付时间, 团长备注, 商品, 订单金额, 退款金额, 订单状态, 自提点, 收货人, 联系电话, 详细地址
2. IF the Excel file is missing required columns, THEN THE Order_Parser SHALL return an error message listing the missing columns
3. WHEN the Excel file is valid, THE Order_Parser SHALL extract each row as an order record
4. THE Order_Parser SHALL parse 支付时间 into a DateTime format
5. THE Order_Parser SHALL parse 订单金额 and 退款金额 as decimal values with 2 decimal places
6. WHEN parsing is complete, THE System SHALL store all orders in the database with a batch identifier
7. THE System SHALL associate all orders from one Excel file with a single upload batch timestamp

### Requirement 2: Order Data Storage and Management

**User Story:** As a Shop_Owner, I want orders to be stored with their complete information, so that I can review and manage order history.

#### Acceptance Criteria

1. THE System SHALL store each order with fields: group_tour_number, orderer, member_remarks, payment_time, group_leader_remarks, product, order_amount, refund_amount, order_status, pickup_point, consignee, contact_phone, detailed_address
2. THE System SHALL create an index on group_tour_number for efficient querying
3. THE System SHALL create an index on contact_phone for blacklist matching
4. THE System SHALL create an index on orderer for blacklist matching
5. WHEN an order is stored, THE System SHALL extract the product name from the 商品 column
6. THE System SHALL maintain referential integrity between orders and their upload batch

### Requirement 3: Blacklist Entry Management

**User Story:** As a Shop_Owner, I want to add, modify, and delete blacklist entries, so that I can maintain an accurate list of Malicious_Buyers.

#### Acceptance Criteria

1. WHEN a Shop_Owner creates a Blacklist_Entry, THE System SHALL store: ktt_name, wechat_name, wechat_id, order_name_phone, phone_numbers, order_address1, order_address2, blacklist_reason, risk_level
2. THE System SHALL extract phone numbers from order_name_phone using regex pattern `1[3-9]\d{9}` and store them in phone_numbers as a JSON array
3. WHEN a Shop_Owner updates a Blacklist_Entry, THE System SHALL re-extract phone numbers if order_name_phone is modified
4. WHEN a Shop_Owner deletes a Blacklist_Entry, THE System SHALL remove the entry from the database
5. THE System SHALL create an index on ktt_name for efficient matching
6. THE System SHALL create an index on phone_numbers for efficient matching
7. THE System SHALL assign a unique 10-character identifier to each Blacklist_Entry

### Requirement 4: Automatic Blacklist Detection

**User Story:** As a Shop_Owner, I want orders to be automatically checked against the blacklist, so that I can identify potentially fraudulent orders without manual review.

#### Acceptance Criteria

1. WHEN orders are uploaded, THE Blacklist_Matcher SHALL compare each order against all Blacklist_Entries
2. THE Blacklist_Matcher SHALL perform phone matching with similarity threshold 0.9 and assign Risk_Level HIGH when matched
3. THE Blacklist_Matcher SHALL perform name matching with similarity threshold 0.8 and assign Risk_Level MEDIUM when matched
4. THE Blacklist_Matcher SHALL perform address matching with similarity threshold 0.7 and assign Risk_Level LOW when matched
5. THE Blacklist_Matcher SHALL use SequenceMatcher algorithm to calculate similarity scores
6. WHEN multiple matches are found for one order, THE System SHALL record the highest Risk_Level
7. THE System SHALL store match results in fields: is_blacklist_checked, blacklist_risk_level, blacklist_match_info, blacklist_match_details
8. THE Blacklist_Matcher SHALL normalize names by removing spaces and special characters before comparison
9. THE Blacklist_Matcher SHALL extract phone numbers from contact_phone using regex before comparison

### Requirement 5: Blacklist Detection Results Display

**User Story:** As a Shop_Owner, I want to view which orders matched the blacklist, so that I can review suspicious orders and take appropriate action.

#### Acceptance Criteria

1. THE System SHALL display orders with blacklist matches in a filterable list
2. THE System SHALL show Risk_Level (HIGH/MEDIUM/LOW) for each matched order
3. THE System SHALL display match_details showing which field matched (phone/name/address) and the similarity score
4. THE System SHALL allow filtering orders by Risk_Level
5. THE System SHALL allow filtering orders by is_blacklist_checked status
6. WHEN a Shop_Owner views a matched order, THE System SHALL display the associated Blacklist_Entry details including blacklist_reason

### Requirement 6: Product and Recipe Association

**User Story:** As a Shop_Owner, I want to link products to recipes, so that the system can calculate ingredient requirements for production.

#### Acceptance Criteria

1. THE System SHALL allow Shop_Owner to create Product_Recipe_Mappings
2. WHEN creating a mapping, THE System SHALL validate that the recipe exists in the recipes table
3. THE System SHALL store product_name and recipe_id for each mapping
4. THE System SHALL allow one product to map to exactly one recipe
5. THE System SHALL allow one recipe to be mapped by multiple products
6. WHEN a product name from orders has no mapping, THE System SHALL flag it as unmapped
7. THE System SHALL provide a list of all unique product names from uploaded orders to facilitate mapping creation

### Requirement 7: Production Batch Selection

**User Story:** As a Shop_Owner, I want to select Group_Tour_Numbers for a production cycle, so that I can specify which orders to produce.

#### Acceptance Criteria

1. THE System SHALL display all unique Group_Tour_Numbers from uploaded orders
2. THE System SHALL allow Shop_Owner to select multiple Group_Tour_Numbers for a Production_Batch
3. WHEN a Group_Tour_Number is selected, THE System SHALL include all orders with that Group_Tour_Number in the Production_Batch
4. THE System SHALL display the total number of orders for each Group_Tour_Number
5. THE System SHALL allow Shop_Owner to save a Production_Batch with a name and creation timestamp
6. THE System SHALL prevent duplicate Group_Tour_Numbers within a single Production_Batch

### Requirement 8: Material Requirements Calculation

**User Story:** As a Shop_Owner, I want the system to automatically calculate total ingredient quantities for a Production_Batch, so that I can eliminate manual calculation errors and save time.

#### Acceptance Criteria

1. WHEN a Shop_Owner confirms a Production_Batch, THE Material_Calculator SHALL retrieve all orders in the batch
2. FOR EACH order, THE Material_Calculator SHALL look up the Product_Recipe_Mapping for the order's product
3. IF a product has no mapping, THEN THE Material_Calculator SHALL skip that order and log a warning
4. FOR EACH mapped product, THE Material_Calculator SHALL retrieve the recipe's current version ingredients from recipe_version_ingredients
5. THE Material_Calculator SHALL sum the weight of each ingredient across all orders in the batch
6. THE Material_Calculator SHALL output a Material_List with ingredient_name and total_weight in grams
7. THE Material_Calculator SHALL round total weights to 2 decimal places
8. THE System SHALL display the Material_List grouped by ingredient with total quantities
9. THE System SHALL allow exporting the Material_List to Excel format for procurement

### Requirement 9: Production Batch History

**User Story:** As a Shop_Owner, I want to view historical Production_Batches, so that I can review past material calculations and production records.

#### Acceptance Criteria

1. THE System SHALL store each Production_Batch with: batch_name, creation_timestamp, selected_group_tour_numbers, calculated_material_list
2. THE System SHALL display a list of all Production_Batches ordered by creation_timestamp descending
3. WHEN a Shop_Owner views a historical batch, THE System SHALL display the Material_List that was calculated
4. THE System SHALL display which Group_Tour_Numbers were included in each batch
5. THE System SHALL allow Shop_Owner to recalculate a historical batch with current recipe data

### Requirement 10: Mobile-First User Interface

**User Story:** As a Shop_Owner, I want a mobile-optimized interface, so that I can manage orders and production on my phone.

#### Acceptance Criteria

1. THE System SHALL render all pages with responsive design for mobile screens (320px to 768px width)
2. THE System SHALL use touch-friendly controls with minimum tap target size of 44x44 pixels
3. THE System SHALL display data tables with horizontal scrolling on mobile devices
4. THE System SHALL use mobile-optimized file upload controls for Excel files
5. THE System SHALL display blacklist match results in a card-based layout on mobile
6. THE System SHALL provide swipe gestures for navigating between order details on mobile

### Requirement 11: Excel Order File Format Validation

**User Story:** As a Shop_Owner, I want clear error messages when my Excel file format is incorrect, so that I can fix issues and successfully upload orders.

#### Acceptance Criteria

1. WHEN the Order_Parser detects invalid data types, THE System SHALL return an error message specifying the row number and column name
2. IF 订单金额 or 退款金额 cannot be parsed as numbers, THEN THE System SHALL return an error with the problematic value
3. IF 支付时间 cannot be parsed as a date, THEN THE System SHALL return an error with the problematic value
4. THE System SHALL validate that 联系电话 matches the pattern `1[3-9]\d{9}` or is empty
5. IF validation fails, THEN THE System SHALL not store any orders from that file
6. THE System SHALL provide a summary of all validation errors before rejecting the file

### Requirement 12: Blacklist Matching Performance

**User Story:** As a Shop_Owner, I want blacklist checking to complete quickly, so that I can review results without long wait times.

#### Acceptance Criteria

1. WHEN checking 100 orders against 100 Blacklist_Entries, THE Blacklist_Matcher SHALL complete within 10 seconds
2. THE System SHALL use database indexes on ktt_name, phone_numbers, and contact_phone to optimize queries
3. THE Blacklist_Matcher SHALL process orders in batches of 50 for large uploads
4. THE System SHALL display a progress indicator during blacklist checking
5. WHEN blacklist checking is complete, THE System SHALL notify the Shop_Owner

### Requirement 13: Data Migration from BlackNameList

**User Story:** As a Shop_Owner, I want to import existing blacklist data from the old BlackNameList system, so that I can preserve historical fraud records.

#### Acceptance Criteria

1. THE System SHALL provide a migration script that reads from the BlackNameList MySQL database
2. THE System SHALL map BlackNameList.blacklist table fields to the new blacklist schema
3. THE System SHALL preserve phone_numbers as JSON arrays during migration
4. THE System SHALL preserve risk_level values during migration
5. THE System SHALL log any records that fail to migrate with error details
6. WHEN migration is complete, THE System SHALL report the count of successfully migrated records

### Requirement 14: Order Status Management

**User Story:** As a Shop_Owner, I want to update order statuses, so that I can track order fulfillment progress.

#### Acceptance Criteria

1. THE System SHALL support order statuses: PENDING, PAID, SHIPPED, DELIVERED, CANCELLED, REFUNDED
2. WHEN a Shop_Owner updates an order status, THE System SHALL validate that the new status is in the allowed list
3. THE System SHALL record the timestamp of each status change
4. THE System SHALL allow filtering orders by order_status
5. WHEN an order status is changed to REFUNDED, THE System SHALL highlight it for blacklist review

### Requirement 15: Ingredient Master Data Management

**User Story:** As a Shop_Owner, I want to manage ingredient information, so that recipes reference accurate ingredient data.

#### Acceptance Criteria

1. THE System SHALL allow Shop_Owner to create ingredients with: name, unit, calories_per_100g, protein_per_100g, fat_per_100g, carbs_per_100g
2. THE System SHALL enforce unique ingredient names
3. THE System SHALL default unit to 'g' (grams) when not specified
4. WHEN an ingredient is deleted, THE System SHALL prevent deletion if it is referenced by any recipe
5. THE System SHALL allow updating ingredient nutritional information without affecting existing recipes

