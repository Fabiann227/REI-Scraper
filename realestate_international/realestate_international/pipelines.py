import json
import os

class JsonWriterPipeline:
    def process_item(self, item, spider):
        listing_id = item.get("listing_id")
        if not listing_id:
            return item
        
        folder = os.path.join(spider.settings.get("DATA_DIR", "data"))
        os.makedirs(folder, exist_ok=True)
        
        file_path = os.path.join(folder, f"{listing_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(dict(item), f, ensure_ascii=False, indent=2)
        spider.logger.info(f"Saved: {file_path}")
        return item
