from fastapi import APIRouter, Depends, HTTPException
from wsdl import call_add, call_subtract

from logging.config import dictConfig
import logging
from config import LogConfig

dictConfig(LogConfig().dict())
logger = logging.getLogger("wsdl-wrapper-custom")


router = APIRouter(
    prefix="/custom",
    tags=["custom"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{n}")
def fibonacci(n: int):
    
    logger.info("Call custom function - fibonacci")
    
    if n < 0:
        raise HTTPException(status_code=404, detail="Number must be positive")
    if n == 0:
        return 0
    if n == 1:
        return 1
    return call_add(fibonacci(call_subtract(n,1)),fibonacci(call_subtract(n,2)))
