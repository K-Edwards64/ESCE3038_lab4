from datetime import datetime
from bson import ObjectId
from fastapi import Body, FastAPI, HTTPException, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import motor.motor_asyncio
from pydantic import BaseModel, BeforeValidator, Field, TypeAdapter
from typing import Annotated, List
from dotenv import load_dotenv
import os

###
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
origins = [ "https://ecse3038-lab3-tester.netlify.app" ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
###


connection = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URL"))

people_db = connection.people


PyObjectId = Annotated[str, BeforeValidator(str)]


class Profile(BaseModel):

    id: PyObjectId | None = Field(default=None, alias="_id")
    Last_Updated: datetime = Field(default_factory=datetime.now)        

    username: str
    color: str
    role: str

class Profile_Collection(BaseModel):
    profiles: List[Profile]

class Tank(BaseModel):

    
    #last_Update: datetime
    id: PyObjectId | None = Field(default=None, alias="_id")
    Last_Updated: datetime = Field(default_factory=datetime.now)

    location: str
    lat: float
    long: float


class Tank_Collection(BaseModel):
    tanks: List[Tank]

class TankUpdate(BaseModel):
    location: str | None = None
    lat: float | None = None
    long: float | None = None


#
@app.post("/profile")
async def create_profile(profile_request: Profile):

    profile_dictionary = profile_request.model_dump()


    if await people_db["Profile"].count_documents({}) < 1:
   
        created_profile = await people_db["Profile"].insert_one(profile_dictionary)
        profile = await people_db["Profile"].find_one({"_id": created_profile.inserted_id})
        JSONprofile = Profile(**profile)
        return JSONResponse(status_code=201, content=jsonable_encoder(JSONprofile))
    else:
        return Response(status_code=400)




###
@app.get("/profile")
async def get_profile():
    profile_collection = await people_db["Profile"].find().to_list(1)

    if await people_db["Profile"].count_documents({}) == 0:
        return ()

    profile = profile_collection[0]
    profile_id = profile["_id"]

    profile = await people_db["Profile"].find_one({"_id": profile_id})

    return Profile(**profile)

#
@app.get("/tank")
async def get_tank():
    tank_collection = await people_db["Tank"].find().to_list(1000)

    if await people_db["Tank"].count_documents({}) == 0:
        return ()
    return TypeAdapter(List[Tank]).validate_python(tank_collection)


#
@app.post("/tank")
async def create_person(tank_request: Tank):

    tank_dictionary = tank_request.model_dump()
   
    created_tank = await people_db["Tank"].insert_one(tank_dictionary)
 

    tank = await people_db["Tank"].find_one({"_id": created_tank.inserted_id})
    JSONtank = Tank(**tank)
   
    return JSONResponse(status_code=201, content=jsonable_encoder(JSONtank))

@app.patch("/tank/{id}")
async def update_tank(id: str, tank_update: TankUpdate):

    tank_dict = tank_update.model_dump(exclude_unset=True)
    
    updated_tank = await people_db["Tank"].update_one({"_id": ObjectId(id)}, {"$set": tank_dict})
    updatedtank = await people_db["Tank"].update_one({"_id": ObjectId(id)}, {"$currentDate": {"Last_Updated": True}})

    check = await people_db["Tank"].find_one({"_id": ObjectId(id)})

    if check is not None:
        tank_after_update = await people_db["Tank"].find_one({"_id": ObjectId(id)})
        return Tank(**tank_after_update)
    else:
        raise HTTPException(status_code=404, detail="Tank Not Found")


@app.delete("/tank/{id}")
async def delete_tank(id: str):
    deleted_tank = await people_db["Tank"].delete_one({"_id": ObjectId(id)})
    updatedtank = await people_db["Tank"].update_one({"_id": ObjectId(id)}, {"$currentDate": {"Last_Updated": True}})

    if deleted_tank.deleted_count == 1:
        return Response(status_code=202)
    else:
        raise HTTPException(status_code=404, detail="Tank Not Found")
    
###

