from pyramid_yosai import YosaiForm
from wtforms.ext.sqlalchemy.fields import QuerySelectField


class RxRefillForm(YosaiForm):

    @classmethod
    def with_refill_query(cls, refill_query_callback):
        field = QuerySelectField("Prescription",
                                 query_factory=refill_query_callback)
        
        cls.current_rx = field
        return cls()
