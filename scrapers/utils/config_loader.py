import os
import logging
from typing import Dict, List, Any
from sqlmodel import Session, create_engine, select
from api.models import FilterDefinition, FilterOption

logger = logging.getLogger(__name__)

class ConfigLoader:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        self.engine = create_engine(self.database_url) if self.database_url else None
        self._cache = {}

    def get_spider_config(self, spider_id: str) -> Dict[str, Any]:
        """
        Fetch all filter definitions and their options for a specific spider.
        """
        if spider_id in self._cache:
            return self._cache[spider_id]

        if not self.engine:
            logger.error("Database engine not initialized. Cannot load config.")
            return {}

        config = {
            "filters": {},
            "raw_definitions": []
        }

        try:
            with Session(self.engine) as session:
                # 1. Fetch filter definitions
                stmt = select(FilterDefinition).where(FilterDefinition.spider_id == spider_id)
                definitions = session.exec(stmt).all()
                
                for defn in definitions:
                    filter_data = {
                        "id": defn.id,
                        "key": defn.filter_key,
                        "type": defn.filter_type,
                        "is_nested": defn.is_nested,
                        "default": defn.default_value,
                        "options": []
                    }
                    
                    # 2. Fetch options for select-type filters
                    if defn.filter_type == "select":
                        opt_stmt = select(FilterOption).where(FilterOption.filter_definition_id == defn.id)
                        options = session.exec(opt_stmt).all()
                        filter_data["options"] = [
                            {
                                "label": opt.option_label, 
                                "value": opt.option_value,
                                "group": opt.group_name,
                                "metadata": opt.extra_metadata
                            }
                            for opt in options
                        ]
                    
                    config["filters"][defn.filter_key] = filter_data
                    config["raw_definitions"].append(defn)
                
            self._cache[spider_id] = config
            return config
        except Exception as e:
            logger.error(f"Error loading config for {spider_id}: {e}")
            return {}
