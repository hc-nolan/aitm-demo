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
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        min-height: 100vh;
        padding: 20px;
    }
    .container {
        max-width: 500px;
        margin: 50px auto;
        background: white;
        padding: 40px;
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    }
    .logo {
        text-align: center;
        margin-bottom: 30px;
    }
    .logo h1 {
        color: #1e3c72;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .logo p {
        color: #666;
        font-size: 14px;
    }
    h2 {
        color: #333;
        margin-bottom: 20px;
        font-size: 24px;
    }
    input[type="text"], input[type="password"] {
        width: 100%;
        padding: 14px;
        margin: 10px 0;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        font-size: 15px;
        transition: border-color 0.3s;
    }
    input[type="text"]:focus, input[type="password"]:focus {
        outline: none;
        border-color: #1e3c72;
    }
    button {
        width: 100%;
        padding: 14px;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-size: 16px;
        font-weight: 600;
        margin-top: 15px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(30, 60, 114, 0.3);
    }
    a {
        color: #1e3c72;
        text-decoration: none;
        font-weight: 500;
    }
    a:hover {
        text-decoration: underline;
    }
    .error {
        background-color: #fee;
        color: #c33;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 15px;
        border-left: 4px solid #c33;
    }
    .info {
        color: #666;
        font-size: 14px;
        margin: 15px 0;
        text-align: center;
    }
    .qr-container {
        text-align: center;
        margin: 20px 0;
        background: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
    }
    .secret {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        font-family: monospace;
        word-break: break-all;
        font-size: 13px;
        border: 2px dashed #ddd;
        margin: 15px 0;
    }
    .dashboard {
        max-width: 900px;
    }
    .dashboard-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 30px;
        border-radius: 12px;
        margin-bottom: 30px;
    }
    .dashboard-header h1 {
        font-size: 28px;
        margin-bottom: 10px;
    }
    .dashboard-header p {
        opacity: 0.9;
        font-size: 14px;
    }
    .account-card {
        background: white;
        padding: 25px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .account-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        padding-bottom: 15px;
        border-bottom: 2px solid #f0f0f0;
    }
    .account-type {
        color: #666;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .account-number {
        color: #999;
        font-size: 13px;
        font-family: monospace;
    }
    .balance {
        font-size: 36px;
        font-weight: 700;
        color: #1e3c72;
        margin: 10px 0;
    }
    .balance-label {
        color: #666;
        font-size: 13px;
        margin-bottom: 5px;
    }
    .transactions {
        margin-top: 20px;
    }
    .transactions h3 {
        color: #333;
        font-size: 18px;
        margin-bottom: 15px;
    }
    .transaction {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px 0;
        border-bottom: 1px solid #f0f0f0;
    }
    .transaction:last-child {
        border-bottom: none;
    }
    .transaction-info {
        flex: 1;
    }
    .transaction-name {
        font-weight: 600;
        color: #333;
        margin-bottom: 3px;
    }
    .transaction-date {
        font-size: 13px;
        color: #999;
    }
    .transaction-amount {
        font-weight: 700;
        font-size: 16px;
    }
    .transaction-amount.positive {
        color: #28a745;
    }
    .transaction-amount.negative {
        color: #333;
    }
    .logout-btn {
        background: white;
        color: #1e3c72;
        border: 2px solid #1e3c72;
        margin-top: 20px;
    }
    .logout-btn:hover {
        background: #f8f9fa;
    }
    .security-badge {
        display: inline-flex;
        align-items: center;
        background: #e8f5e9;
        color: #2e7d32;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        margin-top: 10px;
    }
    .security-badge::before {
        content: "🔒";
        margin-right: 6px;
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
            <title>SecureBank - Login</title>
            {CSS_STYLE}
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <h1>🏦 SecureBank</h1>
                    <p>Your trusted financial partner</p>
                </div>
                <h2>Account Login</h2>
                <form method="post" action="/login">
                    <input type="text" name="username" placeholder="Username" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Sign In</button>
                </form>
                <div class="security-badge">Two-Factor Authentication Protected</div>
                <p class="info">Don't have an account? <a href='/register'>Open an account</a></p>
            </div>
        </body>
    </html>
    """


@app.get("/register", response_class=HTMLResponse)
async def register_page():
    return f"""
    <html>
        <head>
            <title>SecureBank - Open Account</title>
            {CSS_STYLE}
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <h1>🏦 SecureBank</h1>
                    <p>Your trusted financial partner</p>
                </div>
                <h2>Open New Account</h2>
                <form method="post" action="/register">
                    <input type="text" name="username" placeholder="Choose Username" required>
                    <input type="password" name="password" placeholder="Choose Password" required>
                    <button type="submit">Create Account</button>
                </form>
                <p class="info">Already have an account? <a href='/'>Sign in here</a></p>
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
                    <div class="error">Username already exists. Please choose a different username.</div>
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
        name=username, issuer_name="SecureBank"
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
            <title>Setup Two-Factor Authentication</title>
            {CSS_STYLE}
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <h1>🏦 SecureBank</h1>
                </div>
                <h2>Secure Your Account</h2>
                <p class="info">Scan this QR code with your authenticator app (Google Authenticator, Authy, Microsoft Authenticator, etc.)</p>
                <div class="qr-container">
                    <img src="data:image/png;base64,{img_str}" alt="QR Code">
                </div>
                <p class="info">Or manually enter this secret key:</p>
                <div class="secret">{totp_secret}</div>
                <form method="post" action="/verify-mfa-setup">
                    <input type="text" name="totp_code" placeholder="Enter 6-digit code" required maxlength="6" pattern="[0-9]{{6}}">
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
                <div class="error">Invalid verification code. Please try again.</div>
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
                <div class="error">Invalid username or password. Please try again.</div>
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
                <div class="logo">
                    <h1>🏦 SecureBank</h1>
                </div>
                <h2>Verify Your Identity</h2>
                <p class="info">Enter the 6-digit code from your authenticator app</p>
                <form method="post" action="/verify-mfa">
                    <input type="text" name="totp_code" placeholder="Enter 6-digit code" required maxlength="6" pattern="[0-9]{{6}}" autofocus>
                    <button type="submit">Verify</button>
                </form>
                <p class="info"><a href='/logout'>← Cancel</a></p>
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
                <div class="error">Invalid verification code. Please try again.</div>
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
            <title>SecureBank - Account Dashboard</title>
            {CSS_STYLE}
        </head>
        <body>
            <div class="container dashboard">
                <div class="dashboard-header">
                    <h1>Welcome back, {user}!</h1>
                    <p>Last login: Today at 2:34 PM</p>
                </div>

                <div class="account-card">
                    <div class="account-header">
                        <div>
                            <div class="account-type">Checking Account</div>
                            <div class="account-number">****7892</div>
                        </div>
                    </div>
                    <div class="balance-label">Available Balance</div>
                    <div class="balance">$12,847.32</div>
                </div>

                <div class="account-card">
                    <div class="account-header">
                        <div>
                            <div class="account-type">Savings Account</div>
                            <div class="account-number">****4521</div>
                        </div>
                    </div>
                    <div class="balance-label">Available Balance</div>
                    <div class="balance">$45,293.67</div>
                </div>

                <div class="account-card">
                    <div class="transactions">
                        <h3>Recent Transactions</h3>
                        <div class="transaction">
                            <div class="transaction-info">
                                <div class="transaction-name">Salary Deposit</div>
                                <div class="transaction-date">Nov 5, 2025</div>
                            </div>
                            <div class="transaction-amount positive">+$4,250.00</div>
                        </div>
                        <div class="transaction">
                            <div class="transaction-info">
                                <div class="transaction-name">Rent Payment</div>
                                <div class="transaction-date">Nov 1, 2025</div>
                            </div>
                            <div class="transaction-amount negative">-$1,850.00</div>
                        </div>
                        <div class="transaction">
                            <div class="transaction-info">
                                <div class="transaction-name">Grocery Store</div>
                                <div class="transaction-date">Oct 30, 2025</div>
                            </div>
                            <div class="transaction-amount negative">-$127.48</div>
                        </div>
                        <div class="transaction">
                            <div class="transaction-info">
                                <div class="transaction-name">Electric Company</div>
                                <div class="transaction-date">Oct 28, 2025</div>
                            </div>
                            <div class="transaction-amount negative">-$94.32</div>
                        </div>
                        <div class="transaction">
                            <div class="transaction-info">
                                <div class="transaction-name">Online Transfer</div>
                                <div class="transaction-date">Oct 25, 2025</div>
                            </div>
                            <div class="transaction-amount positive">+$500.00</div>
                        </div>
                    </div>
                </div>

                <a href='/logout'><button class="logout-btn">Sign Out</button></a>
            </div>
        </body>
    </html>
    """


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
