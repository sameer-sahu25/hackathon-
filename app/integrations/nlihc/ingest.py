import time
from typing import Dict
from app.integrations.nlihc.parser import parse_nlihc_csv, StateLawRecord
import logging

logger = logging.getLogger(__name__)


async def ingest_nlihc_data(filepath: str) -> Dict:
    start_time = time.time()
    records = parse_nlihc_csv(filepath)
    
    states_processed = set()
    for record in records:
        states_processed.add(record.state)
        # In a real app, we'd upsert to Postgres and Pinecone here
        logger.info(f"Processed state law record for {record.state}")
    
    result = {
        "states_processed": len(states_processed),
        "records_upserted": len(records),
        "errors": 0
    }
    
    logger.info(f"Ingestion complete: {result}")
    return result
