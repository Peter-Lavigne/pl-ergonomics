# pl-ergonomics

Notifications to stop staring at my screen all day.

## Setup

Runs as a systemd user service. The service file lives at `~/.config/systemd/user/ergonomics.service`.

```bash
systemctl --user daemon-reload
systemctl --user enable --now ergonomics
```

To check status or logs:

```bash
systemctl --user status ergonomics
journalctl --user -u ergonomics
```
