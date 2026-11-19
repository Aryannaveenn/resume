# Deploying to EC2 (Nginx, HTTPS and auto-deploy from GitHub)

When you're done, `git push` will make the site live at `https://yourdomain.com` within about 20 seconds.

```
your laptop ──git push──▶ GitHub ──Actions: ssh──▶ EC2 ──git pull──▶ /var/www/resume ◀── Nginx (HTTPS) ◀── visitors
```

Commands marked **(laptop)** run on your Mac. Commands marked **(server)** run on the EC2 instance over SSH.

---

## Part 1: Push the code to GitHub

1. Create a new repository on GitHub (for example `resume`). Public is simplest. Private works too, but needs one extra step in Part 4.
2. **(laptop)** From this folder:

   ```bash
   git add .
   git commit -m "Initial site"
   git remote add origin git@github.com:Aryannaveenn/resume.git
   git push -u origin main
   ```

   The Actions tab will show a failed **Deploy to EC2** run at this point. That's expected, because the server and secrets don't exist yet.

---

## Part 2: Launch the EC2 instance

1. In the AWS console, open **EC2 → Launch instance**.
   - **Name:** `resume-site`
   - **AMI:** Ubuntu Server 26.04 LTS (64-bit x86). The default login user is `ubuntu`.
   - **Instance type:** `t3.micro`. Its 2 vCPUs and 1 GB of RAM are plenty for Nginx serving a static site.
   - **Key pair:** create one called `resume-ec2`, type ED25519, format `.pem`. It downloads to your Mac. Keep it safe.
   - **Network settings → Create security group** with these inbound rules:
     | Type  | Port | Source    |
     |-------|------|-----------|
     | SSH   | 22   | 0.0.0.0/0 |
     | HTTP  | 80   | 0.0.0.0/0 |
     | HTTPS | 443  | 0.0.0.0/0 |

     SSH has to be open to everyone because GitHub Actions connects from IP addresses that change. That's safe because EC2 only accepts key-based logins, not passwords.
2. Click **Launch instance**.
3. **Give it a fixed IP.** Go to **EC2 → Elastic IPs → Allocate Elastic IP address → Allocate**. Then choose **Actions → Associate Elastic IP address**, select your instance and click **Associate**. Without this, the IP changes whenever the instance stops, which would break your DNS and the deploy.
4. **(laptop)** Connect to the server:

   ```bash
   mv ~/Downloads/resume-ec2.pem ~/.ssh/
   chmod 400 ~/.ssh/resume-ec2.pem
   ssh -i ~/.ssh/resume-ec2.pem ubuntu@<ELASTIC_IP>
   ```

   Type `yes` the first time. Everything in Parts 3 to 6 happens in this SSH session.

---

## Part 3: Point your domain at the server

You need a domain for HTTPS. Let's Encrypt won't issue certificates for bare IP addresses. If you don't have a domain yet, skip this part and Part 6. The site will still work over plain HTTP at the IP address.

At your domain registrar (Namecheap, GoDaddy, Cloudflare or Route 53), add two DNS records:

| Type | Name  | Value          |
|------|-------|----------------|
| A    | `@`   | `<ELASTIC_IP>` |
| A    | `www` | `<ELASTIC_IP>` |

If you use Cloudflare, set both records to **DNS only** (grey cloud) for now, so that Certbot can verify the domain.

**(laptop)** Check it with `dig +short yourdomain.com`. It should print your Elastic IP. DNS can take a few minutes to update.

---

## Part 4: Install Nginx and clone the site

1. **(server)** Install the software:

   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y nginx git
   ```

   Visit `http://<ELASTIC_IP>`. You should see the "Welcome to nginx" page.

2. **(server) Private repo only:** let the server read it with a read-only deploy key.

   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N "" -C "ec2-read"
   cat ~/.ssh/github_deploy.pub
   ```

   On GitHub, open the repo, then **Settings → Deploy keys → Add deploy key**. Paste the key, leave **Allow write access** unticked, and save. Then run:

   ```bash
   cat >> ~/.ssh/config <<'EOF'
   Host github.com
     IdentityFile ~/.ssh/github_deploy
     IdentitiesOnly yes
   EOF
   ssh -T git@github.com     # type "yes" once; it should greet you by repo name
   ```

3. **(server)** Clone the site into the web root:

   ```bash
   sudo mkdir -p /var/www/resume
   sudo chown ubuntu:ubuntu /var/www/resume

   # public repo:
   git clone https://github.com/Aryannaveenn/resume.git /var/www/resume
   # private repo (use this instead):
   # git clone git@github.com:Aryannaveenn/resume.git /var/www/resume
   ```

   The folder belongs to `ubuntu`. That lets the deploy run `git pull` without `sudo`, and Nginx can still read the files.

---

## Part 5: Configure Nginx

1. **(server)** Install the site config from the repo:

   ```bash
   sudo cp /var/www/resume/deploy/nginx.conf /etc/nginx/sites-available/resume
   sudo sed -i 's/example\.com/yourdomain.com/g' /etc/nginx/sites-available/resume
   ```

   Replace `yourdomain.com` with your real domain. If you have no domain, run `sudo nano /etc/nginx/sites-available/resume` instead and change the `server_name` line to `server_name _;`.

2. **(server)** Enable the site and turn off the default page:

   ```bash
   sudo ln -s /etc/nginx/sites-available/resume /etc/nginx/sites-enabled/resume
   sudo rm -f /etc/nginx/sites-enabled/default
   sudo nginx -t                  # must say "syntax is ok" and "test is successful"
   sudo systemctl reload nginx
   ```

3. Visit `http://yourdomain.com` (or the IP). You should see your site.

4. Check that the git folder is hidden. Visiting `http://yourdomain.com/.git/config` must return **404**.

---

## Part 6: HTTPS with Certbot

1. **(server)** Install Certbot and request a certificate:

   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

   - Enter your email (it's used for expiry warnings) and agree to the terms.
   - Certbot gets a free Let's Encrypt certificate and edits the Nginx config to serve HTTPS. It also redirects HTTP to HTTPS automatically.

2. **(server)** Confirm that the certificate will renew itself (certificates last 90 days, and a timer renews them):

   ```bash
   sudo certbot renew --dry-run
   systemctl list-timers | grep certbot
   ```

3. Visit `https://yourdomain.com`. You should see the padlock. If you use Cloudflare, you can now switch the records back to **Proxied** and set SSL/TLS mode to **Full (strict)**.

Certbot changes the copy in `/etc/nginx/sites-available/`, not `deploy/nginx.conf` in the repo, so later deploys won't undo the HTTPS setup.

---

## Part 7: Let GitHub Actions SSH into the server

The workflow needs its own SSH key. Don't reuse your `.pem` file. A separate key can be revoked without locking you out.

1. **(server)** Create the deploy key and authorise it:

   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/gha_deploy -N "" -C "github-actions"
   cat ~/.ssh/gha_deploy.pub >> ~/.ssh/authorized_keys
   cat ~/.ssh/gha_deploy
   ```

   Copy the whole private key output, including the `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END ...-----` lines.

2. On GitHub, open the repo, then **Settings → Secrets and variables → Actions → New repository secret**. Add these three secrets:

   | Name          | Value                                   |
   |---------------|-----------------------------------------|
   | `EC2_HOST`    | your Elastic IP (or `yourdomain.com`)   |
   | `EC2_USER`    | `ubuntu`                                |
   | `EC2_SSH_KEY` | the private key you just copied         |

   If you cloned somewhere other than `/var/www/resume`, also open the **Variables** tab and add `EC2_APP_DIR` with that path.

3. **(server)** Delete the private key from the server. GitHub has the only copy now:

   ```bash
   rm ~/.ssh/gha_deploy
   ```

---

## Part 8: Test the pipeline

1. **(laptop)** Make a visible change, for example edit a line in `index.html`. Then:

   ```bash
   git commit -am "Test deploy"
   git push
   ```

2. On GitHub, open **Actions → Deploy to EC2**. The run should go green within about 20 seconds, and the last log line reads `Deployed <commit> to /var/www/resume`.
3. Refresh the site to see the change. You can also re-run a deploy at any time from **Actions → Deploy to EC2 → Run workflow**.

What the workflow does on each push to `main`:

1. Writes the `EC2_SSH_KEY` secret to a temporary key file on the GitHub runner.
2. SSHes in as `EC2_USER@EC2_HOST`.
3. Runs `git fetch` and `git reset --hard origin/main` in `/var/www/resume`. This matches GitHub exactly, even if a file was edited on the server by mistake.
4. Deletes the key from the runner.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Permission denied (publickey)` in Actions | Check that `EC2_SSH_KEY` has the full private key, including the BEGIN and END lines. Check that the public half is in `~/.ssh/authorized_keys` and that `EC2_USER` is `ubuntu`. |
| Actions hangs or times out on SSH | Port 22 isn't open to `0.0.0.0/0` in the security group, or `EC2_HOST` is the old non-elastic IP. |
| `cd: /var/www/resume: No such file` | You cloned to a different folder. Set the `EC2_APP_DIR` variable. |
| `fatal: could not read from remote` on the server | Private repo with no deploy key. Repeat Part 4, step 2, then test with `ssh -T git@github.com`. |
| `Permission denied` writing files during the pull | Run `sudo chown -R ubuntu:ubuntu /var/www/resume`. |
| Certbot fails with a challenge error | DNS doesn't point at the instance yet (check with `dig +short yourdomain.com`), port 80 is closed, or Cloudflare proxy is on. |
| Site shows the old version | Hard refresh (Cmd+Shift+R). HTML is never cached, but CSS and JS are cached for 7 days. |
| Nginx 403 or 404 on the home page | Check the `root` path in `/etc/nginx/sites-available/resume` and run `sudo nginx -t`. |
