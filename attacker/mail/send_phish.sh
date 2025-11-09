curl --url "smtp://localhost:8025" \
  --mail-from "attacker@attacker.com" \
  --mail-rcpt "victim@victim.com" \
  --upload-file - <<'EOF'
Subject: <phishing subject here>
From: attacker@attacker.com
To: victim@victim.com
Date: $(date -R)

<phishing message here>
EOF
