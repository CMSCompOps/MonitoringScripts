

class LinkMetricsItemDto:
    """ @todo DOCUMENT! [just a dataholder for the stupid sql framework
              not to write duplicate items to local database right away] """
    
    def __init__(self, original_metrics_value, item_date, link_dto):
        self.original_metrics_value = original_metrics_value
        self.item_date = item_date
        self.link_dto = link_dto
