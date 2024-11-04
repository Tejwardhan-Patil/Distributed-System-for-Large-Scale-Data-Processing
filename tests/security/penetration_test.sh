#!/bin/bash

# Penetration Testing Script
# This script automates basic security tests on the target system.

# Set target domain or IP address
TARGET="website.com"

# Log file to store test results
LOGFILE="penetration_test_results.log"

# Print and log function
log() {
  echo "$1"
  echo "$1" >> $LOGFILE
}

# Start the test
log "Starting Penetration Test on $TARGET"

# 1. Nmap scan for open ports
log "Running Nmap scan for open ports..."
nmap -sS -O -T4 $TARGET >> $LOGFILE
log "Nmap scan completed."

# 2. SSL/TLS scan for weak ciphers
log "Running SSL scan for weak ciphers..."
sslscan $TARGET >> $LOGFILE
log "SSL scan completed."

# 3. Checking HTTP methods allowed
log "Checking HTTP methods allowed..."
curl -s -X OPTIONS -I http://$TARGET | grep 'Allow' >> $LOGFILE
log "HTTP methods check completed."

# 4. Test for SQL Injection vulnerabilities using SQLMap
log "Running SQLMap for SQL Injection test..."
sqlmap -u http://$TARGET --batch >> $LOGFILE
log "SQLMap test completed."

# 5. Check for outdated software packages
log "Checking for outdated packages..."
apt list --upgradable >> $LOGFILE
log "Outdated packages check completed."

# 6. Nikto scan for common vulnerabilities
log "Running Nikto scan..."
nikto -h $TARGET >> $LOGFILE
log "Nikto scan completed."

# 7. Test for XSS vulnerabilities using XSStrike
log "Running XSStrike for XSS testing..."
xsstrike --url http://$TARGET >> $LOGFILE
log "XSStrike XSS test completed."

# 8. Running OWASP ZAP for automated vulnerability scan
log "Running OWASP ZAP automated vulnerability scan..."
zap-baseline.py -t http://$TARGET -r zap_report.html >> $LOGFILE
log "OWASP ZAP scan completed. Report saved as zap_report.html."

# 9. Brute force testing on login page (Hydra)
log "Running Hydra for brute force testing on login page..."
hydra -l admin -P /usr/share/wordlists/rockyou.txt $TARGET http-post-form "/login.php:username=^USER^&password=^PASS^:F=incorrect" >> $LOGFILE
log "Brute force testing completed."

# 10. Directory enumeration using Dirb
log "Running Dirb for directory enumeration..."
dirb http://$TARGET >> $LOGFILE
log "Directory enumeration completed."

# 11. DNS enumeration using DNSRecon
log "Running DNSRecon for DNS enumeration..."
dnsrecon -d $TARGET >> $LOGFILE
log "DNS enumeration completed."

# 12. Test for file upload vulnerabilities
log "Checking for unrestricted file upload vulnerabilities..."
curl -F "file=@testfile.php" http://$TARGET/upload >> $LOGFILE
log "File upload test completed."

# 13. Checking for weak SSH configurations
log "Checking for weak SSH configurations..."
ssh-audit $TARGET >> $LOGFILE
log "SSH configuration check completed."

# 14. WPSCAN for WordPress vulnerability check
log "Running WPScan for WordPress vulnerability check..."
wpscan --url http://$TARGET --enumerate vp >> $LOGFILE
log "WPScan completed."

# 15. Searching for sensitive information in source code using GitLeaks
log "Running GitLeaks to search for sensitive information..."
gitleaks --path /var/www/html/ --report-format json --report-path gitleaks_report.json >> $LOGFILE
log "GitLeaks scan completed."

# 16. Running Trivy to check for vulnerabilities in Docker containers
log "Running Trivy to check for vulnerabilities in Docker containers..."
trivy image $TARGET:latest >> $LOGFILE
log "Trivy scan completed."

# 17. Checking for misconfigured headers using Security Headers
log "Checking for misconfigured security headers..."
curl -I http://$TARGET | grep -i "x-" >> $LOGFILE
log "Security headers check completed."

# 18. WAF detection using WAFW00F
log "Running WAFW00F to detect WAF presence..."
wafw00f http://$TARGET >> $LOGFILE
log "WAF detection completed."

# 19. Running Burp Suite for advanced security testing
log "Running Burp Suite scan..."
burpsuite -t http://$TARGET >> $LOGFILE
log "Burp Suite scan completed."

# 20. Test for SSRF vulnerabilities
log "Running SSRF vulnerability test..."
curl -s http://$TARGET/fetch?url=http://internal_service >> $LOGFILE
log "SSRF test completed."

# 21. Checking for open S3 buckets
log "Checking for open S3 buckets..."
aws s3 ls s3://$TARGET --no-sign-request >> $LOGFILE
log "S3 bucket check completed."

# 22. Network security scan using OpenVAS
log "Running OpenVAS for network security scan..."
openvas -q --target $TARGET >> $LOGFILE
log "OpenVAS scan completed."

# 23. Test for insecure direct object references (IDOR)
log "Testing for IDOR vulnerabilities..."
curl -X GET http://$TARGET/account?id=1 >> $LOGFILE
curl -X GET http://$TARGET/account?id=2 >> $LOGFILE
log "IDOR test completed."

# 24. Test for Cross-Site Request Forgery (CSRF)
log "Running CSRF test..."
csrfpoc -u http://$TARGET/login -m POST -d "username=nate&password=paul" >> $LOGFILE
log "CSRF test completed."

# 25. Vulnerability scan using OpenSCAP
log "Running OpenSCAP for security compliance check..."
oscap xccdf eval --profile xccdf_org.ssgproject.content_profile_standard $TARGET >> $LOGFILE
log "OpenSCAP scan completed."

# Test conclusion
log "Penetration test completed on $TARGET. Review the log file $LOGFILE for detailed results."