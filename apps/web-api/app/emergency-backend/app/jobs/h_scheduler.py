"""
Background scheduler for polling Pamalis database and processing human behavior alerts.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from app.db.mongo import get_client
from app.modules.hub.h_route import ingest_human_alert
from app.utils.time import utcnow_iso

logger = logging.getLogger(__name__)

# ============================================
# HUMAN BEHAVIOR (PAMALIS) DATA PROCESSING
# ============================================

async def process_human_alert(alert: Dict, incidents_collection) -> bool:
    """Process a single human behavior alert from Pamalis"""
    try:
        alert_id = alert.get("alert_id") or alert.get("_id")
        logger.info(f"Processing human behavior alert: {alert_id}")
        
        # Check if already processed
        if alert.get("emergency_processed") is True:
            logger.debug(f"Alert {alert_id} already processed")
            return False
        
        # Map Pamalis fields to match your expected format
        mapped_payload = {
            "alert_id": alert.get("alert_id"),
            "session_id": alert.get("session_id"),
            "timestamp": alert.get("timestamp"),
            "camera": alert.get("camera"),
            "location": alert.get("location"),
            "threat_level": alert.get("threat_level"),
            "threat_score": alert.get("threat_score"),
            "sustained_seconds": alert.get("sustained_seconds"),
            "action": alert.get("action"),
            "action_confidence": alert.get("action_confidence"),
            "objects_detected": alert.get("objects_detected", []),
            "action_contribution": alert.get("action_contribution"),
            "object_contribution": alert.get("object_contribution"),
            "synergy_bonus": alert.get("synergy_bonus"),
            "reasoning": alert.get("reasoning"),
            "human_summary": alert.get("human_summary"),
            "has_weapon": alert.get("has_weapon", False),
            "frame_number": alert.get("frame_number"),
            "alert_number": alert.get("alert_number")
        }
        
        # Call the ingest endpoint
        result = await ingest_human_alert(mapped_payload)
        
        if result and result.get("id"):
            logger.info(f"✅ Successfully ingested human behavior alert: {result.get('id')}")
            return True
        else:
            logger.warning(f"⚠️ Failed to ingest human behavior alert: {alert_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing human behavior alert {alert.get('alert_id')}: {e}")
        return False

async def poll_human_database():
    """Main polling function for human behavior (Pamalis) database"""
    logger.info("🚀 Starting human behavior database poller...")
    
    consecutive_errors = 0
    
    while True:
        try:
            client = get_client()
            
            # Pamalis database
            pamalis_db = client["alerts_db"]
            alerts_collection = pamalis_db["alerts"]
            
            # Your database
            emergency_db = client["emergency_db"]
            
            # Check if collection exists and has data
            alerts_count = await alerts_collection.count_documents({})
            logger.info(f"📊 Human behavior alerts: {alerts_count} documents")
            
            if alerts_count == 0:
                logger.warning("No alerts found in human behavior database")
                await asyncio.sleep(30)
                continue
            
            # Find alerts not yet processed by EMERGENCY SYSTEM
            cursor = alerts_collection.find({
                "emergency_processed": {"$ne": True}
            }).sort("timestamp", -1).limit(5)
            
            alerts = await cursor.to_list(length=5)
            
            if alerts:
                logger.info(f"📦 Found {len(alerts)} new human behavior alerts")
                
                for alert in alerts:
                    logger.info(f"Processing human behavior alert {alert.get('alert_id')} - Threat: {alert.get('threat_level')}")
                    
                    success = await process_human_alert(
                        alert, 
                        emergency_db
                    )
                    
                    # Mark as processed by EMERGENCY SYSTEM only
                    await alerts_collection.update_one(
                        {"_id": alert["_id"]},
                        {
                            "$set": {
                                "emergency_processed": True,
                                "emergency_processed_at": utcnow_iso(),
                                "emergency_success": success
                            }
                        }
                    )
                    
                    await asyncio.sleep(1)
                
                consecutive_errors = 0
            else:
                total = await alerts_collection.count_documents({})
                emergency_processed = await alerts_collection.count_documents({"emergency_processed": True})
                logger.info(f"Human behavior - Processed: {emergency_processed}/{total}")
            
            await asyncio.sleep(10)
            
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"❌ Human behavior polling error (attempt {consecutive_errors}): {e}")
            await asyncio.sleep(min(30 * (2 ** consecutive_errors), 300))

async def start_human_scheduler():
    """Start the human behavior background poller"""
    try:
        asyncio.create_task(poll_human_database())
        logger.info("✅ Human behavior database poller scheduled")
    except Exception as e:
        logger.error(f"❌ Failed to start human behavior scheduler: {e}")