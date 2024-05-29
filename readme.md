## TinyASGI

For use with Pyodide which doesnt supports foreign modules, like in **Cloudflare Python Worker**.

Packed into two python files for ease of use

Only implements extremely basic functions because you really shouldn't use this for that case..

*`asgi.py` is from Cloudflare/workerd/src/pyodide/_internal/asgi.py but without external dependancy.*

### Syntax

```python
from server import App
from server import Requests, Response
from server import HTMLResponse, JSONResponse
from server import HTTPException

app = App()

@app.get("/")
async def root(req: Requests):
    return JSONResponse({"result": "ok"})

@app.post("/")
async def root2(req: Requests):
    raise HTTPException(status_code = 400, detail = "Not implemented")
    # or 
    # raise HTTPException(404)

```


### Dependencies
- asyncio
- inspect
- contextlib
- json
- urllib
- typing
- re
- +) Pyodide
