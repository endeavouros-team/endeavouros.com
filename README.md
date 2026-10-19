# EndeavourOS website

This repository holds the source for the endeavouros.com website.
[Astro](https://astro.build), a static site generator, turns that source into static HTML.
The deployed site has no runtime, database, admin panel or writable file in its webroot.

## How a change reaches the server

1. Edit files in this repository.
2. Push the changes to GitHub.
3. Push a `v*` tag.
4. GitHub's CI builds the release tarball and attaches it to a Release.
5. Download that file and unpack it on the server.

A commit is a saved set of changes with a message; push means send commits to GitHub; a
tag is a named bookmark on a commit, and pushing it starts the build; CI is GitHub's
automatic build jobs.

The tarball is named `eos-site-<tag>-<short sha>.tar.gz`, for example
`eos-site-v2026.10.20-4a92b64.tar.gz`. It is output, never input. Nobody runs it, edits it
or makes it by hand. You never build the site on your machine to publish it. The
development server on your own machine is only for looking at your change before you
push.

## Set up your machine, once

These steps are for EndeavourOS. Python 3.11 or newer is already installed, and `make`
runs the project checks.

From any directory, install Git, make, Node.js, npm and the GitHub command-line tool:

    sudo pacman -S --needed git make nodejs npm github-cli

Pacman may ask `Proceed with installation? [Y/n]`; press Enter. It prints package progress
and returns to the prompt without an error when it succeeds. `--needed` leaves an already
installed package alone.

From any directory, connect the GitHub command-line tool to your account:

    gh auth login

Choose GitHub.com, HTTPS, answer `Y` to `Authenticate Git with your GitHub credentials?`,
and log in with a web browser. Success ends with
`✓ Logged in as` followed by your GitHub user name. This also stores the credentials
that `git push` needs.

From any directory, tell Git who you are once because a commit records an author and the
first commit otherwise stops with `Author identity unknown`:

    git config --global user.name "Your Name"
    git config --global user.email "you@example.com"

Use the name and email address of your GitHub account. The commands print nothing when
they succeed.

From any directory, move to your home directory:

    cd ~

`cd` changes directory and prints nothing when it succeeds.

From your home directory, clone the repository, which means download the project and its
change history:

    gh repo clone endeavouros-team/endeavouros.com

Success starts with `Cloning into 'endeavouros.com'...` and returns to the prompt without
an error. The files are now in `~/endeavouros.com` because this command ran from your
home directory.

From your home directory, enter the Astro directory:

    cd ~/endeavouros.com/astro

The command prints nothing. Your prompt is now in `~/endeavouros.com/astro`.

From `~/endeavouros.com/astro`, install the exact dependency versions recorded by the
project:

    npm ci

Success includes a line like `added 271 packages, and audited 272 packages in 1s`; the
counts and seconds vary. It is followed by a vulnerabilities notice that suggests
`npm audit fix`. The notice is expected and must be ignored. Do not run `npm audit fix`
because it would rewrite the lockfile that the build audits. Use `npm ci`, not
`npm install`, because `npm ci` installs exactly what the committed lockfile pins. The
build audits that lockfile before running any dependency code; the Reference says what
it rejects.

On another distribution, install Node 22.12 or newer. For people who manage Node with
nvm, `astro/.nvmrc` names Node 22.

## See the site on your machine

Start every work session by updating your copy. This prevents you from editing an old
version while somebody else's changes are already on GitHub.

From any directory, enter the repository root:

    cd ~/endeavouros.com

From `~/endeavouros.com`, download and apply the latest commits:

    git pull

Success prints `Already up to date.` or a summary ending in `Fast-forward` and changed
files.

If the list of updated files includes `astro/package-lock.json`, enter the Astro
directory and install its exact dependency versions again before starting the server:

    cd ~/endeavouros.com/astro
    npm ci

From `~/endeavouros.com`, enter the Astro directory:

    cd ~/endeavouros.com/astro

From `~/endeavouros.com/astro`, start the development server:

    npm run dev

Success includes these lines:

    ┃ Local    http://localhost:4321/
    watching for file changes...

Open the local URL in a browser; `localhost` is your own machine. Saving a file in your
editor reloads the page. The terminal stays busy until you press Ctrl-C, which stops the
server and returns to the prompt.

The server keeps this terminal busy. Open a second terminal for the commands below; it
starts in your home directory, so begin with the `cd` line each section gives.

## Everyday tasks

File paths in these tasks are relative to the repository root,
`~/endeavouros.com`. Do the task you came for, then go to "Publish"; the tasks are
independent.

### Write a news post

Copy the newest post (today `titan-nova-is-available.md`) so the existing post stays
unchanged.

From any directory, enter the repository root:

    cd ~/endeavouros.com

From `~/endeavouros.com`, copy the newest post to its new filename:

    cp astro/src/content/news/titan-nova-is-available.md astro/src/content/news/triton-is-out.md

The command prints nothing. The filename becomes the URL, so this example appears at
`/news/triton-is-out/`.

`triton-is-out` and `triton.jpg` are examples. Replace both with names for your post,
using lowercase words joined by hyphens.

The year directory may not exist yet. From `~/endeavouros.com`, create it first:

    mkdir -p astro/src/assets/news/2026

The command prints nothing and creates the directory when it is missing.

From `~/endeavouros.com`, copy the hero image from your Downloads directory into the
news assets first:

    cp ~/Downloads/triton.jpg astro/src/assets/news/2026/triton.jpg

The command prints nothing. The image is now available to the post and the Astro image
pipeline.

Open the new file in your editor. Front matter is the block between the `---` lines at
the top of a post. It has these schema fields:

- `title`: the page heading; at least 4 characters.
- `description`: a 20-200 character summary used on the news list, in the feed and in
  page metadata.
- `date`: the publication date as `YYYY-MM-DD`, for example `2026-10-20`.
- `author`: the displayed author name; at least 2 characters.
- `hero`: a path to an image placed in `astro/src/assets/news/<year>/`, for example
  `../../assets/news/2026/triton.jpg`.
- `heroAlt`: a description of the hero image, or an empty string under the rules below.
- `heroDecorative`: `true` or `false`; it records whether an empty description is
  deliberate.

Change every field the copied post carries: `title`, `description`, `date`, `author`,
`hero`, `heroAlt` and `heroDecorative`. Keep the `---` lines and the `name: value` form.
Then delete the copied body and write yours.

The hero fields have three states. A described image has useful `heroAlt` text and
`heroDecorative: false`. A deliberately decorative image has `heroAlt: ""` and
`heroDecorative: true`; release art directly below a heading that names the release is a
common example because repeating the heading would burden a screen reader. An image that
nobody has reviewed yet has `heroAlt: ""` and `heroDecorative: false`. Do not mistake the
last state for an accessibility decision.

The body after the front matter is Markdown. Existing posts use headings, bold text,
lists, links and images. These four lines show the common forms:

    ## Installation changes
    This release has **new hardware support**.
    - The installer now detects more hardware.
    Read the [release notes](https://example.com/release-notes).

An inline image can use the hero image already copied:

    ![The Triton live session](../../assets/news/2026/triton.jpg)

The `../../` path climbs from `astro/src/content/news/` to `astro/src/`.

A link to a website that no page already links to fails the build in CI, or in
`make verify`, with a `check-build` message naming the link. Add that website to
`contentOrigins` in `data/site.toml` and push again because every outbound website must
be reviewed. The development server does not run this check.

Check the post in the development server. From any directory, enter the Astro directory:

    cd ~/endeavouros.com/astro

From `~/endeavouros.com/astro`, start the server if it is not already running:

    npm run dev

The post opens at `http://localhost:4321/news/triton-is-out/`. If a front-matter field is
missing or malformed, the terminal running `npm run dev` prints
`[InvalidContentEntryDataError] news → triton-is-out data does not match collection schema.`
followed by the field, for example `description: Too small: expected string to have >=20
characters`. The browser keeps showing the old page, or, if the server was started after
the mistake, nothing answers at `localhost:4321`. Fix the field; if the server stopped,
start it again.

### Publish a new ISO or change its download links

Edit `data/release.toml`. Under `[current]`, update `codename`, `date`, `iso`, `sha512`
and `sizeBytes`. Confirm `sha512Suffix` and `sigSuffix` still match the published files.
Update the `magnet` and `torrent` lines because they also carry the ISO filename. Change
the nested signing or requirements fields only when those facts change.

Mirror URLs compose themselves from each mirror's `base`, the ISO filename and the two
suffixes. This matters because one release edit regenerates every ISO, checksum and
signature link, so one kind of link cannot drift to a different release.

From any directory, enter the repository root:

    cd ~/endeavouros.com

From `~/endeavouros.com`, validate the data and test every composed mirror URL:

    make check
    make mirrors

A pass from `make check` ends with a line starting `data ok`. `make mirrors` ends with a
reachable count.
It warns rather than fails when a URL is unavailable, so read every warning and check it
by hand.

### Add or drop a mirror

Edit `data/mirrors.toml`. A mirror entry looks like this real one:

    [[mirrors]]
    id          = "urban-wave-za"
    continent   = "Africa"
    country     = "South Africa"
    countryCode = "ZA"
    name        = "Urban Wave"
    base        = "https://mirrors.urbanwave.co.za/endeavouros/iso"

Copy an entry, paste it under the `# ---------- <Continent> ----------` comment for its
continent, for example `# ---------- Africa ----------`, and change all six values. The
`id` uses lowercase words and hyphens and must be unique. The `base` is the directory
that holds the ISO, without a trailing slash. `data/README.md` has the full rules.

To drop a mirror, delete its block or add `active = false` under it.

From any directory, enter the repository root:

    cd ~/endeavouros.com

From `~/endeavouros.com`, validate the data and test every composed mirror URL:

    make check
    make mirrors

A pass from `make check` ends with a line starting `data ok`. A problem from `make mirrors`
appears as a
`warn` row naming the mirror and which of `iso`, `sha512` or `sig` failed. Open that link
in a browser because some mirrors refuse scripted requests but serve browsers. Warnings
do not fail this target.

Preview the result at `http://localhost:4321/download/` and find the mirror. Its three
links for the ISO, checksum and signature are composed from `base`, which keeps them on
the same release.

### Change the ARM images

Edit `data/arm-images.toml`.

From any directory, enter the repository root:

    cd ~/endeavouros.com

From `~/endeavouros.com`, validate the data and test every composed ARM image URL:

    make check
    make arm

A pass from `make check` ends with a line starting `data ok`. A completely clean ARM check
ends with
`arm ok` and reports the device and URL counts. Warnings do not fail the target, so read
them.

### Change wording on a page

Open `astro/src/pages/<page>.astro`, for example `astro/src/pages/about-us.astro`. Change
the words between the HTML-like tags and leave the tags in place. Navigation, taglines
and the footer live in `data/site.toml` instead.

Check the page in the development server. From any directory, enter the Astro directory:

    cd ~/endeavouros.com/astro

From `~/endeavouros.com/astro`, start the server if it is not already running:

    npm run dev

A pass prints `http://localhost:4321/`; the edited page, for example
`http://localhost:4321/about-us/`, opens and shows the new wording.

## Publish

You need push access to the repository; everyone on the website team has it. Anyone else
opens a pull request instead, see `CONTRIBUTING.md`.

From any directory, enter the repository root:

    cd ~/endeavouros.com

From `~/endeavouros.com`, you can run the same checks as CI before continuing:

    make verify
    make links

This optional check takes about a minute and saves a round trip when something is wrong;
CI runs it anyway.

From `~/endeavouros.com`, inspect the worktree:

    git status

It lists the current branch and every changed, new or deleted file. Confirm that only the
intended files appear.

From `~/endeavouros.com`, stage every intended change:

    git add -A

Stage means mark a change to go into the next commit, and `git add -A` stages every file
that `git status` listed. The command prints nothing. A second `git status` lists the
files under `Changes to be committed`.

If `git status` listed a file you did not change, unstage it with
`git restore --staged <path>` and look at it before going on. For example, from
`~/endeavouros.com`:

    git restore --staged data/release.toml

From `~/endeavouros.com`, make the commit:

    git commit -m "news: Triton is out"

Replace the example message with one describing your change. Use a lowercase
`area: summary` subject. For the mirror task, for example, use this instead:

    git commit -m "mirrors: add Urban Wave"

Run one commit command, not both. Success prints the branch, a short commit ID and the
number of files changed.

From `~/endeavouros.com`, push the commit:

    git push

Success ends with the local and remote branch names and returns to the prompt. Open the
repository's [Actions](https://github.com/endeavouros-team/endeavouros.com/actions) page
and wait for the Check run to show a green tick. The run for your commit is the top row
carrying your commit message. To watch it in the terminal instead, run this from
`~/endeavouros.com`:

    gh run watch

It first asks which run to watch; pick the top one. Success ends with every Check job
marked complete and successful. A green Check run does not publish the site.

Open the [Releases](https://github.com/endeavouros-team/endeavouros.com/releases) page to
see the tags already used. A tag can also exist without a Release when its build failed, so
check your copy as well, from `~/endeavouros.com`:

    git tag -l v2026.10.20

Output means the tag exists; append `.1`. No output means it is free.

Next make and push the release tag. A tag is a named bookmark on a commit; pushing one is
what starts the build. Use `vYYYY.MM.DD`, for example `v2026.10.20`. Use `.1`, `.2` and so
on for another release on the same day, for example `v2026.10.20.1`. Use your tag, not
the example, in every later command.

From `~/endeavouros.com`, tag the commit and push the tag:

    git tag -a v2026.10.20 -m "news: Triton"
    git push origin v2026.10.20

The first command prints nothing. The second ends with `[new tag]` and
`v2026.10.20 -> v2026.10.20`. Pushing the tag starts the Build site workflow. Pushing to
`main` alone publishes nothing.

Open the Actions page and wait for the Build site run to show a green tick. From
`~/endeavouros.com`, the terminal alternative is:

    gh run watch

Again pick the top run when asked. Success ends with every Build site job marked complete
and successful. The Releases page then lists an asset named
`eos-site-v2026.10.20-<short sha>.tar.gz`, for example
`eos-site-v2026.10.20-4a92b64.tar.gz`.

From `~/endeavouros.com`, download the release tarball:

    gh release download v2026.10.20 -p '*.tar.gz' -D ~/Downloads

Use your tag in this command. Success prints the download progress and the file appears
in `~/Downloads`. Keeping it outside the repository prevents a later `git add -A` from
staging the tarball. The Releases page in a browser provides the same file.

On your own computer, copy the tarball the way you already reach the server. For example,
from any directory:

    scp ~/Downloads/eos-site-v2026.10.20-*.tar.gz you@server:

Replace `you` and `server` with your server account and host. Success prints transfer
progress and puts the file in that account's home directory.

On the server, start in the home directory that holds the copied tarball. Create a fresh
directory, unpack into it, set its ownership, swap it into place and reload nginx:

    sudo rm -rf /var/www/endeavouros.com.new
    sudo mkdir /var/www/endeavouros.com.new
    sudo tar -xzf eos-site-v2026.10.20-*.tar.gz -C /var/www/endeavouros.com.new/
    sudo chown -R root:root /var/www/endeavouros.com.new
    sudo mv /var/www/endeavouros.com /var/www/endeavouros.com.old
    sudo mv /var/www/endeavouros.com.new /var/www/endeavouros.com
    sudo nginx -t && sudo systemctl reload nginx

Use your tag in the tarball name. `/var/www/endeavouros.com` is the webroot named in
`deploy/nginx-production.conf` and must match the host. The webroot therefore holds only
this release. Tar adds and replaces files but never removes old ones, which is why the
release is unpacked into a fresh directory. An rsync of an extracted copy needs
`--delete` for the same reason.

The webroot and everything in it must be owned by root or a dedicated deploy user, and
the nginx user must have no write access through ownership, group or ACL. Neither the
tarball nor nginx can enforce that rule. On 2026-09-23 the previous host's root page was
replaced by a defacement. How the file was written was not established, so ownership is a
rule, not a diagnosis.

The first five server commands print nothing on success. Success from the nginx test
includes `syntax is ok` and `test is successful`; the reload prints no error.

After the swap, verify the public site. From any directory on a machine with `curl`, run:

    curl -sI https://endeavouros.com/ | grep -iE 'content-security-policy|strict-transport|x-content-type|x-frame|referrer-policy'
    curl -s  https://endeavouros.com/robots.txt
    curl -sI https://endeavouros.com/feed/
    curl -sI https://endeavouros.com/comments/feed/
    curl -sI https://endeavouros.com/endeavouros-arm-install/
    curl -sI https://endeavouros.com/privacy-policy-2/
    curl -sI https://arm.endeavouros.com/
    curl -sI https://www.endeavouros.com/

The first prints the security headers. `robots.txt` must print `Allow: /` and a sitemap.
A redirect appears as an `HTTP/2 301` line followed by a `location:` line naming its
destination. The next lines must return, in order: 301 to `/news/feed.xml`, 410, 301 to
`/endeavouros-arm/`, 301 to `/privacy-policy/`, 301 to `/endeavouros-arm/`, and 301 to
`https://endeavouros.com/` without a TLS error. The `arm.` check is expected to fail until
its DNS moves from the previous host; the reference gives the required order.

After the checks pass, on the server from any directory, remove the old release:

    sudo rm -rf /var/www/endeavouros.com.old

This removes the rollback copy, so run it only after the new release passes the checks.

Back on your own computer, open the page you published, for example
`https://endeavouros.com/news/triton-is-out/`, or
`https://endeavouros.com/download/` for a mirror, and confirm the change is there.

On your own computer, from any directory, return to the repository root:

    cd ~/endeavouros.com

From `~/endeavouros.com`, probe the live site:

    make spam-check

A clean run ends with `no hijack signals` and says that the cloaking and keyword checks
are clean. Read any hygiene warning as deployment work still to do.

## When something goes wrong

- `npm ci` fails. From `~/endeavouros.com/astro`, check the Node version:

        node --version

  It must print `v22.12.0` or higher. On EndeavourOS, from any directory, bring Node.js
  and npm current:

        sudo pacman -Syu nodejs npm

- `make check` fails: its message names the file and field. Correct that value and run the
  check again.
- The browser cannot reach `localhost:4321` after `npm run dev`: read the terminal. A post
  with a bad front-matter field stops the server before it listens. Fix the field and start
  the server again.
- A Check run is red: open it; the failed step names the problem. Fix the problem, commit
  it and push again. A new Check run starts for the new commit.
- A Build site run is red: if your change caused it, fix the problem, commit and push,
  then push a new tag with `.1` appended because the first tag points at the old commit.
  If it failed for a reason outside your change, rebuild the same tag as "Cutting and
  rebuilding a release" under Reference describes.
- `git push` is rejected. From `~/endeavouros.com`, update your copy, then try the push
  again:

        git pull
        git push

  If `git pull` reports a conflict, stop and ask in the team channel rather than guessing.
- The site did not change after a push: no tag was pushed, the Build site run is red, or
  the tarball was downloaded but not unpacked and swapped in. Check the Releases page and
  the Actions page in that order.
- The build is green but the site is invisible to search: read the `PUBLIC_INDEXABLE`
  section in the reference.

## Reference

### Layout

- `astro/` is the main site: home, download, news, ARM and the info section.
- `data/` is content that is not markup: release, mirrors, navigation, packages and ARM
  images.
- `brand/` holds the logo SVGs and the colour tokens from which the site derives its CSS.
- `deploy/nginx-production.conf` is the live site configuration. The preview host uses
  `deploy/preview/nginx-preview.conf` and `deploy/preview/docker-compose.yml`.
- `scripts/` holds the data validators, link check and WordPress importer. Build-output
  gates live in `astro/scripts/`, where the build can run them.

### The shared data directory

`data/` is the single source of truth. The Astro content layer reads it directly. Nothing
in it is markup, so a mirror or release edit needs no toolchain installed.

| File | Holds |
|---|---|
| `data/release.toml` | The current ISO: filename, date, checksum, signing key and torrent |
| `data/mirrors.toml` | The 26 download mirrors |
| `data/site.toml` | Navigation, taglines and footer links |
| `data/packages.toml` | Preset packages and bootloader options |
| `data/arm-images.toml` | The 6 ARM device images |

Download URLs are **composed, never stored**. Each mirror has a `base`; the ISO, checksum
and signature URLs combine it with the filename and suffixes in `release.toml`. A release
bump changes `[current]` plus the magnet and torrent links and regenerates all 78 mirror
URLs. A checksum link therefore cannot drift away from its image.
`data/arm-images.toml` uses the same rule.

`make check` validates the field contract. `make mirrors` and `make arm` confirm that the
composed URLs resolve. The URL checks warn rather than fail because a briefly unavailable
mirror must not block a build. Read the output. Make an unreachable mirror an error with:

    python3 scripts/check-mirrors.py --strict

See `data/README.md` for the complete field contract.

### Build targets

The complete Make target list is:

    make check          # validate data/ against the field contract
    make links          # check internal links in astro/dist/
    make mirrors        # check every composed mirror URL
    make arm            # check every composed ARM image URL
    make spam-check     # probe the live site for a hijack
    make dev-astro      # run Astro's development server on :4321
    make build-astro    # build the site into astro/dist/
    make build          # alias for make build-astro
    make verify         # build, then run the build-output gate
    make serve          # serve astro/dist/ on :8812 for LAN review
    make deploy-preview # build and rsync to the preview host
    make clean          # remove the dist/ and .astro/ trees

There is no separate asset step. The fingerprinted assets all come out under
`astro/dist/_astro/`; images in `astro/src/assets/` are resized and converted there.
Build output is gitignored, so a clean checkout and `make build-astro` reproduce it
exactly.

Node 22.12 or later is required. The committed `.nvmrc` pins it. Use `npm ci` rather than
`npm install` because it installs exactly what the lockfile pins. `npm run build` runs
`astro/scripts/audit-lock.mjs` first. The audit rejects an install script, an off-registry
resolution or a missing integrity hash unless the package is allowlisted.

### Deploying to production

The production server has no build toolchain. CI builds the site and attaches its tarball
to a GitHub Release. Deployment downloads that output and unpacks it into the webroot.

#### Cutting and rebuilding a release

Release tags use `vYYYY.MM.DD`, with `.1`, `.2` and so on for another release that day.
`v2026.09.06` was the launch, so its next same-day tag would be:

    git tag -a v2026.09.06.1 -m "mirror list and news update"
    git push origin v2026.09.06.1

A pushed `v*` tag starts `.github/workflows/build.yml`. A push to `main` does not publish;
`.github/workflows/check.yml` checks ordinary commits and pull requests only.

The release job validates `data/`, audits the lockfile, builds with
`PUBLIC_INDEXABLE=true`, runs the build-output gate and internal-link check, and asserts
that `robots.txt` allows crawling and names the sitemap and that no page contains
`noindex`. A missing production flag fails this job instead of publishing the release.

Watch it with:

    gh run watch --repo endeavouros-team/endeavouros.com

To rebuild an existing tag after a CI fix or a partially failed run, open Actions, choose
Build site, choose Run workflow and enter the tag. Manual dispatch checks out that tag,
builds it and replaces the asset on its existing Release.

Download an asset with:

    gh release download v2026.09.06.1 --repo endeavouros-team/endeavouros.com

The asset name carries the tag and short commit: `eos-site-<tag>-<short sha>.tar.gz`. The
launch build, for example, was `eos-site-v2026.09.06-4a92b64.tar.gz`.

The generated release notes retain the direct extraction command:

    tar -xzf eos-site-v2026.09.06.1-*.tar.gz -C /var/www/endeavouros.com/

Use it only into an empty destination, or into a fresh directory that is then swapped
into place, as the Publish section explains; an old or unrelated file otherwise survives
extraction.

#### nginx and the webroot

`deploy/nginx-production.conf` is the production configuration. Check every `CONFIRM`
line against the host: the `server_name` values and whether www DNS points there, the
webroot, TLS certificate paths and the `arm.endeavouros.com` block. Confirm that no other
server block claims any of the names because include order decides between duplicate
claims.

The certificate must cover `endeavouros.com`, `www.endeavouros.com` and
`arm.endeavouros.com`. The www and arm names redirect over HTTPS, and nginx cannot send a
redirect until the TLS handshake succeeds. The www block's comment contains the
`certbot --expand` command. At launch the certificate lineage covered only the bare name,
so HTTPS-first browsers refused www.

As of 2026-10-04, `arm.endeavouros.com` DNS still points to the previous host and returns
the forum front page with status 200. The new host's arm blocks are not reached. First
confirm that the new certificate covers arm, then move its DNS record, then test the
redirect.

Install and test the configuration with:

    sudo cp deploy/nginx-production.conf /etc/nginx/sites-available/endeavouros.com
    sudo ln -sf /etc/nginx/sites-available/endeavouros.com /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx

It sends Content Security Policy, HSTS, `X-Content-Type-Options`, `X-Frame-Options`,
`Referrer-Policy`, `Permissions-Policy` and `Cross-Origin-Opener-Policy`. It gives
`/_astro/*` permanent caching and carries five redirects plus a 410 for
`/comments/feed/`, preserving old WordPress URLs.

Access logs remain enabled. `/privacy-policy/` promises that request logs are kept for no
more than 90 days, so the host's logrotate configuration must enforce that promise.

#### Verifying the deploy

Run the HTTP checks in the Publish section after every deploy. The arm line is expected to
fail while its 2026-10-04 DNS state remains unchanged; follow the order above to fix it.

`make spam-check` fetches the live site as a browser, as Googlebot and as a click arriving
from Google. It reports response divergence and gambling vocabulary and needs no host
access. Run it after every deploy. A clean result is not an all-clear: Google verifies
Googlebot by IP, not only by user-agent, so an external check cannot see a cloak keyed to
real crawler address ranges. Only Search Console URL Inspection settles that by showing
the crawled page.

#### PUBLIC_INDEXABLE

`PUBLIC_INDEXABLE=true` is required for production and fails silently when omitted.
Without it, every page gets `<meta name="robots" content="noindex, nofollow">` and
`robots.txt` serves `Disallow: /`. The site looks correct but is invisible to search. The
flag is unset by default so every preview build is noindex. Letting CI set it is the reason
to prefer the release tarball over a hand-built archive. The implementation is in
`astro/src/layouts/Base.astro` and `astro/src/pages/robots.txt.ts`.

#### Building by hand, if CI is unavailable

Run one command:

    PUBLIC_INDEXABLE=true make verify          # -> astro/dist/

Do not build first and call `make verify` later. `make verify` builds before running the
gate, so that sequence rebuilds without the flag and overwrites the indexable output with
a noindex build.

### Discovery repository

Discovery, the wiki, is in
`https://github.com/endeavouros-team/discovery.endeavouros.com`. It has the same layout.

### Imported news

News contains release announcements from Mercury onward. They were imported from the
WordPress REST API before the cutover. That API disappeared with the WordPress install,
so `scripts/import-news.py` can no longer fetch posts. It remains for its link-rewriting
rules and as a record of the import. Widening the archive needs another source for the
post bodies.

### Operational notes

The release runbook, preview host and search-index recovery notes live outside this
repository.
