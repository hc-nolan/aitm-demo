from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import secrets

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=secrets.token_hex(32))

USERS = {"admin": "password"}


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/home", status_code=status.HTTP_302_FOUND)

    return """
    <html>
        <body>
            <h2>Login</h2>
            <form method="post" action="/login">
                <input type="text" name="username" placeholder="Username" required><br><br>
                <input type="password" name="password" placeholder="Password" required><br><br>
                <button type="submit">Login</button>
            </form>
        </body>
    </html>
    """


@app.post("/login")
async def login(request: Request, username: str = Form(), password: str = Form()):
    if USERS.get(username) == password:
        request.session["user"] = username
        return RedirectResponse("/home", status_code=status.HTTP_302_FOUND)

    return HTMLResponse("<h2>Invalid credentials</h2><a href='/'>Back</a>")


@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

    return f"""
    <html>
        <body>
            <h1>Welcome, {user}!</h1>
            <a href='/logout'>Logout</a>
        </body>
    </html>
    """


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
