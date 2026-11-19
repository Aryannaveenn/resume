# Aryan Naveen: resume site

A static portfolio site (plain HTML, CSS and JS, no build step) hosted on AWS EC2 behind Nginx.

- `index.html`, `styles.css`, `main.js`: the site. Open `index.html` in a browser to preview.
- `.github/workflows/deploy.yml`: on every push to `main`, SSHes into the EC2 instance and pulls the latest code.
- `deploy/nginx.conf`: Nginx site config for the server.
- [`DEPLOY.md`](DEPLOY.md): step-by-step guide covering EC2, Nginx, HTTPS with Certbot, and the GitHub Actions SSH setup.

The "Save as PDF" button prints the page with a print stylesheet that lays it out as a resume.

## How deploys work

`git push` to `main` → GitHub Actions → SSH into EC2 → `git fetch` and `git reset --hard origin/main` in `/var/www/resume`. Nginx serves that folder directly, so the change is live as soon as the job finishes. There's no build or restart.

The workflow needs these repo secrets: `EC2_HOST`, `EC2_USER` and `EC2_SSH_KEY`. You can also set an optional `EC2_APP_DIR` variable. See [DEPLOY.md](DEPLOY.md) for the full setup.
