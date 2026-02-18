import os
import shutil
import asyncio
import logging
from app.core.rag_logic import RAGService

logger = logging.getLogger(__name__)

class CleanupService:
    def __init__(self, data_dir: str, vector_store_dir: str, rag_service: RAGService, interval_minutes: int = 10):
        self.data_dir = data_dir
        self.vector_store_dir = vector_store_dir
        self.rag_service = rag_service
        self.interval_seconds = interval_minutes * 60

    async def start_cleanup_loop(self):
        """Infinite loop to clean up files periodically."""
        logger.info(f"Cleanup service started with {self.interval_seconds/60} min interval.")
        while True:
            await asyncio.sleep(self.interval_seconds)
            self.reset_data()

    def reset_data(self):
        """Deletes all uploaded data and clears the vector store."""
        try:
            logger.info("Executing periodic data reset...")
            
            # Clear data directory
            if os.path.exists(self.data_dir):
                for filename in os.listdir(self.data_dir):
                    file_path = os.path.join(self.data_dir, filename)
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
            
            # Clear vector store directory
            if os.path.exists(self.vector_store_dir):
                shutil.rmtree(self.vector_store_dir)
            
            os.makedirs(self.data_dir, exist_ok=True)
            os.makedirs(self.vector_store_dir, exist_ok=True)

            # Reset the rag_service instance's link to vector store
            self.rag_service.vector_store = None
            
            logger.info("Reset complete. Knowledge base is now empty.")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
