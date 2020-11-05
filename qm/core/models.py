from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator


class TimestampMixin():
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)


class AbstractBaseModel(models.Model):
    id = fields.IntField(pk=True)

    class Meta:
        abstract = True


class RoleModel(TimestampMixin, AbstractBaseModel):
    pass


# db models finally
class Calendar(RoleModel):
    """
    The Calendar Model
    """
    google_id = fields.CharField(max_length=100, unique=True, null=False)
    webhook_channel = fields.CharField(max_length=100, null=True)
    webhook_created_at = fields.DatetimeField(null=True)

    events: fields.ReverseRelation['Event']

    class Meta:
        table = "calendars"


class Event(RoleModel):
    """
    The Event Model
    """
    google_id = fields.CharField(max_length=100, unique=True, null=False)
    open_at = fields.DatetimeField(null=False)
    created = fields.BooleanField(default=False, null=False)
    opened = fields.BooleanField(default=False, null=False)

    calendar = fields.ForeignKeyField("models.Calendar", related_name="events")

    class Meta:
        table = "events"


Calendar_Pydantic = pydantic_model_creator(Calendar, name="Calendar")
Event_Pydantic = pydantic_model_creator(Event, name='Event')
