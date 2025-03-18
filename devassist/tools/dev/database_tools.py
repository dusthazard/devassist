"""
Database development tools for generating database schemas and queries.
"""

import os
import logging
import json
import re
from typing import Dict, List, Any, Optional, Union

from devassist.tools.base.tool import BaseTool
from devassist.tools.base.tool_result import ToolResult

class SqlGeneratorTool(BaseTool):
    """
    Tool for generating SQL queries and schemas.
    """
    
    name = "sql_generator"
    description = "Generate SQL queries and database schemas"
    parameters = {
        "type": "object",
        "properties": {
            "query_type": {
                "type": "string",
                "description": "Type of SQL query or statement to generate",
                "enum": ["select", "insert", "update", "delete", "create_table", "alter_table", "create_index", "schema"]
            },
            "database_type": {
                "type": "string",
                "description": "Database type for SQL dialect",
                "enum": ["mysql", "postgresql", "sqlite", "sqlserver", "oracle"]
            },
            "table_name": {
                "type": "string",
                "description": "Name of the table to query or modify"
            },
            "columns": {
                "type": "array",
                "description": "Columns to include (for SELECT) or define (for CREATE)",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Column name"
                        },
                        "type": {
                            "type": "string",
                            "description": "Column data type (for CREATE TABLE)"
                        },
                        "constraints": {
                            "type": "array",
                            "description": "Column constraints (for CREATE TABLE)",
                            "items": {
                                "type": "string"
                            }
                        },
                        "value": {
                            "type": "string",
                            "description": "Value for INSERT or UPDATE"
                        }
                    },
                    "required": ["name"]
                }
            },
            "conditions": {
                "type": "string",
                "description": "WHERE clause conditions"
            },
            "description": {
                "type": "string",
                "description": "Description of the query purpose"
            }
        },
        "required": ["query_type", "database_type"]
    }
    
    def execute(self,
                query_type: str,
                database_type: str,
                table_name: Optional[str] = None,
                columns: Optional[List[Dict[str, Any]]] = None,
                conditions: Optional[str] = None,
                description: Optional[str] = None,
                **kwargs) -> Union[Dict[str, Any], ToolResult]:
        """
        Generate SQL queries based on the given specifications.
        
        Args:
            query_type: Type of SQL query to generate.
            database_type: Database type for SQL dialect.
            table_name: Name of the table to query or modify.
            columns: Columns to include or define.
            conditions: WHERE clause conditions.
            description: Description of the query purpose.
            **kwargs: Additional parameters.
            
        Returns:
            The generated SQL query.
        """
        try:
            # Validate inputs
            if query_type not in ["select", "insert", "update", "delete", "create_table", "alter_table", "create_index", "schema"]:
                return ToolResult.error(
                    self.name,
                    f"Invalid query type: {query_type}. Valid types are: select, insert, update, delete, create_table, alter_table, create_index, schema."
                )
            
            if database_type not in ["mysql", "postgresql", "sqlite", "sqlserver", "oracle"]:
                return ToolResult.error(
                    self.name,
                    f"Invalid database type: {database_type}. Valid types are: mysql, postgresql, sqlite, sqlserver, oracle."
                )
            
            # Table name required for most queries
            if query_type != "schema" and not table_name:
                return ToolResult.error(
                    self.name,
                    f"Table name is required for {query_type} queries."
                )
            
            # Generate SQL based on query type
            if query_type == "select":
                sql = self._generate_select(database_type, table_name, columns, conditions)
            elif query_type == "insert":
                sql = self._generate_insert(database_type, table_name, columns)
            elif query_type == "update":
                sql = self._generate_update(database_type, table_name, columns, conditions)
            elif query_type == "delete":
                sql = self._generate_delete(database_type, table_name, conditions)
            elif query_type == "create_table":
                sql = self._generate_create_table(database_type, table_name, columns)
            elif query_type == "alter_table":
                sql = self._generate_alter_table(database_type, table_name, columns)
            elif query_type == "create_index":
                sql = self._generate_create_index(database_type, table_name, columns)
            elif query_type == "schema":
                sql = self._generate_schema(database_type, table_name, columns)
            else:
                return ToolResult.error(
                    self.name,
                    f"Unsupported query type: {query_type}"
                )
            
            return ToolResult.success(
                self.name,
                {
                    "sql": sql,
                    "query_type": query_type,
                    "database_type": database_type,
                    "description": description
                }
            )
            
        except Exception as e:
            logging.error(f"Error generating SQL: {e}")
            return ToolResult.error(self.name, f"Failed to generate SQL: {str(e)}")
    
    def _generate_select(self,
                       database_type: str,
                       table_name: str,
                       columns: Optional[List[Dict[str, Any]]] = None,
                       conditions: Optional[str] = None) -> str:
        """
        Generate a SELECT query.
        
        Args:
            database_type: Database type.
            table_name: Table name.
            columns: Columns to select.
            conditions: WHERE conditions.
            
        Returns:
            The generated SELECT query.
        """
        # Format column names
        if columns and len(columns) > 0:
            column_str = ", ".join([self._format_identifier(c["name"], database_type) for c in columns])
        else:
            column_str = "*"
        
        # Basic query
        sql = f"SELECT {column_str}\nFROM {self._format_identifier(table_name, database_type)}"
        
        # Add conditions if provided
        if conditions:
            sql += f"\nWHERE {conditions}"
        
        sql += ";"
        
        return sql
    
    def _generate_insert(self,
                        database_type: str,
                        table_name: str,
                        columns: List[Dict[str, Any]]) -> str:
        """
        Generate an INSERT query.
        
        Args:
            database_type: Database type.
            table_name: Table name.
            columns: Columns and values to insert.
            
        Returns:
            The generated INSERT query.
        """
        if not columns or len(columns) == 0:
            raise ValueError("Columns are required for INSERT statements")
        
        # Format column names and values
        column_names = [self._format_identifier(c["name"], database_type) for c in columns]
        
        # Get values with proper formatting
        values = []
        for col in columns:
            if "value" in col:
                values.append(self._format_value(col["value"], database_type))
            else:
                values.append("NULL")
        
        # Build the INSERT statement
        sql = f"INSERT INTO {self._format_identifier(table_name, database_type)} "
        sql += f"({', '.join(column_names)})\n"
        sql += f"VALUES ({', '.join(values)});"
        
        return sql
    
    def _generate_update(self,
                        database_type: str,
                        table_name: str,
                        columns: List[Dict[str, Any]],
                        conditions: Optional[str] = None) -> str:
        """
        Generate an UPDATE query.
        
        Args:
            database_type: Database type.
            table_name: Table name.
            columns: Columns and values to update.
            conditions: WHERE conditions.
            
        Returns:
            The generated UPDATE query.
        """
        if not columns or len(columns) == 0:
            raise ValueError("Columns are required for UPDATE statements")
        
        # Format column assignments
        assignments = []
        for col in columns:
            if "value" in col:
                column_name = self._format_identifier(col["name"], database_type)
                value = self._format_value(col["value"], database_type)
                assignments.append(f"{column_name} = {value}")
        
        if not assignments:
            raise ValueError("At least one column must have a value for UPDATE statements")
        
        # Build the UPDATE statement
        sql = f"UPDATE {self._format_identifier(table_name, database_type)}\n"
        sql += f"SET {', '.join(assignments)}"
        
        # Add conditions if provided
        if conditions:
            sql += f"\nWHERE {conditions}"
        else:
            # Warning about unconditional update
            sql += "\n/* WARNING: This UPDATE has no WHERE clause and will update ALL rows */\n"
        
        sql += ";"
        
        return sql
    
    def _generate_delete(self,
                        database_type: str,
                        table_name: str,
                        conditions: Optional[str] = None) -> str:
        """
        Generate a DELETE query.
        
        Args:
            database_type: Database type.
            table_name: Table name.
            conditions: WHERE conditions.
            
        Returns:
            The generated DELETE query.
        """
        # Build the DELETE statement
        sql = f"DELETE FROM {self._format_identifier(table_name, database_type)}"
        
        # Add conditions if provided
        if conditions:
            sql += f"\nWHERE {conditions}"
        else:
            # Warning about unconditional delete
            sql += "\n/* WARNING: This DELETE has no WHERE clause and will delete ALL rows */\n"
        
        sql += ";"
        
        return sql
    
    def _generate_create_table(self,
                              database_type: str,
                              table_name: str,
                              columns: List[Dict[str, Any]]) -> str:
        """
        Generate a CREATE TABLE statement.
        
        Args:
            database_type: Database type.
            table_name: Table name.
            columns: Column definitions.
            
        Returns:
            The generated CREATE TABLE statement.
        """
        if not columns or len(columns) == 0:
            raise ValueError("Columns are required for CREATE TABLE statements")
        
        # Start the CREATE TABLE statement
        sql = f"CREATE TABLE {self._format_identifier(table_name, database_type)} (\n"
        
        # Add column definitions
        column_defs = []
        primary_keys = []
        
        for col in columns:
            col_name = self._format_identifier(col["name"], database_type)
            
            # Get column type with database-specific mapping
            col_type = self._map_column_type(col.get("type", "VARCHAR"), database_type)
            
            # Start the column definition
            col_def = f"    {col_name} {col_type}"
            
            # Add constraints if provided
            constraints = col.get("constraints", [])
            
            # Process constraints
            for constraint in constraints:
                constraint = constraint.upper()
                
                # Handle primary key constraint specially
                if constraint == "PRIMARY KEY":
                    primary_keys.append(col["name"])
                else:
                    col_def += f" {constraint}"
            
            column_defs.append(col_def)
        
        # Add primary key constraint if any
        if primary_keys:
            pk_constraint = f"    PRIMARY KEY ({', '.join([self._format_identifier(pk, database_type) for pk in primary_keys])})"
            column_defs.append(pk_constraint)
        
        # Combine all column definitions
        sql += ",\n".join(column_defs)
        
        # Close the CREATE TABLE statement
        sql += "\n);"
        
        return sql
    
    def _generate_alter_table(self,
                             database_type: str,
                             table_name: str,
                             columns: List[Dict[str, Any]]) -> str:
        """
        Generate an ALTER TABLE statement.
        
        Args:
            database_type: Database type.
            table_name: Table name.
            columns: Column operations.
            
        Returns:
            The generated ALTER TABLE statement.
        """
        if not columns or len(columns) == 0:
            raise ValueError("Column operations are required for ALTER TABLE statements")
        
        # Start the ALTER TABLE statement
        sql = f"ALTER TABLE {self._format_identifier(table_name, database_type)}\n"
        
        # Process column operations
        operations = []
        for col in columns:
            operation = col.get("operation", "ADD").upper()
            col_name = self._format_identifier(col["name"], database_type)
            
            if operation == "ADD":
                col_type = self._map_column_type(col.get("type", "VARCHAR"), database_type)
                operation_sql = f"ADD COLUMN {col_name} {col_type}"
                
                # Add constraints if provided
                constraints = col.get("constraints", [])
                for constraint in constraints:
                    operation_sql += f" {constraint}"
                    
            elif operation == "DROP":
                operation_sql = f"DROP COLUMN {col_name}"
                
            elif operation == "MODIFY" or operation == "ALTER COLUMN":
                # Use different syntax depending on database type
                if database_type == "mysql":
                    operation_sql = f"MODIFY COLUMN {col_name}"
                elif database_type in ["postgresql", "sqlite"]:
                    operation_sql = f"ALTER COLUMN {col_name}"
                elif database_type == "sqlserver":
                    operation_sql = f"ALTER COLUMN {col_name}"
                elif database_type == "oracle":
                    operation_sql = f"MODIFY {col_name}"
                else:
                    operation_sql = f"MODIFY COLUMN {col_name}"
                
                # Add type if provided
                if "type" in col:
                    col_type = self._map_column_type(col["type"], database_type)
                    operation_sql += f" {col_type}"
                    
                # Add constraints if provided
                constraints = col.get("constraints", [])
                for constraint in constraints:
                    operation_sql += f" {constraint}"
                    
            elif operation == "RENAME":
                # Use different syntax depending on database type
                new_name = self._format_identifier(col.get("new_name", ""), database_type)
                if database_type == "mysql" or database_type == "sqlserver":
                    operation_sql = f"RENAME COLUMN {col_name} TO {new_name}"
                elif database_type == "postgresql" or database_type == "sqlite":
                    operation_sql = f"RENAME COLUMN {col_name} TO {new_name}"
                elif database_type == "oracle":
                    operation_sql = f"RENAME COLUMN {col_name} TO {new_name}"
                else:
                    operation_sql = f"RENAME COLUMN {col_name} TO {new_name}"
            else:
                # Unknown operation
                operation_sql = f"/* Unsupported operation: {operation} */"
                
            operations.append(operation_sql)
        
        # Combine all operations with appropriate separator
        if database_type in ["mysql", "postgresql", "sqlserver", "oracle"]:
            sql += ",\n".join(operations)
        else:
            # SQLite requires separate ALTER TABLE statements
            sql = "\n".join([f"ALTER TABLE {self._format_identifier(table_name, database_type)} {op};" for op in operations])
            return sql  # Return early for SQLite
        
        # Close the ALTER TABLE statement
        sql += ";"
        
        return sql
    
    def _generate_create_index(self,
                              database_type: str,
                              table_name: str,
                              columns: List[Dict[str, Any]]) -> str:
        """
        Generate a CREATE INDEX statement.
        
        Args:
            database_type: Database type.
            table_name: Table name.
            columns: Columns to include in the index.
            
        Returns:
            The generated CREATE INDEX statement.
        """
        if not columns or len(columns) == 0:
            raise ValueError("Columns are required for CREATE INDEX statements")
        
        # Extract index properties
        index_name = f"idx_{table_name}_" + "_".join([c["name"] for c in columns])
        is_unique = any(c.get("unique", False) for c in columns)
        
        # Start the CREATE INDEX statement
        if is_unique:
            sql = f"CREATE UNIQUE INDEX {self._format_identifier(index_name, database_type)}\n"
        else:
            sql = f"CREATE INDEX {self._format_identifier(index_name, database_type)}\n"
        
        sql += f"ON {self._format_identifier(table_name, database_type)} "
        
        # Add columns
        column_names = [self._format_identifier(c["name"], database_type) for c in columns]
        sql += f"({', '.join(column_names)});"
        
        return sql
    
    def _generate_schema(self,
                        database_type: str,
                        table_name: Optional[str] = None,
                        tables: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Generate a complete database schema.
        
        Args:
            database_type: Database type.
            table_name: Optional table name filter.
            tables: Table definitions.
            
        Returns:
            The generated schema.
        """
        if not tables or len(tables) == 0:
            raise ValueError("Table definitions are required for schema generation")
        
        # Build schema
        sql = "-- Generated Database Schema\n\n"
        
        for table in tables:
            table_name = table["name"]
            columns = table.get("columns", [])
            primary_keys = [c["name"] for c in columns if "primary_key" in c.get("constraints", [])]
            foreign_keys = table.get("foreign_keys", [])
            
            # Create table
            sql += f"-- Table: {table_name}\n"
            sql += self._generate_create_table(database_type, table_name, columns)
            sql += "\n\n"
            
            # Add foreign key constraints
            if foreign_keys:
                sql += f"-- Foreign Keys for {table_name}\n"
                for fk in foreign_keys:
                    fk_table = fk["references_table"]
                    fk_column = fk["column"]
                    fk_references_column = fk.get("references_column", "id")
                    
                    fk_sql = f"ALTER TABLE {self._format_identifier(table_name, database_type)}\n"
                    fk_sql += f"ADD CONSTRAINT fk_{table_name}_{fk_column}_{fk_table}\n"
                    fk_sql += f"FOREIGN KEY ({self._format_identifier(fk_column, database_type)})\n"
                    fk_sql += f"REFERENCES {self._format_identifier(fk_table, database_type)} "
                    fk_sql += f"({self._format_identifier(fk_references_column, database_type)});\n\n"
                    
                    sql += fk_sql
        
        return sql
    
    def _format_identifier(self, identifier: str, database_type: str) -> str:
        """
        Format an identifier according to the database type.
        
        Args:
            identifier: The identifier to format.
            database_type: The database type.
            
        Returns:
            The formatted identifier.
        """
        if not identifier:
            return '""'
        
        # Use appropriate quoting based on database type
        if database_type == "mysql":
            return f"`{identifier}`"
        elif database_type == "postgresql" or database_type == "sqlite":
            return f'"{identifier}"'
        elif database_type == "sqlserver":
            return f"[{identifier}]"
        elif database_type == "oracle":
            return f'"{identifier}"'
        else:
            return identifier
    
    def _format_value(self, value: str, database_type: str) -> str:
        """
        Format a value with improved SQL injection protection.
        """
        if value is None:
            return "NULL"
        
        # Handle numeric values
        if isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '', 1).isdigit()):
            return str(value)
        
        # Handle special values
        if value.upper() == "NULL":
            return "NULL"
        elif value.upper() == "TRUE":
            return "TRUE" if database_type in ["postgresql"] else "1"
        elif value.upper() == "FALSE":
            return "FALSE" if database_type in ["postgresql"] else "0"
        elif value.upper() in ["CURRENT_TIMESTAMP", "NOW()"]:
            # Handle timestamp functions for each database
            timestamp_funcs = {
                "mysql": "NOW()",
                "postgresql": "CURRENT_TIMESTAMP",
                "sqlite": "CURRENT_TIMESTAMP",
                "sqlserver": "GETDATE()",
                "oracle": "SYSDATE"
            }
            return timestamp_funcs.get(database_type, "CURRENT_TIMESTAMP")
        
        # Default: properly escape string values for all database types
        # Double single quotes for SQL escape
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    
    def _map_column_type(self, column_type: str, database_type: str) -> str:
        """
        Map a generic column type to a database-specific type.
        
        Args:
            column_type: The generic column type.
            database_type: The database type.
            
        Returns:
            The database-specific column type.
        """
        # Uppercase the column type
        column_type = column_type.upper()
        
        # Type mappings
        type_mappings = {
            "mysql": {
                "STRING": "VARCHAR(255)",
                "TEXT": "TEXT",
                "INTEGER": "INT",
                "FLOAT": "FLOAT",
                "DECIMAL": "DECIMAL(10,2)",
                "BOOLEAN": "TINYINT(1)",
                "DATE": "DATE",
                "DATETIME": "DATETIME",
                "TIMESTAMP": "TIMESTAMP",
                "BINARY": "BLOB"
            },
            "postgresql": {
                "STRING": "VARCHAR(255)",
                "TEXT": "TEXT",
                "INTEGER": "INTEGER",
                "FLOAT": "REAL",
                "DECIMAL": "DECIMAL(10,2)",
                "BOOLEAN": "BOOLEAN",
                "DATE": "DATE",
                "DATETIME": "TIMESTAMP",
                "TIMESTAMP": "TIMESTAMP",
                "BINARY": "BYTEA"
            },
            "sqlite": {
                "STRING": "TEXT",
                "TEXT": "TEXT",
                "INTEGER": "INTEGER",
                "FLOAT": "REAL",
                "DECIMAL": "REAL",
                "BOOLEAN": "INTEGER",
                "DATE": "TEXT",
                "DATETIME": "TEXT",
                "TIMESTAMP": "TEXT",
                "BINARY": "BLOB"
            },
            "sqlserver": {
                "STRING": "NVARCHAR(255)",
                "TEXT": "NVARCHAR(MAX)",
                "INTEGER": "INT",
                "FLOAT": "FLOAT",
                "DECIMAL": "DECIMAL(10,2)",
                "BOOLEAN": "BIT",
                "DATE": "DATE",
                "DATETIME": "DATETIME",
                "TIMESTAMP": "DATETIME",
                "BINARY": "VARBINARY(MAX)"
            },
            "oracle": {
                "STRING": "VARCHAR2(255)",
                "TEXT": "CLOB",
                "INTEGER": "NUMBER(10)",
                "FLOAT": "FLOAT",
                "DECIMAL": "NUMBER(10,2)",
                "BOOLEAN": "NUMBER(1)",
                "DATE": "DATE",
                "DATETIME": "TIMESTAMP",
                "TIMESTAMP": "TIMESTAMP",
                "BINARY": "BLOB"
            }
        }
        
        # Get type mapping for the specified database
        db_mappings = type_mappings.get(database_type, {})
        
        # Return mapped type or original if no mapping found
        return db_mappings.get(column_type, column_type)


class NoSqlGeneratorTool(BaseTool):
    """
    Tool for generating NoSQL database schemas and queries.
    """
    
    name = "nosql_generator"
    description = "Generate NoSQL database schemas and queries"
    parameters = {
        "type": "object",
        "properties": {
            "database_type": {
                "type": "string",
                "description": "NoSQL database type",
                "enum": ["mongodb", "dynamodb", "firebase", "cosmosdb", "redis"]
            },
            "operation_type": {
                "type": "string",
                "description": "Type of NoSQL operation to generate",
                "enum": ["schema", "query", "insert", "update", "delete", "index"]
            },
            "collection_name": {
                "type": "string",
                "description": "Name of the collection/table/document"
            },
            "schema": {
                "type": "object",
                "description": "Schema definition for the collection"
            },
            "query_filter": {
                "type": "object",
                "description": "Query filter conditions"
            },
            "data": {
                "type": "object",
                "description": "Data for insert or update operations"
            },
            "description": {
                "type": "string",
                "description": "Description of the operation purpose"
            }
        },
        "required": ["database_type", "operation_type"]
    }
    
    def execute(self,
                database_type: str,
                operation_type: str,
                collection_name: Optional[str] = None,
                schema: Optional[Dict[str, Any]] = None,
                query_filter: Optional[Dict[str, Any]] = None,
                data: Optional[Dict[str, Any]] = None,
                description: Optional[str] = None,
                **kwargs) -> Union[Dict[str, Any], ToolResult]:
        """
        Generate NoSQL database operations based on the given specifications.
        
        Args:
            database_type: NoSQL database type.
            operation_type: Type of operation to generate.
            collection_name: Name of the collection/table.
            schema: Schema definition.
            query_filter: Query filter conditions.
            data: Data for insert or update operations.
            description: Description of the operation purpose.
            **kwargs: Additional parameters.
            
        Returns:
            The generated NoSQL operation.
        """
        try:
            # Validate inputs
            if database_type not in ["mongodb", "dynamodb", "firebase", "cosmosdb", "redis"]:
                return ToolResult.error(
                    self.name,
                    f"Invalid database type: {database_type}. Valid types are: mongodb, dynamodb, firebase, cosmosdb, redis."
                )
            
            if operation_type not in ["schema", "query", "insert", "update", "delete", "index"]:
                return ToolResult.error(
                    self.name,
                    f"Invalid operation type: {operation_type}. Valid types are: schema, query, insert, update, delete, index."
                )
            
            # Collection name required for most operations
            if operation_type != "schema" and not collection_name:
                return ToolResult.error(
                    self.name,
                    f"Collection name is required for {operation_type} operations."
                )
            
            # Generate code based on database and operation type
            if database_type == "mongodb":
                code = self._generate_mongodb(operation_type, collection_name, schema, query_filter, data)
                language = "javascript"
            elif database_type == "dynamodb":
                code = self._generate_dynamodb(operation_type, collection_name, schema, query_filter, data)
                language = "javascript"
            elif database_type == "firebase":
                code = self._generate_firebase(operation_type, collection_name, schema, query_filter, data)
                language = "javascript"
            elif database_type == "cosmosdb":
                code = self._generate_cosmosdb(operation_type, collection_name, schema, query_filter, data)
                language = "javascript"
            elif database_type == "redis":
                code = self._generate_redis(operation_type, collection_name, schema, query_filter, data)
                language = "javascript"
            else:
                return ToolResult.error(
                    self.name,
                    f"Unsupported database type: {database_type}"
                )
            
            return ToolResult.success(
                self.name,
                {
                    "code": code,
                    "language": language,
                    "database_type": database_type,
                    "operation_type": operation_type,
                    "description": description
                }
            )
            
        except Exception as e:
            logging.error(f"Error generating NoSQL operation: {e}")
            return ToolResult.error(self.name, f"Failed to generate NoSQL operation: {str(e)}")
    
    def _generate_mongodb(self,
                         operation_type: str,
                         collection_name: Optional[str] = None,
                         schema: Optional[Dict[str, Any]] = None,
                         query_filter: Optional[Dict[str, Any]] = None,
                         data: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate MongoDB operations.
        
        Args:
            operation_type: Type of operation.
            collection_name: Collection name.
            schema: Schema definition.
            query_filter: Query filter.
            data: Data for insert/update.
            
        Returns:
            The generated MongoDB operation.
        """
        if operation_type == "schema":
            # MongoDB schema validation
            code = "// MongoDB Schema Validation\n"
            code += "db.createCollection(\"" + (collection_name or "collection") + "\", {\n"
            code += "  validator: {\n"
            code += "    $jsonSchema: {\n"
            code += "      bsonType: \"object\",\n"
            
            if schema:
                # Add title and description
                code += "      title: \"" + (schema.get("title", collection_name or "schema")) + "\",\n"
                if "description" in schema:
                    code += "      description: \"" + schema["description"] + "\",\n"
                
                # Add required fields
                if "required" in schema and isinstance(schema["required"], list):
                    required_fields = schema["required"]
                    code += "      required: [" + ", ".join([f"\"{field}\"" for field in required_fields]) + "],\n"
                
                # Add properties
                if "properties" in schema and isinstance(schema["properties"], dict):
                    code += "      properties: {\n"
                    
                    for prop_name, prop_def in schema["properties"].items():
                        code += f"        {prop_name}: {{\n"
                        
                        # Add property type
                        prop_type = prop_def.get("type", "string")
                        bson_type = self._map_to_bson_type(prop_type)
                        code += f"          bsonType: \"{bson_type}\",\n"
                        
                        # Add description if present
                        if "description" in prop_def:
                            code += f"          description: \"{prop_def['description']}\",\n"
                        
                        # Add additional constraints
                        if "minimum" in prop_def:
                            code += f"          minimum: {prop_def['minimum']},\n"
                        if "maximum" in prop_def:
                            code += f"          maximum: {prop_def['maximum']},\n"
                        if "minLength" in prop_def:
                            code += f"          minLength: {prop_def['minLength']},\n"
                        if "maxLength" in prop_def:
                            code += f"          maxLength: {prop_def['maxLength']},\n"
                        if "pattern" in prop_def:
                            code += f"          pattern: \"{prop_def['pattern']}\",\n"
                        if "enum" in prop_def:
                            enum_values = prop_def["enum"]
                            enum_str = ", ".join([f"\"{v}\"" if isinstance(v, str) else str(v) for v in enum_values])
                            code += f"          enum: [{enum_str}],\n"
                        
                        # Close property definition
                        code += "        },\n"
                    
                    code += "      }\n"
                
            code += "    }\n"
            code += "  }\n"
            code += "});\n"
            
            # Add indexes if specified in schema
            if schema and "indexes" in schema:
                code += "\n// Create indexes\n"
                for idx in schema["indexes"]:
                    if isinstance(idx, dict):
                        fields = idx.get("fields", [])
                        options = idx.get("options", {})
                        
                        index_obj = {}
                        for field in fields:
                            index_obj[field] = 1
                        
                        code += f"db.{collection_name}.createIndex({json.dumps(index_obj)}, {json.dumps(options)});\n"
            
            return code
        
        elif operation_type == "query":
            # MongoDB query
            code = "// MongoDB Query\n"
            if not query_filter:
                query_filter = {}
            
            code += f"db.{collection_name}.find({json.dumps(query_filter, indent=2)});\n"
            return code
        
        elif operation_type == "insert":
            # MongoDB insert
            code = "// MongoDB Insert\n"
            if not data:
                data = {"field1": "value1", "field2": "value2"}
            
            code += f"db.{collection_name}.insertOne({json.dumps(data, indent=2)});\n"
            return code
        
        elif operation_type == "update":
            # MongoDB update
            code = "// MongoDB Update\n"
            if not query_filter:
                query_filter = {"_id": "documentId"}
            
            if not data:
                data = {"$set": {"field1": "new_value"}}
            elif not any(k.startswith('$') for k in data.keys()):
                # Wrap with $set if no operators are provided
                data = {"$set": data}
            
            code += f"db.{collection_name}.updateOne(\n"
            code += f"  {json.dumps(query_filter, indent=2)},\n"
            code += f"  {json.dumps(data, indent=2)}\n"
            code += ");\n"
            return code
        
        elif operation_type == "delete":
            # MongoDB delete
            code = "// MongoDB Delete\n"
            if not query_filter:
                query_filter = {"_id": "documentId"}
            
            code += f"db.{collection_name}.deleteOne({json.dumps(query_filter, indent=2)});\n"
            return code
        
        elif operation_type == "index":
            # MongoDB index
            code = "// MongoDB Index\n"
            if not schema or "indexes" not in schema:
                # Default index
                code += f"db.{collection_name}.createIndex({ {\"field1\": 1} });\n"
            else:
                for idx in schema["indexes"]:
                    if isinstance(idx, dict):
                        fields = idx.get("fields", [])
                        options = idx.get("options", {})
                        
                        index_obj = {}
                        for field in fields:
                            index_obj[field] = 1
                        
                        code += f"db.{collection_name}.createIndex({json.dumps(index_obj)}, {json.dumps(options)});\n"
            
            return code
        
        else:
            return f"// Unsupported operation type for MongoDB: {operation_type}"
    
    def _generate_dynamodb(self,
                          operation_type: str,
                          collection_name: Optional[str] = None,
                          schema: Optional[Dict[str, Any]] = None,
                          query_filter: Optional[Dict[str, Any]] = None,
                          data: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate DynamoDB operations.
        
        Args:
            operation_type: Type of operation.
            collection_name: Table name.
            schema: Schema definition.
            query_filter: Query filter.
            data: Data for insert/update.
            
        Returns:
            The generated DynamoDB operation.
        """
        if operation_type == "schema":
            # DynamoDB create table
            code = "// DynamoDB Create Table with AWS SDK v3\n"
            code += "import { DynamoDBClient, CreateTableCommand } from '@aws-sdk/client-dynamodb';\n\n"
            code += "const client = new DynamoDBClient();\n\n"
            
            code += "async function createTable() {\n"
            code += "  const params = {\n"
            code += f"    TableName: '{collection_name or 'table'}',\n"
            code += "    KeySchema: [\n"
            
            # Add key schema
            if schema and "KeySchema" in schema:
                for key in schema["KeySchema"]:
                    code += f"      {{\n"
                    code += f"        AttributeName: '{key.get('AttributeName', 'id')}',\n"
                    code += f"        KeyType: '{key.get('KeyType', 'HASH')}'\n"
                    code += f"      }},\n"
            else:
                # Default primary key
                code += "      {\n"
                code += "        AttributeName: 'id',\n"
                code += "        KeyType: 'HASH'\n"
                code += "      }\n"
            
            code += "    ],\n"
            code += "    AttributeDefinitions: [\n"
            
            # Add attribute definitions
            if schema and "AttributeDefinitions" in schema:
                for attr in schema["AttributeDefinitions"]:
                    code += f"      {{\n"
                    code += f"        AttributeName: '{attr.get('AttributeName', 'id')}',\n"
                    code += f"        AttributeType: '{attr.get('AttributeType', 'S')}'\n"
                    code += f"      }},\n"
            else:
                # Default attribute definition
                code += "      {\n"
                code += "        AttributeName: 'id',\n"
                code += "        AttributeType: 'S'\n"
                code += "      }\n"
            
            code += "    ],\n"
            
            # Add capacity settings
            code += "    BillingMode: 'PROVISIONED',\n"
            code += "    ProvisionedThroughput: {\n"
            code += "      ReadCapacityUnits: 5,\n"
            code += "      WriteCapacityUnits: 5\n"
            code += "    }\n"
            
            # Add GSI if present
            if schema and "GlobalSecondaryIndexes" in schema:
                code += ",\n    GlobalSecondaryIndexes: [\n"
                for idx in schema["GlobalSecondaryIndexes"]:
                    code += "      {\n"
                    code += f"        IndexName: '{idx.get('IndexName', 'GSI1')}',\n"
                    code += "        KeySchema: [\n"
                    
                    # Add GSI key schema
                    for key in idx.get("KeySchema", []):
                        code += f"          {{\n"
                        code += f"            AttributeName: '{key.get('AttributeName', 'gsi_key')}',\n"
                        code += f"            KeyType: '{key.get('KeyType', 'HASH')}'\n"
                        code += f"          }},\n"
                    
                    code += "        ],\n"
                    code += "        Projection: {\n"
                    code += f"          ProjectionType: '{idx.get('Projection', {}).get('ProjectionType', 'ALL')}'\n"
                    code += "        },\n"
                    code += "        ProvisionedThroughput: {\n"
                    code += "          ReadCapacityUnits: 5,\n"
                    code += "          WriteCapacityUnits: 5\n"
                    code += "        }\n"
                    code += "      },\n"
                
                code += "    ]\n"
            
            code += "  };\n\n"
            code += "  try {\n"
            code += "    const command = new CreateTableCommand(params);\n"
            code += "    const data = await client.send(command);\n"
            code += "    console.log('Table created:', data);\n"
            code += "    return data;\n"
            code += "  } catch (error) {\n"
            code += "    console.error('Error creating table:', error);\n"
            code += "    throw error;\n"
            code += "  }\n"
            code += "}\n\n"
            code += "createTable();\n"
            
            return code
        
        elif operation_type == "query":
            # DynamoDB query
            code = "// DynamoDB Query with AWS SDK v3\n"
            code += "import { DynamoDBClient, QueryCommand } from '@aws-sdk/client-dynamodb';\n"
            code += "import { marshall, unmarshall } from '@aws-sdk/util-dynamodb';\n\n"
            code += "const client = new DynamoDBClient();\n\n"
            
            code += "async function queryTable() {\n"
            code += "  const params = {\n"
            code += f"    TableName: '{collection_name}',\n"
            
            # Add key condition expression
            if query_filter and "KeyConditionExpression" in query_filter:
                code += f"    KeyConditionExpression: '{query_filter['KeyConditionExpression']}',\n"
            else:
                code += "    KeyConditionExpression: 'id = :id',\n"
            
            # Add filter expression if present
            if query_filter and "FilterExpression" in query_filter:
                code += f"    FilterExpression: '{query_filter['FilterExpression']}',\n"
            
            # Add expression attribute values
            code += "    ExpressionAttributeValues: {\n"
            if query_filter and "ExpressionAttributeValues" in query_filter:
                for k, v in query_filter["ExpressionAttributeValues"].items():
                    code += f"      '{k}': {json.dumps(v)},\n"
            else:
                code += "      ':id': { S: 'example-id' }\n"
            
            code += "    }\n"
            code += "  };\n\n"
            
            code += "  try {\n"
            code += "    const command = new QueryCommand(params);\n"
            code += "    const data = await client.send(command);\n"
            code += "    const items = data.Items.map(item => unmarshall(item));\n"
            code += "    console.log('Query results:', items);\n"
            code += "    return items;\n"
            code += "  } catch (error) {\n"
            code += "    console.error('Error querying table:', error);\n"
            code += "    throw error;\n"
            code += "  }\n"
            code += "}\n\n"
            code += "queryTable();\n"
            
            return code
        
        elif operation_type == "insert":
            # DynamoDB put item
            code = "// DynamoDB Put Item with AWS SDK v3\n"
            code += "import { DynamoDBClient, PutItemCommand } from '@aws-sdk/client-dynamodb';\n"
            code += "import { marshall } from '@aws-sdk/util-dynamodb';\n\n"
            code += "const client = new DynamoDBClient();\n\n"
            
            code += "async function putItem() {\n"
            code += "  const item = "
            
            if data:
                code += json.dumps(data, indent=2).replace("\n", "\n  ")
            else:
                code += "{\n"
                code += "    id: 'unique-id',\n"
                code += "    name: 'Example Item',\n"
                code += "    createdAt: new Date().toISOString()\n"
                code += "  }"
            
            code += ";\n\n"
            code += "  const params = {\n"
            code += f"    TableName: '{collection_name}',\n"
            code += "    Item: marshall(item)\n"
            code += "  };\n\n"
            
            code += "  try {\n"
            code += "    const command = new PutItemCommand(params);\n"
            code += "    const data = await client.send(command);\n"
            code += "    console.log('Item added successfully:', data);\n"
            code += "    return data;\n"
            code += "  } catch (error) {\n"
            code += "    console.error('Error adding item:', error);\n"
            code += "    throw error;\n"
            code += "  }\n"
            code += "}\n\n"
            code += "putItem();\n"
            
            return code
        
        elif operation_type == "update":
            # DynamoDB update item
            code = "// DynamoDB Update Item with AWS SDK v3\n"
            code += "import { DynamoDBClient, UpdateItemCommand } from '@aws-sdk/client-dynamodb';\n"
            code += "import { marshall } from '@aws-sdk/util-dynamodb';\n\n"
            code += "const client = new DynamoDBClient();\n\n"
            
            code += "async function updateItem() {\n"
            code += "  const params = {\n"
            code += f"    TableName: '{collection_name}',\n"
            
            # Add key
            code += "    Key: marshall({\n"
            if query_filter:
                for k, v in query_filter.items():
                    if k not in ["KeyConditionExpression", "FilterExpression", "ExpressionAttributeValues"]:
                        code += f"      {k}: '{v}',\n"
            else:
                code += "      id: 'example-id'\n"
            
            code += "    }),\n"
            
            # Add update expression
            code += "    UpdateExpression: 'SET "
            
            update_parts = []
            if data:
                for k in data.keys():
                    update_parts.append(f"{k} = :{k.replace('.', '_')}")
            else:
                update_parts = ["updatedField = :updatedField", "updatedAt = :updatedAt"]
            
            code += ", ".join(update_parts) + "',\n"
            
            # Add expression attribute values
            code += "    ExpressionAttributeValues: marshall({\n"
            if data:
                for k, v in data.items():
                    code += f"      ':{k.replace('.', '_')}': {json.dumps(v)},\n"
            else:
                code += "      ':updatedField': 'new value',\n"
                code += "      ':updatedAt': new Date().toISOString()\n"
            
            code += "    }),\n"
            code += "    ReturnValues: 'ALL_NEW'\n"
            code += "  };\n\n"
            
            code += "  try {\n"
            code += "    const command = new UpdateItemCommand(params);\n"
            code += "    const data = await client.send(command);\n"
            code += "    console.log('Item updated successfully:', data);\n"
            code += "    return data;\n"
            code += "  } catch (error) {\n"
            code += "    console.error('Error updating item:', error);\n"
            code += "    throw error;\n"
            code += "  }\n"
            code += "}\n\n"
            code += "updateItem();\n"
            
            return code
        
        elif operation_type == "delete":
            # DynamoDB delete item
            code = "// DynamoDB Delete Item with AWS SDK v3\n"
            code += "import { DynamoDBClient, DeleteItemCommand } from '@aws-sdk/client-dynamodb';\n"
            code += "import { marshall } from '@aws-sdk/util-dynamodb';\n\n"
            code += "const client = new DynamoDBClient();\n\n"
            
            code += "async function deleteItem() {\n"
            code += "  const params = {\n"
            code += f"    TableName: '{collection_name}',\n"
            
            # Add key
            code += "    Key: marshall({\n"
            if query_filter:
                for k, v in query_filter.items():
                    if k not in ["KeyConditionExpression", "FilterExpression", "ExpressionAttributeValues"]:
                        code += f"      {k}: '{v}',\n"
            else:
                code += "      id: 'example-id'\n"
            
            code += "    })\n"
            code += "  };\n\n"
            
            code += "  try {\n"
            code += "    const command = new DeleteItemCommand(params);\n"
            code += "    const data = await client.send(command);\n"
            code += "    console.log('Item deleted successfully:', data);\n"
            code += "    return data;\n"
            code += "  } catch (error) {\n"
            code += "    console.error('Error deleting item:', error);\n"
            code += "    throw error;\n"
            code += "  }\n"
            code += "}\n\n"
            code += "deleteItem();\n"
            
            return code
        
        elif operation_type == "index":
            # DynamoDB index is part of schema, so we'll demonstrate updating a table to add an index
            code = "// DynamoDB Update Table to Add GSI with AWS SDK v3\n"
            code += "import { DynamoDBClient, UpdateTableCommand } from '@aws-sdk/client-dynamodb';\n\n"
            code += "const client = new DynamoDBClient();\n\n"
            
            code += "async function addGlobalSecondaryIndex() {\n"
            code += "  const params = {\n"
            code += f"    TableName: '{collection_name}',\n"
            code += "    AttributeDefinitions: [\n"
            code += "      {\n"
            code += "        AttributeName: 'indexField',\n"
            code += "        AttributeType: 'S'\n"
            code += "      }\n"
            code += "    ],\n"
            code += "    GlobalSecondaryIndexUpdates: [\n"
            code += "      {\n"
            code += "        Create: {\n"
            code += "          IndexName: 'indexFieldIndex',\n"
            code += "          KeySchema: [\n"
            code += "            {\n"
            code += "              AttributeName: 'indexField',\n"
            code += "              KeyType: 'HASH'\n"
            code += "            }\n"
            code += "          ],\n"
            code += "          Projection: {\n"
            code += "            ProjectionType: 'ALL'\n"
            code += "          },\n"
            code += "          ProvisionedThroughput: {\n"
            code += "            ReadCapacityUnits: 5,\n"
            code += "            WriteCapacityUnits: 5\n"
            code += "          }\n"
            code += "        }\n"
            code += "      }\n"
            code += "    ]\n"
            code += "  };\n\n"
            
            code += "  try {\n"
            code += "    const command = new UpdateTableCommand(params);\n"
            code += "    const data = await client.send(command);\n"
            code += "    console.log('GSI added successfully:', data);\n"
            code += "    return data;\n"
            code += "  } catch (error) {\n"
            code += "    console.error('Error adding GSI:', error);\n"
            code += "    throw error;\n"
            code += "  }\n"
            code += "}\n\n"
            code += "addGlobalSecondaryIndex();\n"
            
            return code
        
        else:
            return f"// Unsupported operation type for DynamoDB: {operation_type}"
    
    def _generate_firebase(self,
                          operation_type: str,
                          collection_name: Optional[str] = None,
                          schema: Optional[Dict[str, Any]] = None,
                          query_filter: Optional[Dict[str, Any]] = None,
                          data: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate Firebase operations.
        
        Args:
            operation_type: Type of operation.
            collection_name: Collection name.
            schema: Schema definition.
            query_filter: Query filter.
            data: Data for insert/update.
            
        Returns:
            The generated Firebase operation.
        """
        if operation_type == "schema":
            # Firebase does not have explicit schema definitions, but we can show a Firestore rules file
            code = "// Firebase Firestore Security Rules\n"
            code += "rules_version = '2';\n"
            code += "service cloud.firestore {\n"
            code += "  match /databases/{database}/documents {\n"
            
            # Define rules for the collection
            code += f"    match /{collection_name or 'collection'}/{{documentId}} {{\n"
            code += "      // Allow read if authenticated\n"
            code += "      allow read: if request.auth != null;\n\n"
            
            # Add validation rules if schema provided
            if schema and "properties" in schema:
                code += "      // Allow write if validated\n"
                code += "      allow write: if request.auth != null && isValidDocument();\n\n"
                
                code += "      // Validation function\n"
                code += "      function isValidDocument() {\n"
                code += "        let incomingData = request.resource.data;\n"
                
                validations = []
                
                for prop_name, prop_def in schema["properties"].items():
                    prop_type = prop_def.get("type", "string")
                    
                    # Add type validation
                    if prop_type == "string":
                        validations.append(f"incomingData.{prop_name} is string")
                    elif prop_type == "number" or prop_type == "integer":
                        validations.append(f"incomingData.{prop_name} is number")
                    elif prop_type == "boolean":
                        validations.append(f"incomingData.{prop_name} is bool")
                    elif prop_type == "array":
                        validations.append(f"incomingData.{prop_name} is list")
                    elif prop_type == "object":
                        validations.append(f"incomingData.{prop_name} is map")
                    
                    # Add additional constraints
                    if prop_type == "string":
                        if "minLength" in prop_def:
                            validations.append(f"incomingData.{prop_name}.size() >= {prop_def['minLength']}")
                        if "maxLength" in prop_def:
                            validations.append(f"incomingData.{prop_name}.size() <= {prop_def['maxLength']}")
                        if "pattern" in prop_def:
                            validations.append(f"incomingData.{prop_name}.matches('{prop_def['pattern']}')")
                    
                    if (prop_type == "number" or prop_type == "integer") and ("minimum" in prop_def or "maximum" in prop_def):
                        if "minimum" in prop_def:
                            validations.append(f"incomingData.{prop_name} >= {prop_def['minimum']}")
                        if "maximum" in prop_def:
                            validations.append(f"incomingData.{prop_name} <= {prop_def['maximum']}")
                
                # Add required field validations
                if "required" in schema and isinstance(schema["required"], list):
                    for field in schema["required"]:
                        validations.append(f"incomingData.{field} != null")
                
                # Add all validations to the function
                if validations:
                    code += "        return " + " && \n               ".join(validations) + ";\n"
                else:
                    code += "        return true;\n"
                
                code += "      }\n"
            else:
                code += "      // Allow write if authenticated\n"
                code += "      allow write: if request.auth != null;\n"
            
            code += "    }\n"
            code += "  }\n"
            code += "}\n"
            
            return code
        
        elif operation_type == "query":
            # Firebase Firestore query
            code = "// Firebase Firestore Query\n"
            code += "import { collection, query, where, getDocs } from 'firebase/firestore';\n"
            code += "import { db } from './firebase-config'; // Your Firebase config file\n\n"
            
            code += "async function queryDocuments() {\n"
            code += f"  const collectionRef = collection(db, '{collection_name}');\n"
            
            # Build query constraints
            constraints = []
            if query_filter:
                for field, value in query_filter.items():
                    if isinstance(value, dict) and "operator" in value and "value" in value:
                        operator = value["operator"]
                        filter_value = value["value"]
                    else:
                        operator = "=="
                        filter_value = value
                    
                    # Format value based on type
                    if isinstance(filter_value, str):
                        filter_value = f"'{filter_value}'"
                    elif isinstance(filter_value, bool):
                        filter_value = str(filter_value).lower()
                    else:
                        filter_value = str(filter_value)
                    
                    constraints.append(f"where('{field}', '{operator}', {filter_value})")
            
            if constraints:
                code += "  const q = query(collectionRef, " + ", ".join(constraints) + ");\n"
            else:
                code += "  // Query all documents (you may want to limit this in production)\n"
                code += "  const q = query(collectionRef);\n"
            
            code += "\n  try {\n"
            code += "    const querySnapshot = await getDocs(q);\n"
            code += "    const documents = [];\n"
            code += "    querySnapshot.forEach((doc) => {\n"
            code += "      documents.push({\n"
            code += "        id: doc.id,\n"
            code += "        ...doc.data()\n"
            code += "      });\n"
            code += "    });\n"
            code += "    console.log('Documents found:', documents);\n"
            code += "    return documents;\n"
            code += "  } catch (error) {\n"
            code += "    console.error('Error querying documents:', error);\n"
            code += "    throw error;\n"
            code += "  }\n"
            code += "}\n\n"
            code += "queryDocuments();\n"
            
            return code
        
        elif operation_type == "insert":
            # Firebase Firestore insert
            code = "// Firebase Firestore Add Document\n"
            code += "import { collection, addDoc } from 'firebase/firestore';\n"
            code += "import { db } from './firebase-config'; // Your Firebase config file\n\n"
            
            code += "async function addDocument() {\n"
            code += f"  const collectionRef = collection(db, '{collection_name}');\n"
            code += "  const docData = "
            
            if data:
                code += json.dumps(data, indent=2).replace("\n", "\n  ")
            else:
                code += "{\n"
                code += "    name: 'Example Document',\n"
                code += "    createdAt: new Date(),\n"
                code += "    status: 'active'\n"
                code += "  }"
            
            code += ";\n\n"
            code += "  try {\n"
            code += "    const docRef = await addDoc(collectionRef, docData);\n"
            code += "    console.log('Document added with ID:', docRef.id);\n"
            code += "    return { id: docRef.id, ...docData };\n"
            code += "  } catch (error) {\n"
            code += "    console.error('Error adding document:', error);\n"
            code += "    throw error;\n"
            code += "  }\n"
            code += "}\n\n"
            code += "addDocument();\n"
            
            return code
        
        elif operation_type == "update":
            # Firebase Firestore update
            code = "// Firebase Firestore Update Document\n"
            code += "import { doc, updateDoc } from 'firebase/firestore';\n"
            code += "import { db } from './firebase-config'; // Your Firebase config file\n\n"
            
            code += "async function updateDocument() {\n"
            
            # Document ID
            doc_id = "document_id"
            if query_filter and isinstance(query_filter, dict):
                if "id" in query_filter:
                    doc_id = query_filter["id"]
                elif "documentId" in query_filter:
                    doc_id = query_filter["documentId"]
            
            code += f"  const docRef = doc(db, '{collection_name}', '{doc_id}');\n"
            code += "  const updateData = "
            
            if data:
                code += json.dumps(data, indent=2).replace("\n", "\n  ")
            else:
                code += "{\n"
                code += "    updatedField: 'new value',\n"
                code += "    updatedAt: new Date()\n"
                code += "  }"
            
            code += ";\n\n"
            code += "  try {\n"
            code += "    await updateDoc(docRef, updateData);\n"
            code += "    console.log('Document successfully updated');\n"
            code += "    return { id: docRef.id, ...updateData };\n"
            code += "  } catch (error) {\n"
            code += "    console.error('Error updating document:', error);\n"
            code += "    throw error;\n"
            code += "  }\n"
            code += "}\n\n"
            code += "updateDocument();\n"
            
            return code
        
        elif operation_type == "delete":
            # Firebase Firestore delete
            code = "// Firebase Firestore Delete Document\n"
            code += "import { doc, deleteDoc } from 'firebase/firestore';\n"
            code += "import { db } from './firebase-config'; // Your Firebase config file\n\n"
            
            code += "async function deleteDocument() {\n"
            
            # Document ID
            doc_id = "document_id"
            if query_filter and isinstance(query_filter, dict):
                if "id" in query_filter:
                    doc_id = query_filter["id"]
                elif "documentId" in query_filter:
                    doc_id = query_filter["documentId"]
            
            code += f"  const docRef = doc(db, '{collection_name}', '{doc_id}');\n\n"
            code += "  try {\n"
            code += "    await deleteDoc(docRef);\n"
            code += "    console.log('Document successfully deleted');\n"
            code += "    return { success: true, id: docRef.id };\n"
            code += "  } catch (error) {\n"
            code += "    console.error('Error deleting document:', error);\n"
            code += "    throw error;\n"
            code += "  }\n"
            code += "}\n\n"
            code += "deleteDocument();\n"
            
            return code
        
        elif operation_type == "index":
            # Firebase Firestore indexes are managed in Firebase console or with Firebase CLI
            code = "// Firebase Firestore Index Configuration\n"
            code += "// Note: Firebase indexes are typically created in the Firebase Console or using the Firebase CLI.\n\n"
            
            code += "// Example Firestore Index Configuration (firestore.indexes.json):\n"
            code += "/*\n"
            code += "{\n"
            code += '  "indexes": [\n'
            code += "    {\n"
            code += f'      "collectionGroup": "{collection_name}",\n'
            code += '      "queryScope": "COLLECTION",\n'
            code += '      "fields": [\n'
            
            # Add sample index fields
            if schema and "indexes" in schema:
                for idx in schema["indexes"]:
                    for field in idx.get("fields", []):
                        code += "        {\n"
                        code += f'          "fieldPath": "{field}",\n'
                        code += '          "order": "ASCENDING"\n'
                        code += "        },\n"
            else:
                code += "        {\n"
                code += '          "fieldPath": "field1",\n'
                code += '          "order": "ASCENDING"\n'
                code += "        },\n"
                code += "        {\n"
                code += '          "fieldPath": "field2",\n'
                code += '          "order": "DESCENDING"\n'
                code += "        }\n"
            
            code += "      ]\n"
            code += "    }\n"
            code += "  ],\n"
            code += '  "fieldOverrides": []\n'
            code += "}\n"
            code += "*/\n\n"
            
            code += "// To deploy indexes using Firebase CLI:\n"
            code += "// $ firebase deploy --only firestore:indexes\n"
            
            return code
        
        else:
            return f"// Unsupported operation type for Firebase: {operation_type}"
    
    def _generate_cosmosdb(self,
                          operation_type: str,
                          collection_name: Optional[str] = None,
                          schema: Optional[Dict[str, Any]] = None,
                          query_filter: Optional[Dict[str, Any]] = None,
                          data: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate CosmosDB operations.
        
        Args:
            operation_type: Type of operation.
            collection_name: Container name.
            schema: Schema definition.
            query_filter: Query filter.
            data: Data for insert/update.
            
        Returns:
            The generated CosmosDB operation.
        """
        if operation_type == "schema":
            # CosmosDB container creation
            code = "// Azure CosmosDB Container Creation\n"
            code += "const { CosmosClient } = require('@azure/cosmos');\n\n"
            
            code += "// Initialize CosmosDB client\n"
            code += "const endpoint = process.env.COSMOS_ENDPOINT || 'https://your-cosmosdb-account.documents.azure.com:443/';\n"
            code += "const key = process.env.COSMOS_KEY || 'your_cosmos_key';\n"
            code += "const client = new CosmosClient({ endpoint, key });\n\n"
            
            code += "// Database and container names\n"
            code += "const databaseName = 'myDatabase';\n"
            code += f"const containerName = '{collection_name or 'container'}';\n\n"
            
            code += "async function createContainer() {\n"
            code += "  try {\n"
            code += "    // Get a reference to the database\n"
            code += "    const { database } = await client.databases.createIfNotExists({ id: databaseName });\n"
            code += "    console.log(`Database ${databaseName} created or already exists`);\n\n"
            
            # Define container options
            code += "    // Container definition\n"
            code += "    const containerDefinition = {\n"
            code += f"      id: containerName,\n"
            
            # Define partition key
            if schema and "partitionKey" in schema:
                code += f"      partitionKey: {{ paths: ['{schema['partitionKey']}'] }}"
            else:
                code += "      partitionKey: { paths: ['/id'] }"
            
            # Add indexing policy if provided
            if schema and "indexingPolicy" in schema:
                code += ",\n      indexingPolicy: "
                code += json.dumps(schema["indexingPolicy"], indent=6).replace("\n", "\n      ")
            else:
                # Default indexing policy
                code += ",\n"
                code += "      indexingPolicy: {\n"
                code += "        indexingMode: 'consistent',\n"
                code += "        automatic: true,\n"
                code += "        includedPaths: [\n"
                code += "          { path: '/*' }\n"
                code += "        ],\n"
                code += "        excludedPaths: [\n"
                code += "          { path: '/\"_etag\"/?' }\n"
                code += "        ]\n"
                code += "      }"
            
            code += "\n    };\n\n"
            
            code += "    // Create the container\n"
            code += "    const { container } = await database.containers.createIfNotExists(containerDefinition);\n"
            code += "    console.log(`Container ${containerName} created or already exists`);\n"
            code += "    return container;\n"
            code += "  } catch (error) {\n"
            code += "    console.error('Error creating container:', error);\n"
            code += "    throw error;\n"
            code += "  }\n"
            code += "}\n\n"
            code += "createContainer().catch(console.error);\n"
            
            return code
        
        elif operation_type == "query":
            # CosmosDB query
            code = "// Azure CosmosDB Query\n"
            code += "const { CosmosClient } = require('@azure/cosmos');\n\n"
            
            code += "// Initialize CosmosDB client\n"
            code += "const endpoint = process.env.COSMOS_ENDPOINT || 'https://your-cosmosdb-account.documents.azure.com:443/';\n"
            code += "const key = process.env.COSMOS_KEY || 'your_cosmos_key';\n"
            code += "const client = new CosmosClient({ endpoint, key });\n\n"
            
            code += "// Database and container names\n"
            code += "const databaseName = 'myDatabase';\n"
            code += f"const containerName = '{collection_name}';\n\n"
            
            code += "async function queryItems() {\n"
            code += "  try {\n"
            code += "    // Get container reference\n"
            code += "    const container = client.database(databaseName).container(containerName);\n\n"
            
            # Build query
            code += "    // Define the query\n"
            code += "    const querySpec = {\n"
            code += "      query: "
            
            if query_filter and "query" in query_filter:
                code += f"'{query_filter['query']}'"
            else:
                code += "'SELECT * FROM c WHERE "
                
                conditions = []
                if query_filter:
                    for k, v in query_filter.items():
                        if k != "query" and k != "parameters":
                            if isinstance(v, str):
                                conditions.append(f"c.{k} = @{k}")
                            elif isinstance(v, (int, float)):
                                conditions.append(f"c.{k} = @{k}")
                            elif isinstance(v, bool):
                                conditions.append(f"c.{k} = @{k}")
                            elif isinstance(v, dict) and "operator" in v and "value" in v:
                                conditions.append(f"c.{k} {v['operator']} @{k}")
                
                if conditions:
                    code += " AND ".join(conditions) + "'"
                else:
                    code += "1=1'"
            
            code += ",\n"
            
            # Add parameters
            code += "      parameters: [\n"
            if query_filter and "parameters" in query_filter:
                for param in query_filter["parameters"]:
                    code += f"        {{ name: '@{param['name']}', value: {json.dumps(param['value'])} }},\n"
            elif query_filter:
                for k, v in query_filter.items():
                    if k != "query" and k != "parameters":
                        if isinstance(v, dict) and "operator" in v and "value" in v:
                            code += f"        {{ name: '@{k}', value: {json.dumps(v['value'])} }},\n"
                        else:
                            code += f"        {{ name: '@{k}', value: {json.dumps(v)} }},\n"
            
            code += "      ]\n"
            code += "    };\n\n"
            
            code += "    // Execute the query\n"
            code += "    const { resources } = await container.items.query(querySpec).fetchAll();\n"
            code += "    console.log(`Found ${resources.length} items`);\n"
            code += "    console.log(resources);\n"
            code += "    return resources;\n"
            code += "  } catch (error) {\n"
            code += "    console.error('Error querying items:', error);\n"
            code += "    throw error;\n"
            code += "  }\n"
            code += "}\n\n"
            code += "queryItems().catch(console.error);\n"
            
            return code
        
        elif operation_type == "insert":
            # CosmosDB insert
            code = "// Azure CosmosDB Create Item\n"
            code += "const { CosmosClient } = require('@azure/cosmos');\n\n"
            
            code += "// Initialize CosmosDB client\n"
            code += "const endpoint = process.env.COSMOS_ENDPOINT || 'https://your-cosmosdb-account.documents.azure.com:443/';\n"
            code += "const key = process.env.COSMOS_KEY || 'your_cosmos_key';\n"
            code += "const client = new CosmosClient({ endpoint, key });\n\n"
            
            code += "// Database and container names\n"
            code += "const databaseName = 'myDatabase';\n"
            code += f"const containerName = '{collection_name}';\n\n"
            
            code += "async function createItem() {\n"
            code += "  try {\n"
            code += "    // Get container reference\n"
            code += "    const container = client.database(databaseName).container(containerName);\n\n"
            
            # Define the item to create
            code += "    // Define the new item\n"
            code += "    const newItem = "
            
            if data:
                # If ID is not in the data, add it
                if isinstance(data, dict) and "id" not in data:
                    data_with_id = {"id": "item-" + str(int(time.time()))}
                    data_with_id.update(data)
                    code += json.dumps(data_with_id, indent=2).replace("\n", "\n    ")
                else:
                    code += json.dumps(data, indent=2).replace("\n", "\n    ")
            else:
                code += "{\n"
                code += "      id: 'item-" + str(int(time.time())) + "',\n"
                code += "      name: 'Sample Item',\n"
                code += "      description: 'A sample item created in CosmosDB',\n"
                code += "      category: 'samples',\n"
                code += "      isActive: true,\n"
                code += "      createdAt: new Date().toISOString()\n"
                code += "    }"
            
            code += ";\n\n"
            
            code += "    // Create the item\n"
            code += "    const { resource: createdItem } = await container.items.create(newItem);\n"
            code += "    console.log('Created item:', createdItem);\n"
            code += "    return createdItem;\n"
            code += "  } catch (error) {\n"
            code += "    console.error('Error creating item:', error);\n"
            code += "    throw error;\n"
            code += "  }\n"
            code += "}\n\n"
            code += "createItem().catch(console.error);\n"
            
            return code
        
        elif operation_type == "update":
            # CosmosDB update
            code = "// Azure CosmosDB Update Item\n"
            code += "const { CosmosClient } = require('@azure/cosmos');\n\n"
            
            code += "// Initialize CosmosDB client\n"
            code += "const endpoint = process.env.COSMOS_ENDPOINT || 'https://your-cosmosdb-account.documents.azure.com:443/';\n"
            code += "const key = process.env.COSMOS_KEY || 'your_cosmos_key';\n"
            code += "const client = new CosmosClient({ endpoint, key });\n\n"
            
            code += "// Database and container names\n"
            code += "const databaseName = 'myDatabase';\n"
            code += f"const containerName = '{collection_name}';\n\n"
            
            # Get item ID and partition key
            item_id = "document_id"
            partition_key = "document_id"
            
            if query_filter and isinstance(query_filter, dict):
                if "id" in query_filter:
                    item_id = query_filter["id"]
                
                # Use the partition key from the query filter or default to id
                if "partitionKey" in query_filter:
                    partition_key = query_filter["partitionKey"]
                else:
                    partition_key = item_id
            
            code += "async function updateItem() {\n"
            code += "  try {\n"
            code += "    // Get container reference\n"
            code += "    const container = client.database(databaseName).container(containerName);\n\n"
            
            # Get the existing item
            code += "    // Get the existing item\n"
            code += f"    const itemId = '{item_id}';\n"
            code += f"    const partitionKey = '{partition_key}';\n"
            code += "    const { resource: existingItem } = await container.item(itemId, partitionKey).read();\n\n"
            
            # Define the update
            code += "    // Update the item\n"
            code += "    const updatedItem = {\n"
            code += "      ...existingItem,\n"
            
            if data:
                for k, v in data.items():
                    code += f"      {k}: {json.dumps(v)},\n"
            else:
                code += "      updatedField: 'new value',\n"
                code += "      updatedAt: new Date().toISOString()\n"
            
            code += "    };\n\n"
            
            code += "    // Replace the item\n"
            code += "    const { resource: replacedItem } = await container.item(itemId, partitionKey).replace(updatedItem);\n"
            code += "    console.log('Updated item:', replacedItem);\n"
            code += "    return replacedItem;\n"
            code += "  } catch (error) {\n"
            code += "    console.error('Error updating item:', error);\n"
            code += "    throw error;\n"
            code += "  }\n"
            code += "}\n\n"
            code += "updateItem().catch(console.error);\n"
            
            return code
        
        elif operation_type == "delete":
            # CosmosDB delete
            code = "// Azure CosmosDB Delete Item\n"
            code += "const { CosmosClient } = require('@azure/cosmos');\n\n"
            
            code += "// Initialize CosmosDB client\n"
            code += "const endpoint = process.env.COSMOS_ENDPOINT || 'https://your-cosmosdb-account.documents.azure.com:443/';\n"
            code += "const key = process.env.COSMOS_KEY || 'your_cosmos_key';\n"
            code += "const client = new CosmosClient({ endpoint, key });\n\n"
            
            code += "// Database and container names\n"
            code += "const databaseName = 'myDatabase';\n"
            code += f"const containerName = '{collection_name}';\n\n"
            
            # Get item ID and partition key
            item_id = "document_id"
            partition_key = "document_id"
            
            if query_filter and isinstance(query_filter, dict):
                if "id" in query_filter:
                    item_id = query_filter["id"]
                
                # Use the partition key from the query filter or default to id
                if "partitionKey" in query_filter:
                    partition_key = query_filter["partitionKey"]
                else:
                    partition_key = item_id
            
            code += "async function deleteItem() {\n"
            code += "  try {\n"
            code += "    // Get container reference\n"
            code += "    const container = client.database(databaseName).container(containerName);\n\n"
            
            code += "    // Delete the item\n"
            code += f"    const itemId = '{item_id}';\n"
            code += f"    const partitionKey = '{partition_key}';\n"
            code += "    const { resource: result } = await container.item(itemId, partitionKey).delete()