from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import secrets
import pyotp
import qrcode
import io
import base64

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=secrets.token_hex(32))

# In-memory storage: {username: {"password": str, "totp_secret": str}}
USERS = {}


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
            <p>Don't have an account? <a href='/register'>Register here</a></p>
        </body>
    </html>
    """


@app.get("/register", response_class=HTMLResponse)
async def register_page():
    return """
    <html>
        <body>
            <h2>Register</h2>
            <form method="post" action="/register">
                <input type="text" name="username" placeholder="Username" required><br><br>
                <input type="password" name="password" placeholder="Password" required><br><br>
                <button type="submit">Register</button>
            </form>
            <p>Already have an account? <a href='/'>Login here</a></p>
        </body>
    </html>
    """


@app.post("/register")
async def register(request: Request, username: str = Form(), password: str = Form()):
    if username in USERS:
        return HTMLResponse(
            "<h2>Username already exists</h2><a href='/register'>Back</a>"
        )

    totp_secret = pyotp.random_base32()
    USERS[username] = {"password": password, "totp_secret": totp_secret}

    request.session["setup_user"] = username
    return RedirectResponse("/setup-mfa", status_code=status.HTTP_302_FOUND)


@app.get("/setup-mfa", response_class=HTMLResponse)
async def setup_mfa(request: Request):
    username = request.session.get("setup_user")
    if not username:
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

    totp_secret = USERS[username]["totp_secret"]
    totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
        name=username, issuer_name="Demo App"
    )

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return f"""
    <html>
        <body>
            <h2>Setup Two-Factor Authentication</h2>
            <p>Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)</p>
            <img src="data:image/png;base64,{img_str}" alt="QR Code"><br><br>
            <p>Or manually enter this secret: <strong>{totp_secret}</strong></p>
            <form method="post" action="/verify-mfa-setup">
                <input type="text" name="totp_code" placeholder="Enter 6-digit code" required><br><br>
                <button type="submit">Verify and Complete Setup</button>
            </form>
        </body>
    </html>
    """


@app.post("/verify-mfa-setup")
async def verify_mfa_setup(request: Request, totp_code: str = Form()):
    username = request.session.get("setup_user")
    if not username:
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

    totp_secret = USERS[username]["totp_secret"]
    totp = pyotp.TOTP(totp_secret)

    if totp.verify(totp_code):
        request.session.pop("setup_user")
        request.session["user"] = username
        return RedirectResponse("/home", status_code=status.HTTP_302_FOUND)

    return HTMLResponse(
        "<h2>Invalid code. Please try again.</h2><a href='/setup-mfa'>Back</a>"
    )


@app.post("/login")
async def login(request: Request, username: str = Form(), password: str = Form()):
    user_data = USERS.get(username)
    if user_data and user_data["password"] == password:
        request.session["mfa_user"] = username
        return RedirectResponse("/verify-mfa", status_code=status.HTTP_302_FOUND)

    return HTMLResponse("<h2>Invalid credentials</h2><a href='/'>Back</a>")


@app.get("/verify-mfa", response_class=HTMLResponse)
async def verify_mfa_page(request: Request):
    if not request.session.get("mfa_user"):
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

    return """
    <html>
        <body>
            <h2>Two-Factor Authentication</h2>
            <form method="post" action="/verify-mfa">
                <input type="text" name="totp_code" placeholder="Enter 6-digit code" required><br><br>
                <button type="submit">Verify</button>
            </form>
            <a href='/'>Cancel</a>
        </body>
    </html>
    """


@app.post("/verify-mfa")
async def verify_mfa(request: Request, totp_code: str = Form()):
    username = request.session.get("mfa_user")
    if not username:
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

    totp_secret = USERS[username]["totp_secret"]
    totp = pyotp.TOTP(totp_secret)

    if totp.verify(totp_code):
        request.session.pop("mfa_user")
        request.session["user"] = username
        return RedirectResponse("/home", status_code=status.HTTP_302_FOUND)

    return HTMLResponse("<h2>Invalid code</h2><a href='/verify-mfa'>Back</a>")


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
