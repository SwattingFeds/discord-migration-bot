# Discord Server Migration Bot

A small, Render-ready Discord bot that helps members voluntarily move to a new server.

## Features

- `/invite` — privately shows a destination server invite.
- `/dmoptin` — DMs the invite only to the member who ran the command.
- `/announce` — lets an administrator post a migration announcement to a configured channel.
- `/stats` — shows invite requests and announcements since the current worker started.

**Important:** Discord does not let a bot forcibly move or add members to another server. Members must choose to join using the invite link. This bot does not scrape member lists, mass-DM people, or auto-join users.

## 1. Create the Discord application

1. Open the Discord Developer Portal: https://discord.com/developers/applications
2. Create an application and add a Bot.
3. Copy the bot token. Keep it secret; never commit it or share it.
4. Under OAuth2 > URL Generator, select `bot` and `applications.commands`.
5. Grant only the permissions needed in the source server:
   - View Channels
   - Send Messages
   - Read Message History (optional)
6. Open the generated URL and add the bot to your source server.
7. Make sure the bot can view and send messages in the announcement channel.

You do not need privileged Message Content or Server Members intents for this project.

## 2. Create the destination invite

Create an invite link in the destination server and copy it. Set it as `DESTINATION_INVITE_URL` in Render.

## 3. Deploy on Render

1. Upload this project to a GitHub repository.
2. In Render, choose **New > Blueprint** and connect that repository.
3. Render will detect `render.yaml` and create a Background Worker.
4. Add the environment variables when prompted:
   - `DISCORD_TOKEN` — your bot token
   - `DESTINATION_INVITE_URL` — destination server invite
   - `ANNOUNCEMENT_CHANNEL_ID` — numeric ID of the channel for announcements
   - `ADMIN_ROLE_ID` — optional numeric ID of an admin role; use `0` to rely on Discord Administrator permission
5. Deploy. Check the worker logs for `Bot is ready`.

To copy a channel or role ID, enable Developer Mode in Discord, right-click the channel or role, and choose **Copy ID**.

## 4. Use the commands

- `/invite`
- `/dmoptin`
- `/announce message:We're moving servers!`
- `/stats`

Commands may take a short time to appear after the first startup.

## Local testing

Python 3.10+ is recommended.

```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```

Set the environment variables from `.env.example` in your shell or hosting dashboard, then run:

```bash
python bot.py
```

## Security notes

- Never put your bot token in source code, screenshots, or public repositories.
- If the token is exposed, reset it in the Discord Developer Portal immediately.
- Use a destination invite with the expiry and usage limits you want.
- Only post announcements in channels where you have permission and where members expect server updates.
