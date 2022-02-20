from fastapi import FastAPI
import custom
import wsdl

app = FastAPI()
app.include_router(wsdl.router)
app.include_router(custom.router)
