# ShadowBot - Discord Bot

This is a Discord bot, made mostly for my personal server's use.

It has a few basic utilities, and it's reasonably efficient at running them, but
it also contains a few heavier functions (blocking IO) which prevent it from being optimal for larger servers.

This is *very much* a Work in Progress.

## Docker Build:

The best way to run this bot is via Docker. 

You simply need to expose the ```/config``` directory, launch it once, then edit the config file it generates before re-running.

EG: ```docker run -d --name ShadowBot -v /config:/config shadowmoose/discord-bot```

[You can find the Docker Image here.](https://hub.docker.com/r/shadowmoose/discord-bot)
