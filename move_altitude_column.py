import sqlite3

# Path to your SQLite database file
db_path = 'db.sqlite3'

def move_column(table_name, column_name, new_position):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Step 1: Get the existing columns in the table
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]

    # Step 2: Reorder columns with the specified column in the new position
    column_names.remove(column_name)
    column_names.insert(new_position, column_name)
    
    # Step 3: Create a new table with the columns in the desired order
    new_columns_with_types = [
        f"{col} {columns[column_names.index(col)][2]}"
        for col in column_names
    ]
    
    cursor.execute(f'''
    CREATE TABLE {table_name}_new (
        {", ".join(new_columns_with_types)}
    )
    ''')

    # Step 4: Copy data from the old table to the new table
    columns_without_types = ", ".join(column_names)
    cursor.execute(f'''
    INSERT INTO {table_name}_new ({columns_without_types})
    SELECT {columns_without_types}
    FROM {table_name};
    ''')

    # Step 5: Drop the old table
    cursor.execute(f"DROP TABLE {table_name}")

    # Step 6: Rename the new table to the original table name
    cursor.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")

    # Commit the transaction and close the connection
    conn.commit()
    conn.close()

    print(f"Column '{column_name}' moved to position {new_position + 1} in '{table_name}' table.")

# Execute the function to move the 'altitude' column after the 'longitude' column
move_column('myapp_event', 'altitude', 6)  # 'longitude' is at position 5 (zero-indexed), so altitude should be at position 6