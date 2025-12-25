from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from bson import ObjectId


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class Lead(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lead_name: str = "N/A"
    partner_name: str = ""
    next_follow_up_date: str = ""
    next_follow_up_time: str = ""
    type: str = "Call"
    priority: str = "Warm"
    stage: str = "New Lead"
    tat: str = "In TAT"
    mobile: str = ""
    calls_natc: int = 0  # Calls Not Answered/To Call
    calls_c: int = 0     # Calls Connected/Completed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LeadCreate(BaseModel):
    lead_name: str = "N/A"
    partner_name: str = ""
    next_follow_up_date: str = ""
    next_follow_up_time: str = ""
    type: str = "Call"
    priority: str = "Warm"
    stage: str = "New Lead"
    tat: str = "In TAT"
    mobile: str = ""


class LeadUpdate(BaseModel):
    lead_name: Optional[str] = None
    partner_name: Optional[str] = None
    next_follow_up_date: Optional[str] = None
    next_follow_up_time: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None
    stage: Optional[str] = None
    tat: Optional[str] = None
    mobile: Optional[str] = None
    calls_natc: Optional[int] = None
    calls_c: Optional[int] = None


class Demo(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    time_slot: str = ""  # e.g., "10:00 - 10:30"
    demo_time: str = ""  # e.g., "10:15 AM"
    client_name: str = ""
    company_name: str = ""
    mobile: str = ""
    status: str = "Pending"  # Pending, Completed, Cancelled
    date_type: str = "Today"  # Today, Tomorrow
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DemoCreate(BaseModel):
    time_slot: str = ""
    demo_time: str = ""
    client_name: str = ""
    company_name: str = ""
    mobile: str = ""
    status: str = "Pending"
    date_type: str = "Today"


class DemoUpdate(BaseModel):
    time_slot: Optional[str] = None
    demo_time: Optional[str] = None
    client_name: Optional[str] = None
    company_name: Optional[str] = None
    mobile: Optional[str] = None
    status: Optional[str] = None
    date_type: Optional[str] = None


class CallLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str
    call_type: str  # 'natc' (not answered) or 'c' (connected)
    duration: int = 0  # in seconds
    notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CallLogCreate(BaseModel):
    lead_id: str
    call_type: str  # 'natc' or 'c'
    duration: int = 0
    notes: str = ""


def serialize_doc(doc):
    """Serialize MongoDB document, handling datetime and ObjectId."""
    if doc is None:
        return None
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == '_id':
                continue
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, ObjectId):
                result[key] = str(value)
            else:
                result[key] = value
        return result
    return doc


# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Lead Dialer API"}


# Lead Routes
@api_router.get("/leads", response_model=List[Lead])
async def get_leads():
    leads = await db.leads.find({}, {"_id": 0}).to_list(1000)
    for lead in leads:
        if 'created_at' in lead and isinstance(lead['created_at'], str):
            lead['created_at'] = datetime.fromisoformat(lead['created_at'])
        if 'updated_at' in lead and isinstance(lead['updated_at'], str):
            lead['updated_at'] = datetime.fromisoformat(lead['updated_at'])
    return leads


@api_router.post("/leads", response_model=Lead)
async def create_lead(input: LeadCreate):
    lead_dict = input.model_dump()
    lead_obj = Lead(**lead_dict)
    
    doc = lead_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.leads.insert_one(doc)
    return lead_obj


@api_router.get("/leads/{lead_id}", response_model=Lead)
async def get_lead(lead_id: str):
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@api_router.put("/leads/{lead_id}", response_model=Lead)
async def update_lead(lead_id: str, input: LeadUpdate):
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.leads.update_one(
        {"id": lead_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    return lead


@api_router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str):
    result = await db.leads.delete_one({"id": lead_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Lead deleted successfully"}


# Call Log Routes
@api_router.post("/calls", response_model=CallLog)
async def create_call_log(input: CallLogCreate):
    # Verify lead exists
    lead = await db.leads.find_one({"id": input.lead_id})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    call_dict = input.model_dump()
    call_obj = CallLog(**call_dict)
    
    doc = call_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.call_logs.insert_one(doc)
    
    # Update lead's call counts
    if input.call_type == 'natc':
        await db.leads.update_one(
            {"id": input.lead_id},
            {"$inc": {"calls_natc": 1}}
        )
    elif input.call_type == 'c':
        await db.leads.update_one(
            {"id": input.lead_id},
            {"$inc": {"calls_c": 1}}
        )
    
    return call_obj


@api_router.get("/calls/{lead_id}", response_model=List[CallLog])
async def get_call_logs(lead_id: str):
    calls = await db.call_logs.find({"lead_id": lead_id}, {"_id": 0}).to_list(1000)
    return calls


# Demo Routes
@api_router.get("/demos", response_model=List[Demo])
async def get_demos():
    demos = await db.demos.find({}, {"_id": 0}).to_list(100)
    return demos


@api_router.post("/demos", response_model=Demo)
async def create_demo(input: DemoCreate):
    demo_dict = input.model_dump()
    demo_obj = Demo(**demo_dict)
    
    doc = demo_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.demos.insert_one(doc)
    return demo_obj


@api_router.put("/demos/{demo_id}", response_model=Demo)
async def update_demo(demo_id: str, input: DemoUpdate):
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = await db.demos.update_one(
        {"id": demo_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Demo not found")
    
    demo = await db.demos.find_one({"id": demo_id}, {"_id": 0})
    return demo


@api_router.delete("/demos/{demo_id}")
async def delete_demo(demo_id: str):
    result = await db.demos.delete_one({"id": demo_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Demo not found")
    return {"message": "Demo deleted successfully"}


# Seed sample data
@api_router.post("/seed")
async def seed_data():
    # Check if data already exists
    count = await db.leads.count_documents({})
    if count > 0:
        return {"message": "Data already exists", "count": count}
    
    sample_leads = [
        {"lead_name": "N/A", "partner_name": "Inside Sales (Renewal)", "next_follow_up_date": "26 Dec", "next_follow_up_time": "10:00", "type": "Call", "priority": "Warm", "stage": "New Lead", "tat": "In TAT", "mobile": "9415053527", "calls_natc": 2, "calls_c": 1},
        {"lead_name": "N/A", "partner_name": "Inside Sales (Renewal)", "next_follow_up_date": "26 Dec", "next_follow_up_time": "10:00", "type": "Call", "priority": "Warm", "stage": "New Lead", "tat": "In TAT", "mobile": "8788588370", "calls_natc": 0, "calls_c": 3},
        {"lead_name": "N/A", "partner_name": "Inside Sales (Renewal)", "next_follow_up_date": "26 Dec", "next_follow_up_time": "10:00", "type": "Call", "priority": "Warm", "stage": "New Lead", "tat": "In TAT", "mobile": "9153548835", "calls_natc": 1, "calls_c": 0},
        {"lead_name": "N/A", "partner_name": "Inside Sales (Renewal)", "next_follow_up_date": "26 Dec", "next_follow_up_time": "10:00", "type": "Call", "priority": "Warm", "stage": "New Lead", "tat": "In TAT", "mobile": "7054872354", "calls_natc": 5, "calls_c": 2},
        {"lead_name": "N/A", "partner_name": "Dipesh Infosys", "next_follow_up_date": "25 Dec", "next_follow_up_time": "14:49", "type": "Call", "priority": "Warm", "stage": "New Lead", "tat": "In TAT", "mobile": "9847939631", "calls_natc": 0, "calls_c": 1},
        {"lead_name": "N/A", "partner_name": "Inside Sales (VMS Se...", "next_follow_up_date": "26 Dec", "next_follow_up_time": "10:00", "type": "Call", "priority": "Warm", "stage": "New Lead", "tat": "In TAT", "mobile": "9862718735", "calls_natc": 3, "calls_c": 0},
        {"lead_name": "N/A", "partner_name": "Inside Sales (3I)", "next_follow_up_date": "26 Dec", "next_follow_up_time": "10:00", "type": "Call", "priority": "Warm", "stage": "New Lead", "tat": "In TAT", "mobile": "8829969926", "calls_natc": 1, "calls_c": 4},
        {"lead_name": "N/A", "partner_name": "Inside Sales (Delhi O...", "next_follow_up_date": "26 Dec", "next_follow_up_time": "10:00", "type": "Call", "priority": "Warm", "stage": "New Lead", "tat": "In TAT", "mobile": "7980361946", "calls_natc": 0, "calls_c": 0},
        {"lead_name": "N/A", "partner_name": "Inside Sales (Delhi O...", "next_follow_up_date": "26 Dec", "next_follow_up_time": "10:00", "type": "Call", "priority": "Warm", "stage": "New Lead", "tat": "In TAT", "mobile": "8957501580", "calls_natc": 2, "calls_c": 1},
        {"lead_name": "N/A", "partner_name": "Inside Sales (3I)", "next_follow_up_date": "26 Dec", "next_follow_up_time": "10:00", "type": "Call", "priority": "Hot", "stage": "New Lead", "tat": "In TAT", "mobile": "7000967473", "calls_natc": 0, "calls_c": 2},
        {"lead_name": "N/A", "partner_name": "Relirich Technologies", "next_follow_up_date": "26 Dec", "next_follow_up_time": "10:00", "type": "Call", "priority": "Warm", "stage": "New Lead", "tat": "In TAT", "mobile": "9817528432", "calls_natc": 4, "calls_c": 0},
        {"lead_name": "N/A", "partner_name": "Inside Sales (Renewal)", "next_follow_up_date": "26 Dec", "next_follow_up_time": "10:00", "type": "Call", "priority": "Warm", "stage": "New Lead", "tat": "In TAT", "mobile": "9823534042", "calls_natc": 1, "calls_c": 1},
        {"lead_name": "N/A", "partner_name": "Movingcloud360 Tec...", "next_follow_up_date": "26 Dec", "next_follow_up_time": "10:00", "type": "Call", "priority": "Hot", "stage": "New Lead", "tat": "In TAT", "mobile": "9315538670", "calls_natc": 0, "calls_c": 5},
        {"lead_name": "N/A", "partner_name": "Inside Sales (VMS Se...", "next_follow_up_date": "26 Dec", "next_follow_up_time": "10:00", "type": "Call", "priority": "Warm", "stage": "New Lead", "tat": "In TAT", "mobile": "7897890056", "calls_natc": 2, "calls_c": 3},
    ]
    
    for lead_data in sample_leads:
        lead = Lead(**lead_data)
        doc = lead.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        await db.leads.insert_one(doc)
    
    return {"message": f"Seeded {len(sample_leads)} leads"}


# Seed demo data
@api_router.post("/seed-demos")
async def seed_demos():
    count = await db.demos.count_documents({})
    if count > 0:
        return {"message": "Demo data already exists", "count": count}
    
    sample_demos = [
        {"time_slot": "10:00 - 10:30", "demo_time": "10:15 AM", "client_name": "Mr. Raj", "company_name": "ABC Enterprises", "mobile": "9560987665", "status": "Pending", "date_type": "Today"},
        {"time_slot": "10:00 - 10:30", "demo_time": "10:15 AM", "client_name": "Mr. Raj", "company_name": "ABC Enterprises", "mobile": "9560987665", "status": "Pending", "date_type": "Today"},
        {"time_slot": "11:00 - 11:30", "demo_time": "11:15 AM", "client_name": "Ms. Priya", "company_name": "XYZ Solutions", "mobile": "8765432109", "status": "Pending", "date_type": "Today"},
        {"time_slot": "14:00 - 14:30", "demo_time": "2:15 PM", "client_name": "Mr. Sharma", "company_name": "Tech Corp", "mobile": "7654321098", "status": "Pending", "date_type": "Today"},
        {"time_slot": "09:00 - 09:30", "demo_time": "9:15 AM", "client_name": "Mr. Kumar", "company_name": "Digital Works", "mobile": "6543210987", "status": "Pending", "date_type": "Tomorrow"},
        {"time_slot": "15:00 - 15:30", "demo_time": "3:15 PM", "client_name": "Ms. Gupta", "company_name": "Innovation Labs", "mobile": "5432109876", "status": "Pending", "date_type": "Tomorrow"},
    ]
    
    for demo_data in sample_demos:
        demo = Demo(**demo_data)
        doc = demo.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.demos.insert_one(doc)
    
    return {"message": f"Seeded {len(sample_demos)} demos"}


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
