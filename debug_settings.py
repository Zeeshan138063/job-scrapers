import os
import sys
from scrapy.utils.project import get_project_settings

def check_settings():
    settings = get_project_settings()
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"SCRAPY_SETTINGS_MODULE: {os.environ.get('SCRAPY_SETTINGS_MODULE')}")
    pipelines = settings.getdict('ITEM_PIPELINES')
    print(f"ITEM_PIPELINES: {pipelines}")
    print(f"BOT_NAME: {settings.get('BOT_NAME')}")

if __name__ == "__main__":
    check_settings()
