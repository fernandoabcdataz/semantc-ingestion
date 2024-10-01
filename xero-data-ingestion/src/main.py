import asyncio
from data_pipeline import run_pipeline
from table_loader import load_json_to_table
from utils import get_logger

logger = get_logger()

async def main():
    """
    runs the data ingestion and loading pipeline
    """
    try:
        logger.info("starting data ingestion and loading pipeline")
        await run_pipeline()
        load_json_to_table()
        logger.info("pipeline completed successfully and BigQuery tables created")
    except Exception as e:
        error_message = f"pipeline error: {str(e)}"
        logger.error(error_message)
        raise

if __name__ == '__main__':
    asyncio.run(main())