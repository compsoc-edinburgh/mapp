
class MachineCreate(BaseModel):
    hostname: str
    is_online: bool
    in_use: bool

class MachineEdit(BaseModel):
    hostname: str | None = None
    is_online: bool | None = None
    in_use: bool | None = None

# rate limiting

# CRUD machine information
@app.get("/machines")
@user_required
def get_machines():
    pass
@app.post("/machines")
@admin_required
def post_machines(machine: MachineCreate):
    pass
@app.get("/machines/{id}")
@user_required
def get_machine(id: int):
    pass
@app.patch("/machines/{id}")
@worker_required
def patch_machine(id: int, machine: MachineEdit):
    pass
@app.delete("/machines/{id}")
@admin_required
def delete_machine(id: int):
    pass
