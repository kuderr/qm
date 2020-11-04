import sqlalchemy
from sqlalchemy import func

metadata = sqlalchemy.MetaData()


calendars_table = sqlalchemy.Table(
    "calendars",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("google_id", sqlalchemy.String(100),
                      unique=True, nullable=False),
    sqlalchemy.Column("webhook_channel", sqlalchemy.String(100),
                      unique=True),
    sqlalchemy.Column("webhook_created_at", sqlalchemy.DateTime()),

    sqlalchemy.Column("time_created", sqlalchemy.DateTime(),
                      default=func.utcnow()),
    sqlalchemy.Column("time_updated", sqlalchemy.DateTime(),
                      default=func.utcnow(), onupdate=func.utcnow()),
)


events_table = sqlalchemy.Table(
    "events",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("google_id", sqlalchemy.String(100),
                      unique=True, nullable=False),
    sqlalchemy.Column("open_at", sqlalchemy.DateTime(),
                      nullable=False),
    sqlalchemy.Column(
        "created",
        sqlalchemy.Boolean(),
        server_default=sqlalchemy.sql.expression.false(),
        nullable=False,
    ),
    sqlalchemy.Column(
        "opened",
        sqlalchemy.Boolean(),
        server_default=sqlalchemy.sql.expression.false(),
        nullable=False,
    ),
    sqlalchemy.Column(
        "calendar_id", sqlalchemy.ForeignKey(calendars_table.c.id),
        nullable=False),

    sqlalchemy.Column("time_created", sqlalchemy.DateTime(),
                      default=func.utcnow()),
    sqlalchemy.Column("time_updated", sqlalchemy.DateTime(),
                      default=func.utcnow(), onupdate=func.utcnow()),
)
