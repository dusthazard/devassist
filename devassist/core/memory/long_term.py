"""
Long-term memory module for the DevAssist framework.

This module provides persistent storage for development context, project 
information, user preferences, and other long-lived data that should persist
across sessions.
"""

from typing import Dict, List, Any, Optional, Union
import uuid
import time
import json
import os
import logging
from pathlib import Path

from devassist.core.memory.base_memory import BaseMemory

class LongTermMemory(BaseMemory):
    """
    Persistent implementation of the BaseMemory interface.
    
    Provides a file-based persistent memory store for development context 
    and project information that should persist across sessions.
    
    Features:
    - File-based storage with JSON serialization
    - Indexing for fast retrieval
    - Query capabilities for finding relevant information
    - Automatic organization by projects and categories
    """
    
    def __init__(
        self, 
        storage_path: Optional[str] = None,
        index_in_memory: bool = True,
        max_items_per_category: int = 1000,
        **kwargs
    ):
        """
        Initialize a LongTermMemory instance.
        
        Args:
            storage_path: Path to store memory files. If None, uses a default location.
            index_in_memory: Whether to keep an in-memory index for faster searches.
            max_items_per_category: Maximum number of items to store per category.
            **kwargs: Additional configuration options.
        """
        super().__init__(**kwargs)
        
        # Set storage path
        if storage_path is None:
            home_dir = os.path.expanduser("~")
            storage_path = os.path.join(home_dir, ".devassist", "memory")
        
        self.storage_path = storage_path
        self.index_in_memory = index_in_memory
        self.max_items_per_category = max_items_per_category
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Create indexes
        self.index: Dict[str, Dict[str, Any]] = {}
        self.category_index: Dict[str, List[str]] = {}
        self.project_index: Dict[str, List[str]] = {}
        
        # Load index from disk if using in-memory indexing
        if self.index_in_memory:
            self._load_index()
            
        self.logger = logging.getLogger("devassist.memory.long_term")
        self.logger.info(f"Long-term memory initialized at {self.storage_path}")
    
    def add(self, item: Dict[str, Any]) -> str:
        """
        Add an item to memory and return its identifier.
        
        Args:
            item: The item to add to memory.
            
        Returns:
            A string identifier for the added item.
        """
        # Generate a unique identifier
        identifier = str(uuid.uuid4())
        
        # Add metadata
        item_with_metadata = item.copy()
        timestamp = time.time()
        
        # Extract project and category information if available
        project = item.get("project", "default")
        category = item.get("category", "general")
        
        item_with_metadata["_meta"] = {
            "id": identifier,
            "created_at": timestamp,
            "updated_at": timestamp,
            "project": project,
            "category": category
        }
        
        # Save the item to disk
        self._save_item(identifier, item_with_metadata)
        
        # Update the index
        if self.index_in_memory:
            self.index[identifier] = item_with_metadata
            
            # Update category index
            if category not in self.category_index:
                self.category_index[category] = []
            self.category_index[category].append(identifier)
            
            # Prune category if it exceeds the maximum size
            if len(self.category_index[category]) > self.max_items_per_category:
                # Remove the oldest item
                oldest_id = self.category_index[category].pop(0)
                self._remove_from_indexes(oldest_id)
                
                # Also remove the file
                self._delete_item_file(oldest_id)
            
            # Update project index
            if project not in self.project_index:
                self.project_index[project] = []
            self.project_index[project].append(identifier)
        
        self.logger.debug(f"Added item {identifier[:8]} to {project}/{category}")
        return identifier
    
    def get(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an item from memory by its identifier.
        
        Args:
            identifier: The identifier of the item to retrieve.
            
        Returns:
            The retrieved item, or None if not found.
        """
        # Check in-memory index first if available
        if self.index_in_memory and identifier in self.index:
            return self.index[identifier]
        
        # Otherwise, load from disk
        item_path = self._get_item_path(identifier)
        if not os.path.exists(item_path):
            return None
        
        try:
            with open(item_path, "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading item {identifier}: {e}")
            return None
    
    def search(self, query: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search memory for items matching the query.
        
        Args:
            query: The search query.
            limit: Maximum number of results to return.
            
        Returns:
            A list of matching items.
        """
        results = []
        
        # Check for project and category filters
        project_filter = query.pop("project", None)
        category_filter = query.pop("category", None)
        
        # Determine which items to search
        item_ids_to_search = []
        
        # If using in-memory index
        if self.index_in_memory:
            # Filter by project if specified
            if project_filter:
                item_ids_to_search = self.project_index.get(project_filter, [])
            # Filter by category if specified
            elif category_filter:
                item_ids_to_search = self.category_index.get(category_filter, [])
            # Otherwise, search all items
            else:
                item_ids_to_search = list(self.index.keys())
                
            # Perform the search
            for identifier in item_ids_to_search:
                item = self.index.get(identifier)
                if item and self._matches_query(item, query):
                    results.append({
                        "id": identifier,
                        "item": item,
                        "created_at": item.get("_meta", {}).get("created_at", 0)
                    })
                    
                    if len(results) >= limit:
                        break
        else:
            # If not using in-memory index, scan the storage directory
            for item_file in os.listdir(self.storage_path):
                if not item_file.endswith(".json"):
                    continue
                
                identifier = item_file[:-5]  # Remove .json extension
                item = self.get(identifier)
                
                # Skip if item doesn't match project or category filters
                if project_filter and item.get("_meta", {}).get("project") != project_filter:
                    continue
                if category_filter and item.get("_meta", {}).get("category") != category_filter:
                    continue
                
                if item and self._matches_query(item, query):
                    results.append({
                        "id": identifier,
                        "item": item,
                        "created_at": item.get("_meta", {}).get("created_at", 0)
                    })
                    
                    if len(results) >= limit:
                        break
        
        # Sort by creation time (newest first)
        results.sort(key=lambda x: x["created_at"], reverse=True)
        
        self.logger.debug(f"Search found {len(results)} results")
        return results
    
    def update(self, identifier: str, item: Dict[str, Any]) -> bool:
        """
        Update an item in memory.
        
        Args:
            identifier: The identifier of the item to update.
            item: The updated item.
            
        Returns:
            True if the update was successful, False otherwise.
        """
        # Check if the item exists
        existing_item = self.get(identifier)
        if existing_item is None:
            return False
        
        # Preserve metadata
        item_with_metadata = item.copy()
        if "_meta" in existing_item:
            item_with_metadata["_meta"] = existing_item["_meta"]
            item_with_metadata["_meta"]["updated_at"] = time.time()
        else:
            # This shouldn't happen, but just in case
            item_with_metadata["_meta"] = {
                "id": identifier,
                "created_at": time.time(),
                "updated_at": time.time(),
                "project": item.get("project", "default"),
                "category": item.get("category", "general")
            }
        
        # Save the updated item
        self._save_item(identifier, item_with_metadata)
        
        # Update the index
        if self.index_in_memory:
            # Check if project or category changed
            old_project = existing_item.get("_meta", {}).get("project", "default")
            old_category = existing_item.get("_meta", {}).get("category", "general")
            
            new_project = item.get("project", old_project)
            new_category = item.get("category", old_category)
            
            # Update metadata with new project/category if changed
            if new_project != old_project:
                item_with_metadata["_meta"]["project"] = new_project
                
                # Update project indexes
                if old_project in self.project_index and identifier in self.project_index[old_project]:
                    self.project_index[old_project].remove(identifier)
                
                if new_project not in self.project_index:
                    self.project_index[new_project] = []
                self.project_index[new_project].append(identifier)
                
            if new_category != old_category:
                item_with_metadata["_meta"]["category"] = new_category
                
                # Update category indexes
                if old_category in self.category_index and identifier in self.category_index[old_category]:
                    self.category_index[old_category].remove(identifier)
                
                if new_category not in self.category_index:
                    self.category_index[new_category] = []
                self.category_index[new_category].append(identifier)
            
            # Update the main index
            self.index[identifier] = item_with_metadata
        
        self.logger.debug(f"Updated item {identifier[:8]}")
        return True
    
    def delete(self, identifier: str) -> bool:
        """
        Delete an item from memory.
        
        Args:
            identifier: The identifier of the item to delete.
            
        Returns:
            True if the deletion was successful, False otherwise.
        """
        # Remove from indexes first
        if self.index_in_memory:
            self._remove_from_indexes(identifier)
        
        # Then delete the file
        return self._delete_item_file(identifier)
    
    def clear(self) -> None:
        """
        Clear all items from memory.
        """
        for item_file in os.listdir(self.storage_path):
            if not item_file.endswith(".json"):
                continue
            
            try:
                os.remove(os.path.join(self.storage_path, item_file))
            except Exception as e:
                self.logger.error(f"Error deleting file {item_file}: {e}")
        
        # Clear the indexes
        if self.index_in_memory:
            self.index = {}
            self.category_index = {}
            self.project_index = {}
            
        self.logger.info("Long-term memory cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory system.
        
        Returns:
            A dictionary containing memory statistics.
        """
        # Count the number of items
        if self.index_in_memory:
            item_count = len(self.index)
            project_count = len(self.project_index)
            category_count = len(self.category_index)
        else:
            item_count = len([f for f in os.listdir(self.storage_path) if f.endswith(".json")])
            project_count = 0
            category_count = 0
        
        # Get the total size of all items
        total_size = sum(
            os.path.getsize(os.path.join(self.storage_path, f)) 
            for f in os.listdir(self.storage_path) 
            if os.path.isfile(os.path.join(self.storage_path, f)) and f.endswith(".json")
        )
        
        # Get the number of items per project (up to 5 most populous projects)
        projects_by_size = {}
        if self.index_in_memory:
            for project, items in self.project_index.items():
                projects_by_size[project] = len(items)
            
            # Sort by number of items, take top 5
            top_projects = sorted(projects_by_size.items(), key=lambda x: x[1], reverse=True)[:5]
            project_stats = {project: count for project, count in top_projects}
        else:
            project_stats = {}
        
        return {
            "type": "long_term",
            "storage_path": self.storage_path,
            "index_in_memory": self.index_in_memory,
            "item_count": item_count,
            "project_count": project_count,
            "category_count": category_count,
            "total_size_bytes": total_size,
            "top_projects": project_stats
        }
    
    def get_all_projects(self) -> List[str]:
        """
        Get a list of all projects in memory.
        
        Returns:
            A list of project names.
        """
        if self.index_in_memory:
            return list(self.project_index.keys())
        else:
            # If not using in-memory index, scan all items to find unique projects
            projects = set()
            for item_file in os.listdir(self.storage_path):
                if not item_file.endswith(".json"):
                    continue
                
                identifier = item_file[:-5]  # Remove .json extension
                item = self.get(identifier)
                if item:
                    project = item.get("_meta", {}).get("project", "default")
                    projects.add(project)
            
            return list(projects)
    
    def get_all_categories(self) -> List[str]:
        """
        Get a list of all categories in memory.
        
        Returns:
            A list of category names.
        """
        if self.index_in_memory:
            return list(self.category_index.keys())
        else:
            # If not using in-memory index, scan all items to find unique categories
            categories = set()
            for item_file in os.listdir(self.storage_path):
                if not item_file.endswith(".json"):
                    continue
                
                identifier = item_file[:-5]  # Remove .json extension
                item = self.get(identifier)
                if item:
                    category = item.get("_meta", {}).get("category", "general")
                    categories.add(category)
            
            return list(categories)
    
    def get_project_items(self, project: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all items for a specific project.
        
        Args:
            project: The project name.
            limit: Maximum number of items to return.
            
        Returns:
            A list of items for the specified project.
        """
        return self.search({"project": project}, limit=limit)
    
    def get_category_items(self, category: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all items for a specific category.
        
        Args:
            category: The category name.
            limit: Maximum number of items to return.
            
        Returns:
            A list of items for the specified category.
        """
        return self.search({"category": category}, limit=limit)
    
    def _get_item_path(self, identifier: str) -> str:
        """
        Get the file path for an item.
        
        Args:
            identifier: The identifier of the item.
            
        Returns:
            The file path for the item.
        """
        return os.path.join(self.storage_path, f"{identifier}.json")
    
    def _save_item(self, identifier: str, item: Dict[str, Any]) -> None:
        """
        Save an item to disk.
        
        Args:
            identifier: The identifier of the item.
            item: The item to save.
        """
        item_path = self._get_item_path(identifier)
        
        try:
            with open(item_path, "w") as f:
                json.dump(item, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving item {identifier}: {e}")
    
    def _delete_item_file(self, identifier: str) -> bool:
        """
        Delete an item file from disk.
        
        Args:
            identifier: The identifier of the item.
            
        Returns:
            True if deletion was successful, False otherwise.
        """
        item_path = self._get_item_path(identifier)
        if not os.path.exists(item_path):
            return False
        
        try:
            os.remove(item_path)
            return True
        except Exception as e:
            self.logger.error(f"Error deleting item {identifier}: {e}")
            return False
    
    def _remove_from_indexes(self, identifier: str) -> None:
        """
        Remove an item from all indexes.
        
        Args:
            identifier: The identifier of the item to remove.
        """
        if identifier in self.index:
            # Get project and category before removing from main index
            meta = self.index[identifier].get("_meta", {})
            project = meta.get("project", "default")
            category = meta.get("category", "general")
            
            # Remove from main index
            del self.index[identifier]
            
            # Remove from project index
            if project in self.project_index and identifier in self.project_index[project]:
                self.project_index[project].remove(identifier)
                
                # Clean up empty project lists
                if not self.project_index[project]:
                    del self.project_index[project]
            
            # Remove from category index
            if category in self.category_index and identifier in self.category_index[category]:
                self.category_index[category].remove(identifier)
                
                # Clean up empty category lists
                if not self.category_index[category]:
                    del self.category_index[category]
    
    def _load_index(self) -> None:
        """
        Load the index from disk.
        """
        self.index = {}
        self.category_index = {}
        self.project_index = {}
        
        for item_file in os.listdir(self.storage_path):
            if not item_file.endswith(".json"):
                continue
            
            identifier = item_file[:-5]  # Remove .json extension
            
            try:
                with open(os.path.join(self.storage_path, item_file), "r") as f:
                    item = json.load(f)
                    
                    # Add to main index
                    self.index[identifier] = item
                    
                    # Extract project and category
                    meta = item.get("_meta", {})
                    project = meta.get("project", "default")
                    category = meta.get("category", "general")
                    
                    # Add to project index
                    if project not in self.project_index:
                        self.project_index[project] = []
                    self.project_index[project].append(identifier)
                    
                    # Add to category index
                    if category not in self.category_index:
                        self.category_index[category] = []
                    self.category_index[category].append(identifier)
            except Exception as e:
                self.logger.error(f"Error loading index for {identifier}: {e}")
    
    def _matches_query(self, item: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """
        Check if an item matches a query.
        
        Args:
            item: The item to check.
            query: The query to match against.
            
        Returns:
            True if the item matches the query, False otherwise.
        """
        for key, value in query.items():
            # Handle nested keys with dot notation
            if "." in key:
                parts = key.split(".")
                curr = item
                for part in parts:
                    if isinstance(curr, dict) and part in curr:
                        curr = curr[part]
                    else:
                        return False
                
                if curr != value:
                    return False
            
            # Handle text search with special _text key
            elif key == "_text" and isinstance(value, str):
                # Convert item to string and check if value is contained
                item_str = json.dumps(item).lower()
                if value.lower() not in item_str:
                    return False
            
            # Handle date range with special _date_after and _date_before keys
            elif key == "_date_after" and "_meta" in item:
                created_at = item["_meta"].get("created_at", 0)
                if created_at < value:
                    return False
            elif key == "_date_before" and "_meta" in item:
                created_at = item["_meta"].get("created_at", 0)
                if created_at > value:
                    return False
            
            # Handle simple keys
            elif key not in item or item[key] != value:
                return False
        
        return True
