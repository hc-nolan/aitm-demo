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


CSS_STYLE = """
<style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        max-width: 500px;
        margin: 50px auto;
        padding: 20px;
        background-color: #f5f5f5;
    }
    .container {
        background: white;
        padding: 40px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    h1, h2 {
        color: #333;
        margin-top: 0;
    }
    input[type="text"], input[type="password"] {
        width: 100%;
        padding: 12px;
        margin: 8px 0;
        border: 1px solid #ddd;
        border-radius: 4px;
        box-sizing: border-box;
        font-size: 14px;
    }
    button {
        width: 100%;
        padding: 12px;
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 16px;
        margin-top: 10px;
    }
    button:hover {
        background-color: #0056b3;
    }
    a {
        color: #007bff;
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
    .error {
        color: #dc3545;
        margin-bottom: 15px;
    }
    .info {
        color: #666;
        font-size: 14px;
        margin: 15px 0;
    }
    .qr-container {
        text-align: center;
        margin: 20px 0;
    }
    .secret {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 4px;
        font-family: monospace;
        word-break: break-all;
    }
</style>
"""


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/home", status_code=status.HTTP_302_FOUND)

    return f"""
    <html>
        <head>
            <title>Login</title>
            {CSS_STYLE}
        </head>
        <body>
            <div class="container">
                <h2>Login</h2>
                <form method="post" action="/login">
                    <input type="text" name="username" placeholder="Username" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Login</button>
                </form>
                <p class="info">Don't have an account? <a href='/register'>Register here</a></p>
            </div>
        </body>
    </html>
    """


@app.get("/register", response_class=HTMLResponse)
async def register_page():
    return f"""
    <html>
        <head>
            <title>Register</title>
            {CSS_STYLE}
        </head>
        <body>
            <div class="container">
                <h2>Register</h2>
                <form method="post" action="/register">
                    <input type="text" name="username" placeholder="Username" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Register</button>
                </form>
                <p class="info">Already have an account? <a href='/'>Login here</a></p>
            </div>
        </body>
    </html>
    """


@app.post("/register")
async def register(request: Request, username: str = Form(), password: str = Form()):
    if username in USERS:
        return HTMLResponse(f"""
        <html>
            <head>
                <title>Error</title>
                {CSS_STYLE}
            </head>
            <body>
                <div class="container">
                    <h2 class="error">Username already exists</h2>
                    <a href='/register'>← Back to registration</a>
                </div>
            </body>
        </html>
        """)

    # Generate TOTP secret for new user
    totp_secret = pyotp.random_base32()
    USERS[username] = {"password": password, "totp_secret": totp_secret}

    # Store username temporarily for MFA setup
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

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return f"""
    <html>
        <head>
            <title>Setup MFA</title>
            {CSS_STYLE}
        </head>
        <body>
            <div class="container">
                <h2>Setup Two-Factor Authentication</h2>
                <p class="info">Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)</p>
                <div class="qr-container">
                    <img src="data:image/png;base64,{img_str}" alt="QR Code">
                </div>
                <p class="info">Or manually enter this secret:</p>
                <div class="secret">{totp_secret}</div>
                <form method="post" action="/verify-mfa-setup">
                    <input type="text" name="totp_code" placeholder="Enter 6-digit code" required maxlength="6">
                    <button type="submit">Verify and Complete Setup</button>
                </form>
            </div>
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

    return HTMLResponse(f"""
    <html>
        <head>
            <title>Error</title>
            {CSS_STYLE}
        </head>
        <body>
            <div class="container">
                <h2 class="error">Invalid code. Please try again.</h2>
                <a href='/setup-mfa'>← Back</a>
            </div>
        </body>
    </html>
    """)


@app.post("/login")
async def login(request: Request, username: str = Form(), password: str = Form()):
    user_data = USERS.get(username)
    if user_data and user_data["password"] == password:
        request.session["mfa_user"] = username
        return RedirectResponse("/verify-mfa", status_code=status.HTTP_302_FOUND)

    return HTMLResponse(f"""
    <html>
        <head>
            <title>Error</title>
            {CSS_STYLE}
        </head>
        <body>
            <div class="container">
                <h2 class="error">Invalid credentials</h2>
                <a href='/'>← Back to login</a>
            </div>
        </body>
    </html>
    """)


@app.get("/verify-mfa", response_class=HTMLResponse)
async def verify_mfa_page(request: Request):
    if not request.session.get("mfa_user"):
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

    return f"""
    <html>
        <head>
            <title>Two-Factor Authentication</title>
            {CSS_STYLE}
        </head>
        <body>
            <div class="container">
                <h2>Two-Factor Authentication</h2>
                <p class="info">Enter the 6-digit code from your authenticator app</p>
                <form method="post" action="/verify-mfa">
                    <input type="text" name="totp_code" placeholder="Enter 6-digit code" required maxlength="6">
                    <button type="submit">Verify</button>
                </form>
                <p class="info"><a href='/'>← Cancel</a></p>
            </div>
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

    return HTMLResponse(f"""
    <html>
        <head>
            <title>Error</title>
            {CSS_STYLE}
        </head>
        <body>
            <div class="container">
                <h2 class="error">Invalid code</h2>
                <a href='/verify-mfa'>← Try again</a>
            </div>
        </body>
    </html>
    """)


@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

    return f"""
    <html>
        <head>
            <title>Home</title>
            {CSS_STYLE}
        </head>
        <body>
            <div class="container">
                <h1>Welcome, {user}!</h1>
                <p class="info">You have successfully logged in with two-factor authentication.</p>
                <a href='/logout'>Logout →</a>
            </div>
        </body>
    </html>
    """


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
