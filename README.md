# DB migrations

```bash
# first time
aerich init -t core.settings.TORTOISE_ORM
aerich init-db

# new versions
aerich migrate --name message
aerich upgrade
```
