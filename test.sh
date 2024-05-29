#!/bin/bash

TEST=$(mktemp -d)
pushd .

cd $TEST
mkdir $TEST/src
cp -r src $TEST/src

cat <<-EOF > $TEST/wrangler.toml
    name = "hello"
    main = "src/main.py"
    compatibility_flags = ["python_workers"]
EOF

cat <<-EOF > $TEST/src/main.py
    from asgi import fetch
    from server import App, Request, BaseModel

    async def on_fetch(request, env):
        import asgi
        return await asgi.fetch(app, request, env)

    app = App()

    @app.get("/")
    async def root():
        return {"message": "Hello, World!"}

    class Item(BaseModel):
        name: str
        description: str | None = None
        price: float
        tax: float | None = None

    @app.get("/env")
    async def root(req: Request):
        env = req.scope["env"]
        return {"message": "Here is an example of getting an environment variable: " + env.MESSAGE}

    @app.post("/items/")
    async def create_item(item: Item):
        return item

    @app.put("/items/{item_id}")
    async def create_item(item_id: int, item: Item, q: str | None = None):
        result = {"item_id": item_id, **item.dict()}
        if q:
            result.update({"q": q})
        return result

    @app.get("/items/{item_id}")
    async def read_item(item_id: int):
        return {"item_id": item_id}

EOF

npm i wrangler
node ./node_modules/wrangler/bin/wrangler.js dev --port 8787 &
sleep 5;
curl -X GET 127.0.0.1:8787/
curl -X POST 127.0.0.1:8787/

popd