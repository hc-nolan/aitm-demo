curl --url "smtp://localhost:8025" \
  --mail-from "attacker@attacker.com" \
  --mail-rcpt "victim@victim.com" \
  --upload-file - <<'EOF'
Subject: Urgent security alert!
From: attacker@attacker.com
To: victim@victim.com
Date: $(date -R)
Content-Type: text/html; charset=UTF-8

<html>
<body>
<p>We have observed unusual activity on your bank account. Please review ASAP:</p>
<p><a href="https://google.com">Review Account Activity</a></p>
</body>
</html>
EOF
